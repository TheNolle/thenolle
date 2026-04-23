import os, json, re
from lxml import etree

TEMPLATE = 'src/about.svg.template'
OUTPUT = 'images/about.svg'
ABOUT_FILE = 'about/about.json'

PLACEHOLDER_MAP = {
    '{{FOLLOWERS}}':     'followers',
    '{{REPOSITORIES}}':  'repositories',
    '{{STARS}}':         'stars',
    '{{CONTRIBUTIONS}}': 'contributions',
}

def load_data() -> dict:
    if not os.path.exists(ABOUT_FILE):
        print(f'Warning: {ABOUT_FILE} not found - all values will be 0')
        return {k: 0 for k in PLACEHOLDER_MAP.values()}
    with open(ABOUT_FILE) as f:
        return json.load(f)

def apply_placeholder(root: etree._Element, placeholder: str, value: str) -> None:
    for element in root.iter():
        if element.text and placeholder in element.text:
            element.text = element.text.replace(placeholder, value)
            print(f'Replaced {placeholder} -> "{value}"')
        if element.tail and placeholder in element.tail:
            element.tail = element.tail.replace(placeholder, value)
        for attr, attr_value in list(element.attrib.items()):
            if placeholder in attr_value:
                element.set(attr, attr_value.replace(placeholder, value))
                print(f'Replaced attr {attr}: {placeholder} -> "{value}"')

def inject() -> None:
    data = load_data()
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.parse(TEMPLATE, parser).getroot()
    for placeholder, key in PLACEHOLDER_MAP.items():
        value = str(data.get(key, 0))
        apply_placeholder(root, placeholder, value)
    etree.ElementTree(root).write(OUTPUT, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    print(f'\nDone -> {OUTPUT}')

if __name__ == '__main__':
    inject()