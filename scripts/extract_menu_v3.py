"""提取菜單資料 v3：含 COMBO schema 和 menu-section-desc"""
import re, json
from pathlib import Path

SRC = Path("/mnt/user-data/outputs/farmtable.html")
OUT_DIR = Path("/home/claude/cms_build/_data")
html = SRC.read_text(encoding="utf-8")

menu_start = html.find("<!-- =================== MENU =================== -->")
menu_end = html.find("<!-- =================== 食材小故事 =================== -->")
menu_html = html[menu_start:menu_end]

cat_pattern = re.compile(r'<!-- ===== (\w+) ===== -->\s*\n\s*<div class="menu-section[^"]*"\s+data-cat="([^"]+)"[^>]*>')
categories = []
for m in cat_pattern.finditer(menu_html):
    categories.append({"internal_name": m.group(1), "data_cat": m.group(2), "start": m.start()})

for i in range(len(categories)):
    categories[i]["end"] = categories[i+1]["start"] if i+1 < len(categories) else len(menu_html)


def extract_section_meta(section_html):
    out = {}
    for field, pat in [
        ("tag", r'<span class="menu-section-tag">([^<]+)</span>'),
        ("title", r'<h3 class="menu-section-title">([^<]+)</h3>'),
        ("en", r'<span class="menu-section-en">([^<]+)</span>'),
    ]:
        m = re.search(pat, section_html)
        if m: out[field] = m.group(1).strip()
    # menu-section-desc (只有 COMBO 有)
    m = re.search(r'<p class="menu-section-desc">\s*(.*?)\s*</p>', section_html, re.DOTALL)
    if m:
        out["desc"] = re.sub(r'\s+', ' ', m.group(1)).strip()
    return out


def find_blocks_by_class(section_html, class_name):
    """穩健地找出每個指定 class 的 div 區段"""
    items = []
    pat = re.compile(rf'<div class="{class_name}"([^>]*)>')
    for m in pat.finditer(section_html):
        start = m.start()
        attrs = m.group(1)
        depth = 1
        pos = m.end()
        while pos < len(section_html):
            next_open = section_html.find('<div', pos)
            next_close = section_html.find('</div>', pos)
            if next_close == -1: break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                pos = next_close + 6
                if depth == 0:
                    items.append((attrs, section_html[start:pos]))
                    break
    return items


def parse_menu_item(attrs, ihtml):
    """解析普通菜（menu-item）"""
    if "alcohol-warning" in attrs: return None
    out = {"wide": "span 2" in attrs}
    tags = re.findall(r'<span class="item-tag([^"]*)">([^<]+)</span>', ihtml)
    if tags:
        out["tags"] = [{"style": c.strip(), "text": t.strip()} for c, t in tags]
    for field, pat in [
        ("name", r'<h4 class="item-name">([^<]+)</h4>'),
        ("en", r'<div class="item-en">([^<]+)</div>'),
        ("price", r'<div class="item-price">([^<]+)</div>'),
    ]:
        m = re.search(pat, ihtml)
        if m: out[field] = m.group(1).strip()
    m = re.search(r'<p class="item-desc">(.*?)</p>', ihtml, re.DOTALL)
    if m: out["desc"] = m.group(1).strip()
    return out


def parse_combo_card(attrs, chtml):
    """解析 COMBO 套餐卡（combo-card）"""
    out = {"type": "combo"}
    tags = re.findall(r'<span class="item-tag([^"]*)">([^<]+)</span>', chtml)
    if tags:
        out["tags"] = [{"style": c.strip(), "text": t.strip()} for c, t in tags]
    for field, pat in [
        ("name", r'<h3 class="item-name">([^<]+)</h3>'),
        ("en", r'<div class="item-en">([^<]+)</div>'),
        ("price", r'<div class="item-price"[^>]*>([^<]+)</div>'),
    ]:
        m = re.search(pat, chtml)
        if m: out[field] = m.group(1).strip()
    # combo-includes
    m = re.search(r'<ul class="combo-includes">(.*?)</ul>', chtml, re.DOTALL)
    if m:
        items = re.findall(r'<li>([^<]+)</li>', m.group(1))
        out["includes"] = [s.strip() for s in items]
    return out


sections = []
for cat in categories:
    sec_html = menu_html[cat["start"]:cat["end"]]
    meta = extract_section_meta(sec_html)
    items = []

    # 先找 combo-card（如果是 COMBO 區）
    if cat["internal_name"] == "COMBO":
        for attrs, ch in find_blocks_by_class(sec_html, "combo-card"):
            p = parse_combo_card(attrs, ch)
            if p: items.append(p)
    else:
        # 普通菜
        for attrs, ih in find_blocks_by_class(sec_html, "menu-item"):
            p = parse_menu_item(attrs, ih)
            if p:
                p["type"] = "item"
                items.append(p)

    sections.append({
        "internal_name": cat["internal_name"],
        "data_cat": cat["data_cat"],
        "meta": meta,
        "items": items,
    })
    print(f"  [{cat['internal_name']}] {meta.get('title', '?')} - {len(items)} 項")

total = sum(len(s["items"]) for s in sections)
print(f"\n總計 {total} 項")

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "menu.json"
out.write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"輸出: {out} ({out.stat().st_size//1024} KB)")
