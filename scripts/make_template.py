"""把原 HTML 改造成模板：
1. 把 menu 區塊整段換成 <!-- BUILD:MENU --> 標記
2. 把 space 區塊整段換成 <!-- BUILD:SPACE --> 標記  
3. 把 DISH_PHOTOS 物件換成 <!-- BUILD:DISH_PHOTOS --> 標記
4. 把 FORCE_PORTRAIT 換成 <!-- BUILD:FORCE_PORTRAIT --> 標記
5. 警語區塊保留在模板裡（因為飲品分類內），用佔位符標記
6. 其他區塊（NAV/HERO/MARQUEE/STORY/食材/EVENTS/GREEN&SAFE/SOCIAL/BANNER/FOOTER）原樣保留
"""
import re
from pathlib import Path

SRC = Path("/mnt/user-data/outputs/farmtable.html")
DST = Path("/home/claude/cms_build/src/index.html")
DST.parent.mkdir(parents=True, exist_ok=True)

html = SRC.read_text(encoding="utf-8")

# 1. 抓警語區塊 HTML（要放在飲品 grid 內）
warn_match = re.search(
    r'<div class="alcohol-warning"[^>]*>.*?</div>\s*</div>',
    html, re.DOTALL
)
if warn_match:
    # 警語結構是 <div class="alcohol-warning">...<img>...<strong>...</strong>...</div>
    # 但這個 regex 可能太貪婪，用更精準的：找開始 <div class="alcohol-warning"，計數對應 </div>
    warn_start = html.find('<div class="alcohol-warning"')
    depth = 1
    pos = html.find('>', warn_start) + 1
    while pos < len(html):
        no = html.find('<div', pos)
        nc = html.find('</div>', pos)
        if nc == -1: break
        if no != -1 and no < nc:
            depth += 1
            pos = no + 4
        else:
            depth -= 1
            pos = nc + 6
            if depth == 0:
                break
    warning_html_full = html[warn_start:pos]
    print(f"警語區塊長度: {len(warning_html_full)} 字元")
else:
    warning_html_full = ""

# 2. 替換 MENU 區塊（從 <!-- =================== MENU =================== --> 之後到 <!-- =================== 食材小故事）
menu_marker = "<!-- =================== MENU =================== -->"
menu_end_marker = "<!-- =================== 食材小故事 =================== -->"
menu_start_idx = html.find(menu_marker) + len(menu_marker)
menu_end_idx = html.find(menu_end_marker)

# 留下 MENU header（section 開頭、一些 wrapper），只替換 menu-section 內容
# 看一下 MENU 區塊頭部
menu_head_html = html[menu_start_idx:menu_end_idx]
# menu_head_html 大概長：
#   <section class="menu" id="menu">
#     <div class="section-head">...</div>
#     <div class="menu-tabs">...</div>
#     <!-- ===== COMBO ===== --> ... </section>
# 我需要保留 section head 和 tabs，只替換 menu sections

# 找 section 開頭
sec_open_match = re.search(r'<section class="menu"[^>]*>', menu_head_html)
section_open = sec_open_match.group(0)
section_open_end = sec_open_match.end()

# 找第一個 <!-- ===== COMBO ===== --> 的位置
first_cat_idx = menu_head_html.find("<!-- ===== COMBO ===== -->")
# 找最後 </section>
last_section_close = menu_head_html.rfind("</section>")

# 把 [first_cat_idx, last_section_close] 之間替換為 <!-- BUILD:MENU --> ... <!-- BUILD:/MENU -->
header_part = menu_head_html[:first_cat_idx]  # section_head + menu-tabs
footer_part = menu_head_html[last_section_close:]  # </section>

new_menu_html = (
    header_part +
    "<!-- BUILD:MENU -->\n  <!-- replaced at build time -->\n  <!-- BUILD:/MENU -->\n  " +
    footer_part
)

html = html[:menu_start_idx] + "\n" + new_menu_html + html[menu_end_idx:]
print(f"MENU 區塊已轉成模板")

# 3. 替換 SPACE 區塊（整個 section 內容替換）
space_start_marker = "<!-- =================== RESTAURANT SPACE =================== -->"
space_end_marker = "<!-- =================== EVENTS =================== -->"
space_start = html.find(space_start_marker) + len(space_start_marker)
space_end = html.find(space_end_marker)
space_html = html[space_start:space_end]

# 找 section 開閉
sm = re.search(r'<section class="space"[^>]*>', space_html)
section_open_idx = sm.end()
section_close_idx = space_html.rfind("</section>")

# 替換中間內容
new_space_html = (
    space_html[:section_open_idx] +
    "\n<!-- BUILD:SPACE -->\n<!-- replaced at build time -->\n<!-- BUILD:/SPACE -->\n" +
    space_html[section_close_idx:]
)

html = html[:space_start] + "\n" + new_space_html + html[space_end:]
print("SPACE 區塊已轉成模板")

# 4. 替換 DISH_PHOTOS
m = re.search(r"const DISH_PHOTOS = \{\n.*?\n  \};", html, re.DOTALL)
if m:
    html = html[:m.start()] + "<!-- BUILD:DISH_PHOTOS -->\n  /* replaced at build */\n  <!-- BUILD:/DISH_PHOTOS -->" + html[m.end():]
    print("DISH_PHOTOS 已轉成模板")

# 5. 替換 FORCE_PORTRAIT
m = re.search(r"const FORCE_PORTRAIT = new Set\(\[\n.*?\n    \]\);", html, re.DOTALL)
if m:
    html = html[:m.start()] + "<!-- BUILD:FORCE_PORTRAIT -->\n    /* replaced at build */\n    <!-- BUILD:/FORCE_PORTRAIT -->" + html[m.end():]
    print("FORCE_PORTRAIT 已轉成模板")

# 寫出
DST.write_text(html, encoding="utf-8")
print(f"\n模板大小: {DST.stat().st_size // 1024} KB")
print(f"模板輸出: {DST}")

# 把警語存出來給 build.js 用
warn_path = Path("/home/claude/cms_build/_data/_warning.html")
warn_path.write_text(warning_html_full, encoding="utf-8")
print(f"警語區塊存到: {warn_path}")
