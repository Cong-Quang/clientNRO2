from dataclasses import dataclass, field


@dataclass
class MapLink:
    dest: int
    npc_id: int = -1
    item_id: int = -1
    move_type: int = 0  # 0=waypoint 1=npc_menu 2=npc_index 3=item 4=walk
    wp_pos: int = 0     # -1=left 0=center 1=right
    menus: list = field(default_factory=list)
    menus_sub: list = field(default_factory=list)
    menus_sub2: list = field(default_factory=list)
    walk_x: int = -1
    walk_y: int = -1


TRAI_DAT = [42, 21, 0, 1, 2, 3, 4, 5, 6, 27, 28, 29, 30, 47, 42, 24, 53, 58, 59, 60, 61, 62, 55, 56, 54, 57]
NAMEK = [43, 22, 7, 8, 9, 11, 12, 13, 10, 31, 32, 33, 34, 43, 25]
XAYDA = [44, 23, 14, 15, 16, 17, 18, 20, 19, 35, 36, 37, 38, 52, 44, 26, 84, 113, 127, 129]
NAPPA = [68, 69, 70, 71, 72, 64, 65, 63, 66, 67, 73, 74, 75, 76, 77, 81, 82, 83, 79, 80, 131, 132, 133]
TUONG_LAI = [102, 92, 93, 94, 96, 97, 98, 99, 100, 103]
COLD = [109, 108, 107, 110, 106, 105]
THAP_LEO = [46, 45, 48, 50, 154, 155, 166]
MANH_VO_BT = [153, 156, 157, 158, 159]
KHI_GAS = [149, 147, 152, 151, 148]
MAP_KHAC = [181, 139, 140, 126, 173, 174, 175, 123, 124, 122]

PLANETS = {
    "Trái Đất": TRAI_DAT,
    "Namek": NAMEK,
    "Xayda": XAYDA,
    "Fide": NAPPA,
    "Tương lai": TUONG_LAI,
    "Cold": COLD,
    "Tháp leo": THAP_LEO,
    "Khu vực bang": MANH_VO_BT,
    "Khi Gas": KHI_GAS,
    "Map Khác": MAP_KHAC,
}

KHI_GAS_SET = set(KHI_GAS)
MANH_VO_BT_SET = set(MANH_VO_BT)
TUONG_LAI_SET = set(TUONG_LAI)

POWER_40B = 40_000_000_000
POWER_60B = 60_000_000_000

CLAN_MAP_START, CLAN_MAP_END = 53, 62
COLD_MAP_START, COLD_MAP_END = 105, 110
NRD_MAP_START, NRD_MAP_END = 85, 91
SPECIAL_MAP_START, SPECIAL_MAP_END = 153, 159


def _normalize(s: str) -> str:
    import re
    return re.sub(r'\s+', '', s.lower().strip())


