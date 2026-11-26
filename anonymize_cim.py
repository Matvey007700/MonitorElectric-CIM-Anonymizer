#!/usr/bin/env python3
"""Streaming deterministic anonymizer for CIM RDF/XML models.

Usage: python anonymize_cim.py input.xml output_anonymized.xml
Requires: lxml (pip install lxml)
"""
import sys, re, hashlib, uuid, json, os
from lxml import etree

RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
ABOUT = '{%s}about' % RDF
RESOURCE = '{%s}resource' % RDF
NS = uuid.UUID('4a4c7c48-2d0c-5dbe-8e39-6a76d911b9aa')

def digest(value, n=12):
    return hashlib.sha256(value.encode('utf-8', 'replace')).hexdigest()[:n].upper()

def fake_uuid(value):
    return str(uuid.uuid5(NS, value))

def fake_digits(value):
    h = hashlib.sha256(value.encode('utf-8', 'replace')).hexdigest()
    out = ''.join(str(int(c, 16) % 10) for c in h)
    return (out * ((len(value) // len(out)) + 1))[:len(value)]

def anon_rdf_id(value):
    if value.startswith('#'):
        raw = value[1:]
        # Keep URI fragment shape predictable; UUID-like identifiers stay UUID-like.
        if re.fullmatch(r'_?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', raw):
            prefix = '_' if raw.startswith('_') else ''
            return '#' + prefix + fake_uuid(raw.lstrip('_'))
        return '#anon_' + digest(raw, 24)
    return value

def class_label(local):
    low = local.lower()
    if 'substation' in low: return 'ПС'
    if 'transformer' in low: return 'ТП'
    if 'line' in low: return 'ЛЭП'
    if 'customer' in low or 'usagepoint' in low: return 'Абонент'
    if 'person' in low or 'employee' in low: return 'Сотрудник'
    if 'organisation' in low or 'organization' in low: return 'Организация'
    if 'pole' in low: return 'Опора'
    if 'breaker' in low or 'switch' in low: return 'Коммутационный аппарат'
    return 'Объект'

SENSITIVE = ('address','street','city','postal','phone','telephone','mobile','email','mail',
             'passport','taxid','inn','kpp','account','contract','personnel','employee',
             'firstname','lastname','middlename','surname','serialnumber','inventory',
             'comment','attachment','log','latitude','longitude','coordinate','longitude',
             'description','fullname','contact')

def transform_element(el, stats):
    local_class = el.tag.split('}')[-1]
    obj_id = el.get(ABOUT)
    if obj_id:
        el.set(ABOUT, anon_rdf_id(obj_id))
        stats['objects'] += 1
    for node in el.iter():
        # Rewrite internal RDF links only; external QName references are left intact.
        ref = node.get(RESOURCE)
        if ref and ref.startswith('#'):
            node.set(RESOURCE, anon_rdf_id(ref))
            stats['references'] += 1
        prop = node.tag.split('}')[-1]
        low = prop.lower()
        text = node.text
        if not text or not text.strip():
            continue
        value = text.strip()
        if prop.endswith('.name') or prop == 'name':
            node.text = f'{class_label(local_class)}-{digest((obj_id or "") + "|" + value, 10)}'
            stats['names'] += 1
        elif prop.endswith('.mRIDStr'):
            # Keep system prefixes (e.g. sk_line_) and replace the identifying suffix.
            m = re.match(r'^(.*?)(\d+)$', value)
            node.text = (m.group(1) + fake_digits(m.group(2))) if m else 'anon_' + digest(value, 16)
            stats['identifiers'] += 1
        elif prop.endswith('.mRID') and re.fullmatch(r'[0-9a-fA-F-]{32,36}', value):
            node.text = fake_uuid(value)
            stats['identifiers'] += 1
        elif any(k in low for k in SENSITIVE):
            if 'latitude' in low or 'longitude' in low or 'coordinate' in low:
                h = hashlib.sha256(value.encode()).hexdigest()
                # Deterministic synthetic coordinates unrelated to the source location.
                num = int(h[:12], 16) / float(16**12 - 1)
                node.text = f'{(num * 160 - 80):.6f}' if 'latitude' in low else f'{(num * 340 - 170):.6f}'
            elif value.isdigit():
                node.text = fake_digits(value)
            else:
                node.text = 'Обезличено-' + digest(value, 10)
            stats['sensitive_fields'] += 1

def main(src, dst):
    stats = {'objects':0,'references':0,'names':0,'identifiers':0,'sensitive_fields':0}
    context = etree.iterparse(src, events=('start','end'), huge_tree=True, resolve_entities=False, no_network=True)
    depth = 0
    root_started = False
    with etree.xmlfile(dst, encoding='utf-8', buffered=True) as xf:
        xf.write_declaration()
        writer = None
        for event, el in context:
            if event == 'start':
                depth += 1
                if depth == 1:
                    root_started = True
                    writer = xf.element(el.tag, el.attrib, nsmap=el.nsmap)
                    writer.__enter__()
                continue
            if depth == 2:
                transform_element(el, stats)
                xf.write(el)
                el.clear()
                while el.getprevious() is not None:
                    del el.getparent()[0]
            elif depth > 2:
                # child elements are retained until their direct RDF object is emitted
                pass
            elif depth == 1:
                if writer is not None:
                    writer.__exit__(None, None, None)
            depth -= 1
    with open(dst + '.report.json','w',encoding='utf-8') as f:
        json.dump({'input':os.path.basename(src),'output':os.path.basename(dst),'counts':stats,
                   'note':'Internal rdf:about/rdf:resource links were rewritten consistently. Verify domain-specific fields before production use.'},f,ensure_ascii=False,indent=2)
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python anonymize_cim.py input.xml output_anonymized.xml')
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2])
