+++
title = "龍蝦（OpenClaw）的排程任務：Heartbeat Cron vs Isolated Cron 的差異與選擇"
date = 2026-02-12
description = "在 OpenClaw 設定 cron job 時，該用 main session 的 heartbeat 流程還是 isolated session？從實際使用經驗出發，比較兩種排程方式的差異與適用場景"

[taxonomies]
categories = [ "經驗分享" ]
tags = [ "openclaw" ]

[extra]
+++

在[上一篇](@/blog/openclaw-tailscale-integration/index.md)提到我把龍蝦（OpenClaw）跑在家裡的 Mac Mini 上當個人 AI 助手用。除了安全性上，最重要的就是有效性，我最常就是直接在 Slack 和他對話，請他幫我改 Config 作一些設定，不會自己去深入研究應該要怎麼設定。

# 我的第一個定時任務（Cron Job）

第一個想到想作的定時任務是「總結我跟龍蝦之間的對話」，主要是想要在一天的忙碌後，回顧自己到底改了哪些東西，也方便作下一步的規劃。當時也沒有多想，就跟龍蝦提需求，讓他自己完成，他就幫我建立了用 **Main Session + systemEvent** 的方式來實作，當時還遇到沒有觸發的問題，龍蝦查了一下發現少了 Heartbeat 的設置，也自動幫我補上了。

後續也建立了幾個定時任務，例如去回顧我今天完成的待辦事項與行事曆，定時抓取重要的經濟與股市新聞，檢查龍蝦的版本是否有更新、修改了什麼等等，雖然都用對話的方式讓龍蝦自己去設定，但在討論中偶爾他會提出這樣的任務應該要跑在獨立的 Session 上，因為不需要其他的資訊，聽起來也合理就設定了。

直到最近在檢視 Token 的使用時，才發現主要的 Session 一直會在處理 Heartbeat 的任務，會填滿 Context Window。在想著要優化 Token 的使用效率，反而才弄懂了 Heartbeat Cron 與 Isolated Cron 的差異。

# 兩種排程方式的差異

OpenClaw 的 Cron Job 分成兩種運作模式，Heartbeat Cron 與 Isolated Cron。

## Heartbeat Cron (Main Session)

設定 `sessionTarget: "main"` 搭配 `payload.kind: "systemEvent"`，排程觸發時任務會在 Main Session 上執行，也就是共用預設的對話。

**核心特性：**
- 任務可以讀取 Main Session 的完整對話上下文。也就是為什麼我提到我想總結對話時，龍蝦決定幫我用這個設定
- 走 Heartbeat Prompt（`HEARTBEAT.md`的處理路徑

**適合的場景：**
- 任務需要依賴對話脈絡

**限制：**
- 每次執行都會增加 main session 的 context，長期下來 token 消耗會增加
- 如果你的 `heartbeat` 設成 `0m`（關閉），用 `wakeMode: next-heartbeat` 不會生效，因為根本沒有週期性的 Heartbeat Tick
- 排程任務跟預設對話共用同一條 session，互相會影響上下文

## Isolated Cron

設定 `sessionTarget: "isolated"` 搭配 `payload.kind: "agentTurn"`，每次觸發時會開一個全新的獨立 session 來執行任務。

**核心特性：**
- 每次執行都是乾淨的上下文，不會讀到也不會污染 main session
- 可以指定不同的 model 和 thinking 模式
- 支援 `delivery` 設定，可以把結果直接送到 Channel

**適合的場景：**
- 任務不需要對話脈絡，例如定時抓 RSS、天氣摘要、新聞整理
- 想節省 token 用量，每次乾淨執行
- 想把結果發送到特定的 Channel
- 想用不同的 model 或 thinking 模式設定來跑特定任務

**限制：**
- 每次都是全新 session，沒有跨次執行的記憶

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
