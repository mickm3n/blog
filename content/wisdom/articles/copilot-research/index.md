+++
title = "Github Copilot 造成程式碼品質下降"
date = 2024-02-16
description = "研究顯示，GitHub Copilot 可能會降低程式碼品質，尤其在大型專案中，易增加重複代碼且對重構無幫助。"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "generative-ai", "github-copilot",]

+++

創作者：David Ramel From [Visual Studio Magazine](https://visualstudiomagazine.com/Home.aspx)

文章：[New GitHub Copilot Research Finds 'Downward Pressure on Code Quality'](https://visualstudiomagazine.com/articles/2024/01/25/copilot-research.aspx)

跟之前 [用 Github Copilot 寫新學的 Rust 的感觸](@/blog/2023-github-copilot/index.md) 類似：在小範圍可以幫助產生代碼，即使在不熟悉語言的情況下。

但在有成熟架構的大專案裡會帶來很多缺點：
* 增加重複的程式碼，而不是重用
* 在重構（Refactoring）上沒有幫助

也想到之前看過的這篇《[面試應該用 Code Review 取代 Leetcode](https://chrlschn.dev/blog/2023/07/interviews-age-of-ai-ditch-leetcode-try-code-reviews-instead/)》。

演算法相關問題的程式碼能夠快速生成之後，大型程式碼的解讀、優化與溝通能力才是與 AI 時代最需要的能力。
