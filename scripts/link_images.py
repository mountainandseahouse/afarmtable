"""
把 images/menu/*.webp 對映回 menu.json 的每一道菜
（用菜名 + 副檔名替換不安全字元的方式對應）
"""
import json, re
from pathlib import Path

MENU = Path("/home/claude/cms_build/_data/menu.json")
IMG_DIR = Path("/home/claude/cms_build/images/menu")

def safe_filename(name):
    return re.sub(r'[\\/:*?"<>|]', '_', name)

# 列出所有圖片
all_imgs = list(IMG_DIR.iterdir())
print(f"圖片總數: {len(all_imgs)}")

# 用 stem (檔名不含副檔名) 對映
img_by_stem = {}
for img in all_imgs:
    img_by_stem[img.stem] = img.name

data = json.loads(MENU.read_text(encoding="utf-8"))

matched = 0
unmatched = []
for sec in data:
    list_key = "combos" if "combos" in sec else "items"
    for item in sec.get(list_key, []):
        if "name" not in item:
            continue
        # 嘗試用菜名對映
        clean_name = safe_filename(item["name"])
        if clean_name in img_by_stem:
            item["image"] = f"/images/menu/{img_by_stem[clean_name]}"
            matched += 1
        else:
            # 試試用 _ 換空白
            alt = clean_name.replace(" ", "_")
            if alt in img_by_stem:
                item["image"] = f"/images/menu/{img_by_stem[alt]}"
                matched += 1
            else:
                unmatched.append(item["name"])

print(f"成功對映: {matched}")
if unmatched:
    print(f"未對映 ({len(unmatched)}):")
    for n in unmatched:
        print(f"  - {n!r}")

MENU.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n已更新 menu.json")
