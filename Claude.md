# 建立文章規則

1. 標題的最高層級必須是 H1，也就是 #

## Wisdom 文章

當建立新的 wisdom 文章時：

1. 在 `content/wisdom/articles/` 下建立新資料夾，資料夾名稱使用英文，應反映文章核心主題
2. 在資料夾內建立 `index.md` 檔案
3. 使用以下格式：

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

4. tags 必須使用英文
5. 建立文章後，執行 `zola build` 確認連結正確無誤
