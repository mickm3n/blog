+++
title = "OpenClaw 掃雷：Cron Job 的 Delivery Mode"
date = 2026-02-13
description = "在設定 OpenClaw Cron Job 時踩到 Announce Delivery Mode 的雷——輸出格式怎麼改都不對，最後發現是系統多做了一層 LLM 摘要。記錄排查過程與兩種 Delivery Mode 的差異。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw",]

+++

上一篇介紹了【[透過 Tailscale 從任何裝置存取家裡的 OpenClaw](@/blog/openclaw-tailscale-integration/index.md)】的設定，這篇接著記錄在設定 Cron Job 時踩到的雷。

# 起因

最近在幫龍蝦設定 Cron Job，想讓他定期做一些任務，然後把結果送到 Slack。在設定的過程中，龍蝦建議可以用 `announce` 這個 delivery mode——這樣 Agent 就不需要額外呼叫 Slack 的 message 工具來發訊息，只要設定好目標 channel 的資訊，系統就會自動把結果送過去。

聽起來蠻合理的，少一個步驟、少一層出錯的可能，就接受了龍蝦的提議。

# 格式怎麼改都不對

設定完之後，Cron Job 確實會跑，Slack 也確實收到了訊息。但問題是——**送到 Slack 的內容格式完全不對**。

我在 prompt 裡很明確地定義了輸出的格式，包含表格、條列、特定的 Markdown 結構，但最後到 Slack 的內容都變成了散文式的段落，結構全部被打散。

跟龍蝦來來回回改了好幾次 prompt，試過各種強化語氣的寫法——「嚴格遵守以下格式」、「禁止任何改寫」——結果都一樣。Agent 產出的原始內容其實格式是對的，但送到 Slack 之後就變了樣。

這個狀況蠻讓人困惑的，因為如果你只看 Agent 的 log，會發現他確實按照你的要求產出了正確格式的內容，但最終到達 Slack 的東西就是不一樣。

# 找到真正的原因

後來跟 Claude Code 一起仔細看執行的細節，才發現問題出在 `announce` delivery mode 的機制。

在 `announce` 模式下，Agent 產出回覆之後，**系統會對 Agent 的原始輸出再做一次 LLM 摘要**，然後把摘要（不是原文）送到指定的 channel。也就是說，不管你在 prompt 裡怎麼精心設計輸出格式，最後都會被這一層摘要改寫成散文。

難怪怎麼調 prompt 都沒用——問題根本不在 Agent 那端，而是在 delivery 的過程中被系統插了一手。

最後把 delivery mode 改成 `none` 就解決了：

```bash
openclaw cron edit <jobId> --no-deliver
```

改成 `none` 之後，Agent 需要自己呼叫 message 工具把內容發到 Slack，但好處是你可以完全控制送出去的內容，格式不會被動到。

# Announce Delivery Mode 是什麼

回頭整理一下 OpenClaw Cron Job 的兩種 delivery mode。

## `announce` 模式（預設）

執行流程：
1. Isolated session 的 Agent 根據 `payload.message` 產出回覆
2. 系統對 Agent 的原始輸出做一次 LLM 摘要
3. 摘要被送到 `delivery.channel` + `delivery.to` 指定的目標
4. 同時，一個簡短摘要也會 post 到 main session

設定方式：

```bash
openclaw cron edit <jobId> --announce
```

## `none` 模式

- 系統不做任何 delivery
- Agent 需要自己使用 message 工具直接發訊息到目標 channel
- 輸出內容完全由 Agent 控制，格式不會被改寫

設定方式：

```bash
openclaw cron edit <jobId> --no-deliver
```

在 `none` 模式下，需要在 `payload.message` 裡明確指示 Agent 使用 message 工具發送訊息，例如：「使用 message 工具將完整內容原文發送到 Slack channel `<channelId>`」。

# 什麼時候適合用 Announce

雖然這次踩了雷，但 `announce` 模式本身的設計其實是有道理的。它的核心概念是：**把 Agent 冗長的執行過程壓縮成一則人類可讀的通知**。

適合的場景：

- **監控告警型任務**：「每天檢查伺服器狀態，有異常就通知我」。Agent 可能做了大量分析——查 logs、跑 health check、比較 metrics——但你只需要一句「一切正常」或「CPU 異常偏高」。這種情境下摘要反而是你要的。
- **資訊彙整型任務**：「每週整理 GitHub issues 進度」。Agent 的原始產出可能很長，摘要幫你抓重點推到 channel。
- **懶人模式**：不需要在 prompt 裡處理 message 工具的呼叫邏輯，系統自動搞定 delivery，設定成本最低。

不適合的場景：

- **格式敏感的輸出**：表格、清單、特定 Markdown 結構——摘要會把結構打散
- **原文轉發需求**：你希望 Agent 產出什麼，channel 就收到什麼
- **結構化內容**：摘要傾向壓縮成散文，會丟失原始排版

簡單來說，`announce` 是「我只想被通知結果，不在乎格式」的模式；`none` 是「我要完全控制輸出」的模式。根據任務的性質選擇就好。

# 小結

這次的經驗其實蠻典型的——問題的表象是「Agent 不聽話、格式一直錯」，但真正的原因是對系統機制不夠了解。如果只是一直改 prompt，永遠不會解決問題，因為問題不在 prompt。

在用這類 AI Agent 平台的時候，理解系統在你的 prompt 和最終輸出之間做了哪些事情，還是蠻重要的。不然會花很多時間在錯誤的地方除錯。
