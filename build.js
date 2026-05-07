/**
 * build.js
 *
 * 把 src/index.html (模板) + _data/*.json (內容) + images/* 組成 dist/index.html
 *
 * 模板裡有特殊註解標記，build 時會替換：
 *   <!-- BUILD:MENU --> ... <!-- BUILD:/MENU -->
 *   <!-- BUILD:SPACE --> ... <!-- BUILD:/SPACE -->
 *   <!-- BUILD:DISH_PHOTOS --> (替換 DISH_PHOTOS 物件)
 *   <!-- BUILD:FORCE_PORTRAIT --> (替換 FORCE_PORTRAIT 陣列)
 */

const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const SRC_HTML = path.join(ROOT, 'src', 'index.html');
const DATA_DIR = path.join(ROOT, '_data');
const DIST_DIR = path.join(ROOT, 'dist');

// 確保 dist 存在
if (!fs.existsSync(DIST_DIR)) fs.mkdirSync(DIST_DIR, { recursive: true });

// 讀資料
const menu = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'menu.json'), 'utf-8'));
const space = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'space.json'), 'utf-8'));
const forcePortrait = JSON.parse(fs.readFileSync(path.join(DATA_DIR, 'force_portrait.json'), 'utf-8'));

// 讀模板
let html = fs.readFileSync(SRC_HTML, 'utf-8');

// ============= 渲染菜單 =============
// 警語區塊：原樣讀入，build 時插入飲品分類末端
const warningHtml = fs.existsSync(path.join(DATA_DIR, '_warning.html'))
  ? fs.readFileSync(path.join(DATA_DIR, '_warning.html'), 'utf-8')
  : '';

function escapeHtml(s) {
  // 注意：這裡刻意「不」escape，因為菜名英文等可能含 & 等字元
  // 實際資料是受信任的（只能透過 CMS 後台寫入）
  return s == null ? '' : String(s);
}

function renderTags(tags) {
  if (!tags || tags.length === 0) return '';
  const inner = tags.map(t => {
    const cls = (t.style || '').trim();
    const clsAttr = cls ? ` ${cls}` : '';
    return `<span class="item-tag${clsAttr}">${escapeHtml(t.text)}</span>`;
  }).join('\n          ');
  return `<div class="item-tags">${inner}</div>`;
}

function renderMenuItem(item) {
  const wideAttr = item.wide ? ' style="grid-column: span 2; background: rgba(45, 74, 46, 0.05);"' : '';
  const parts = [];
  if (item.tags && item.tags.length) parts.push(`          ${renderTags(item.tags)}`);
  if (item.name) parts.push(`          <h4 class="item-name">${escapeHtml(item.name)}</h4>`);
  if (item.en) parts.push(`          <div class="item-en">${escapeHtml(item.en)}</div>`);
  if (item.desc) parts.push(`          <p class="item-desc">${escapeHtml(item.desc)}</p>`);

  const priceLine = item.price ? `        <div class="item-price">${escapeHtml(item.price)}</div>` : '';
  return `      <div class="menu-item"${wideAttr}>
        <div class="item-content">
${parts.join('\n')}
        </div>
${priceLine}
      </div>`;
}

function renderComboCard(item) {
  const includesHtml = item.includes
    ? `        <ul class="combo-includes">
${item.includes.map(s => `          <li>${escapeHtml(s)}</li>`).join('\n')}
        </ul>`
    : '';
  const tagsHtml = item.tags && item.tags.length ? renderTags(item.tags) : '';
  return `      <div class="combo-card">
        ${tagsHtml}
        <h3 class="item-name">${escapeHtml(item.name || '')}</h3>
        <div class="item-en">${escapeHtml(item.en || '')}</div>
        <div class="item-price" style="margin: 0.5rem 0;">${escapeHtml(item.price || '')}</div>
${includesHtml}
      </div>`;
}

function renderSection(sec) {
  const meta = sec.meta || {};
  const headParts = [];
  if (meta.tag) headParts.push(`      <span class="menu-section-tag">${escapeHtml(meta.tag)}</span>`);
  if (meta.title) headParts.push(`      <h3 class="menu-section-title">${escapeHtml(meta.title)}</h3>`);
  if (meta.en) headParts.push(`      <span class="menu-section-en">${escapeHtml(meta.en)}</span>`);
  const headHtml = `    <div class="menu-section-head">\n${headParts.join('\n')}\n    </div>`;

  const descHtml = meta.desc ? `\n    <p class="menu-section-desc">\n      ${escapeHtml(meta.desc)}\n    </p>` : '';

  // 渲染項目
  let itemsBlock;
  if (sec.internal_name === 'COMBO') {
    const comboList = sec.combos || sec.items || [];
    const cards = comboList.map(renderComboCard).join('\n\n');
    itemsBlock = `\n    <div class="combo-grid">\n${cards}\n    </div>`;
  } else {
    const items = (sec.items || []).map(renderMenuItem).join('\n\n');
    // 飲品分類在啤酒卡後加警語區塊
    let warningBlock = '';
    if (sec.internal_name === 'DRINK' && warningHtml) {
      warningBlock = '\n      ' + warningHtml;
    }
    itemsBlock = `\n    <div class="menu-grid">\n${items}${warningBlock}\n    </div>`;
  }

  // 對應的 show class
  const showClass = sec.internal_name === 'COMBO' ? ' show' : '';
  return `  <!-- ===== ${sec.internal_name} ===== -->
  <div class="menu-section${showClass}" data-cat="${sec.data_cat}">
${headHtml}${descHtml}${itemsBlock}
  </div>`;
}

