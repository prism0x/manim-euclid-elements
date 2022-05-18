from copy import deepcopy
from curses.ascii import DEL
import re
from manim import *
from manim_speech import VoiceoverScene
from manim_speech.interfaces.azure import AzureSpeechSynthesizer
from math import floor, ceil
import json
import manimpango
from numpy import poly

# dict1 = json.loads(open("book-01-proposition-47-short.json").read())
# dict1 = json.loads(open("book-01-proposition-47.json").read())

# GLOBAL_SPEED = 1.15
# AUDIO_OFFSET = 0.0

GLOBAL_SPEED = 1
AUDIO_OFFSET = 0.0
BASE_SHAPE_COLOR = GRAY_D
BASE_DOT_COLOR = GRAY_C
BASE_TEXT_COLOR = GRAY_C

HIGHLIGHT_COLOR = YELLOW_B


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

    def label_length(self):
        tokens = self.tag.split()
        type_ = tokens[0]

        if type_ == "circle:":
            return len(tokens[2])
        else:
            return len(tokens[1])


class Section:
    def __init__(
        self, text, duration, text_offset, appearing_shapes, disappearing_shapes
    ):
        self.duration = duration
        self.text = text
        self.text_offset = text_offset
        self.appearing_shapes = appearing_shapes
        self.disappearing_shapes = disappearing_shapes

    def __repr__(self):
        return (
            "<section: %s, duration: %.3f, text_offset: %d, appearing: %s, disappearing: %s>"
            % (
                self.text,
                self.duration,
                self.text_offset,
                str(self.appearing_shapes),
                str(self.disappearing_shapes),
            )
        )


def reformat_prose(prose: str):
    def get_letters_from_tag(tag: str):
        tokens = tag.split(" ")
        type_ = tokens[0]
        if type_ == "circle":
            return tokens[2]
        else:
            return tokens[1]

    result = re.sub("[^\S\n\t]+\[Prop.*\]\.", ".", prose)
    result = re.sub("\[Prop.*\]", "", result)
    result = (
        result.replace(")", "")
        .replace("(", "")
        .replace("]", "")
        .replace("[", "")
        .replace("{", r'<say-as interpret-as="characters">{')
        .replace("}", r"}</say-as>")
        # .replace("{", r'<say-as interpret-as="characters">{')
        # .replace(" point}", r" point}</say-as>")
        # .replace(" line}", r" line}</say-as>")
        # .replace(" angle}", r" angle}</say-as>")
        # .replace(" polygon}", r" polygon}</say-as>")
    )

    tag_count = 1
    bookmarks = []
    tag_replaced = ""
    offset = 0
    # extra_char_count = 0
    while offset < len(result):
        char = result[offset]
        if char == "{":
            tag = result[offset + 1 :].split("}")[0]
            # tag = tag.replace(" ", "-")
            # tag = "%d-" % (tag_count) + tag
            letters = get_letters_from_tag(tag)
            # bookmarks.append(Bookmark(tag_count, tag, len(tag_replaced)-extra_char_count))
            # tag_replaced += '<say-as interpret-as="characters">' + letters + "</say-as>"
            bookmarks.append(Bookmark(tag_count, tag, len(tag_replaced)))
            tag_replaced += letters
            # extra_char_count += len('<say-as interpret-as="characters">'+"</say-as>")
            tag_count += 1
            offset += len(tag) + 1
        elif char == "}":
            offset += 1
        else:
            tag_replaced += char
            offset += 1

    # print(bookmarks)
    # print(tag_replaced)

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
        transform_[1] -= 0.3
        return np.array(transform_ + [0])

    if isinstance(mode, float):
        # transform_ = (proj(ceil(mode), l) + proj(floor(mode), l)) / 2
        a = proj(ceil(mode), l)
        b = proj(floor(mode), l)
        t = mode - floor(mode)
        transform_ = b + (a - b) * t
    else:
        transform_ = proj(mode, l)

    transform_[0] *= size[0]
    transform_[1] *= -1 * size[1]

    return np.array(coor + [0]) + transform_


colors = [
    BLUE_B,
    # TEAL_B,
    # GREEN_B,
    YELLOW_B,
    # GOLD_B,
    # RED_B,
    MAROON_B,
    # PURPLE_B,
]
current_color_count = 0


def get_angle(p1, p2, p3):
    v1 = p1 - p2
    v2 = p3 - p2

    unit_v1 = v1 / np.linalg.norm(v1)
    unit_v2 = v2 / np.linalg.norm(v2)
    dot_product = np.dot(unit_v1, unit_v2)
    angle = np.arccos(dot_product)
    return angle


