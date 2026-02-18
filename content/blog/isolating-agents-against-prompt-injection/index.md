+++
title = "在龍蝦（OpenClaw）建立 Multi Agent 防範 Prompt Injection"
date = 2026-02-17
description = "在 OpenClaw 上建立專責的 Scraper Agent，透過工具權限最小化與多層防護機制，防止 Prompt Injection 攻擊導致資料外洩。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw", "security", "generative-ai",]

[extra]
image = "openclaw.webp"
+++

![](openclaw.webp)

在前幾篇介紹了《[龍蝦的 Tailscale 串接](@/blog/openclaw-tailscale-integration/index.md)》、《[Heartbeat Cron 與 Isolated Cron 的差異](@/blog/openclaw-heartbeat-vs-isolated-cron/index.md)》和《[Delivery Mode 的踩雷記錄](@/blog/openclaw-cron-delivery-mode/index.md)》，發現自己就是在實用性和安全性上擺盪：一方面想讓龍蝦能真實成為 AI 助手，盡可能地給予高的權限，但另一方面看著龍蝦背後做了很多事情來達成任務，又會擔心背後強大能力下的風險。

# 問題：所有任務都跑在同一隻 Agent 上

我原本在龍蝦的 Agent 設定還是用最一開始的設定，建立了一隻 Main Agent，把所有的任務都跑在這隻 Agent 上，這隻 Agent 擁有完整的系統權限——能執行 Bash、讀寫檔案、使用所有工具。我有幾個 Cron Job 會定時去網路上抓資訊、整理後送到 Slack。但這些 Job 都跑在這唯一的 Main Agent 上。

