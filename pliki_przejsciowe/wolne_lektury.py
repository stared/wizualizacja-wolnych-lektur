import requests
import simplejson as json
from bs4 import BeautifulSoup
# from lxml import etree
# from StringIO import StringIO
import networkx

basepath = "/Users/piotrmigdal/Dropbox/Projects/Visualization/wolnelektury/"

books = json.loads(requests.get("http://wolnelektury.pl/api/books/").content)
example = "http://wolnelektury.pl/katalog/lektura/antymonachomachia/"


def extract_motifs(url):
    '''Given url of a book returns list like:
    [(u'Ksi\u0105\u017cka', 'ksiazka', 8), (u'Gniew', 'gniew', 7), ...]'''
    soup = BeautifulSoup(requests.get(url).content)
    res = []
    try:
        motlist = soup.find("div", id="theme-list-wrapper").find("ul").find_all("li")
        for el in map(lambda x: x.find("a"), motlist):
            name, count = el.string.rsplit(" ", 1)
            count = int(count[1:-1])
            code = el.get("href").split("/")[-2]
            res.append((name, code, count))
        res.sort(key=lambda x: -x[-1])
    except:
        pass
    return res

book_motifs = []
for book in books:
    res = extract_motifs(book["url"])
    print "%s (%s), motifs: %d" % (book["title"], book["author"], len(res))
    book_motifs.append({"title": book["title"], "author": book["author"],
                        "motifs": res})

json.dump(book_motifs, open(basepath + "book_motifs.json", 'w'), indent=4)

book_motifs = json.load(open(basepath + "book_motifs.json"))

motif_counts = {}
for el in book_motifs:
    for motif in el["motifs"]:
        try:
            motif_counts[motif[1]] += motif[2]
        except:
            motif_counts[motif[1]] = motif[2]

sorted(motif_counts.items(), key=lambda x: -x[1])[:10]

motif_pair_counts = {}
for el in book_motifs:
    for motif1 in el["motifs"]:
        for motif2 in el["motifs"]:
            if motif1[1] < motif2[1]:
                try:
                    motif_pair_counts[(motif1[1], motif2[1])] += motif1[2] * motif2[2]
                except:
                    motif_pair_counts[(motif1[1], motif2[1])] = motif1[2] * motif2[2]

sorted(motif_pair_counts.items(), key=lambda x: -x[1])[:10]

motif_pair_correl = {}
for el in book_motifs:
    motif_count_in_book = float(sum([motif[2] for motif in el["motifs"]]))
    for motif1 in el["motifs"]:
        for motif2 in el["motifs"]:
            if motif1[1] < motif2[1]:
                try:
                    motif_pair_correl[(motif1[1], motif2[1])] += motif1[2] * motif2[2] / motif_count_in_book
                except:
                    motif_pair_correl[(motif1[1], motif2[1])] = motif1[2] * motif2[2] / motif_count_in_book
# jeszcze nie dzielone prze sume motywow

sorted(motif_pair_correl.items(), key=lambda x: -x[1])[:10]

def oe_ratio(n, nx, ny, nxy):
    return float(n) * float(nxy) / (float(nx) * float(ny))


def calc_motif_eo(counts_dict, pair_count_dict, no_of_books, min_count=0,
                  eo_threshold=0):
    motif_eo = []
    pairs = pair_count_dict.items()
    for pair, count in pairs:
        nx = counts_dict[pair[0]]
        ny = counts_dict[pair[1]]
        eo = oe_ratio(n=no_of_books, nx=nx, ny=ny, nxy=pair_count_dict[pair])
        if nx > min_count and ny > min_count and eo > eo_threshold:
            motif_eo.append((pair, eo))
    motif_eo.sort(key=lambda x: -x[-1])
    return motif_eo


# motif_eo = calc_motif_eo(motif_counts, motif_pair_counts, len(books),
#                          min_count=200, eo_threshold=20.)

# motif_eo_200 = calc_motif_eo(motif_counts, motif_pair_counts, len(books),
#                          min_count=200, eo_threshold=0.)

total_motif_count = sum(motif_counts.values())
# 72112

# >>> len(filter(lambda x: x>200, motif_counts.values()))
# 123

motif_eo_200_t1d5 = calc_motif_eo(motif_counts, motif_pair_correl, total_motif_count,
                          min_count=200, eo_threshold=1.5)
motif_eo_more_edges = calc_motif_eo(motif_counts, motif_pair_correl, total_motif_count,
                          min_count=200, eo_threshold=1.0)

motif_eo_88_t1d5 = calc_motif_eo(motif_counts, motif_pair_correl, total_motif_count,
                          min_count=88, eo_threshold=1.5)

def associated(pair_list, motif):
    res1 = [(k[0], v) for k, v in pair_list if k[1] == motif]
    res2 = [(k[1], v) for k, v in pair_list if k[0] == motif]
    return sorted(res1 + res2, key=lambda x: -x[1])


def export2graphml(counts_list, pairs_weighted, output_path=(basepath + "wolnelektury.graphml")):
    G = networkx.Graph()
    for k, v in counts_list:
        G.add_node(k, weight=v)

    for x in pairs_weighted:
        G.add_edge(x[0][0], x[0][1], weight=x[1])

    networkx.write_graphml(G, output_path)
    print "Saved!\nNodes: %d\tEdges: %d" % (len(counts_list), len(pairs_weighted))

export2graphml(filter(lambda x: x[1] > 200, motif_counts.items()), motif_eo_200_t1d5,
    output_path=(basepath + "wolne_motywy_c200_t1d5.graphml"))

export2graphml(filter(lambda x: x[1] > 200, motif_counts.items()), motif_eo_more_edges,
    output_path=(basepath + "wolne_motywy_c200_t1d0.graphml"))

export2graphml(filter(lambda x: x[1] > 88, motif_counts.items()), motif_eo_more_edges,
    output_path=(basepath + "wolne_motywy_c88_t1d5.graphml"))

# xpathselector = '//*[@id="theme-list-wrapper"]/div/ul'

# tree = etree.parse(StringIO(requests.get(example)), etree.HTMLParser())
# x = tree.xpath(xpathselector)
