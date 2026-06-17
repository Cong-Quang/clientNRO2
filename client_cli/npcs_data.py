NPC_TEMPLATES = {
    0: "Ông Gôhan", 1: "Ông Paragus", 2: "Ông Moori", 3: "Rương đồ",
    4: "Đậu thần", 5: "Con mèo", 6: "Khu vực", 7: "Bunma",
    8: "Dende", 9: "Appule", 10: "Dr. Brief", 11: "Cargo",
    12: "Cui", 13: "Quy Lão Kame", 14: "Trưởng lão Guru", 15: "Vua Vegeta",
    16: "Uron", 17: "Bò Mộng", 18: "Thần mèo Karin", 19: "Thượng Đế",
    20: "Thần Vũ Trụ", 21: "Bà Hạt Mít", 22: "Trọng tài", 23: "Ghi danh",
    24: "Rồng Thiêng", 25: "Lính canh", 26: "Độc Nhãn", 27: "Rồng Thần Namec",
    28: "Cửa hàng ký gửi", 29: "Rồng Omega", 30: "Rồng 2 sao",
    31: "Rồng 3 sao", 32: "Rồng 4 sao", 33: "Rồng 5 sao",
    34: "Rồng 6 sao", 35: "Rồng 7 sao", 36: "Rồng 1 sao",
    37: "Bunma", 38: "Ca Lích", 39: "Santa", 40: "Mabư mập",
    41: "Trung thu", 42: "Quốc Vương", 43: "Tổ Sư Kaio", 44: "Ôsin",
    45: "Kibit", 46: "Babiđây", 47: "Giu-ma Đầu Bò", 48: "Ngộ Không",
    49: "Đường Tăng", 50: "Quả trứng", 51: "Dưa hấu", 52: "Hùng Vương",
    53: "Tapion", 54: "Lý Tiểu Nương", 55: "Bill", 56: "Whis",
    57: "Champa", 58: "Vados", 59: "Trọng tài", 60: "Goku SSJ",
    61: "Goku SSJ", 62: "Potage", 63: "Jaco", 64: "Thiên Sứ Whis",
    65: "Yarirobe", 66: "Nồi bánh", 67: "Mr Popo", 68: "Panchy",
    69: "Thỏ Đại Ca", 70: "Bardock", 71: "Berry", 72: "Đặc Cầu",
    73: "Fide", 74: "Tori-Bot", 75: "Thỏ Đỏ ChiChi", 76: "Granola",
    77: "Quả trứng linh thú", 78: "Ông già Noel", 79: "Cây thông Noel",
    80: "Npc", 81: "Chi Chi", 82: "Rương Sưu Tầm", 83: "Dr. Myuu",
    84: "Xe nước mía", 103: "Chú Bé Đần", 104: "Khá BảnH",
    105: "Tiến Bry", 106: "Bulma Tết Nguyên Đăng", 107: "Bill Bí Ngô",
    108: "Heart", 109: "Bulma Bunny", 110: "Bunma Rực Rỡ",
}


def npc_name(temp_id: int) -> str:
    return NPC_TEMPLATES.get(temp_id, f"NPC_{temp_id}")