def build_graph() -> dict[int, list[MapLink]]:
    g: dict[int, list[MapLink]] = {}

    def ensure(m):
        if m not in g:
            g[m] = []

    def add_waypoint_chain(*maps):
        for i, m in enumerate(maps):
            ensure(m)
            if i > 0:
                nm = MapLink(dest=maps[i - 1], move_type=0, wp_pos=-1)
                g[m].append(nm)
            if i < len(maps) - 1:
                nm = MapLink(dest=maps[i + 1], move_type=0, wp_pos=1)
                g[m].append(nm)

    def add_npc_link(from_map, to_map, npc=-1, menus=None, menus_sub=None, menus_sub2=None,
                     item=-1, move_type=1, walk_x=-1, walk_y=-1, wp_pos=0):
        ensure(from_map)
        g[from_map].append(MapLink(dest=to_map, npc_id=npc, item_id=item, move_type=move_type,
                                    menus=menus or [], menus_sub=menus_sub or [],
                                    menus_sub2=menus_sub2 or [],
                                    walk_x=walk_x, walk_y=walk_y, wp_pos=wp_pos))

    def add_portal_group(from_map, to_maps, npc, indices):
        for i, tm in enumerate(to_maps):
            idx = indices[i] if i < len(indices) else 0
            add_npc_link(from_map, tm, npc=npc, move_type=2, menus=[idx])

    add_waypoint_chain(42, 0, 1, 2, 3, 4, 5, 6)
    add_waypoint_chain(43, 7, 8, 9, 11, 12, 13, 10)
    add_waypoint_chain(52, 44, 14, 15, 16, 17, 18, 20, 19)
    add_waypoint_chain(53, 58, 59, 60, 61, 62, 55, 56, 54, 57)
    add_waypoint_chain(68, 69, 70, 71, 72, 64, 65, 63, 66, 67, 73, 74, 75, 76, 77, 81, 82, 83, 79, 80)
    add_waypoint_chain(102, 92, 93, 94, 96, 97, 98, 99, 100, 103)
    add_waypoint_chain(3, 27, 28, 29, 30)
    add_waypoint_chain(11, 31, 32, 33, 34)
    add_waypoint_chain(17, 35, 36, 37, 38)
    add_waypoint_chain(109, 108, 107, 110, 106)
    add_waypoint_chain(47, 46, 45, 48)
    add_waypoint_chain(131, 132, 133)
    add_waypoint_chain(160, 161, 162, 163)
    add_waypoint_chain(153, 156, 157, 158, 159)
    add_waypoint_chain(46, 45, 48, 50, 154, 155, 166)
    add_waypoint_chain(149, 147, 152, 151, 148)
    add_waypoint_chain(173, 174, 175)
    add_waypoint_chain(123, 124, 122)

    add_waypoint_chain(0, 21)
    add_waypoint_chain(1, 47)
    add_waypoint_chain(47, 111)
    add_waypoint_chain(2, 24)
    add_waypoint_chain(5, 29)
    add_waypoint_chain(7, 22)
    add_waypoint_chain(9, 25)
    add_waypoint_chain(13, 33)
    add_waypoint_chain(14, 23)
    add_waypoint_chain(16, 26)
    add_waypoint_chain(20, 37)
    add_waypoint_chain(39, 21)
    add_waypoint_chain(40, 22)
    add_waypoint_chain(41, 23)
    add_waypoint_chain(109, 105)
    add_waypoint_chain(109, 106)
    add_waypoint_chain(106, 107)
    add_waypoint_chain(108, 105)
    add_waypoint_chain(80, 105)
    add_waypoint_chain(84, 104)
    add_waypoint_chain(139, 140)

    add_npc_link(19, 68, npc=12, menus=["Đến Nappa", "", "", "Đồng ý"])
    add_npc_link(68, 19, npc=12)
    add_npc_link(19, 109, npc=12, menus=["Đến Cold"])
    add_npc_link(0, 123, npc=49, move_type=2, menus=[0])
    add_npc_link(123, 0, npc=49, move_type=2, menus=[0])
    add_npc_link(122, 0, npc=49, move_type=2, menus=[1])

    add_portal_group(24, [25, 26, 84], npc=10, indices=[0, 1, 2])
    add_portal_group(25, [24, 26, 84], npc=11, indices=[0, 1, 2])
    add_portal_group(26, [24, 25, 84], npc=12, indices=[0, 1, 2])
    add_npc_link(84, 21, npc=10, move_type=2, menus=[0])

    add_npc_link(27, 102, npc=38, move_type=2, menus=[1])
    add_npc_link(28, 102, npc=38, move_type=2, menus=[1])
    add_npc_link(29, 102, npc=38, move_type=2, menus=[1])
    add_npc_link(102, 27, npc=38, move_type=2, menus=[1])

    add_npc_link(27, 53, npc=25, menus=["Vào (miễn phí)", "", "", "Tham Gia", "OK"])
    add_npc_link(52, 127, npc=44, menus=["OK"])
    add_npc_link(52, 129, npc=23, menus=["Đại Hội Võ Thuật Lần thứ 23"])
    add_npc_link(52, 113, npc=23, menus=["Giải Siêu Hạng"])
    add_npc_link(113, 52, npc=22, menus=["Về Đại Hội Võ Thuật"])
    add_npc_link(127, 52, npc=44, menus=["Về Đại Hội Võ Thuật"])
    add_npc_link(129, 52, npc=23, menus=["Về Đại Hội Võ Thuật"])

    add_npc_link(80, 131, npc=60, move_type=2, menus=[0])
    add_npc_link(131, 80, npc=60, move_type=2, menus=[1])

    add_npc_link(5, 153, npc=13, menus=["Nói chuyện", "Về khu vực bang"])
    add_npc_link(153, 5, npc=10, menus=["Đảo Kame"])
    add_npc_link(153, 156, npc=47, menus=["OK"])

    add_npc_link(45, 48, npc=19, move_type=2, menus=[3])
    add_npc_link(48, 45, npc=20, move_type=2, menus=[3, 0])
    add_npc_link(48, 50, npc=20, move_type=2, menus=[3, 1])
    add_npc_link(50, 48, npc=44, move_type=2, menus=[0])
    add_npc_link(50, 154, npc=44, move_type=2, menus=[1])
    add_npc_link(154, 50, npc=55, move_type=2, menus=[0])
    add_npc_link(154, 155, npc=44, move_type=2, menus=[1])
    add_npc_link(155, 154, npc=44, move_type=2, menus=[0])

    add_npc_link(155, 166, move_type=4, walk_x=1400, walk_y=600)
    add_npc_link(46, 47, move_type=4, walk_x=80, walk_y=700)
    add_npc_link(45, 46, move_type=4, walk_x=80, walk_y=700)
    add_npc_link(46, 45, move_type=4, walk_x=380, walk_y=90)

    add_npc_link(0, 149, npc=67, menus=["OK", "Đồng ý"])

    add_npc_link(24, 139, npc=63, move_type=2, menus=[0])
    add_npc_link(139, 24, npc=63, move_type=2, menus=[0])
    add_npc_link(126, 19, npc=53, menus=["OK"])
    add_npc_link(19, 126, npc=53, menus=["OK"])
    add_npc_link(52, 181, npc=44, menus=["Bình hút năng lượng", "OK"])
    add_npc_link(181, 52, npc=44, menus=["Về nhà"])

    add_npc_link(160, 161, item=992, move_type=3)
    add_npc_link(181, 52, item=1852, move_type=3)

    for gender in [0, 1, 2]:
        home = gender * 7
        ensure(home)
        if 173 not in [l.dest for l in g.get(home, []) if l.move_type == 0]:
            add_npc_link(home, 173, npc=81, move_type=2, menus=[2])
            add_npc_link(173, home, npc=81, move_type=2, menus=[2])

    return g


CAPSULE_CHAIN = {
    21: [0, 42],
    22: [7, 43],
    23: [14, 44, 52],
    24: [84, 25, 26],
    25: [84, 24, 26],
    26: [84, 24, 25],
    29: [5, 6, 42],
    38: [52],
    # add more capsule chains as needed
}

CAPSULE_ITEM_IDS = {194, 193}

MIN_PATH_LENGTH_FOR_CAPSULE = 4


def is_nrd_map(mid: int) -> bool:
    return NRD_MAP_START <= mid <= NRD_MAP_END


def is_future_map(mid: int) -> bool:
    return mid in TUONG_LAI_SET


def is_cold_map(mid: int) -> bool:
    return COLD_MAP_START <= mid <= COLD_MAP_END


def is_clan_map(mid: int) -> bool:
    return CLAN_MAP_START <= mid <= CLAN_MAP_END


def is_special_map(mid: int) -> bool:
    return SPECIAL_MAP_START <= mid <= SPECIAL_MAP_END


def requires_clan(mid: int) -> bool:
    return mid in KHI_GAS_SET or mid in MANH_VO_BT_SET or is_clan_map(mid)