def get_shape_animations(dict_, tag: str, point_labels):
    global current_color_count
    # letters, type_ = tag.split(" ")
    tokens = tag.split(" ")
    type_ = tokens[0]
    letters = tokens[1]
    current_color = colors[current_color_count % len(colors)]
    current_color_count += 1

    if type_ == "point":
        point = dict_["points"][letters[0]]
        obj = Dot(point).set_fill(current_color)
    elif type_ == "line":
        points = [dict_["points"][i] for i in letters]
        obj = Line(start=points[0], end=points[1]).set_color(current_color)
    elif type_ == "polygon":
        if letters in dict_["polygonl"]:
            letters = dict_["polygonl"][letters]
        points = [dict_["points"][i] for i in letters]
        obj = (
            Polygon(*points)
            .set_color(current_color)
            .set_fill(current_color, opacity=0.75)
        )
    elif type_ == "angle":
        points = [dict_["points"][i] for i in letters]
        angle = get_angle(*points)
        v1 = points[2] - points[1]
        v2 = points[0] - points[1]

        radius = min(np.linalg.norm(v1), np.linalg.norm(v2)) * 0.2
        points = [dict_["points"][i] for i in letters]
        line1 = Line(start=points[0], end=points[1]).set_color(current_color)
        line2 = Line(start=points[1], end=points[2]).set_color(current_color)

        if abs(angle - np.pi / 2) < 1e-9:
            p1 = points[1]
            v1_ = radius / np.linalg.norm(v1) * v1
            v2_ = radius / np.linalg.norm(v2) * v2

            polygon_points = [p1, p1 + v1_, p1 + v1_ + v2_, p1 + v2_]
            angle_obj = (
                Polygon(*polygon_points)
                .set_color(current_color)
                .set_fill(current_color, opacity=0.75)
            )
        else:
            intersectee = (
                Polygon(*points)
                .set_color(current_color)
                .set_fill(current_color, opacity=0.75)
            )
            circle = Circle(radius=radius).move_to(points[1])

            angle_obj = (
                Intersection(circle, intersectee)
                .set_color(current_color)
                .set_fill(current_color, opacity=0.75)
            )
            # obj = VGroup(
            #     Line(start=points[0], end=points[1]).set_color(current_color),
            #     Line(start=points[1], end=points[2]).set_color(current_color),
            # )
        obj = VGroup(VGroup(line1, line2), angle_obj)
        # return Write(obj), FadeOut(obj)
    elif type_ == "circle":
        # if letters in dict_["polygonl"]:
        #     letters = dict_["polygonl"][letters]
        letters = tokens[2]
        points = [dict_["points"][i] for i in letters]
        center = dict_["points"][tokens[1]]
        radius = np.linalg.norm(center - points[0])
        obj = (
            Circle(radius=radius)
            .move_to(center)
            .set_color(current_color)
            .set_fill(current_color, opacity=0.75)
        )
    else:
        raise Exception(type_)

    copy_letters = [
        point_labels[l].copy().set_fill(current_color)
        for l in letters
        if l in point_labels
    ]
    letters_highlight = AnimationGroup(*[FadeIn(i) for i in copy_letters], lag_ratio=1)
    letters_unhighlight = AnimationGroup(
        *[FadeOut(i) for i in copy_letters],
    )
    anim_in = AnimationGroup(Write(obj), letters_highlight)
    anim_out = AnimationGroup(FadeOut(obj), letters_unhighlight)

    return anim_in, anim_out


