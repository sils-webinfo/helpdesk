import rdflib
import sys
try:
    # python 2
    from urllib import urlopen
except:
    # python 3
    from urllib.request import urlopen


def is_html(representation):
    return representation.info().get(
        "content-type").startswith("text/html")


def is_json(representation):
    return representation.info().get(
        "content-type").startswith("application/json")


def show(url, in_format, out_format="turtle"):
    graph = rdflib.Graph()
    graph.parse(url, format=in_format)
    if len(graph) > 0:
        print("\nStructured data encoded as {}: {} triples found\n".format(
            in_format, len(graph)))
        graph.bind("schema", rdflib.Namespace(
            "http://schema.org/"))
        graph.bind("rdfa", rdflib.Namespace(
            "http://www.w3.org/ns/rdfa#"))
        print(graph.serialize(format=out_format).decode('utf-8'))
    else:
        print("\nNo structured data encoded as {}\n".format(in_format))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: %s URL [...]" % sys.argv[0])
        sys.exit(1)

    for url in sys.argv[1:]:
        representation = urlopen(url)
        if is_html(representation):
            for format in ("rdfa", "microdata"):
                show(url, format)
        elif is_json(representation):
            show(url, "json-ld")
        else:
            print("No structured data found.")
