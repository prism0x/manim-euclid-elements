import re
from manim import *
from manim_speech import VoiceoverScene
from manim_speech.interfaces.azure import AzureSpeechSynthesizer
from math import floor, ceil
import json
import manimpango

dict1 = json.loads(open("book-01-proposition-47.json").read())


class Bookmark:
    def __init__(self, tag_count, tag, text_offset):
        self.tag_count = tag_count
        self.tag = tag
        self.text_offset = text_offset

    def __repr__(self):
        return "<bookmark: %d, tag: %s, text_offset: %s>" % (
            self.tag_count,
            self.tag,
            self.text_offset,
        )


def reformat_prose(prose: str):
    result = re.sub("[^\S\n\t]+\[Prop.*\]\.", ".", prose)
    result = re.sub("\[Prop.*\]", "", result)
    result = (
        result.replace("{", r'<say-as interpret-as="characters">{')
        .replace(")", "")
        .replace("(", "")
        .replace("]", "")
        .replace("[", "")
        .replace(" point}", r" point}</say-as>")
        .replace(" line}", r" line}</say-as>")
        .replace(" angle}", r" angle}</say-as>")
        .replace(" polygon}", r" polygon}</say-as>")
    )

    tag_count = 1
    bookmarks = []
    tag_replaced = ""
    offset = 0
    while offset < len(result):
        char = result[offset]
        if char == "{":
            tag = result[offset + 1 :].split("}")[0]
            # tag = tag.replace(" ", "-")
            # tag = "%d-" % (tag_count) + tag
            bookmarks.append(Bookmark(tag_count, tag, len(tag_replaced)))
            tag_replaced += tag.split()[0]
            tag_count += 1
            offset += len(tag) + 1
        elif char == "}":
            offset += 1
        else:
            tag_replaced += char
            offset += 1

    # print(bookmarks)
    # print(tag_replaced)
    # import ipdb; ipdb.set_trace()

    return tag_replaced, bookmarks


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
    dict_, figure_buff=0.4, dot_radius=0.05, point_label_font_size=30, stroke_width=2
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
                if label in dict_["letters"]
            }

            # Create point labels
            self.point_labels = {
                label: Text(
                    label,
                    font_size=point_label_font_size,
                    weight=manimpango.Weight.HEAVY.name,
                    font="Open Sans",
                )
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
                voiceover_txt, bookmarks = reformat_prose(line)
                if "Prop" in "voiceover_txt":
                    raise Exception()
                print(line)
                print(">> ", voiceover_txt)
                with self.voiceover(text=voiceover_txt) as tracker:
                    prev_offset = 0
                    # import ipdb; ipdb.set_trace()
                    text = None
                    for word_boundary in tracker.data["word_boundaries"]:
                        duration = (
                            word_boundary["audio_offset"] - prev_offset
                        ) / 10000000
                        self.wait(duration)
                        if text is not None:
                            self.remove(text)
                        text = Text(word_boundary["text"])
                        self.add(text)
                        prev_offset = word_boundary["audio_offset"]
                    self.remove(text)
                self.wait()

    return MyScene()


config["disable_caching"] = True
# config["quality"] = "low_quality"
# import ipdb; ipdb.set_trace()

scene1 = generate_scene(dict1)
scene1.render()
