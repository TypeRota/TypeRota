#!/usr/bin/env python3
"""把 data/stats.json 渲染成 assets/stats-*.svg 和 assets/heat-*.svg。

为什么不用第三方卡片服务：那些服务会把空格子写死成浅灰，深色主题下
一片刺眼；自己画才能两版都控色。

为什么用 <text> 而不是转 path：这张图每天在 Actions 里重跑，CI 上没有
思源、Maple Mono 这些字体。交给访客浏览器的系统字体栈渲染，零安装。
"""
import json
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "stats.json"
OUT = ROOT / "assets"

W = 1200
MONO = ('ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
        '"Liberation Mono",monospace')
SANS = ('-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC",'
        '"PingFang SC","Microsoft YaHei",sans-serif')

THEMES = {
    "dark": {
        "bg": "#0B1024", "line": "#232B4A", "title": "#8892B4", "num": "#EDEFF7",
        "label": "#C8CFE2", "sub": "#6E7A99", "accent": "#A78BFA", "gold": "#EFC77E",
        "ramp": ["#171E33", "#4A3B6B", "#7B5FB0", "#A78BFA", "#D8C7FF"],
    },
    "light": {
        "bg": "#FBFAFE", "line": "#E4DFF2", "title": "#6B7280", "num": "#241A3E",
        "label": "#3A3452", "sub": "#8B84A3", "accent": "#7C5BD6", "gold": "#C99A3E",
        "ramp": ["#EBEDF0", "#DCD2F2", "#BEA6EC", "#9B7BDC", "#7C5BD6"],
    },
}

CELL, GAP = 17, 4
PITCH = CELL + GAP
PAD = 40


def txt(x, y, s, fill, size=17, anchor="start", weight=400, family=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    fam = family or MONO
    return (f'<text x="{x:.0f}" y="{y}" fill="{fill}" font-size="{size}" '
            f'font-weight="{weight}" font-family=\'{fam}\'{a}>{escape(str(s))}</text>')


def level(n):
    return 0 if n == 0 else 1 if n <= 4 else 2 if n <= 11 else 3 if n <= 20 else 4


def stats_card(s, t):
    """一张 1200x236 的计量板：提交 / 代码行 / 协作 / 贡献。"""
    H = 236
    day = s.get("day", 0)
    cols = [
        (f'{s["commits"]:,}', "提交", f'{s["repo_count"]} 个仓库'),
        (f'+{s["added"]:,}', "新增代码行", f'−{s["deleted"]:,} 行 · {s["files"]} 个文件'),
        (f'{s["reviewed"] + s["commented"]:,}', "协作", f'评审 {s["reviewed"]} · 讨论 {s["commented"]}'),
        (f'{s["contributions"]:,}', "贡献", "近一年"),
    ]
    parts = [f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>']
    parts.append(txt(40, 44, "工作计量", t["title"], 16, weight=500, family=SANS))
    parts.append(txt(W - 40, 44, f'第 {day} 天 · 更新于 {s["generated_at"][:10]}',
                     t["sub"], 13, anchor="end", family=SANS))
    parts.append(f'<path d="M40 62H{W-40}" stroke="{t["line"]}" stroke-width="1"/>')

    for i, (big, label, sub) in enumerate(cols):
        x = 40 + i * 282
        if i:
            parts.append(f'<path d="M{x-36} 84V222" stroke="{t["line"]}" stroke-width="1"/>')
        parts.append(txt(x, 132, big, t["num"], 46, weight=500))
        parts.append(txt(x, 172, label, t["label"], 15, weight=500, family=SANS))
        parts.append(txt(x, 200, sub, t["sub"], 12.5, family=SANS))

    parts.append(txt(W - 40, 222, "typerota", t["accent"], 12, anchor="end", weight=500))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="工作计量">'
            + "".join(parts) + "</svg>")


def heat_card(s, t):
    """贡献热力图：53 周 × 7 天。"""
    cal = s["calendar"]
    weeks = cal["weeks"]
    grid_y = 66
    H = grid_y + 7 * PITCH - GAP + 8
    parts = [f'<rect width="{W}" height="{H}" rx="16" fill="{t["bg"]}"/>']
    parts.append(txt(PAD, 30, f'近一年贡献 · {cal["start"]} → {cal["end"]}', t["title"], 16))
    parts.append(txt(W - PAD, 30, f'共 {s["contributions"]:,} 次', t["num"], 16,
                     anchor="end", weight=500))

    prev_month, prev_x = None, -999
    for ci, week in enumerate(weeks):
        for ri, day in enumerate(week):
            parts.append(f'<rect x="{PAD + ci * PITCH}" y="{grid_y + ri * PITCH}" width="{CELL}" '
                         f'height="{CELL}" rx="4.2" fill="{t["ramp"][level(day["n"])]}"/>')
        mid_day = week[3] if len(week) > 3 else week[-1]
        mid = __import__("datetime").date.fromisoformat(mid_day["d"])
        x = PAD + ci * PITCH
        if mid.month != prev_month and x - prev_x >= 46:
            anchor = "end" if x > W - PAD - 40 else "start"
            parts.append(txt(x, 54, f"{mid.month}月", t["sub"], 13.5, anchor=anchor))
            prev_month, prev_x = mid.month, x
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" role="img" aria-label="近一年贡献热力图">'
            + "".join(parts) + "</svg>")


def main():
    s = json.loads(DATA.read_text())
    import datetime
    born = datetime.date.fromisoformat(s["born"])
    s["day"] = (datetime.date.today() - born).days + 1
    OUT.mkdir(exist_ok=True)
    for th, t in THEMES.items():
        (OUT / f"stats-{th}.svg").write_text(stats_card(s, t))
        (OUT / f"heat-{th}.svg").write_text(heat_card(s, t))
    print(f'assets/stats-{{dark,light}}.svg · assets/heat-{{dark,light}}.svg · 第 {s["day"]} 天')


if __name__ == "__main__":
    main()