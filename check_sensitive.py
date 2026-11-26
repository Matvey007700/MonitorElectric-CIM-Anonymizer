
from lxml import etree

SENSITIVE = (
    "address", "street", "city", "phone", "email",
    "passport", "taxid", "inn", "kpp", "account",
    "contract", "employee", "firstname", "lastname",
    "middlename", "surname", "personnel", "comment",
    "description", "contact", "serialnumber", "inventory"
)

def audit():
    original = etree.iterparse(
        "input.xml", events=("end",), huge_tree=True
    )
    anonymized = etree.iterparse(
        "output_anonymized.xml", events=("end",), huge_tree=True
    )

    checked = 0
    unchanged = 0
    total_elements = 0

    print("Сравниваем поля исходной и новой модели...")

    for (event1, a), (event2, b) in zip(original, anonymized):
        total_elements += 1
        name = a.tag.split("}")[-1].lower()

        if any(word in name for word in SENSITIVE) or name == "name" or name.endswith(".name"):
            if a.text and a.text.strip():
                checked += 1
                if a.text == b.text:
                    unchanged += 1

        a.clear()
        b.clear()

        pa = a.getparent()
        pb = b.getparent()

        if pa is not None:
            while a.getprevious() is not None:
                del pa[0]

        if pb is not None:
            while b.getprevious() is not None:
                del pb[0]

    print("\n========== РЕЗУЛЬТАТ ==========")
    print("Проверено полей:", checked)
    print("Не изменено:", unchanged)
    print("Элементов XML:", total_elements)

    if unchanged == 0:
        print("Все проверенные поля изменены.")
    else:
        print("ВНИМАНИЕ: найдены неизменённые поля.")

audit()
