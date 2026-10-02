# core/ganzhi.py
TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DIZHI   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

def build_jiazi() -> list[dict]:
    result = []
    for i in range(60):
        stem = TIANGAN[i % 10]
        branch = DIZHI[i % 12]
        result.append({
            "index": i + 1,
            "stem": stem,
            "branch": branch,
            "name": stem + branch,
            "xun": DIZHI[(i // 10) * 1 % 12],  # 旬首，可选
        })
    return result

JIAZI = build_jiazi()