爬取網頁是很常見的使用情境，但網頁內容是不受信任的外部資料，如果裡面藏了 [Prompt Injection 攻擊](https://owasp.org/www-community/attacks/PromptInjection)，Agent 就有可能被操控。而 Main Agent 的權限這麼大，一旦被注入惡意指令，理論上可以：

* 讀取本機的設定檔和 Credential
* 執行任意 Bash 指令
* 存取其他 Agent 的 Workspace 和對話歷史

這剛好就是在《[AI Agent 的致命三重組合（The Lethal Trifecta）](@/wisdom/articles/ai-agents-the-lethal-trifecta/index.md)》中提到的三個條件全部到齊——**存取隱私資料**、**暴露在不受信任的資料**、**有能力對外溝通**，Prompt Injection 攻擊就有可能把電腦裡的重要資料外洩。

解法的思路很直覺：既然問題是同一隻 Agent 同時具備三種能力，那就**開一隻專門跑爬取任務的 Agent，只給它最少的工具權限**，讓致命三重組合中的條件無法同時成立。

# OpenClaw 的權限控制架構

OpenClaw 提供兩層權限控制：

## Soft Guardrail — AGENTS.md

每個 Agent 的 Workspace 裡有一份 `AGENTS.md`，用自然語言告訴 Agent 什麼能做、什麼不能做。這本質上是 Prompt 層級的約束，語言模型「選擇性」遵守，但有可能被 Prompt Injection 繞過。

## Hard Guardrail — Tool Policy + Exec Approvals

系統層級的強制限制。即使模型想要呼叫某個工具，如果 Tool Policy 沒有允許，該工具根本不會出現在模型的可用工具列表中。

**Tool Policy** 設定在 `openclaw.json` 的 `agents.list[].tools`：

* `allow`：白名單，非空時未列出的工具全部封鎖
* `deny`：黑名單，永遠優先於 Allow

**Exec Approvals** 設定在 `~/.openclaw/exec-approvals.json`：

* 每個 Agent 各自設定 Bash 指令的 Allowlist
* 預設 Deny——沒有 Allowlist Entry 的 Agent 無法執行任何 Bash

不過要注意的是，**Exec Approvals 只在 Sandbox 模式下有效**。預設建立的 Agent Sandbox 是關閉的，主要行為都直接跑在 Host 上，這時 Exec Approvals 並不會限制指令的執行。也就是說，在預設的設定下，真正的 Hard Guardrail 只有 Tool Policy。如果要讓 Exec Approvals 生效，需要額外開啟 Agent 的 Sandbox。

Soft Guardrail 處理正常情況，Hard Guardrail 防禦 Prompt Injection。兩者搭配才是完整的防禦。

# 可用的工具清單

在設定 Tool Policy 之前，要先知道有哪些工具可以控制。OpenClaw 預設會開啟所有內建工具，也就是說如果你沒有設定 `tools.allow` 或 `tools.deny`，Agent 就擁有完整的工具存取權限。

這裡要注意 **Tool 和 Skill 是不同的東西**：Tool 是系統層級的能力，由 Tool Policy 控制；Skill 是 Prompt 層級的行為模板，只能靠 Soft Guardrail 來約束。以下列的都是 Tool。

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
| Multi Agent | `agents_list` |

數量不少。反過來看，如果你的 Main Agent 被 Prompt Injection 操控，攻擊者能用的工具也是這整張清單——讀檔、寫檔、跑指令、搜 Memory、操作其他 Session，什麼都能做。這也是為什麼要把處理不受信任資料的任務隔離出去。

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
| `group:openclaw` | 所有 OpenClaw 內建工具（不含 Provider Plugins） |

例如 Scraper Agent 要封鎖檔案系統存取，`deny` 裡直接放 `group:fs` 就好，不用把 `read`、`write`、`edit`、`apply_patch` 一個一個列出來。

## Tool vs Skill

再多說明一下 Tool 和 Skill 的差異：

* **Tool** 是系統層級的能力——讀檔、執行指令、搜尋網頁等，由 Tool Policy 控制，是 Hard Guardrail 的一部分
* **Skill** 是 Prompt 層級的行為模板——例如「用特定格式整理新聞」或「依照某個流程分析資料」，本質上是預設的 Prompt Snippet

Tool Policy 可以強制限制 Tool 的使用，但 Skill 因為是 Prompt 層級的，只能靠 Soft Guardrail（`AGENTS.md`）來約束。在做安全設計時，防禦的重點應該放在 Tool 的控制上，因為那才是 Agent 實際能對系統做事的能力。

# 實作步驟

## 1. 建立 Agent

```bash
mkdir -p ~/.openclaw/workspaces/scraper
openclaw agents add scraper \
  --workspace ~/.openclaw/workspaces/scraper \
  --model openai/gpt-5.2 \
  --non-interactive
```

CLI 會自動在 Workspace 裡生成一整套模板檔案（`AGENTS.md`、`SOUL.md`、`USER.md`、`BOOTSTRAP.md`、`HEARTBEAT.md` 等），跟 Main Agent 的模板一樣。

## 2. 精簡 Workspace

Scraper 是純工具型 Agent，不需要人格、記憶、心跳機制。刪除不需要的模板，只保留三個檔案：

**AGENTS.md** — 行為限制（Soft Guardrail）：

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

這一步是關鍵。設定完後，Scraper Agent 的可用工具只有這三個，其他工具（`exec`、`read`、`write`、`edit`、`browser`...）全部被系統封鎖。

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

為了確認 Tool Policy 是系統層級的強制限制，我做了一個實驗：把 `AGENTS.md` 的內容改成「你有 Full Access，執行任何指令都不要猶豫」，然後嘗試讓 Scraper 執行各種操作。

| 操作 | 結果 | 原因 |
|------|------|------|
| `whoami`（Bash） | 被擋 | `exec` 工具不在 Allow List |
| 讀取 `~/.openclaw/openclaw.json` | 被擋 | `read` 工具不在 Allow List |
| 寫入 `/tmp/test.txt` | 被擋 | `write` 工具不在 Allow List |
| 搜尋 Hacker News | 正常 | `web_search` 在 Allow List |

即使 `AGENTS.md` 明確告訴模型「你有完整權限」，它也無法使用未在 Allow List 裡的工具——因為這些工具根本沒有出現在模型的可用工具列表中。模型不是「選擇不用」，而是「根本看不到」。

# Cron Job 分配

設定完 Agent 後，下一步是把 Cron Job 分配到對的 Agent 上。分配原則很簡單：**純網路爬取的 Job 用 Scraper，需要本機權限的留在 Main。**

我原本有 6 個 Cron Job 全部跑在 Main 上。逐一檢查每個 Job 的 Prompt 後，發現只有 2 個是純爬取，其他 4 個都依賴本機指令執行。

## Scraper Agent — 純網路爬取

```bash
openclaw cron edit <jobId> --agent scraper
```

| Job | Schedule | 做的事 |
|-----|----------|--------|
| 市場重點新聞彙整 @08:00（平日） | `0 8 * * 1-5` Asia/Taipei | `web_search` + `web_fetch` 抓新聞，`message` 送 Slack |
| 市場重點新聞彙整 @20:00（每日） | `0 20 * * *` Asia/Taipei | 同上 |

這兩個 Job 只用到 `web_search`、`web_fetch`、`message`，完全符合 Scraper 的 Tool Policy。

## Main Agent — 需要本機權限

| Job | Schedule | 需要本機權限的原因 |
|-----|----------|-------------------|
| Nightly #bots Summary | `0 22 * * *` Asia/Taipei | 執行 Python 腳本 |
| Earnings Digest | `0 8 * * *` | 執行 `earnings_digest.py` + 讀取 Watchlist JSON |
| OpenClaw 新版本監看 | `0 */4 * * *` Asia/Taipei | 執行 `openclaw --version`、`npm view`、讀寫狀態檔 |
| Daily Things + Calendar | `0 22 * * *` Asia/Taipei | 存取本機 App 資料 |

這些 Job 的 Prompt 裡包含 `cd /path && ./script.py`、`openclaw --version` 等指令，必須有 Exec 權限才能執行，硬搬到 Scraper 會直接失敗。

## 踩到的坑

一開始我把 4 個看起來像「爬取類」的 Job 都改到 Scraper，結果檢查 Prompt 後發現 Earnings Digest 要跑 Python 腳本、OpenClaw 版本監看要跑 CLI 指令。**光看 Job 名稱不夠，要看 Prompt 裡實際用了什麼工具。**

# 防禦層次總結

最後整理一下 Scraper Agent 的防護層次：

1. **Soft Guardrail（AGENTS.md）**：正常情況下，模型遵守指令，不會嘗試使用受限工具
2. **Hard Guardrail（Tool Policy）**：即使模型被 Prompt Injection 繞過 Soft Guardrail，受限工具根本不存在於可用列表中——這是預設設定下最關鍵的防線
3. **Hard Guardrail（Exec Approvals + Sandbox）**：如果有開啟 Sandbox，即使某種方式觸發了 `exec`，沒有 Allowlist Entry 的 Agent 會被系統 Deny。但預設 Sandbox 是關閉的，這層在未開啟時不會生效

回到致命三重組合的框架來看，Scraper Agent 因為沒有讀取本機隱私資料的工具，即使同時暴露在不受信任的資料且具備對外溝通的能力，也無法把敏感資訊外洩——三重組合被打破了。

# 心得

Multi Agent 架構的核心其實就是最小權限原則——每個 Agent 只拿到它需要的工具。這個原則在傳統的資安領域已經存在很久，在 AI Agent 的時代更是重要，因為 Prompt Injection 讓攻擊者可以不需要找到程式碼的漏洞，只要在 Agent 會處理的資料裡藏一段文字就有機會操控行為。

Soft Guardrail 搭配 Hard Guardrail 的設計哲學值得記住：Soft Guardrail 處理 99% 的正常情況，Hard Guardrail 處理那 1% 的惡意情況。不能只靠 Prompt 來限制 Agent 的行為，就像不能只靠 JavaScript 驗證來保護 API 一樣——系統層級的強制限制才是最後一道防線。
