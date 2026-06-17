class Char:
    def __init__(self):
        self.charID = -1
        self.cName = ""
        self.cgender = 0
        self.clevel = 0
        self.cHP = 0
        self.cHPFull = 0
        self.cHPGoc = 0
        self.cMP = 0
        self.cMPFull = 0
        self.cMPGoc = 0
        self.cDamFull = 0
        self.cDamGoc = 0
        self.cDefull = 0
        self.cDefGoc = 0
        self.cCriticalFull = 0
        self.cCriticalGoc = 0
        self.cCritDameFull = 0
        self.cspeed = 4
        self.cBonusSpeed = 0
        self.cTiemNang = 0
        self.cNangdong = 0
        self.exp = 0
        self.cPower = 0
        self.cStamina = 0
        self.xu = 0
        self.luong = 0
        self.luongKhoa = 0
        self.xuInBox = 0
        self.giamST = 0
        self.hpFromTN = 0
        self.mpFromTN = 0
        self.damFromTN = 0
        self.defFromTN = 0
        self.expForOneAdd = 0
        self.cResFire = 0
        self.cResIce = 0
        self.cResWind = 0
        self.cMiss = 0
        self.cExactly = 0
        self.cFatal = 0
        self.cPk = 0
        self.cTypePk = 0
        self.cx = 24
        self.cy = 24
        self.cdir = 1
        self.head = 0
        self.body = 0
        self.leg = 0
        self.bag = 0
        self.wp = 0

    def format(self) -> str:
        lines = []
        lines.append(f"Name: {self.cName}  Lv: {self.clevel}")
        lines.append(f"HP: {_fmt(self.cHP)}/{_fmt(self.cHPFull)}  MP: {_fmt(self.cMP)}/{_fmt(self.cMPFull)}")
        lines.append(f"Damage: {_fmt(self.cDamFull)}  Defense: {_fmt(self.cDefull)}")
        lines.append(f"Crit: {self.cCriticalFull}%  CritDmg: {self.cCritDameFull}")
        lines.append(f"Speed: {self.cspeed}  Potential: {_fmt(self.cTiemNang)}")
        lines.append(f"Gold: {_fmt(self.xu)}  Box: {_fmt(self.xuInBox)}")
        lines.append(f"Gem: {_fmt(self.luong)}  Locked: {_fmt(self.luongKhoa)}")
        lines.append(f"At ({self.cx},{self.cy})")
        return "\n".join(lines)


def _fmt(n: int) -> str:
    if n >= 1_000_000_000:
        b = n // 1_000_000_000
        r = (n % 1_000_000_000) // 100_000_000
        return f"{b},{r}b" if r else f"{b}b"
    if n >= 1_000_000:
        return f"{n//1_000_000}m"
    if n >= 1_000:
        return f"{n//1_000}k"
    return str(n)
