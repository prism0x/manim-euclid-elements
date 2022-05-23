import json
from manim import *
from proposition import generate_scene

config["disable_caching"] = True
config["quality"] = "low_quality"

books = [
    # "elements-data/data/book-01.json",
    "elements-data/data/book-02.json",
    # "elements-data/data/book-03.json",
    # "elements-data/data/book-04.json",
    # "elements-data/data/book-05.json",
    # "elements-data/data/book-06.json",
    # "elements-data/data/book-07.json",
    # "elements-data/data/book-08.json",
    # "elements-data/data/book-09.json",
    # "elements-data/data/book-10.json",
    # "elements-data/data/book-11.json",
    # "elements-data/data/book-12.json",
    # "elements-data/data/book-13.json",
]

book_dicts = [json.loads(open(i).read()) for i in books]

for path in books:
    book_dict = json.loads(open(path).read())
    # book_dict = [book_dict[4]]
    basename = os.path.basename(path).split(".")[0]
    for prop_dict in book_dict:
        title = prop_dict["title"]
        if "Proposition" not in title:
            continue
        prop_count = int(title.split()[1])
        title = "Proposition-%02d" % (prop_count)
        name = "Book-%s-%s" % (basename, title)
        print("\n\nRendering %s into %s\n\n" % (title, name))
        scene = generate_scene(
            prop_dict,
            name=name,
        )
        scene().render()
        config["output_file"] = None
