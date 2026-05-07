"""
提取菜單資料 v3：兩套 schema
- 普通菜（MEAT/PASTA/VEGGIE/KIDS/SIDE/DESSERT/DRINK）→ items[]
- COMBO 套餐 → combos[]，每個有 includes 清單
"""
import re, json
from pathlib import Path

SRC = Path("/mnt/user-data/outputs/farmtable.html")
OUT_DIR = Path("/home/claude/cms_build/_data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
html = SRC.read_text(encoding="utf-8")

menu_start = html.find("<!-- =================== MENU =================== -->")
menu_end = html.find("<!-- =================== 食材小故事 =================== -->")
menu_html = html[menu_start:menu_end]

# 找各分類區段
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

    # COMBO 區獨有的 menu-section-desc
    m = re.search(r'<p class="menu-section-desc">\s*(.*?)\s*</p>', section_html, re.DOTALL)
    if m:
        # 清理多餘空白
        desc = re.sub(r'\s+', ' ', m.group(1)).strip()
        out["desc"] = desc
    return out


def find_blocks(section_html, class_match):
    """找指定 class 的 div 區塊（深度匹配）"""
    items = []
    for m in re.finditer(rf'<div class="{class_match}"([^>]*)>', section_html):
        start = m.start()
        attrs = m.group(1)
        depth = 1
        pos = m.end()
        while pos < len(section_html):
            no = section_html.find('<div', pos)
            nc = section_html.find('</div>', pos)
            if nc == -1: break
            if no != -1 and no < nc:
                depth += 1; pos = no + 4
            else:
                depth -= 1; pos = nc + 6
                if depth == 0:
                    items.append((attrs, section_html[start:pos]))
                    break
    return items


def parse_menu_item(attrs, ihtml):
    if "alcohol-warning" in attrs: return None
    out = {"wide": "span 2" in attrs}
    tags = re.findall(r'<span class="item-tag([^"]*)">([^<]+)</span>', ihtml)
    if tags:
        out["tags"] = [{"style": c.strip(), "text": t.strip()} for c, t in tags]
    for f, p in [
        ("name", r'<h4 class="item-name">([^<]+)</h4>'),
        ("en", r'<div class="item-en">([^<]+)</div>'),
        ("price", r'<div class="item-price">([^<]+)</div>'),
    ]:
        m = re.search(p, ihtml)
        if m: out[f] = m.group(1).strip()
    m = re.search(r'<p class="item-desc">(.*?)</p>', ihtml, re.DOTALL)
    if m: out["desc"] = re.sub(r'\s+', ' ', m.group(1)).strip()
    return out


def parse_combo_card(attrs, chtml):
    """COMBO 卡片：item-tags + item-name (h3) + item-en + item-price + combo-includes (ul li)"""
    out = {}
    tags = re.findall(r'<span class="item-tag([^"]*)">([^<]+)</span>', chtml)
    if tags:
        out["tags"] = [{"style": c.strip(), "text": t.strip()} for c, t in tags]
    for f, p in [
        ("name", r'<h3 class="item-name">([^<]+)</h3>'),
        ("en", r'<div class="item-en">([^<]+)</div>'),
        ("price", r'<div class="item-price"[^>]*>([^<]+)</div>'),
    ]:
        m = re.search(p, chtml)
        if m: out[f] = m.group(1).strip()

    # combo-includes 的 li 們
    includes_match = re.search(r'<ul class="combo-includes">(.*?)</ul>', chtml, re.DOTALL)
    if includes_match:
        includes_html = includes_match.group(1)
        items = re.findall(r'<li>(.*?)</li>', includes_html, re.DOTALL)
        out["includes"] = [re.sub(r'\s+', ' ', i).strip() for i in items]
    return out


sections = []
for cat in categories:
    sec_html = menu_html[cat["start"]:cat["end"]]
    meta = extract_section_meta(sec_html)
    section = {
        "internal_name": cat["internal_name"],
        "data_cat": cat["data_cat"],
        "meta": meta,
    }

    if cat["internal_name"] == "COMBO":
        # 用 combo-card
        combos = []
        for attrs, chtml in find_blocks(sec_html, "combo-card"):
            parsed = parse_combo_card(attrs, chtml)
            if parsed: combos.append(parsed)
        section["combos"] = combos
        section["type"] = "combo"
        print(f"  [COMBO] {meta.get('title', '?')} - {len(combos)} 套餐")
    else:
        items = []
        for attrs, ihtml in find_blocks(sec_html, "menu-item"):
            p = parse_menu_item(attrs, ihtml)
            if p: items.append(p)
        section["items"] = items
        section["type"] = "regular"
        print(f"  [{cat['internal_name']}] {meta.get('title', '?')} - {len(items)} 道菜")

    sections.append(section)

regular_count = sum(len(s.get("items", [])) for s in sections)
combo_count = sum(len(s.get("combos", [])) for s in sections)
print(f"\n總計: {regular_count} 道普通菜 + {combo_count} 套餐 = {regular_count + combo_count}")

out = OUT_DIR / "menu.json"
out.write_text(json.dumps(sections, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"輸出: {out} ({out.stat().st_size//1024} KB)")
