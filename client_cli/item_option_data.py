"""
Item Option Template data - mapping option ID to display name.
Option names use # as placeholder for param value.
"""

OPTION_NAMES = {
    # Basic stats
    0: "Sức đánh +#",
    1: "HP +#",
    2: "KI +#",
    3: "Giáp +#",
    4: "Né đòn +#",
    5: "Chí mạng +#",
    6: "Sức đánh +#%",
    7: "HP +#%",
    8: "KI +#%",
    9: "Giáp +#%",
    10: "Sức đánh chí mạng +#%",
    11: "Sức đánh +#",
    12: "HP +#",
    13: "KI +#",
    14: "Giáp +#",
    15: "Né đòn +#",
    16: "Chí mạng +#",
    17: "Sức đánh chí mạng +#%",
    18: "Sức đánh +#",
    19: "Sức đánh +#%",
    20: "Sức đánh tiềm năng +#",
    21: "HP tiềm năng +#",
    22: "Sức đánh +#%",
    23: "HP +#%",
    24: "KI tiềm năng +#",
    25: "Giáp tiềm năng +#",
    26: "Chí mạng tiềm năng +#",
    27: "Sức đánh chí mạng tiềm năng +#%",
    28: "Né đòn tiềm năng +#",
    29: "Sức đánh +#",
    30: "Sức đánh +#",
    31: "HP +#",
    32: "KI +#",
    33: "Giáp +#",
    # Special options
    34: "Sao pha lê cấp #",
    35: "Mặt trăng #",
    36: "Mặt trời #",
    37: "Bỏ qua né đòn +#%",
    38: "Tấn công +#%",
    39: "Phòng thủ +#%",
    40: "HP khi đánh quái +#",
    41: "#",  # Color name (name starts with $ or #)
    42: "Hút KI +#",
    43: "Hút HP khi đánh +#",
    44: "Tăng sức đánh khi nộ +#",
    45: "Giảm sức đánh địch +#%",
    46: "Giảm HP địch +#%",
    47: "Giảm giáp địch +#%",
    48: "Thể lực +#",
    49: "Sức đánh +#",
    50: "Hồi phục KI #%",
    51: "Tấn công x#",
    52: "Chí mạng x#",
    53: "Phòng thủ x#",
    54: "HP x#",
    55: "KI x#",
    56: "Sức đánh +#",
    57: "HP +#",
    58: "KI +#",
    59: "Giáp +#",
    60: "Né đòn +#",
    61: "Chí mạng +#",
    62: "Sức đánh chí mạng +#%",
    63: "Hút HP +#%",
    64: "Hút KI +#%",
    65: "Phản sát thương +#%",
    66: "Giảm sát thương +#%",
    67: "Tấn công +#%",
    68: "Tỷ lệ ra thêm +#",
    69: "Tăng sát thương +#%",
    # Upgrade & Stars
    72: "Cấp độ [+#]",  # Upgrade level
    73: "Số sao thường #",
    74: "Thời gian sử dụng #",
    75: "Chỉ số chính xác +#",
    76: "Sức đánh +#",
    77: "Hút HP #%",
    78: "Hút KI #%",
    79: "Phòng thủ +#%",
    80: "Sức đánh +#%",
    81: "Sức đánh chí mạng +#",
    82: "Tấn công +#",
    83: "HP +#%",
    84: "KI +#%",
    85: "Giáp +#%",
    86: "Sức đánh +#%",
    87: "KI +#%",
    88: "Hút HP khi đánh quái +#%",
    89: "Tỷ lệ rơi đồ +#%",
    90: "Kinh nghiệm +#%",
    91: "Vàng +#%",
    92: "Sức đánh +#",
    93: "Tỷ lệ rơi đồ +#",
    94: "Sức đánh +#",
    95: "HP +#",
    96: "KI +#",
    97: "Giáp +#",
    98: "Né đòn +#",
    99: "Chí mạng +#",
    100: "Sức đánh chí mạng +#%",
    101: "Vô hiệu hóa khiêu chiến",
    # Star slots
    102: "Số sao đã ép",  # Current stars filled
    103: "Phản sát thương +#%",
    104: "Hút HP từ quái +#%",
    105: "Nhân đôi sức đánh",
    106: "Bỏ qua né đòn",
    107: "Số sao tối đa",  # Max star slots
    108: "X2 sức đánh #%",
    109: "Giảm thời gian hồi chiêu #%",
    110: "Tấn công +#%",
    111: "Hồi phục #%",
    112: "Tấn công #",
    113: "Phòng thủ #",
    114: "Tấnông #%",
    115: "Phòng thủ #%",
    116: "HP #%",
    117: "HP khi đánh quái #%",
    118: "KI #%",
    119: "Sức đánh #",
    120: "Mỗi 5s hồi #% HP",
    121: "Mỗi 5s hồi #% KI",
    122: "Giảm sát thương #%",
    123: "Giáp khi đánh quái #",
    124: "Né đòn #%",
    125: "Chí mạng #%",
    126: "Sức đánh chí mạng #%",
    127: "Sức đánh #",
    128: "HP #",
    129: "KI #",
    130: "Giáp #",
    131: "Né đòn #",
    132: "Chí mạng #",
    133: "Sức đánh chí mạng #%",
    134: "Sức đánh #%",
    135: "HP #%",
    # Special sets
    136: "Giảm sát thương khi bị đánh #%",
    137: "Hút KI khi đánh #%",
    138: "Miễn nhiễm #",
    139: "Phản sát thương #",
    140: "Hút HP #",
    141: "Hút KI #",
    142: "Tấn công +#%",
    143: "Phòng thủ +#%",
    144: "HP +#%",
    145: "KI +#%",
    146: "Tăng sát thương khi đánh quái #%",
    147: "Tăng sức đánh #%",
    148: "Tăng giáp #%",
    149: "Tăng HP #%",
    150: "Tăng KI #%",
    151: "Bỏ qua phòng thủ #%",
    152: "Tấn công #%",
    153: "Phòng thủ #%",
    154: "HP #%",
    155: "KI #%",
    156: "Sức đánh #",
    157: "HP #",
    158: "KI #",
    159: "Giáp #",
    160: "Hồi HP #%",
    161: "Hồi KI #%",
    162: "Kháng sát thương chí mạng #%",
    163: "Giảm thời gian hồi chiêu #%",
    164: "X2 vàng #%",
    165: "X2 kinh nghiệm #%",
    166: "Tăng sức đánh khi nộ #%",
    167: "Tăng KI khi nộ #%",
    168: "Tăng HP khi nộ #%",
    169: "Giảm sức đánh địch #%",
    170: "Giảm giáp địch #%",
    171: "Giảm HP địch #%",
    172: "Choáng #%",
    173: "Trói #%",
    174: "Đóng băng #%",
    175: "Đốt cháy #%",
    176: "Độc #%",
    177: "Giảm KI địch #%",
    178: "Cướp HP #%",
    179: "Cướp KI #%",
    180: "Giảm hồi phục địch #%",
    181: "Tăng hồi phục #%",
    182: "Khiên #%",
    183: "Phản đòn #%",
    184: "Hồi sinh #%",
    185: "Tàng hình #%",
    186: "Tăng tốc #%",
    187: "Giảm tốc #%",
    188: "Tăng sát thương khi đánh quái #%",
    189: "Giảm sát thương từ quái #%",
    190: "Tăng kinh nghiệm #%",
    191: "Tăng vàng #%",
    192: "Tăng tỷ lệ rơi đồ #%",
    193: "Tăng tỷ lệ rơi item quý #%",
    194: "Sức đánh #",
    195: "HP #",
    196: "KI #",
    197: "Giáp #",
    198: "Né đòn #",
    199: "Chí mạng #",
    200: "Sức đánh chí mạng #%",
    201: "Sức đánh #",
    202: "HP #",
    203: "KI #",
    204: "Giáp #",
    205: "Né đòn #",
    206: "Chí mạng #",
    207: "Bỏ qua né đòn #",
    208: "Sức đánh chí mạng #%",
    209: "# sao",  # Star count for enchant
    210: "Giảm sát thương khi bị đánh #%",
    211: "Giảm thời gian hồi chiêu #%",
    212: "Hồi HP khi đánh #%",
    213: "Hồi KI khi đánh #%",
    214: "Sức đánh #%",
    215: "Phòng thủ #%",
    216: "HP #%",
    217: "KI #%",
    218: "#",  # Special text
    219: "Sức đánh #%",
    220: "Danh hiệu #",  # Title
    221: "Sức đánh #%",
    222: "Phòng thủ #%",
    223: "HP #%",
    224: "KI #%",
    225: "Sức đánh chí mạng #%",
    226: "Né đòn #%",
    227: "Bỏ qua né đòn #",
    228: "Cường hóa lỗ sao cấp #",  # Star slot enhancement
    229: "Tỷ lệ thành công +#%",
    230: "Giảm sát thương khi bị đánh #%",
    231: "Hút HP khi đánh #%",
    232: "Hút KI khi đánh #%",
    233: "Miễn nhiễm sát thương #%",
    234: "Giảm sát thương chí mạng #%",
    235: "Tăng sức đánh theo HP #%",
    236: "Tăng sức đánh theo KI #%",
    237: "Tăng sức đánh theo giáp #%",
    238: "Sức đánh #%",
    239: "Giáp #%",
    240: "HP #%",
    241: "KI #%",
    242: "Né đòn #%",
    243: "Chí mạng #%",
    244: "HP #",
    245: "KI #",
    246: "Sức đánh #",
    247: "Giáp #",
    248: "Tấn công #",
    249: "Phòng thủ #",
    250: "HP #",
    251: "KI #",
}


