# 農人餐桌 官網 + 後台

這個 repo 包含農人餐桌的官網原始碼，整合了 Decap CMS 後台，可在 `/admin` 路徑登入修改菜單和餐廳空間。

---

## 📁 專案結構

```
afarmtable/
├── src/index.html         ← 模板（含 BUILD 標記）
├── _data/                 ← 內容資料（後台會寫入這裡）
│   ├── menu.json          ← 50 道菜（含 COMBO）
│   ├── space.json         ← 餐廳空間 4 個區域
│   ├── force_portrait.json← 強制直式圖片清單
│   └── _warning.html      ← 酒精警語區塊（HTML 片段）
├── images/
│   ├── menu/              ← 50 張菜品照（後台上傳）
│   └── space/             ← 4 張空間照（後台上傳）
├── admin/                 ← Decap CMS 後台
│   ├── index.html         ← 後台入口（→ /admin/）
│   └── config.yml         ← 後台欄位 schema
├── build.js               ← 把 src + _data 組成 dist
├── netlify.toml           ← Netlify 設定（含 build 指令）
├── package.json           ← Node 設定
├── scripts/               ← 提取/維護腳本（部署不需要）
└── dist/                  ← build 產出（給 Netlify 部署用）
```

---

## 🚀 部署步驟

### 1. 把這個 repo push 到 GitHub
```bash
git init
git add .
git commit -m "Initial deploy with Decap CMS"
git remote add origin https://github.com/<USER>/afarmtable.git
git push -u origin main
```

或用 GitHub 網頁版「Upload files」介面拖曳上傳。

### 2. Netlify 連結 GitHub repo（你已完成）
在 Netlify 建好的 site → Site settings 確認：
- **Build command**: `node build.js`
- **Publish directory**: `dist`
- **Branch**: `main`

### 3. 啟用 Netlify Identity（重要，後台登入需要）

1. Netlify Dashboard → Site → **Identity** → Click **Enable Identity**
2. **Registration preferences** 改為 **Invite only**（避免任何人註冊）
3. **External providers**（可選）：可以開啟 Google / GitHub 登入

### 4. 啟用 Git Gateway

1. Netlify Dashboard → Site → **Identity** → **Services** 區
2. 點 **Enable Git Gateway**

### 5. 邀請第一位後台用戶（你自己）

1. Netlify Dashboard → Site → **Identity** → **Invite users**
2. 輸入你的 email → 寄出
3. 你的信箱會收到邀請連結 → 點擊 → 設定密碼
4. 之後到 `https://你的網址/admin/` 用 email + 密碼登入

---

## ✏️ 日常使用：修改菜單

1. 打開 `https://你的網址/admin/`
2. 用邀請的 email + 密碼登入
3. 左側選單會看到：
   - 📋 菜單管理
   - 🏠 餐廳空間
4. 點進去填表單修改 → 點右上 **Publish** → 儲存
5. **約 1–2 分鐘後**，網站會自動更新（Netlify 重新 build）

> ⚠️ 後台改動會自動 commit 到你的 GitHub repo。你可以在 GitHub 看到完整版本紀錄、需要時可以 rollback。

---

## 🛠️ 開發/維護

### 本地測試 build
需要 Node.js 20+
```bash
node build.js
# 輸出在 dist/index.html
```

### 修改非後台覆蓋的內容（譬如警語、Hero 文案、社群連結）
直接編輯 `src/index.html`，再跑 `node build.js`。

### 新增菜色
建議直接從後台新增。如果需要批量處理，可參考 `scripts/extract_menu.py`。

---

## ⚠️ 重要提醒

### 千萬不要動的東西
- `internal_name`（菜單分類的內部代號）
- `data_cat`（菜單分類的 tab 屬性）
- 警語區塊（`_warning.html`，法規規範，亂改會違法）

### 圖片命名
後台上傳圖片時，建議用「菜名 + 副檔名」當檔名（譬如 `嚴選海陸歡樂餐.webp`），這樣將來維護時容易對應。

### 部署失敗排查
1. Netlify Dashboard → Site → **Deploys** → 點失敗的部署看 log
2. 常見原因：menu.json 格式錯誤、build.js 缺檔
3. 從 GitHub commit 紀錄 rollback 到上一個成功版本

---

## 📞 後台用戶管理

- 邀請新用戶：Identity → Invite users
- 移除用戶：Identity → 找到該用戶 → Delete
- 重設密碼：用戶在登入頁點 "Forgot password"

免費方案上限：**5 個 active users**。超過要升級。

---

## 🔄 rollback 策略

如果某次後台改動把網站搞壞了：

1. Netlify Dashboard → Deploys
2. 找到上次正常的部署
3. 點 ⋮ → **Publish deploy**
4. 網站立刻回到那個版本
5. 然後到後台 → 重做正確的修改

或在 GitHub repo 用 git revert。
