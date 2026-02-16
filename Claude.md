# 部落格架構

## 技術框架
- 使用 [Zola](https://www.getzola.org/) 靜態網站產生器
- 設定檔：`config.toml`
- 語言：`zh-tw`（繁體中文）
- 部署平台：Netlify（見 `netlify.toml`）

## 內容結構

```
content/
├── blog/                          # 原創文章（經驗分享）
├── wisdom/articles/               # 閱讀筆記（讀別人文章的心得）
├── about/                         # 關於頁面
├── now/                           # Now 頁面
├── reading-notes/                 # 讀書筆記
└── changelog/                     # 變更記錄
```

每篇文章放在獨立資料夾中，資料夾名稱使用英文，內含 `index.md` 和相關圖片。

## 建立文章規則

1. 標題的最高層級必須是 H1，也就是 #
2. tags 必須使用英文
3. 建立文章後，執行 `zola build` 確認連結正確無誤

### Blog 文章（經驗分享）

在 `content/blog/` 下建立新資料夾：

```markdown
+++
title = "文章標題"
date = YYYY-MM-DD
description = "文章描述"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "tag1", "tag2",]

[extra]
image = "圖片檔名.webp"   # 選用，用於 Open Graph
+++

文章內容...
```

### Wisdom 文章（閱讀筆記）

在 `content/wisdom/articles/` 下建立新資料夾：

```markdown
+++
title = "文章標題"
date = YYYY-MM-DD
description = "文章描述"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "tag1", "tag2",]

+++

創作者：[作者名稱](作者連結)

文章：[文章標題](文章連結)

文章內容...
```

## 內部連結語法

使用 Zola 的內部連結格式引用其他文章：
- Blog 文章：`[顯示文字](@/blog/資料夾名稱/index.md)`
- Wisdom 文章：`[顯示文字](@/wisdom/articles/資料夾名稱/index.md)`

## 圖片標註格式

```html
![](image.webp)
<p class="image-caption">圖片說明 from <a href="來源網址">來源名稱</a></p>
```

## 嵌入 YouTube

```
{{ youtube(id="影片ID") }}
```

# 寫作風格

## 語言
- 主要使用繁體中文
- 技術名詞保留英文（如 Prompt Injection、Agent、Cron Job、Tool Policy）
- 中英混合自然切換，不刻意翻譯已有共識的技術術語

## 語氣與結構
- 對話式語氣，像在跟朋友分享經驗，不是寫論文
- 用第一人稱「我」自然敘述
- 段落簡短直接，不拖泥帶水
- 列點用於列舉，但主要敘事用段落
- 常從個人經驗或前幾篇文章的脈絡開頭，帶出本篇主題
- 文末通常有「心得」或「小結」段落作收尾反思
- 偶爾用 `>` blockquote 插入個人的旁白或吐槽

## 閱讀筆記風格
- 開頭列出原作者和文章連結
- 用自己的話重新整理重點，不是逐段翻譯
- 加入自己的觀點和延伸思考
- 篇幅精簡，抓核心概念

## 經驗分享風格
- 從實際遇到的問題或情境出發
- 記錄過程中踩到的坑和解決方式
- 包含具體的程式碼、指令、設定
- 有清楚的步驟或架構說明
