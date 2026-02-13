+++
title = "龍蝦（OpenClaw）的排程任務：Heartbeat Cron vs Isolated Cron 的差異與選擇"
date = 2026-02-13
description = "在 OpenClaw 設定 cron job 時，該用 main session 的 heartbeat 流程還是 isolated session？從實際使用經驗出發，比較兩種排程方式的差異與適用場景"

[taxonomies]
categories = [ "經驗分享" ]
tags = [ "openclaw" ]

[extra]
image = "openclaw.webp"
+++

![](openclaw.webp)

在[上一篇](@/blog/openclaw-tailscale-integration/index.md)提到我把龍蝦跑在家裡的 Mac Mini 上當個人 AI 助手用。除了安全性上，另一個重點就是有效性。我最常就是直接在 Slack 和他對話，探索如何讓龍蝦協助我完成日常工作。如果覺得有什麼設定需要調整，會請他直接幫我改 Config 作一些設定，不會自己去深入研究應該要怎麼設定。

# 我的第一個定時任務（Cron Job）

第一個想到想作的定時任務是「在每天晚上十點總結我跟龍蝦之間的對話」。想要在一天的對話後，回顧自己到底改了哪些東西，方便作下一步的規劃。當時也沒有多想，就跟龍蝦提需求，讓他自己完成，他就幫我建立了用 **Main Session + systemEvent** 的方式來實作，當時也有遇到沒有定時觸發的問題，龍蝦查了一下發現少了 Heartbeat 的設置，也自動幫我補上了。

後續也建立了幾個定時任務，例如去回顧我今天待辦事項的完成狀況與行事曆、定時抓取重要的經濟與股市新聞、監控龍蝦的版本是否有更新等等。雖然也是都用對話的方式讓龍蝦自己去設定，但在討論中偶爾他會提出**這樣的任務因為不需要其他的資訊應該要跑在獨立的 Session 上**，聽起來也合理就設定了。

直到最近在檢視 Token 的使用時，才發現主要的 Session 會一直在處理 Heartbeat 的任務，塞滿 Main Session 的 Context Window。在想著要優化 Token 使用效率的過程，反而才弄懂了 Heartbeat Cron 與 Isolated Cron 的差異。

# OpenClaw 的 Heartbeat 機制

在比較兩種排程方式之前，先簡單理解 OpenClaw 的 Heartbeat 機制。

Heartbeat 是 OpenClaw 讓 Agent **從被動回應變成主動巡查**的核心機制。每隔一段時間（預設 30 分鐘），Gateway 會對 Agent 發送一個 Heartbeat Prompt，Agent 會去讀取工作區中的 `HEARTBEAT.md` 檔案，檢查裡面列出的待辦事項，然後決定要回傳靜默的 `HEARTBEAT_OK`（沒事）還是主動發訊息通知（有事）。

`HEARTBEAT.md` 本質上就是一份你希望 Agent 定期監控的巡查清單，例如：收信箱是否有緊急郵件、行事曆是否有即將到來的會議、Git 是否有未合併的 PR 等。如果 `HEARTBEAT.md` 存在但內容是空的（只有空行和 Markdown 標題），OpenClaw 會跳過該次 Heartbeat 以節省運算資源。

關鍵的設計在於：Heartbeat 運行在與對話相同的 Main Session 中，Agent 能記住之前檢查過什麼、避免重複通知，並根據過去的結果來調整判斷。

# Heartbeat Cron 與 Isolated Cron 的配置方式

## Heartbeat Cron

設定 `sessionTarget: "main"` 搭配 `payload.kind: "systemEvent"`，排程觸發時任務會在 Main Session 上執行，也就是共用預設的對話。

**核心特性：**
- 任務可以讀取 Main Session 的完整對話上下文。也就是為什麼我提到我想總結對話時，龍蝦決定幫我用這個設定
- 走 Heartbeat Prompt（`HEARTBEAT.md`）的處理路徑

**適合的場景：**
- 任務需要依賴對話脈絡

**限制：**
- 每次執行都會增加 main session 的 context，長期下來 token 消耗會增加
- 如果你的 `heartbeat` 設成 `0m`（關閉），用 `wakeMode: next-heartbeat` 不會生效，因為沒有週期性的 Heartbeat Tick
- 排程任務跟預設對話共用同一條 session，會互相影響上下文

**實用設定提示：**
- 可以設定 `activeHours`（例如 `08:00–24:00`）限制 heartbeat 只在特定時段內執行，避免半夜收到不緊急的通知
- 預設情況下 heartbeat 會用主模型處理，但簡單的巡查任務不一定需要最強的模型，可以選擇較經濟的模型來降低成本

## Isolated Cron

設定 `sessionTarget: "isolated"` 搭配 `payload.kind: "agentTurn"`，每次觸發時會開一個全新的獨立 session 來執行任務。

**核心特性：**
- 每次執行都是乾淨的上下文，不會讀到也不會污染 main session
- 可以指定不同的 model 和 thinking 模式
- 支援 `delivery` 設定，可以把結果直接送到 Channel

**適合的場景：**
- 任務不需要對話脈絡，例如定時抓 RSS、天氣摘要、新聞整理
- 想節省 token 用量，每次乾淨執行

**限制：**
- 每次都是全新 session，沒有跨次執行的記憶，除非額外透過檔案來持久化狀態

# 怎麼選？

簡單的判斷方式：**這個任務需不需要知道我之前跟龍蝦聊了什麼？**

* 需要 → Heartbeat Cron
* 不需要 → Isolated Cron

更具體來說，Main Session 的共享 Context 在以下場景才真正有不可替代的價值：

1. **需要感知「剛才聊了什麼」的連續判斷** — 你跟龍蝦說「我在等小明回那份合約的信，來了馬上通知我」，Heartbeat 下次醒來時因為在同一個 Session，天然就知道這件事要優先看。Isolated Cron 不在同一個 Context 裡，你得額外把這種臨時性的意圖寫進某個 State File，它才知道。
2. **避免跟對話內容重複通知** — 如果你 10 分鐘前在聊天裡已經處理了某封郵件，Heartbeat 因為看得到對話歷史，不會再通知你一次。Isolated Cron 看不到主對話發生了什麼，除非另外做去重複的邏輯。
3. **跨任務的「連點成線」判斷** — 上午跟龍蝦討論了 A 客戶的專案進度，下午 Heartbeat 醒來發現 A 客戶寄了一封信，它能把這兩件事關聯起來判斷緊急程度。Isolated Cron 缺少這個上下文，只能根據信件本身的內容做判斷。

但說實話，這些「優勢」在實務上的效益不一定大，只要用向量資料庫或檔案方式來儲存狀態，Isolated Cron 就能得知歷史狀態，達到一樣的效果。但重複使用 Main Session 則會導致 Context Window 會越來越大，每次 Heartbeat 都帶著完整對話歷史跑一次 Model Call，Token 花費得很快。Isolated Cron 的隔離性反而是優點：Scope 明確、Prompt 精簡、失敗不影響主對話、更容易 Debug。

大部分的定時任務其實都不需要對話脈絡，所以 Isolated Cron 會是比較常用的選擇。把 Main Session 保持乾淨，只有在真正需要「感知對話流」的軟性判斷場景才走 Heartbeat Cron。

# 心得

回頭看，一開始因為任務本身的需求（總結對話）而和龍蝦一起選了 Heartbeat Cron，但大多數排程任務用 Isolated Cron 會更合適。了解兩者的差異之後，就能根據任務的性質做出更好的選擇。
