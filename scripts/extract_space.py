"""提取餐廳空間區資料 → space.json + 4 張圖片"""
import re, json, base64
from pathlib import Path

SRC = Path("/mnt/user-data/outputs/farmtable.html")
DATA_DIR = Path("/home/claude/cms_build/_data")
IMG_DIR = Path("/home/claude/cms_build/images/space")
IMG_DIR.mkdir(parents=True, exist_ok=True)

html = SRC.read_text(encoding="utf-8")

# 抓 SPACE section
m_start = html.find("<!-- =================== RESTAURANT SPACE =================== -->")
m_end = html.find("<!-- =================== EVENTS =================== -->")
space_html = html[m_start:m_end]

data = {}

# section head
m = re.search(r'<div class="section-num">([^<]+)</div>', space_html)
if m: data["section_num"] = m.group(1).strip()

m = re.search(r'<h2 class="section-title">(.*?)</h2>', space_html, re.DOTALL)
if m: data["section_title_html"] = m.group(1).strip()

m = re.search(r'<p class="section-tag">(.*?)</p>', space_html, re.DOTALL)
if m: data["section_tag"] = m.group(1).strip()

# === Hero ===
hero = {}
m = re.search(r'<div class="space-hero-img">\s*<img src="(data:image/(\w+);base64,([^"]+))" alt="([^"]+)"', space_html)
if m:
    fmt = m.group(2)
    b64 = m.group(3)
    alt = m.group(4)
    ext = "webp" if fmt == "webp" else ("jpg" if fmt == "jpeg" else fmt)
    fname = f"hero.{ext}"
    (IMG_DIR / fname).write_bytes(base64.b64decode(b64))
    hero["image"] = f"/images/space/{fname}"
    hero["alt"] = alt

m = re.search(r'<div class="space-zone-mark">\s*<span class="zone-num">([^<]+)</span>\s*<span class="zone-en">([^<]+)</span>', space_html)
if m:
    hero["zone_num"] = m.group(1).strip()
    hero["zone_en"] = m.group(2).strip()

m = re.search(r'<div class="space-hero-caption">.*?<h3>(.*?)</h3>', space_html, re.DOTALL)
if m: hero["title_html"] = m.group(1).strip()

m = re.search(r'<p class="space-hero-desc">\s*(.*?)\s*</p>', space_html, re.DOTALL)
if m: hero["desc"] = re.sub(r'\s+', ' ', m.group(1)).strip()

# meta（適合 / 氛圍）
hero["meta"] = []
for m in re.finditer(r'<div><span class="meta-label">([^<]+)</span><span class="meta-value">([^<]+)</span></div>', space_html):
    hero["meta"].append({"label": m.group(1).strip(), "value": m.group(2).strip()})

data["hero"] = hero

# === Trio ===
trio = []
# 抓三個 space-card
def find_cards(html_, class_name):
    cards = []
    pat = re.compile(rf'<div class="{class_name}">')
    for m in pat.finditer(html_):
        start = m.start()
        depth = 1
        pos = m.end()
        while pos < len(html_):
            no = html_.find('<div', pos)
            nc = html_.find('</div>', pos)
            if nc == -1: break
            if no != -1 and no < nc:
                depth += 1
                pos = no + 4
            else:
                depth -= 1
                pos = nc + 6
                if depth == 0:
                    cards.append(html_[start:pos])
                    break
    return cards

cards = find_cards(space_html, "space-card")
print(f"找到 {len(cards)} 張 space-card")

for i, ch in enumerate(cards):
    card = {}
    # image
    m = re.search(r'<img src="(data:image/(\w+);base64,([^"]+))" alt="([^"]+)"', ch)
    if m:
        fmt = m.group(2)
        b64 = m.group(3)
        alt = m.group(4)
        ext = "webp" if fmt == "webp" else ("jpg" if fmt == "jpeg" else fmt)
        fname = f"zone{i+1}.{ext}"
        (IMG_DIR / fname).write_bytes(base64.b64decode(b64))
        card["image"] = f"/images/space/{fname}"
        card["alt"] = alt
    # tag style 是否特殊（KIDS PLAY 有 style=clay）
    m = re.search(r'<div class="space-card-tag"([^>]*)>', ch)
    if m:
        card["tag_style"] = "clay" if "var(--clay)" in m.group(1) else ""
    # zone-num-sm 或 svg + label
    m = re.search(r'<span class="zone-num-sm">([^<]+)</span>\s*<span>([^<]+)</span>', ch)
    if m:
        card["zone_num"] = m.group(1).strip()
        card["zone_label"] = m.group(2).strip()
        card["has_icon"] = False
    else:
        # 親子廚房有 SVG 圖示
        m2 = re.search(r'<svg[^>]*>.*?</svg>\s*<span>([^<]+)</span>', ch, re.DOTALL)
        if m2:
            card["zone_label"] = m2.group(1).strip()
            card["has_icon"] = True
    # title
    m = re.search(r'<h4>(.*?)</h4>', ch, re.DOTALL)
    if m: card["title_html"] = m.group(1).strip()
    # desc
    m = re.search(r'<p>([^<]+)</p>', ch)
    if m: card["desc"] = m.group(1).strip()
    trio.append(card)

data["trio"] = trio

DATA_DIR.mkdir(parents=True, exist_ok=True)
out = DATA_DIR / "space.json"
out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"輸出: {out}")
print(f"圖片數: {len(list(IMG_DIR.iterdir()))}")
print(f"\n摘要:")
print(json.dumps({"hero_title": data["hero"].get("title_html"),
                   "trio_titles": [c.get("title_html") for c in trio]},
                  ensure_ascii=False, indent=2))
