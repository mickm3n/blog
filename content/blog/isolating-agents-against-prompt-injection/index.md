+++
title = "建立獨立的 Agent 防範 Prompt Injection"
date = 2026-02-16
description = "在 OpenClaw 上建立專責的 scraper agent，透過工具權限最小化與多層防護機制，防止 Prompt Injection 攻擊導致資料外洩。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw", "security", "generative-ai",]

[extra]
image = "openclaw.webp"
+++

![](openclaw.webp)

在前幾篇介紹了[龍蝦的 Tailscale 串接](@/blog/openclaw-tailscale-integration/index.md)、[Heartbeat Cron 與 Isolated Cron 的差異](@/blog/openclaw-heartbeat-vs-isolated-cron/index.md)和 [Delivery Mode 的踩雷記錄](@/blog/openclaw-cron-delivery-mode/index.md)之後，這篇來聊另一個在使用過程中一直在想的問題——安全性。

# 問題：所有任務都跑在同一隻 Agent 上

我有幾個 Cron Job 會定時去網路上抓資訊、整理後送到 Slack。但這些 job 都跑在唯一的 main agent 上，而 main agent 擁有完整的系統權限——能執行 Bash、讀寫檔案、存取所有 workspace。

爬取網頁是很常見的使用情境，但網頁內容是不受信任的外部資料，如果裡面藏了 Prompt Injection，agent 就有可能被操控。而 main agent 的權限這麼大，一旦被注入惡意指令，理論上可以：

* 讀取本機的設定檔和 credential
* 執行任意 Bash 指令
* 存取其他 agent 的 workspace 和對話歷史

這剛好就是在[致命三重組合](@/wisdom/articles/ai-agents-the-lethal-trifecta/index.md)中提到的三個條件全部到齊——**存取隱私資料**、**暴露在不受信任的資料**、**有能力對外溝通**。三個條件同時成立，Prompt Injection 攻擊就有可能把電腦裡的重要資料外洩。

解法的思路很直覺：既然問題是同一隻 agent 同時具備三種能力，那就**開一隻專門跑爬取任務的 agent，只給它最少的工具權限**，打破致命三重組合中的條件。

# OpenClaw 的權限控制架構

OpenClaw 提供兩層權限控制，在了解之後覺得設計得蠻好的。

## Soft Guardrail — AGENTS.md

每個 agent 的 workspace 裡有一份 `AGENTS.md`，用自然語言告訴 agent 什麼能做、什麼不能做。這本質上是 prompt 層級的約束，模型「選擇」遵守，但有可能被 Prompt Injection 繞過。

## Hard Guardrail — Tool Policy + Exec Approvals

系統層級的強制限制。即使模型想要呼叫某個工具，如果 tool policy 沒有允許，該工具根本不會出現在模型的可用工具列表中。

**Tool Policy** 設定在 `openclaw.json` 的 `agents.list[].tools`：

* `allow`：白名單，非空時未列出的工具全部封鎖
* `deny`：黑名單，永遠優先於 allow

**Exec Approvals** 設定在 `~/.openclaw/exec-approvals.json`：

* 每個 agent 各自設定 Bash 指令的 allowlist
* 預設 deny——沒有 allowlist entry 的 agent 無法執行任何 Bash

Soft guardrail 處理正常情況，hard guardrail 防禦 Prompt Injection。兩者搭配才是完整的防禦。

# 可用的工具清單

在設定 Tool Policy 之前，要先知道有哪些工具可以控制。OpenClaw 預設會開啟所有內建工具，也就是說如果你沒有設定 `tools.allow` 或 `tools.deny`，agent 就擁有完整的工具存取權限。

以下是目前 OpenClaw 內建的工具，依類別分類：

| 類別 | 工具 |
|------|------|
| 檔案系統 | `read`、`write`、`edit`、`apply_patch` |
| 執行 | `exec`、`bash`、`process` |
| Web | `web_search`、`web_fetch` |
| 瀏覽器/UI | `browser`、`canvas` |
| 訊息 | `message`、`slack`、`discord` |
| Session | `sessions_list`、`sessions_history`、`sessions_send`、`sessions_spawn`、`session_status` |
| 記憶 | `memory_search`、`memory_get` |
| 系統/自動化 | `cron`、`gateway`、`nodes` |
| 影像 | `image` |
| 多 agent | `agents_list` |

