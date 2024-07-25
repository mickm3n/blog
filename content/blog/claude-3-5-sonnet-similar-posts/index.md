+++
title = "與 Claude 3.5 Sonnet 協作開發「相似文章推薦」"
date = 2024-07-25

[taxonomies]
categories = ["經驗分享"]
tags = ["generative-ai"]

[extra]
image = "og-image.webp"
+++

# 動機

上次【[與 Claude 3.5 Sonnet 協作完成開發並部署 RSS Filter 到 Netlify Functions 上](@/blog/claude-3-5-sonnet-build-functions/index.md)】的體驗良好，對於用 AI 來協作開發蠻感興趣的，想藉由這樣的模式做更多事，擴大自己能夠開發的項目範圍。

最近對中文文字處理蠻感興趣的，做了短暫的研究後，發現這幾年自然語言處理在 Transformer 模型出現之後快速的起飛。從五年前的 [Bidirectional Encoder Representations from Transformers (BERT)](https://zh.wikipedia.org/zh-tw/BERT) 到最近兩年很紅的的 [Generative Pre-Training (GPT)](https://zh.wikipedia.org/zh-tw/%E5%9F%BA%E4%BA%8E%E8%BD%AC%E6%8D%A2%E5%99%A8%E7%9A%84%E7%94%9F%E6%88%90%E5%BC%8F%E9%A2%84%E8%AE%AD%E7%BB%83%E6%A8%A1%E5%9E%8B)，利用預訓練好的語言模型，在大多數的自然語言處理問題就已經有一定的水準。

一直以來，都想在自己的部落格裡做相似文章的推薦，不過之前會卡在不知道怎麼處理中文最適合，所以遲遲沒有下手。在 2024 大型語言模型很流行的今天，感覺直接把整篇文章轉成語意向量（Embedding）就能達到一定的水準，如此簡單直接的方式，也很適合當作一個小練習。

# 作法

簡單拆解這個任務會有以下步驟：
1. 算出每篇文章的語意向量
2. 對於每兩篇文章計算向量的距離，距離越小表示越相似
3. 對每篇文章選出最相似的 N 筆文章
4. 在每篇文章的結尾用 Card View 放最相似的文章
5. 最後設定 Github Actions 在文章更新時自動更新語意向量和最相似的文章

[Anthropic](https://docs.anthropic.com/en/docs/build-with-claude/embeddings) 本身沒有出 Embedding API，最後在 [OpenAI](https://platform.openai.com/docs/guides/embeddings/what-are-embeddings) 和 [Gemini](https://ai.google.dev/gemini-api/docs/embeddings) 選擇文件比較詳細的 OpenAI。

流程上甚至可以直接參考 OpenAI 提供的【[Recommendation using embeddings and nearest neighbor search](https://cookbook.openai.com/examples/recommendation_using_embeddings)】範例，很接近我們設定的目標，在這個範例還有提供對 Embeddings 做快取的步驟，減少 API 的使用量，減少計算成本。

過程中有遇到處理 Zola 的 Markdown 的問題，需要額外處理 [Front matter](https://www.getzola.org/documentation/content/page/#front-matter)，不過只要進一步提供 AI 一個範例和你想取出的部分，就能快速生成堪用的程式碼。

而第二步和第三步的交叉計算與取 [K Nearest Neighbor (KNN)](https://zh.wikipedia.org/zh-tw/K-%E8%BF%91%E9%82%BB%E7%AE%97%E6%B3%95) 的運算也都是很常見的程式，在遇到效能瓶頸之前生成的代碼基本上都沒問題。

生成上最困難的部分是與 Zola 的整合，一方面因為比較小眾，AI 的答案較容易出現幻覺，給出無法用的代碼；一方面測試上與除錯也不太容易。

之前在做 Google Analytics View Count 的整合時，有發現可以利用 [load_data](https://www.getzola.org/documentation/templates/overview/#load-data) 的方法，去讀取預先算好的檔案。這次也是直接把算好的最相似網頁儲存成一個 Map，用 `page.path` 當索引鍵，用來取得最相近的網頁的檔案路徑，因為 [get_page](https://www.getzola.org/documentation/templates/overview/#get-page) 需要用檔案路徑當作參數。

```json,linenos
{
    "/changelog/": "blog/wordpress-to-zola/index.md:blog/comment-system/index.md:blog/fix-open-graph-in-twitter-card/index.md",
    "/about/": "blog/wordpress-to-zola/index.md:wisdom/articles/15-years-in-programming.md:changelog.md",
    "...": "...",
}
```
當有多個檔案路徑時，我目前用冒號做分隔。

最後就可以在 template 中讀取檔案、分割字串、用 `get_page` 得到 `page` 的物件：
```html,linenos
{% set top_3_nn = load_data(path="static/data/top_3_nn.json") %}
{% if top_3_nn[page.path] %}
{% set top_3_nn_paths = top_3_nn[page.path] | split(pat=":") %}
{% for path in top_3_nn_paths %}
{% set page = get_page(path=path) %}
{{ macro::card(page=page) }}
{% endfor %}
{% endif %}
```

接著是整合進網頁，這邊就是 AI 比我擅長的部分，方法是提供一個類似樣式的圖片，要求 AI 生成 HTML 和 CSS 樣式，而最難的部分也還是 zola 的整合，這次的做法是寫一個 macro，能利用上一步傳入的 page 物件組合出 card view 需要的資訊。
```html,linenos,hl_lines=9-16
{% macro card(page) %}
{% if page.extra.image %}
{% set image = config.base_url ~ page.path ~ page.extra.image %}
{% else %}
{% set image = get_url(path="images/default-og-image.webp") %}
{% endif %}
{% set ancestors = page.ancestors %}
{% set breadcrumb = "" %}
{% for ancestor in ancestors %}
{% set section = get_section(path=ancestor) %}
{% if loop.first %}
{% set_global breadcrumb = '<a href="' ~ section.permalink ~ '">' ~ section.title ~ '</a>' %}
{% else %}
{% set_global breadcrumb = breadcrumb ~ ' > ' ~ '<a href="' ~ section.permalink ~ '">' ~ section.title ~ '</a>' %}
{% endif %}
{% endfor %}
<div class="recommended-article">
    <div class="article-image">
        <img src="{{ image }}">
    </div>
    <div class="article-info">
        <div class="article-meta">
            <span class="article-category">{{ breadcrumb | safe }}</span>
            <span class="article-date">{{ page.date }}</span>
        </div>
        <h3 class="article-title">
            <a href="{{ page.permalink }}">{{ page.title }}</a>
        </h3>
    </div>
</div>
{% endmacro card %}
```

過程中有踩到一個雷是在 Tera 的迴圈裡，如果用 `set` 去改變變數的值，變動的影響範圍只有在迴圈內（如上圖 highlight 處）。要影響到外面的變數，要使用 `set_global`，詳見 [Assignments](https://keats.github.io/tera/docs/#assignments)。

最後生成 Github Actions 的 Template 也是很常見的任務，只是有可能會用到比較舊版的 Action 或者是不會自動幫你設定程式語言的版本或是對 Dependency 或結果做快取，這些細節還是需要根據需求額外看文件做調整。

# 心得

之前阻止自己去開發的原因，主要有三：
* 缺乏先備知識
* 程式開發的初始摩擦力
* 與美觀和使用者介面相關的調整，如 HTML 和 CSS

與生成式 AI 協作可以用很短的時間突破後兩項。在研究先備知識上，只要是夠普遍的知識，跟 AI 做討論出現幻覺的機率也會比較低。在生成式 AI 時代，多嘗試創造擴大能力邊界真的是蠻重要的事。