const menuHtml = menu.map(renderSection).join('\n\n');

// ============= 渲染 DISH_PHOTOS（給 lightbox 用）=============
// 改用相對路徑而不是 base64
const dishPhotos = {};
menu.forEach(sec => {
  const list = sec.items || sec.combos || [];
  list.forEach(item => {
    if (item.image && item.name) {
      dishPhotos[item.name] = item.image;
    }
  });
});

const dishPhotosJs = `const DISH_PHOTOS = {\n` +
  Object.entries(dishPhotos).map(([k, v]) =>
    `    ${JSON.stringify(k)}: ${JSON.stringify(v)}`
  ).join(',\n') +
  `\n  };`;

const forcePortraitJs = `const FORCE_PORTRAIT = new Set([\n` +
  forcePortrait.map(k => `      ${JSON.stringify(k)}`).join(',\n') +
  `\n    ]);`;

// ============= 渲染 SPACE 區 =============
function renderHeroMeta(metaList) {
  if (!metaList || !metaList.length) return '';
  return metaList.map(m =>
    `        <div><span class="meta-label">${escapeHtml(m.label)}</span><span class="meta-value">${escapeHtml(m.value)}</span></div>`
  ).join('\n');
}

function renderSpaceCard(card, index) {
  const tagStyleAttr = card.tag_style === 'clay' ? ' style="background: var(--clay);"' : '';
  let tagInner;
  if (card.has_icon) {
    // KIDS PLAY 樣式：SVG 圖示 + 標籤
    tagInner = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v8M8 6l4-4 4 4M5 12h14l-2 9H7l-2-9z"/></svg>
          <span>${escapeHtml(card.zone_label)}</span>`;
  } else {
    tagInner = `<span class="zone-num-sm">${escapeHtml(card.zone_num)}</span>
          <span>${escapeHtml(card.zone_label)}</span>`;
  }
  return `    <div class="space-card">
      <div class="space-card-img">
        <img src="${escapeHtml(card.image)}" alt="${escapeHtml(card.alt)}" loading="lazy">
      </div>
      <div class="space-card-body">
        <div class="space-card-tag"${tagStyleAttr}>
          ${tagInner}
        </div>
        <h4>${card.title_html || ''}</h4>
        <p>${escapeHtml(card.desc)}</p>
      </div>
    </div>`;
}

const spaceHtml = `  <div class="section-head">
    <div>
      <div class="section-num">${escapeHtml(space.section_num || '')}</div>
      <h2 class="section-title">${space.section_title_html || ''}</h2>
    </div>
    <p class="section-tag">${space.section_tag || ''}</p>
  </div>

  <!-- Hero zone -->
  <div class="space-hero">
    <div class="space-hero-img">
      <img src="${escapeHtml(space.hero.image)}" alt="${escapeHtml(space.hero.alt)}" loading="lazy">
    </div>
    <div class="space-hero-caption">
      <div class="space-zone-mark">
        <span class="zone-num">${escapeHtml(space.hero.zone_num)}</span>
        <span class="zone-en">${escapeHtml(space.hero.zone_en)}</span>
      </div>
      <h3>${space.hero.title_html || ''}</h3>
      <p class="space-hero-desc">
        ${escapeHtml(space.hero.desc)}
      </p>
      <div class="space-hero-meta">
${renderHeroMeta(space.hero.meta)}
      </div>
    </div>
  </div>

  <!-- Trio -->
  <div class="space-trio">

${space.trio.map(renderSpaceCard).join('\n\n')}

  </div>`;

// ============= 把渲染結果放回模板 =============
function replaceBlock(html, marker, content) {
  const re = new RegExp(`<!-- BUILD:${marker} -->[\\s\\S]*?<!-- BUILD:/${marker} -->`, 'm');
  return html.replace(re, `<!-- BUILD:${marker} -->\n${content}\n<!-- BUILD:/${marker} -->`);
}

html = replaceBlock(html, 'MENU', menuHtml);
html = replaceBlock(html, 'SPACE', spaceHtml);
html = html.replace(/<!-- BUILD:DISH_PHOTOS -->[\s\S]*?<!-- BUILD:\/DISH_PHOTOS -->/m,
  `<!-- BUILD:DISH_PHOTOS -->\n  ${dishPhotosJs}\n  <!-- BUILD:/DISH_PHOTOS -->`);
html = html.replace(/<!-- BUILD:FORCE_PORTRAIT -->[\s\S]*?<!-- BUILD:\/FORCE_PORTRAIT -->/m,
  `<!-- BUILD:FORCE_PORTRAIT -->\n    ${forcePortraitJs}\n    <!-- BUILD:/FORCE_PORTRAIT -->`);

// 寫出
fs.writeFileSync(path.join(DIST_DIR, 'index.html'), html);

// 複製 images
function copyDir(src, dst) {
  if (!fs.existsSync(dst)) fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const sp = path.join(src, entry.name);
    const dp = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDir(sp, dp);
    else fs.copyFileSync(sp, dp);
  }
}
copyDir(path.join(ROOT, 'images'), path.join(DIST_DIR, 'images'));

// 複製 admin
if (fs.existsSync(path.join(ROOT, 'admin'))) {
  copyDir(path.join(ROOT, 'admin'), path.join(DIST_DIR, 'admin'));
}

console.log(`✓ Built ${DIST_DIR}/index.html (${(html.length/1024).toFixed(0)} KB)`);
console.log(`✓ Copied images/ to ${DIST_DIR}/images/`);