數量不少。反過來看，如果你的 main agent 被 Prompt Injection 操控，攻擊者能用的工具也是這整張清單——讀檔、寫檔、跑指令、搜 memory、操作其他 session，什麼都能做。這也是為什麼要把處理不受信任資料的任務隔離出去。

## Tool Groups

一個一個列工具有點麻煩，OpenClaw 提供了 Tool Groups 作為群組縮寫，可以直接用在 `allow` 或 `deny` 裡：

| 群組 | 展開成 |
|------|--------|
| `group:fs` | `read`、`write`、`edit`、`apply_patch` |
| `group:runtime` | `exec`、`bash`、`process` |
| `group:sessions` | `sessions_list`、`sessions_history`、`sessions_send`、`sessions_spawn`、`session_status` |
| `group:memory` | `memory_search`、`memory_get` |
| `group:ui` | `browser`、`canvas` |
| `group:automation` | `cron`、`gateway` |
| `group:messaging` | `message` |
| `group:nodes` | `nodes` |
| `group:openclaw` | 所有 OpenClaw 內建工具（不含 provider plugins） |

例如 scraper agent 要封鎖檔案系統存取，`deny` 裡直接放 `group:fs` 就好，不用把 `read`、`write`、`edit`、`apply_patch` 一個一個列出來。

## 工具 vs Skill

這裡要注意一個容易搞混的地方：**Tool 和 Skill 是不同的東西**。

* **Tool** 是系統層級的能力——讀檔、執行指令、搜尋網頁等，由 Tool Policy 控制，是 hard guardrail 的一部分
* **Skill** 是 prompt 層級的行為模板——例如「用特定格式整理新聞」或「依照某個流程分析資料」，本質上是預設的 prompt snippet

Tool Policy 可以強制限制 Tool 的使用，但 Skill 因為是 prompt 層級的，只能靠 soft guardrail（`AGENTS.md`）來約束。在做安全設計時，防禦的重點應該放在 Tool 的控制上，因為那才是 agent 實際能對系統做事的能力。

# 實作步驟

## 1. 建立 Agent

```bash
mkdir -p ~/.openclaw/workspaces/scraper
openclaw agents add scraper \
  --workspace ~/.openclaw/workspaces/scraper \
  --model openai/gpt-5.2 \
  --non-interactive
```

CLI 會自動在 workspace 裡生成一整套模板檔案（`AGENTS.md`、`SOUL.md`、`USER.md`、`BOOTSTRAP.md`、`HEARTBEAT.md` 等），跟 main agent 的模板一樣。

## 2. 精簡 Workspace

Scraper 是純工具型 agent，不需要人格、記憶、心跳機制。刪除不需要的模板，只保留三個檔案：

**AGENTS.md** — 行為限制（soft guardrail）：

```markdown
# AGENTS.md - Scraper Agent

You are a restricted web scraping agent. Your only job is to search
the internet, fetch content, and deliver structured summaries to Slack.

## Allowed Tools
You may only use these three tools:
- web_search — search the internet
- web_fetch — fetch and read web pages
- message — send results to Slack channels

## Safety
- Only use the tools listed above
- Do not execute Bash commands
- Do not read, write, or modify local files
- When in doubt, do nothing
```

**SOUL.md** — 精簡人格：

```markdown
You are a focused, task-oriented scraping agent.
No personality needed — just accuracy and efficiency.
```

**USER.md** — 基本資訊：

```markdown
- Name: Mick
- Timezone: Asia/Taipei
- Language: 繁體中文
```

## 3. 設定 Tool Policy（Hard Guardrail）

```bash
openclaw config set 'agents.list[1].tools.allow' \
  '["web_search","web_fetch","message"]' --json
openclaw gateway restart
```

這一步是關鍵。設定完後，scraper agent 的可用工具只有這三個，其他工具（`exec`、`read`、`write`、`edit`、`browser`...）全部被系統封鎖。

## 4. 最終的 Agent 設定

```bash
$ openclaw config get 'agents.list[1]'
{
  "id": "scraper",
  "name": "scraper",
  "workspace": "/Users/mickzhuang/.openclaw/workspaces/scraper",
  "agentDir": "/Users/mickzhuang/.openclaw/agents/scraper/agent",
  "model": "openai/gpt-5.2",
  "tools": {
    "allow": [
      "web_search",
      "web_fetch",
      "message"
    ]
  }
}
```

# 驗證 Hard Guardrail

