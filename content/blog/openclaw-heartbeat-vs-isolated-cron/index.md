+++
title = "OpenClaw 排程任務：Heartbeat Cron vs Isolated Cron 的差異與選擇"
date = 2026-02-12
description = "在 OpenClaw 設定 cron job 時，該用 main session 的 heartbeat 流程還是 isolated session？從實際使用經驗出發，比較兩種排程方式的差異與適用場景"

[taxonomies]
categories = [ "經驗分享" ]
tags = [ "openclaw" ]

[extra]
+++

在[上一篇](@/blog/openclaw-tailscale-integration/index.md)提到我把 OpenClaw 跑在家裡的 Mac Mini 上當個人 AI 助手用。設定完基礎建設後，自然就會開始想：既然龍蝦 24 小時都在線上，那能不能讓他定時幫我做一些事情？

這就是 OpenClaw 的 cron job 功能。

# 我的第一個 Cron Job

我習慣用對話的方式讓龍蝦自己去設定 cron job，而不是手動下 CLI 或寫 JSON。基本上就是在 Slack 上跟他說「幫我每天晚上八點整理今天的對話重點」，他就會自己把排程建好。

不過一開始想做的任務是「總結我跟龍蝦之間的對話」——要做到這件事，龍蝦需要能讀到 main session 的對話脈絡，所以他自己選擇了用 **main session + systemEvent** 的方式來實作。當時覺得合理，也沒多想。

直到後來我想加更多 cron job，例如定時去抓 RSS、整理待辦清單摘要等等，才發現這些任務其實不需要讀取主對話的上下文。這時候才認知到 OpenClaw 還有另一個選擇：**Isolated Cron**。

# 兩種排程方式的差異

OpenClaw 的 cron job 分成兩種運作模式，核心差別在於 `sessionTarget` 這個欄位：

## Heartbeat Cron（Main Session）

設定 `sessionTarget: "main"` 搭配 `payload.kind: "systemEvent"`，排程觸發時任務會在 main session 上執行，也就是跟你平常對話的那條脈絡是同一條。

**核心特性：**
- 任務可以讀取 main session 的完整對話上下文
- 走 heartbeat prompt / `HEARTBEAT.md` 的處理路徑
- 透過 `wakeMode` 控制觸發方式：`now`（立即喚醒）或 `next-heartbeat`（等下一次心跳）

**適合的場景：**
- 任務需要依賴對話脈絡，例如總結今天跟龍蝦討論了什麼
- 想讓排程任務跟 heartbeat 的既有流程整合
- 任務的輸出需要接續在主對話裡

**限制：**
- 每次執行都會增加 main session 的 context，長期下來 token 消耗會增加
- 如果你的 `heartbeat` 設成 `0m`（關閉），用 `wakeMode: next-heartbeat` 不會生效，因為根本沒有週期性的 tick。這種情況建議用 `wakeMode: now`，或是先把 heartbeat 打開
- 排程任務跟你的手動對話共用同一條 session，互相會影響上下文

## Isolated Cron

設定 `sessionTarget: "isolated"` 搭配 `payload.kind: "agentTurn"`，每次觸發時會開一個全新的獨立 session 來執行任務。

**核心特性：**
- 每次執行都是乾淨的上下文，不會讀到也不會污染 main session
- 可以指定不同的 model 和 thinking 模式
- 支援 `delivery` 設定，可以把結果直接送到 Slack channel

**適合的場景：**
- 任務不需要對話脈絡，例如定時抓 RSS、天氣摘要、新聞整理
- 想節省 token 用量，每次乾淨執行
- 想把結果直接 announce 到特定的 Slack channel
- 想用不同的 model 或 thinking 設定來跑特定任務

**限制：**
- 無法存取 main session 的對話歷史
- 每次都是全新 session，沒有跨次執行的記憶（除非自己透過檔案等方式持久化）

# 怎麼選？

簡單的判斷方式：**這個任務需不需要知道我之前跟龍蝦聊了什麼？**

需要 → Heartbeat Cron（main session）
不需要 → Isolated Cron

大部分的定時任務其實都不需要對話脈絡，所以 Isolated Cron 會是比較常用的選擇。把 main session 保持乾淨，只在真正需要上下文的任務才走 heartbeat 流程。

# 設定範例

## Heartbeat Cron 範例

以下是一個每天早上九點提醒你檢查重點事項的排程，走 main session：

**JSON 設定：**

```json
{
  "name": "Main reminder",
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Taipei" },
  "sessionTarget": "main",
  "wakeMode": "now",
  "payload": {
    "kind": "systemEvent",
    "text": "提醒：檢查今天的重點事項。"
  }
}
```

**CLI 指令：**

```bash
openclaw cron add \
  --name "Main reminder" \
  --cron "0 9 * * *" \
  --session main \
  --system-event "提醒：檢查今天的重點事項" \
  --wake now
```

這裡用 `wakeMode: now` 是因為我的 heartbeat 設成 `0m`，如果用 `next-heartbeat` 的話排程不會被觸發。

## Isolated Cron 範例

以下是一個每天晚上八點產出當日摘要，並自動發送到 Slack channel 的排程：

**JSON 設定：**

```json
{
  "name": "Daily digest isolated",
  "schedule": { "kind": "cron", "expr": "0 20 * * *", "tz": "Asia/Taipei" },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "請整理今日重點摘要（繁中，精簡）。",
    "model": "gpt",
    "thinking": "minimal"
  },
  "delivery": {
    "mode": "announce",
    "channel": "slack",
    "to": "channel:C09UBHM9WAZ",
    "bestEffort": true
  }
}
```

**CLI 指令：**

```bash
openclaw cron add \
  --name "Daily digest isolated" \
  --cron "0 20 * * *" \
  --session isolated \
  --message "請整理今日重點摘要（繁中，精簡）" \
  --announce \
  --target slack \
  --to channel:C09UBHM9WAZ
```

Isolated Cron 的 `delivery` 設定很方便，可以讓任務結果直接送到指定的 Slack channel，不用再手動去查看。

# 小結

| | Heartbeat Cron | Isolated Cron |
|---|---|---|
| sessionTarget | `main` | `isolated` |
| payload.kind | `systemEvent` | `agentTurn` |
| 對話脈絡 | 共用 main session | 獨立乾淨的 session |
| Token 消耗 | 累積在 main context | 每次獨立計算 |
| 結果發送 | 留在 main session | 可 announce 到 Slack |
| Model 選擇 | 跟 main session 一致 | 可獨立指定 |

回頭看，一開始因為任務本身的需求（總結對話）自然地走了 heartbeat 路線，但大多數排程任務用 isolated 會更合適。了解兩者的差異之後，就能根據任務的性質做出更好的選擇。
