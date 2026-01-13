+++
title = "不讓 Claude Code 下班的 Ralph Wiggum Plugin"
date = 2026-01-13
description = "當 AI 助手學會了 while(true) 的精髓——探索 Claude Code 的 Ralph Wiggum plugin，一個讓 Claude 自主迭代直到任務完成的神奇工具"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "Claude Code",]

[extra]
image = "ralph-wiggum.webp"
+++

最近 Claude Code 作者之一的 [Boris Cherny](https://x.com/bcherny) 分享[他如何使用 Claude Code](https://x.com/bcherny/status/2007179832300581177/)。發現他在執行長時間的任務時，會使用 [Ralph Wiggum Plugin](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) 來確保長時間任務的結果符合預期。

# Ralph Wiggum 是誰？

![](ralph-wiggum.webp)

在《辛普森家庭》裡，Ralph Wiggum 是個天真無邪、有點遲鈍但非常執著的小孩。他最經典的特質就是：**不管遇到什麼挫折，都會繼續嘗試，永不放棄**。

用此命名的 Claude Code plugin 代表的理念就是「**持續迭代，直到成功為止**」。

# Ralph Wiggum Plugin 到底在做什麼？

用簡單的程式碼表示就是：

```bash
while true; do
    claude "完成這個功能"
    if [ 任務完成 ]; then
        break
    fi
done
```

看似簡單的程式碼，也隱含了一些事實：
1. 執行的任務需要能重複執行，不管是因為要處理的任務數量很多，例如寫測試直到覆蓋率大於 85%，或是透過重複的迭代可以讓結果更好，例如調整參數直到效能達標。
2. 必須能明確定義任務結束的條件，也就隱含著任務的成功與否可以被驗證。

# Ralph Wiggum plugin 的實作：防止 Claude Code 速速下班

## 1. 用 Slash Command 快速啟動循環

Plugin 實作了 Slash Command `/ralph-loop` 指令來啟動迭代循環：

使用範例：
```bash
/ralph-loop "建立一個 REST API。需求：CRUD 操作、輸入驗證、測試覆蓋率 > 80%。完成後輸出 <promise>COMPLETE</promise>" --completion-promise "COMPLETE" --max-iterations 50
```

從參數裡我們我們可以看到：
* 任務描述：`建立一個 REST API。需求：CRUD 操作、輸入驗證、測試覆蓋率 > 80%。`
* 完成條件：`需求：CRUD 操作、輸入驗證、測試覆蓋率 > 80%`
* 完成的停止方法：`完成後輸出 <promise>COMPLETE</promise>"` + `--completion-promise "COMPLETE"`
* 最大迭代次數以防止無限循環：`--max-iterations 50`

## 2. Stop Hook 攔截退出企圖

這是這個 Ralph Wiggum Plugin 的精隨。通常 Claude Code 在完成任務後會自然結束對話，但 Ralph Wiggum Plugin 透過 **Stop Hook** 攔截了這個退出動作，並且重複執行任務直到 Agent 驗證完成條件送出 Promise，或是到達設定的最大迭代次數。

# 適合使用 Ralph Wiggum Plugin 的場景

- 有明確成功標準的任務（例如：所有測試通過）
- 需要迭代改進的任務（例如：調整參數直到效能達標）
- Greenfield 專案（你可以放心讓它跑）
- 有自動驗證機制的任務（tests, linters）

# 不適合的場景
- 需要人類判斷或設計決策的任務
- 一次性操作（例如：資料庫 migration）
- 成功標準不明確的任務
