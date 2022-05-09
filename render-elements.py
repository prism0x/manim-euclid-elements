import re
from manim import *
from manim_speech import VoiceoverScene
from manim_speech.interfaces.azure import AzureSpeechSynthesizer

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


def generate_scene(dict_):
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
