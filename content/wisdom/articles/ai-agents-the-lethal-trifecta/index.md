+++
title = "AI Agents 的致命三重組合：安全性思考框架"
date = 2025-08-23
description = "探討 Simon Willison 提出的 AI Agents 安全性評估框架，分析 Prompt Injection 攻擊的風險條件。"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "generative-ai", "security",]

+++

作者：[Simon Willison](https://simonwillison.net/about/)

文章：[AI agents and the "lethal trifecta"](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)

蠻喜歡 Simon Willison 提出的 AI Agents 的致命三重組合（The Lethal Trifecta），可以當作思考 AI Agents 安全性的捷徑，分別是：

- **存取隱私資料**：AI Agent 能夠存取敏感或私人資訊
- **暴露在不受信任的資料**：AI Agent 會處理來自外部或不可信來源的資料
- **有能力對外溝通**：AI Agent 具備向外部服務或系統傳送資料的能力

只要使用的 AI Agents 同時具有這三種能力或在這樣的情況，就有可能受到 Prompt Injection 的攻擊，且能將隱私資料外流。

不管是開發 AI Agents 或是在自己的電腦使用 AI 串接 MCP，這個規則能在心中當作一個安全性的警鐘，注意目前使用的 AI Agents 是否有安全疑慮。
