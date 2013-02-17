import requests
from collections2 import Counter
import simplejson as json
import re


books = json.load(open("books2.json"))
color_stem = json.load(open("stemmizer_kolory.json"))
colors = json.load(open("kolory_nowe.json"))


def root_word(word, stem_dict):
    if word in stem_dict:
        return stem_dict[word]
    else:
        return word


for i, book in enumerate(books):
    if "txt" in book and book["txt"] != "":
        try:
            text = requests.get(book["txt"]).content.decode("utf-8")
        except:
            print "%s file is not working!" % book["title"]
            continue
        pos_start = text.find("\n\n\n")
        pos_end = text.find("-----\nTa lektura, podobnie jak")
        words = re.findall(ur"[\w]+", text[pos_start:pos_end].lower(), re.UNICODE)
        book["word_count"] = len(words)
        counts_all = Counter(words)
        counts_colors = {}
        total_color_count = 0
        for w, c in counts_all.items():
            word = root_word(w, color_stem)
            if word in colors:
                total_color_count += c
                if word in counts_colors:
                    counts_colors[word] += c
                else:
                    counts_colors[word] = c
        counts_colors = sorted(counts_colors.items(), key=lambda x: -x[1])
        book["color_count"] = total_color_count
        book["colors"] = [{"name": k, "count": v, "r": colors[k]["r"],
                           "g": colors[k]["g"], "b": colors[k]["b"]} for k, v in counts_colors]
        print "%d: '%s':\t %d kolorow na %d slow" % (i, book["title"], total_color_count, book["word_count"])


json.dump([book for book in books if "color_count" in book and book["color_count"]], open("colored_books.json", "w"), indent=2)
