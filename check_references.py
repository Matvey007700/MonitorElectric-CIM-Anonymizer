
from lxml import etree

ABOUT = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"
RESOURCE = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"

filename = "output_anonymized.xml"

# Собираем идентификаторы всех объектов
objects = set()

print("Шаг 1. Собираем объекты...")

for _, elem in etree.iterparse(
    filename, events=("end",), huge_tree=True
):
    if ABOUT in elem.attrib:
        objects.add(elem.attrib[ABOUT])

    parent = elem.getparent()
    elem.clear()
    if parent is not None:
        while elem.getprevious() is not None:
            del parent[0]

print("Найдено объектов:", len(objects))

# Проверяем внутренние ссылки
print("\nШаг 2. Проверяем ссылки...")

total = 0
missing = 0

for _, elem in etree.iterparse(
    filename, events=("end",), huge_tree=True
):
    if RESOURCE in elem.attrib:
        ref = elem.attrib[RESOURCE]

        if ref.startswith("#"):
            total += 1
            if ref not in objects:
                missing += 1

    parent = elem.getparent()
    elem.clear()
    if parent is not None:
        while elem.getprevious() is not None:
            del parent[0]

print("\n========== РЕЗУЛЬТАТ ==========")
print("Внутренних ссылок:", total)
print("Не найдено объектов:", missing)

if missing == 0:
    print("ВСЕ ВНУТРЕННИЕ ССЫЛКИ НАЙДЕНЫ")
else:
    print("ОБНАРУЖЕНЫ ОТСУТСТВУЮЩИЕ ОБЪЕКТЫ")
