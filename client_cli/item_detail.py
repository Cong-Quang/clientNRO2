"""
Item Detail Analyzer - phân tích chi tiết item từ options.
"""
from item_option_data import (
    format_option, get_star_info, get_star_display,
    get_upgrade_display, OPTION_NAMES
)
from items_data import item_name


def analyze_item(item: dict) -> dict:
    """Phân tích toàn bộ thông tin item.
    
    Returns dict với:
      - name: tên item
      - id: template id
      - quantity: số lượng
      - upgrade: cấp + (0 nếu ko)
      - stars: dict star info
      - star_display: ★ display
      - upgrade_display: +N
      - options: list formatted option strings
      - content: yêu cầu (level, power, v.v.)
      - is_color: có màu không (option 41)
      - set_name: tên set kích hoạt nếu có
      - is_equip: là đồ mặc được không
      - is_weapon: có phải vũ khí ko
      - is_lock: có khóa ko (từ info/options)
      - has_stars: có lỗ sao không
    """
    item_id = item.get('id', 0)
    qty = item.get('quantity', 1)
    info_str = item.get('info', '')
    content = item.get('content', '')
    options = item.get('options', [])
    
    star_info = get_star_info(options)
    upgrade_disp = get_upgrade_display(options)
    star_disp = get_star_display(options)
    
    # Parse options thành formatted strings
    option_strings = []
    set_name = ""
    for opt in options:
        oid = opt['id']
        param = opt['param']
        
        # Skip upgrade và star options (display riêng)
        if oid in (72, 102, 107, 228):
            continue
        
        # Check set name (option name bắt đầu bằng $)
        name_tpl = OPTION_NAMES.get(oid, "")
        if name_tpl.startswith("$"):
            # $Set Name - đây là set kích hoạt
            name = name_tpl.replace("$", "").replace("#", str(param))
            set_name = name
        
        formatted = format_option(oid, param)
        if formatted and oid != 41:  # skip color name as separate
            option_strings.append(formatted)
    
    # Kiểm tra nếu là đồ mặc được
    is_equip = _is_equip_type(options)
    
    # Check khóa - từ content string
    is_lock = 'khóa' in content.lower() if content else False
    
    return {
        'name': item_name(item_id),
        'id': item_id,
        'quantity': qty,
        'upgrade': star_info['upgrade'],
        'star_info': star_info,
        'star_display': star_disp,
        'upgrade_display': upgrade_disp,
        'options': option_strings,
        'info': info_str,
        'content': content,
        'set_name': set_name,
        'is_equip': is_equip,
        'has_stars': star_info['max_stars'] > 0,
        'is_lock': is_lock,
    }


def _is_equip_type(options: list) -> bool:
    """Check if item is equippable (has base stat options)."""
    equip_options = {
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
        18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33,
        34, 35, 36, 37, 38, 39, 40, 42, 43, 44, 45, 46, 47, 48, 49, 50,
        72, 73, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 92, 93,
        94, 95, 96, 97, 98, 99, 100, 102, 103, 107, 108, 109, 110, 111,
        112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124,
        125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135,
    }
    for opt in options:
        if opt['id'] in equip_options:
            return True
    return False


def find_item_in_lists(items_list: list[dict | None], item_id: int) -> list[dict]:
    """Find items in a list by template ID."""
    found = []
    for idx, item in enumerate(items_list):
        if item and item.get('id') == item_id:
            found.append({'index': idx, 'item': item})
    return found


def find_item_by_id(state, item_id: int) -> dict:
    """Find item by ID across bag, body, and box.
    Returns { 'found': bool, 'items': [{'location': 'bag'|'body'|'box', 'index': i, 'item': item}] }
    """
    results = []
    
    # Search bag
    bag = getattr(state, 'items_bag', []) or []
    for idx, item in enumerate(bag):
        if item and item.get('id') == item_id:
            results.append({'location': 'bag', 'index': idx, 'item': item})
    
    # Search body
    body = getattr(state, 'items_body', []) or []
    for idx, item in enumerate(body):
        if item and item.get('id') == item_id:
            results.append({'location': 'body', 'index': idx, 'item': item})
    
    # Search box
    box = getattr(state, 'items_box', []) or []
    for idx, item in enumerate(box):
        if item and item.get('id') == item_id:
            results.append({'location': 'box', 'index': idx, 'item': item})
    
    return {'found': len(results) > 0, 'items': results}


def format_item_detail(item: dict, index: int = -1, location: str = "bag") -> str:
    """Format detailed item information for display."""
    info = analyze_item(item)
    lines = []
    
    # Header
    prefix = f"[{index}] " if index >= 0 else ""
    loc_tag = location.upper()
    item_id_str = f"[#{info['id']}]"
    
    name_str = info['name']
    if info['upgrade_display']:
        name_str += f" {info['upgrade_display']}"
    if info['star_display']:
        name_str += f"  {info['star_display']}"
    
    lines.append(f"  {prefix}{item_id_str} {name_str}")
    
    if info['quantity'] > 1:
        lines.append(f"      SL: {info['quantity']}")
    
    if info['is_lock']:
        lines.append(f"      🔒 Đã khóa")
    
    # Set kích hoạt
    if info['set_name']:
        lines.append(f"      📦 Set: {info['set_name']}")
    
    # Star detail
    if info['has_stars']:
        si = info['star_info']
        if si['current_stars'] > 0:
            lines.append(f"      Sao đã ép: {si['current_stars']}/{si['max_stars']}")
        if si['empty_slots'] > 0:
            lines.append(f"      Lỗ trống: {si['empty_slots']}")
        if si['slot_enhance'] > 0:
            lines.append(f"      CH lỗ sao: +{si['slot_enhance']}")
    
    # Item options (thuộc tính)
    if info['options']:
        lines.append(f"      Thuộc tính:")
        for opt_str in info['options']:
            lines.append(f"        {opt_str}")
    
    # Content (yêu cầu)
    if info['content']:
        c = info['content'].strip()
        if c:
            lines.append(f"      Yêu cầu: {c}")
    
    return "\n".join(lines)


def format_item_short(item: dict, index: int = -1) -> str:
    """Short format for list display (for /items, /equip)."""
    info = analyze_item(item)
    prefix = f"[{index}] " if index >= 0 else ""
    item_id_str = f"[#{info['id']}]"
    
    name_str = info['name']
    stars_str = ""
    
    if info['upgrade_display']:
        name_str += f" {info['upgrade_display']}"
    if info['star_display']:
        stars_str = f"  {info['star_display']}"
    
    qty_str = f" x{info['quantity']}" if info['quantity'] > 1 else ""
    lock_str = " 🔒" if info['is_lock'] else ""
    
    base = f"{prefix}{item_id_str} {name_str}{qty_str}{lock_str}{stars_str}"
    return base
