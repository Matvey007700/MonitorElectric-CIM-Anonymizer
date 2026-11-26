from lxml import etree

RDF_ABOUT = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"
RDF_RESOURCE = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"


def check_file(filename):
    objects = 0
    references = 0

    print("Проверяется:", filename)

    for _, elem in etree.iterparse(
        filename, events=("end",), huge_tree=True
    ):
        if RDF_ABOUT in elem.attrib:
            objects += 1

        if RDF_RESOURCE in elem.attrib:
            references += 1

        parent = elem.getparent()
        elem.clear()

        if parent is not None:
            while elem.getprevious() is not None:
                del parent[0]

    print("Объектов:", objects)
    print("Ссылок:", references)

    return objects, references


original = check_file("input.xml")
result = check_file("output_anonymized.xml")

print("\n========== РЕЗУЛЬТАТ ==========")
print("Объекты совпадают:", original[0] == result[0])
print("Ссылки совпадают:", original[1] == result[1])
