
from lxml import etree
from collections import Counter

ABOUT = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"

def check(filename):
    classes = Counter()
    ids = set()
    duplicates = 0

    print("Проверяется:", filename)

    for _, elem in etree.iterparse(
        filename, events=("end",), huge_tree=True
    ):
        if ABOUT in elem.attrib:
            classes[elem.tag.split("}")[-1]] += 1

            obj_id = elem.attrib[ABOUT]
            if obj_id in ids:
                duplicates += 1
            ids.add(obj_id)

        parent = elem.getparent()
        elem.clear()

        if parent is not None:
            while elem.getprevious() is not None:
                del parent[0]

    return classes, duplicates


original, dup1 = check("input.xml")
result, dup2 = check("output_anonymized.xml")

print("\n========== РЕЗУЛЬТАТ ==========")
print("Количество типов объектов:", len(original), len(result))
print("Распределение совпадает:", original == result)
print("Дубликаты исходного XML:", dup1)
print("Дубликаты нового XML:", dup2)