def get_option_name(opt_id: int) -> str:
    """Get option template name for an option ID."""
    return OPTION_NAMES.get(opt_id, f"Option_{opt_id}")


def format_option(opt_id: int, param: int) -> str:
    """Format an option with its param value."""
    # Option 41 = color name - skip format (handled separately)
    if opt_id == 41:
        return ""
    name = get_option_name(opt_id)
    if '#' in name:
        return name.replace('#', str(param))
    return f"{name}: {param}"


def get_star_info(options: list) -> dict:
    """Extract star info from item options.
    Returns:
        {
            'current_stars': int,  # số sao đã ép
            'max_stars': int,      # số sao tối đa
            'empty_slots': int,    # số lỗ trống
            'upgrade': int,        # cấp độ nâng cấp (+?)
            'slot_enhance': int,   # cường hóa lỗ sao cấp mấy
        }
    """
    result = {
        'current_stars': 0,
        'max_stars': 0,
        'empty_slots': 0,
        'upgrade': 0,
        'slot_enhance': 0,
    }
    for opt in options:
        oid = opt['id']
        param = opt['param']
        if oid == 102:
            result['current_stars'] = param
        elif oid == 107:
            result['max_stars'] = param
        elif oid == 72:
            result['upgrade'] = param
        elif oid == 228:
            result['slot_enhance'] = param
    if result['max_stars'] > 0:
        result['empty_slots'] = result['max_stars'] - result['current_stars']
    return result


def get_star_display(options: list) -> str:
    """Get star display string like ★★★☆☆ (3/5)"""
    info = get_star_info(options)
    if info['max_stars'] <= 0:
        return ""
    filled = '★' * info['current_stars']
    empty = '☆' * info['empty_slots']
    stars = filled + empty
    extra = ""
    if info['slot_enhance'] > 0:
        extra += f" [CH+{info['slot_enhance']}]"
    return f"{stars} ({info['current_stars']}/{info['max_stars']}){extra}"


def get_upgrade_display(options: list) -> str:
    """Get upgrade display like +4 or empty string."""
    info = get_star_info(options)
    if info['upgrade'] > 0:
        return f"+{info['upgrade']}"
    return ""
