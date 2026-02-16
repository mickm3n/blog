+++
title = "龍蝦（OpenClaw）掃雷記錄：Cron Job 的 Delivery Mode"
date = 2026-02-16
description = "在設定 OpenClaw Cron Job 時踩到 Announce Delivery Mode 的雷——輸出格式怎麼改都不對，最後發現是系統多做了一層 LLM 摘要。記錄排查過程與兩種 Delivery Mode 的差異。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw",]

[extra]
image = "openclaw-debug.webp"

+++

在【[上一篇](@/blog/openclaw-heartbeat-vs-isolated-cron/index.md)】介紹了 Heartbeat Cron 與 Isolated Cron 的差異與適用情境，後來分析自己都沒有需要跑在 Main Session 的場景，所以把現有的定時任務都改成了 Isolated Cron，也關掉了 Heartbeat。但在修改的過程又踩了一個雷，**設定好的 Cron Job 最後的結果都沒有符合自己設定的格式**。這篇記錄一下排查的過程。

# 起因

在重新把 Cron Job 改為 Isolated Cron 的過程中，龍蝦建議可以用 `announce` Delivery Mode，只要設定好結果要送的 Channel，系統就會自動把結果送過去，這樣 Agent 就不需要額外呼叫 Slack 的 Message 工具來發訊息。**嗯，聽起來很合理。**

> 發現跟龍蝦一起設定遇到的問題都是聽起來很合理就接受了🤣

# 格式怎麼改都不對

![](openclaw-debug.webp)

設定完之後，Cron Job 確實會跑，Slack 也確實收到了訊息。但問題是「**送到 Slack 的內容格式，和與龍蝦討論完設定甚至是測試後的格式都不一樣**」。

我在 Prompt 裡很明確地定義了輸出的格式，甚至給了參考範例（[Few Shot Prompting](https://www.promptingguide.ai/techniques/fewshot)），但最後到 Slack 的內容都變成了總結式的段落，沒有依照設定的格式。

要求龍蝦來來回回嘗試改了好幾次，甚至請龍蝦跑了測試，都說沒有問題，但最後送到 Slack 的訊息還是一直重複一樣的問題。燒了 Token 卻沒有任何進展，只是重複地做無效的嘗試。

# 找到真正的原因

後來放棄委任式地讓龍蝦嘗試修改，直接和 Claude Code 一起仔細看執行的細節，才發現問題出在 `announce` Delivery Mode 的機制。

在 `announce` 模式下，Agent 產出回覆之後，**系統會對 Agent 的原始輸出再做一次 LLM 摘要**，然後把摘要送到指定的 Channel。也就是說，不管在 Prompt 裡怎麼精心設計輸出格式，最後都會被這一層摘要改寫成總結式的結果。

最後把 Delivery Mode 改成 `none` 就解決了。改成 `none` 之後，Agent 需要自己呼叫 Message 工具把內容發到 Slack，但你可以完全控制送出去的內容，格式不會被動到。

# Announce Delivery Mode 是什麼

回頭整理一下 OpenClaw Cron Job 的兩種 Delivery Mode。

## `announce` 模式（預設）

執行流程：
1. Isolated Session 的 Agent 根據 `payload.message` 產出回覆
2. 系統對 Agent 的原始輸出做一次 LLM 摘要
3. 摘要被送到 `delivery.channel` + `delivery.to` 指定的目標
4. 同時，一個簡短摘要也會送到 Main Session

設定方式：

```bash
openclaw cron edit <jobId> --announce
```

## `none` 模式

- 系統不做任何 Delivery
- Agent 需要自己使用 Message 工具直接發訊息到目標 Channel
- 輸出內容完全由 Agent 控制，格式不會被改寫

設定方式：

```bash
openclaw cron edit <jobId> --no-deliver
```

在 `none` 模式下，需要在 `payload.message` 裡明確指示 Agent 使用 Message 工具發送訊息，例如：「使用 Message 工具將完整內容原文發送到 Slack channel `<channelId>`」。

# 什麼時候適合用 Announce Delivery Mode

研究了一下 Announce Delivery Mode 的設計，覺得它的初衷應該是「**把 Agent 冗長的執行過程壓縮成一則人類可讀的通知**」。

適合的場景：

- **監控告警型任務**：「每天檢查伺服器狀態，有異常就通知我」。Agent 可能做了大量分析——查 Logs、跑 Health Check、比較 Metrics——但你只需要一句「一切正常」或「CPU 異常偏高」。這種情境下摘要反而是你要的。
- **資訊彙整型任務**：「每週整理 GitHub issues 進度」。Agent 的原始產出可能很長，摘要幫你抓重點推到 channel。
- **懶人模式**：不需要在 Prompt 裡處理 Message 工具的呼叫邏輯，系統自動搞定 Delivery，設定成本最低。

不適合的場景：

- **在意格式或結構化的輸出**：表格、清單、特定 Markdown 結構
- **原文轉發需求**：你希望 Agent 產出什麼，Channel 就收到什麼

簡單來說，`announce` 是「我只想被通知結果，不在乎格式」的模式；`none` 是「我要完全控制輸出」的模式。根據你的任務的性質選擇合適的方式。

# 心得

使用龍蝦和 LLM 的經驗非常相似，在使用過程中如果感受到接近其能力的邊緣，就要花更多心力介入一起 Debug 或是嘗試不同方法。如果只會重複的嘗試，永遠都撞不破那道牆，最後你會覺得這個工具很沒用。切記要讓自己的思維有彈性、覺察工具的限制，讓自己成為更好的駕馭者。
