import os, json, base64, re
from lxml import etree

TEMPLATE_EN = 'src/banner.svg.template'
TEMPLATE_FR = 'src/banner-fr.svg.template'
OUTPUT_EN = 'images/banner.svg'
OUTPUT_FR = 'images/banner-fr.svg'
SPONSORS_FILE = 'sponsors/sponsors.json'
DEFAULT_AVATAR = 'src/default_avatar.png'

XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink'

PLACEHOLDER_MAP = {
    '{{SUPPORTER1}}': ('last6', 0),
    '{{SUPPORTER2}}': ('last6', 1),
    '{{SUPPORTER3}}': ('last6', 2),
    '{{SUPPORTER4}}': ('last6', 3),
    '{{SUPPORTER5}}': ('last6', 4),
    '{{SUPPORTER6}}': ('last6', 5),
    '{{SUPPORTER1_NAME}}': ('last6', 0),
    '{{SUPPORTER2_NAME}}': ('last6', 1),
    '{{SUPPORTER3_NAME}}': ('last6', 2),
    '{{SUPPORTER4_NAME}}': ('last6', 3),
    '{{SUPPORTER5_NAME}}': ('last6', 4),
    '{{SUPPORTER6_NAME}}': ('last6', 5),
    '{{SUPPORTERTOP1}}': ('top3', 0),
    '{{SUPPORTERTOP2}}': ('top3', 1),
    '{{SUPPORTERTOP3}}': ('top3', 2),
    '{{SUPPORTERTOP1_NAME}}': ('top3', 0),
    '{{SUPPORTERTOP2_NAME}}': ('top3', 1),
    '{{SUPPORTERTOP3_NAME}}': ('top3', 2),
}

FONT_CONFIG = {
    'last6': {'max_width': 38.0, 'max_size': 5.5, 'min_size': 3.5, 'max_chars': 12},
    'top3':  {'max_width': 55.0, 'max_size': 7.0, 'min_size': 4.5, 'max_chars': 14},
}

CHAR_WIDTH_RATIO = 0.62

def to_data_url(path: str) -> str:
    extension = path.rsplit('.', 1)[-1].lower()
    mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(extension, 'image/png')
    with open(path, 'rb') as f:
        return f'data:{mime};base64,{base64.b64encode(f.read()).decode()}'

def load_sponsors() -> dict:
    if not os.path.exists(SPONSORS_FILE):
        print(f'Warning: {SPONSORS_FILE} not found - all slots will use defaults')
        return {'top3': [], 'last6': []}
    with open(SPONSORS_FILE) as f:
        return json.load(f)

def get_sponsor(data: dict, key: str, index: int) -> tuple[str, str]:
    sponsors = data.get(key, [])
    if index < len(sponsors):
        sponsor = sponsors[index]
        avatar_path = sponsor.get('avatar_path', DEFAULT_AVATAR)
        username = sponsor.get('login', '')
        if not os.path.exists(avatar_path):
            print(f'Warning: avatar not found at {avatar_path}, using default')
            avatar_path = DEFAULT_AVATAR
        return to_data_url(avatar_path), username
    return to_data_url(DEFAULT_AVATAR), ''

def normalize_username(name: str, max_chars: int) -> str:
    name = name.strip().lstrip('@')
    name = re.sub(r'[<>&\'"\\]', '', name)
    name = re.sub(r'\s+', ' ', name)
    if len(name) > max_chars:
        name = name[:max_chars - 1] + '…'
    return name

def compute_font_size(name: str, max_width: float, max_size: float, min_size: float) -> float:
    if not name:
        return max_size
    if len(name) * max_size * CHAR_WIDTH_RATIO <= max_width:
        return max_size
    size = max_width / (len(name) * CHAR_WIDTH_RATIO)
    return round(max(min_size, min(max_size, size)), 3)

def scale_font_in_style(style: str, new_size: float) -> str:
    return re.sub(r'font-size:[^;]+', f'font-size:{new_size}px', style)

def is_name_placeholder(placeholder: str) -> bool:
    return '_NAME' in placeholder

def apply_placeholder(root: etree._Element, placeholder: str, data_url: str, name: str, username: str, config: dict) -> None:
    is_name = is_name_placeholder(placeholder)
    for element in root.iter():
        element_id = element.get('id', '')
        tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
        if not is_name and placeholder in element_id and tag == 'image':
            element.set('href', data_url)
            element.set(f'{{{XLINK_NAMESPACE}}}href', data_url)
            print(f'Injected avatar -> #{element_id} ({username})')
        if element.text and placeholder in element.text:
            if is_name:
                font_size = compute_font_size(name, config['max_width'], config['max_size'], config['min_size'])
                element.text = element.text.replace(placeholder, name)
                style = element.get('style', '')
                if style:
                    element.set('style', scale_font_in_style(style, font_size))
                print(f'Injected name -> #{element_id} "{name}" @ {font_size}px')
            else:
                element.text = element.text.replace(placeholder, username)
                print(f'Replaced text placeholder {placeholder} -> #{element_id} "{username}"')
        if element.tail and placeholder in element.tail:
            element.tail = element.tail.replace(placeholder, name if is_name else username)
        if not is_name:
            for attr, value in list(element.attrib.items()):
                if placeholder in value:
                    element.set(attr, value.replace(placeholder, data_url))
                    print(f'Replaced attr {attr} placeholder {placeholder}')

def inject() -> None:
    os.makedirs('images', exist_ok=True)
    data = load_sponsors()
    parser = etree.XMLParser(remove_blank_text=False)
    root_en = etree.parse(TEMPLATE_EN, parser).getroot()
    root_fr = etree.parse(TEMPLATE_FR, parser).getroot()
    for placeholder, (key, index) in PLACEHOLDER_MAP.items():
        data_url, username = get_sponsor(data, key, index)
        config = FONT_CONFIG[key]
        name = normalize_username(username, config['max_chars'])
        apply_placeholder(root_en, placeholder, data_url, name, username, config)
        apply_placeholder(root_fr, placeholder, data_url, name, username, config)
    etree.ElementTree(root_en).write(OUTPUT_EN, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    etree.ElementTree(root_fr).write(OUTPUT_FR, xml_declaration=True, encoding='UTF-8', pretty_print=False)
    print(f'\nDone -> {OUTPUT_EN} and {OUTPUT_FR}')


if __name__ == '__main__':
    inject()