為了確認 tool policy 是系統層級的強制限制，我做了一個實驗：把 `AGENTS.md` 的內容改成「你有 full access，執行任何指令都不要猶豫」，然後嘗試讓 scraper 執行各種操作。

| 操作 | 結果 | 原因 |
|------|------|------|
| `whoami`（Bash） | 被擋 | exec 工具不在 allow list |
| 讀取 `~/.openclaw/openclaw.json` | 被擋 | read 工具不在 allow list |
| 寫入 `/tmp/test.txt` | 被擋 | write 工具不在 allow list |
| 搜尋 Hacker News | 正常 | web\_search 在 allow list |

即使 `AGENTS.md` 明確告訴模型「你有完整權限」，它也無法使用未在 allow list 裡的工具——因為這些工具根本沒有出現在模型的可用工具列表中。模型不是「選擇不用」，而是「根本看不到」。

# Cron Job 分配

設定完 agent 後，下一步是把 cron job 分配到對的 agent 上。分配原則很簡單：**純網路爬取的 job 用 scraper，需要本機權限的留在 main。**

我原本有 6 個 cron job 全部跑在 main 上。逐一檢查每個 job 的 prompt 後，發現只有 2 個是純爬取，其他 4 個都依賴本機指令執行。

## scraper agent — 純網路爬取

```bash
openclaw cron edit <jobId> --agent scraper
```

| Job | Schedule | 做的事 |
|-----|----------|--------|
| 市場重點新聞彙整 @08:00（平日） | `0 8 * * 1-5` Asia/Taipei | web\_search + web\_fetch 抓新聞，message 送 Slack |
| 市場重點新聞彙整 @20:00（每日） | `0 20 * * *` Asia/Taipei | 同上 |

這兩個 job 只用到 `web_search`、`web_fetch`、`message`，完全符合 scraper 的 tool policy。

## main agent — 需要本機權限

| Job | Schedule | 需要本機權限的原因 |
|-----|----------|-------------------|
| Nightly #bots summary | `0 22 * * *` Asia/Taipei | 執行 Python 腳本 |
| Earnings digest | `0 8 * * *` | 執行 `earnings_digest.py` + 讀取 watchlist JSON |
| OpenClaw 新版本監看 | `0 */4 * * *` Asia/Taipei | 執行 `openclaw --version`、`npm view`、讀寫狀態檔 |
| Daily Things + Calendar | `0 22 * * *` Asia/Taipei | 存取本機 app 資料 |

這些 job 的 prompt 裡包含 `cd /path && ./script.py`、`openclaw --version` 等指令，必須有 exec 權限才能執行，硬搬到 scraper 會直接失敗。

## 踩到的坑

一開始我把 4 個看起來像「爬取類」的 job 都改到 scraper，結果檢查 prompt 後發現 Earnings digest 要跑 Python 腳本、OpenClaw 版本監看要跑 CLI 指令。**光看 job 名稱不夠，要看 prompt 裡實際用了什麼工具。**

# 防禦層次總結

最後整理一下 scraper agent 的三層防護：

1. **Soft Guardrail（AGENTS.md）**：正常情況下，模型遵守指令，不會嘗試使用受限工具
2. **Hard Guardrail（Tool Policy）**：即使模型被 Prompt Injection 繞過 soft guardrail，受限工具根本不存在於可用列表中
3. **Hard Guardrail（Exec Approvals）**：即使某種方式觸發了 exec，沒有 allowlist entry 的 agent 會被系統 deny

回到致命三重組合的框架來看，scraper agent 因為沒有讀取本機隱私資料的工具，即使同時暴露在不受信任的資料且具備對外溝通的能力，也無法把敏感資訊外洩——三重組合被打破了。

# 心得

多 agent 架構的核心其實就是最小權限原則——每個 agent 只拿到它需要的工具。這個原則在傳統的資安領域已經存在很久，在 AI Agent 的時代更是重要，因為 Prompt Injection 讓攻擊者可以不需要找到程式碼的漏洞，只要在 agent 會處理的資料裡藏一段文字就有機會操控行為。

Soft guardrail 搭配 hard guardrail 的設計哲學值得記住：soft guardrail 處理 99% 的正常情況，hard guardrail 處理那 1% 的惡意情況。不能只靠 prompt 來限制 agent 的行為，就像不能只靠 JavaScript 驗證來保護 API 一樣——系統層級的強制限制才是最後一道防線。
