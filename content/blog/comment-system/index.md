+++
title = "留言功能上線"
date = "2023-06-16"

[taxonomies]
categories = ["網站開發紀錄"]
tags = ["SSG", "zola", "utteranc.es"]

[extra]
image = ""
+++

# 為什麼想要有留言功能

最主要還是想維持網站更新動能。留言功能對我來說好像不太重要，主要是我的文章還是偏心得為主，感覺互動的需求很低。不過可以透過實裝留言功能來檢驗真實的情況也蠻有趣的。另外雖然也可以透過 Twitter 和 Email 聯繫我，但總覺得在網頁上直接有方式留言還是會比較順暢。

# 選擇留言功能的考量點

在 Zola 並沒有官方推薦的留言功能實現方式，而 [Hugo](https://gohugo.io/content-management/comments/) 內建是用 Disqus。但 [Disqus 有蠻多負面評論](https://fatfrogmedia.com/delete-disqus-comments-wordpress/) ，不管在網站效能影響和用戶隱私性上都有一些問題。

既然 Zola 和 Hugo 同為 SSG（Static Site Generator），這次打算從 Hugo 的 [Disqus Alternatives](https://gohugo.io/content-management/comments/#alternatives) 當作嘗試的列表。

原本對於留言功能的考量點沒有太多的想法，不過在嘗試中也漸漸感受到各種方法的差異。

以下以我覺得的重要程度排序：

1. 費用及實現容易度
  - 是否收費？
  - 是否需要自架服務？
2. 可控性
  - 是否有很大的網站效能影響？
  - 是否是 open source？是否還有持續更新？
3. 功能性
  - 是否支援匿名留言？是否支援使用者填入其他資訊？是否提供第三方 Identity Provider (Twitter, Facebook, ...) 登入的方式？
  - 是否支援留言通知功能？
  - 是否只能單純留言，或是可以巢狀回應留言？
4. 安全性
  - 留言內容儲存在自己能控制的地方，還是在提供服務的網站上？
  - 資訊安全考量，第三方的 javascript 是否有插入惡意程式的可能性？

# Disqus Alternatives 的嘗試

## 費用及實現容易度

目前還在評估網站留言功能重要性的階段，不想在現在就產生固定成本，就算有成本也希望能根據用量來計算，至少在留言很少的初期可以幾乎不用費用。於是就淘汰大量的收費服務如 Commento、Hyvor Talk、Mutt、ReplyBox、Talkyard，當中 ReplyBox 有根據流量設計不同的方案，但最低還是要每個月 5 美元。找價格低廉的雲端服務自架或許是可考量的方式，不過目前還沒有想投入太多時間研究，所以也就淘汰了 Isso、Remark42、Staticman、Talkyard。

## 可控性

照順序嘗試到 IntenseDebate 的時候覺得還可以，不用收費，有通知功能，安裝上也很簡易。不過似乎跟 Disqus 有一些共同的問題，也有人提到一些效能上的問題，不過有在實裝後跑了 [PageSpeed](https://pagespeed.web.dev/analysis/https-blog-mickzh-com-reading-notes-the-book-of-joy/q60v9g9oe4?form_factor=mobile)，覺得效能上好像問題不大。不過反而是 Accessibility 忽然降低很多，想像上是安插了留言功能的程式碼的品質不好。此外在開啟 Twitter 登入功能也遇到 Token 失效的問題，加上不是 open source，忽然有一種如果有問題會難解決的感覺，就降低了想使用的慾望。

## 功能性

### Cactus
只能簡易用名稱留言、沒有留言通知、沒有巢狀留言

### IntenseDebate
預設支援用 IntenseDebate 和 Wordpress 的帳號，可以額外開啟 Twitter 和 Facebook 登入，但是 Twitter 開啟後發現有錯誤且無方法修正。支援 Email 留言通知、支援巢狀留言。

### GraphCommento
在設定上卡關無法嘗試。

### Utteranc.es
用 Github Issues 當作儲存留言的地方，只支援用 Github 帳號留言。新留言可以直接透過 Github 的通知。無法用巢狀回覆。

# 最後選擇 Utteranc.es

最後在嘗試完 Utteranc.es、IntenseDebate、Cactus、GraphCommento 後暫時先選了 [Utteranc.es](https://utteranc.es/)。在上線後用 [PageSpeed](https://pagespeed.web.dev/analysis/https-blog-mickzh-com-reading-notes-the-book-of-joy/5xw6sf5fbk?form_factor=mobile)測試的差異不大，javascript 也很簡單。

目前留言功能就會用 Utteranc.es 的樣貌先上線，或許我應該要做個簡易的按鈕讓使用者可以回報討厭用 Github 登入來收集反向的聲音。下一步可以考慮一下這件事要怎麼達成。歡迎大家可以利用留言功能與我互動。