def generate_scene(
    dict_,
    figure_buff=0.4,
    dot_radius=0.03,
    point_label_font_size=30,
    stroke_width=2,
    name=None,
):
    class MyScene(VoiceoverScene):
        def construct(self):
            self.init_voiceover(
                AzureSpeechSynthesizer(
                    voice="en-US-AriaNeural",
                    style="newscast-casual",
                    global_speed=GLOBAL_SPEED
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

            # Transform all coors
            for label, coor in dict_["points"].items():
                dict_["points"][label] = transform_coors(coor + [0])

            for arr in dict_["shapes"]:
                type_ = arr[0]
                if type_ == "line":
                    arr[1] = transform_coors(arr[1] + [0])
                    arr[2] = transform_coors(arr[2] + [0])
                elif type_ == "polygon":
                    arr[1] = [transform_coors(i + [0]) for i in arr[1]]
                elif type_ == "circle":
                    arr[1] = transform_coors(arr[1] + [0])
                    arr[2] *= coors_scale
                elif type_ == "arc":
                    arr[1] = transform_coors(arr[1] + [0])
                    arr[2] = transform_coors(arr[2] + [0])
                    arr[3] = transform_coors(arr[3] + [0])
                else:
                    raise Exception("Unkown shape type: " + type_)

            # Create points
            self.points = {
                label: Dot(radius=dot_radius).set_fill(BASE_DOT_COLOR).move_to(coor)
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
                    color=BASE_TEXT_COLOR,
                )
                for label, _ in dict_["letters"].items()
            }

            # Transpose labels
            for label, point_label in self.point_labels.items():
                self.point_labels[label] = point_label.move_to(
                    # self.points[label].get_center(),
                    transpose_label(
                        self.points[label].get_center(),
                        dict_["letters"][label],
                        [point_label.width, point_label.height],
                    )
                )

            self.static_shapes = []
            for shape in dict_["shapes"]:
                type_ = shape[0]
                if type_ == "line":
                    points = shape[1:]
                    obj = Line(
                        start=points[0],
                        end=points[1],
                        stroke_width=stroke_width,
                    ).set_color(BASE_SHAPE_COLOR)
                elif type_ == "polygon":
                    points = shape[1]
                    obj = Polygon(*points, stroke_width=stroke_width).set_color(
                        BASE_SHAPE_COLOR
                    )
                elif type_ == "circle":
                    center = shape[1]
                    radius = shape[2] / 2
                    obj = (
                        Circle(radius, stroke_width=stroke_width)
                        .move_to(center)
                        .set_color(BASE_SHAPE_COLOR)
                    )
                elif type_ == "arc":
                    center = shape[1]
                    to = shape[2]
                    from_ = shape[3]
                    radius = np.linalg.norm(from_ - center)
                    obj = ArcBetweenPoints(
                        start=from_,
                        end=to,
                        radius=radius,
                        stroke_width=stroke_width,
                    ).set_color(BASE_SHAPE_COLOR)

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

            self.wait(0.5)

            for line in lines:
                voiceover_txt, bookmarks = reformat_prose(line)
                if "Prop" in "voiceover_txt":
                    raise Exception()

                print(line)
                print(">> ", voiceover_txt)

                with self.voiceover(text=voiceover_txt) as tracker:
                    prev_offset = 0
                    text2 = None
                    self.safe_wait(AUDIO_OFFSET)
                    anim_in = None
                    prev_anim_out = None

                    word_boundaries = deepcopy(tracker.data["word_boundaries"])

                    current_text_offset = 0
                    current_audio_offset = 0
                    current_word = ""
                    bookmark_remaining = -1

                    bookmarks_dict = {}
                    sections = []

                    for b in bookmarks:
                        bookmarks_dict[b.text_offset] = b
                    last_text_offset = 0
                    current_bookmark = None
                    prev_bookmark = None

                    while len(word_boundaries) > 0:
                        wb = word_boundaries.pop(0)

                        if wb["text_offset"] in bookmarks_dict:
                            current_bookmark = bookmarks_dict[wb["text_offset"]]
                            bookmark_remaining = current_bookmark.label_length()
                            last_text_offset = wb["text_offset"]

                        current_audio_offset += (
                            wb["audio_offset"] - prev_offset
                        ) / 10000000

                        current_text_offset = wb["text_offset"]
                        current_word += wb["text"]
                        # print(
                        #     wb["text_offset"], bookmark_remaining, current_text_offset
                        # )

                        if (
                            bookmark_remaining
                            - (current_text_offset - last_text_offset + 1)
                            <= 0
                        ):
                            current_tag = []
                            prev_tag = []
                            if (
                                current_bookmark is not None
                                and prev_bookmark is not None
                            ):
                                prev_tag = [prev_bookmark.tag]

                            if current_bookmark is not None:
                                current_tag = [current_bookmark.tag]
                                prev_bookmark = current_bookmark
                                current_bookmark = None

                            # print(current_bookmark, prev_bookmark)
                            sections.append(
                                Section(
                                    current_word,
                                    current_audio_offset,
                                    current_text_offset,
                                    current_tag,
                                    prev_tag,
                                )
                            )
                            # audio_offset_arr.append(current_audio_offset)
                            # text_offset_arr.append(current_text_offset)
                            # word_arr.append(current_word)

                            bookmark_remaining = 0
                            current_text_offset = 0
                            current_audio_offset = 0
                            current_word = ""

                        # bookmark_remaining -= 1

                        prev_offset = wb["audio_offset"]
                        # prev_text_offset = wb["text_offset"]

                    # audio_offset_arr = [AUDIO_OFFSET + i for i in audio_offset_arr]

                    for i in range(len(sections) - 1):
                        if (
                            sections[i + 1].appearing_shapes != []
                            and sections[i + 1].disappearing_shapes != []
                        ):
                            sections[i].disappearing_shapes.extend(
                                sections[i + 1].disappearing_shapes
                            )
                            sections[i + 1].disappearing_shapes = []

                    for s in sections:
                        if len(s.appearing_shapes) == 0:
                            self.safe_wait(s.duration)
                        else:
                            anim_in, anim_out = get_shape_animations(
                                dict_, s.appearing_shapes[0], self.point_labels
                            )

                            if prev_anim_out is None:
                                self.play(anim_in, run_time=s.duration)
                            else:
                                self.play(prev_anim_out, anim_in, run_time=s.duration)
                                prev_anim_out = None
                            prev_anim_out = anim_out

                        if text2 is not None:
                            self.remove(text2)
                        text2 = Text(s.text).shift(3.3 * DOWN)
                        self.add(text2)

                    if prev_anim_out is not None:
                        self.play(prev_anim_out)
                    self.wait()

                if text2 is not None:
                    self.remove(text2)

    if name is not None:
        MyScene.__name__ = name
    return MyScene()


config["disable_caching"] = True
config["quality"] = "low_quality"
# import ipdb; ipdb.set_trace()

scene1 = generate_scene(
    # json.loads(open("book-01-proposition-47.json").read()), name="B01P47"
    json.loads(open("book-03-proposition-02.json").read()),
    name="B03P02",
)
scene1.render()
