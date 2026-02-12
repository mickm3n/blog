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

# 先搞懂 Heartbeat 是什麼

在進入排程比較之前，先簡單理解 OpenClaw 的 Heartbeat 機制。

Heartbeat 是 OpenClaw 讓 agent 從被動回應變成主動巡查的核心機制。每隔一段時間（預設 30 分鐘），Gateway 會對 agent 發送一個 heartbeat prompt，agent 會去讀取工作區中的 `HEARTBEAT.md` 檔案，檢查裡面列出的待辦事項，然後決定要回傳靜默的 `HEARTBEAT_OK`（沒事）還是主動發訊息通知你（有事）。

`HEARTBEAT.md` 本質上就是一份你希望 agent 定期監控的巡查清單，例如：收信箱是否有緊急郵件、行事曆是否有即將到來的會議、Git 是否有未合併的 PR 等。如果 `HEARTBEAT.md` 存在但內容是空的（只有空行和 markdown 標題），OpenClaw 會跳過該次 heartbeat 以節省 API 費用。

關鍵的設計在於：heartbeat 運行在與正常對話相同的 session context 中，agent 能記住之前檢查過什麼、避免重複通知，並根據過去的結果來調整判斷。這就是為什麼 Heartbeat Cron 和 Isolated Cron 會有本質上的差異。

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
- Heartbeat 處理外部內容（例如信箱郵件）時，需留意 prompt injection 風險 — 惡意內容可能被 agent 當作指令執行，使用時需謹慎設定權限

**實用設定提示：**
- 可以設定 `activeHours`（例如 `08:00–24:00`）限制 heartbeat 只在特定時段內執行，避免半夜收到不緊急的通知
- 預設情況下 heartbeat 會用主模型（例如 Opus）處理，但簡單的巡查任務其實不需要最強的模型，像 Gemini Flash-Lite 每百萬 token 僅 50 美分，是 Opus 的六十分之一，做 heartbeat 檢查完全夠用

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

更具體來說，main session 的共享 context 在以下場景才真正有不可替代的價值：

1. **需要感知「剛才聊了什麼」的連續判斷** — 你跟龍蝦說「我在等 John 回那份合約的信，來了馬上通知我」，heartbeat 下次醒來時因為在同一個 session，天然就知道這件事要優先看。Isolated Cron 不在同一個 context 裡，你得額外把這種臨時性的意圖寫進某個 state file，它才知道。
2. **避免跟對話內容重複通知** — 如果你 10 分鐘前在聊天裡已經處理了某封郵件，heartbeat 因為看得到對話歷史，不會再通知你一次。Isolated Cron 看不到主對話發生了什麼，除非你另外做去重邏輯。
3. **跨任務的「連點成線」判斷** — 上午跟龍蝦討論了 A 客戶的專案進度，下午 heartbeat 醒來發現 A 客戶寄了一封信，它能把這兩件事關聯起來判斷緊急程度。Isolated Cron 缺少這個上下文，只能根據信件本身的內容做判斷。

但說實話，這些「優勢」在實務上的邊際效益不一定大 — 如果你用了 persistent memory（向量資料庫或檔案），Isolated Cron 也能讀取歷史狀態，差距就縮小很多。而且 main session 的 context window 會越來越大，每次 heartbeat 都帶著完整對話歷史跑一次 model call，token 成本會累積得很快。Isolated Cron 的隔離性反而是優點：scope 明確、prompt 精簡、失敗不影響主對話、更容易 debug。

大部分的定時任務其實都不需要對話脈絡，所以 Isolated Cron 會是比較常用的選擇。把 main session 保持乾淨，只在真正需要「感知對話流」的軟性判斷場景才走 heartbeat 流程。

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
