import re
from manim import *
from manim_speech import VoiceoverScene
from manim_speech.interfaces.azure import AzureSpeechSynthesizer
from math import floor, ceil
import json

dict1 = json.loads(open("book-01-proposition-47.json").read())


def reformat_prose(prose: str):
    result = re.sub("[^\S\n\t]+\[Prop.*\]\.", ".", prose)
    result = re.sub("\[Prop.*\]", "", result)
    result = (
        result.replace("{", "")
        .replace(")", "")
        .replace("(", "")
        .replace("]", "")
        .replace("[", "")
        .replace(" point}", "")
        .replace(" line}", "")
        .replace(" angle}", "")
        .replace(" polygon}", "")
    )

    return result


def transpose_label(coor, arr, size):
    mode = (arr[0] + 8) % 8

    if len(arr) == 1:
        l = 3
    else:
        l = arr[1] * 3

    def proj(mode, l):
        if mode == 0:
            transform_ = [0.1 * l, -0.1 * l]
        elif mode == 1:
            transform_ = [-0.5, -0.2 * l]
        elif mode == 2:
            transform_ = [-1 - 0.2 * l, -0.2 * l]
        elif mode == 3:
            transform_ = [-1 - 0.2 * l, 0.5]
        elif mode == 4:
            transform_ = [-1, 1]
        elif mode == 5:
            transform_ = [-0.5, 1 + 0.1 * l]
        elif mode == 6:
            transform_ = [0.3 * l, 0.9 + 0.1 * l]
        elif mode == 7:
            transform_ = [0.2 * l, 0.5]
        else:
            transform_ = [0.1 * l, -0.1 * l]
        transform_[0] += 0.5
        return np.array(transform_ + [0])

    if isinstance(mode, float):
        transform_ = (proj(ceil(mode), l) + proj(floor(mode), l)) / 2
    else:
        transform_ = proj(mode, l)

    transform_[0] *= size[0]
    transform_[1] *= -1 * size[1]

    return np.array(coor + [0]) + transform_


def generate_scene(
    dict_, figure_buff=0.2, dot_radius=0.05, point_label_font_size=30, stroke_width=2
):
    class MyScene(VoiceoverScene):
        def construct(self):
            self.init_voiceover(
                AzureSpeechSynthesizer(
                    voice="en-US-AriaNeural",
                    style="newscast-casual",
                    global_speed=1.15
                    # voice="en-US-BrandonNeural", global_speed=1.15
                )
            )
            x_coors = [coor[0] for _, coor in dict_["points"].items()]
            y_coors = [coor[1] for _, coor in dict_["points"].items()]

            xmin = min(x_coors)
            xmax = max(x_coors)
            ymin = min(y_coors)
            ymax = max(y_coors)
            xscale = (1 - figure_buff) * config["frame_width"] / (xmax - xmin)
            yscale = (1 - figure_buff) * config["frame_height"] / (ymax - ymin)
            coors_center = np.array(((xmax + xmin) / 2, (ymax + ymin) / 2, 0.0))
            coors_scale = min(xscale, yscale)

            def transform_coors(coor):
                if not isinstance(coor, np.ndarray):
                    coor = np.array(coor)
                result = coors_scale * (coor - coors_center)
                result[1] *= -1
                return result

            # Create points
            self.points = {
                label: Dot(radius=dot_radius).move_to(transform_coors(coor + [0]))
                for label, coor in dict_["points"].items()
            }

            # Create point labels
            self.point_labels = {
                label: Tex(label, font_size=point_label_font_size)
                for label, _ in dict_["letters"].items()
            }

            # Transpose labels
            for label, point_label in self.point_labels.items():
                self.point_labels[label] = point_label.move_to(
                    transpose_label(
                        self.points[label].get_center(),
                        dict_["letters"][label],
                        [point_label.width, point_label.height],
                    )
                )

            self.static_shapes = []
            for shape in dict_["shapes"]:
                # type, points
                type_ = shape[0]
                if type_ == "line":
                    points = shape[1:]
                    obj = Line(
                        start=transform_coors(points[0] + [0]),
                        end=transform_coors(points[1] + [0]),
                        stroke_width=stroke_width,
                    )
                elif type_ == "polygon":
                    points = shape[1]
                    obj = Polygon(
                        *[transform_coors(i + [0]) for i in points],
                        stroke_width=stroke_width
                    )
                else:
                    raise Exception("Unkown shape type: " + type_)
                self.static_shapes.append(obj)

            # Add shapes
            for obj in self.static_shapes:
                self.add(obj)

            # Add points
            for _, point in self.points.items():
                self.add(point)
            # Add point labels
            for _, point_label in self.point_labels.items():
                self.add(point_label)

            prose: str = dict_["prose"]
            lines = prose.split("\n")
            lines = [i for i in lines if i != ""]

            for line in lines:
                voiceover_txt = reformat_prose(line)
                if "Prop" in "voiceover_txt":
                    raise Exception()
                print(line)
                print(">> ", voiceover_txt)
                with self.voiceover(text=voiceover_txt):
                    pass

                self.wait()

    return MyScene()


config["disable_caching"] = True
config["quality"] = "low_quality"
# import ipdb; ipdb.set_trace()

scene1 = generate_scene(dict1)
scene1.render()
