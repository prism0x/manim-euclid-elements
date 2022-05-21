import json
from manim import *
from proposition import generate_scene

config["disable_caching"] = True
# config["quality"] = "low_quality"

book1_dict = json.loads(open("elements-data/data/01.json").read())

for prop_dict in book1_dict:
    title = prop_dict["title"]
    if "Proposition" not in title:
        continue
    prop_count = int(title.split()[1])
    title = "Proposition-%02d"%(prop_count)
    name = "Book-01-%s"%(title)
    print("\n\nRendering %s into %s\n\n"%(title, name))
    scene = generate_scene(
        prop_dict,
        name=name,
    )
    # import ipdb; ipdb.set_trace()
    scene().render()
    config["output_file"] = None
