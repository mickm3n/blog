+++
title = "不讓你下班！Claude Code 的 Ralph Wiggum plugin"
date = 2026-01-13
description = "當 AI 助手學會了 while(true) 的精髓——探索 Claude Code 的 Ralph Wiggum plugin，一個讓 Claude 自主迭代直到任務完成的神奇工具"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "Claude Code", "AI", "開發工具", "自動化",]

[extra]
+++

## 為什麼需要一個「不讓你下班」的 plugin？

最近在玩 Claude Code 的時候，發現了一個很有意思的 plugin：Ralph Wiggum。第一次看到這個名字，我就笑了——如果你看過《辛普森家庭》，應該馬上能理解這個命名的幽默感。

通常我們使用 AI 助手時，是這樣的流程：
1. 給 Claude 一個任務
2. Claude 做完了（或以為做完了）
3. Claude 說「好了，還有什麼需要幫忙的嗎？」
4. 你發現測試沒過、程式碼有 bug、或功能不完整
5. 再次請 Claude 修正
6. 重複步驟 3-5 直到真正完成

聽起來很累對吧？Ralph Wiggum plugin 的出現，就是要打破這個循環——或者說，把這個循環「自動化」。

## Ralph Wiggum 是誰？

在《辛普森家庭》裡，Ralph Wiggum 是個天真無邪、有點遲鈍但非常執著的小孩。他最經典的特質就是：**不管遇到什麼挫折，都會繼續嘗試，永不放棄**。

記得那個經典場景嗎？Ralph 吃著蠟筆說「我在吃紫色！」（I'm eating purple!），即使大家告訴他那不是食物，他還是樂在其中。這種「我自己的方式」（I'm in danger! *微笑*）的精神，正是這個 plugin 的核心哲學。

把這個角色用來命名 AI 工具的 plugin，實在太貼切了：**持續迭代，直到成功為止**。

## Ralph Wiggum Plugin 的哲學

這個 plugin 的核心概念可以用一句話總結：

> **"Ralph is a Bash loop."**

什麼意思？想像一下這段程式碼：

```bash
while true; do
    claude "完成這個功能"
    if [ 任務完成 ]; then
        break
    fi
done
```

Ralph Wiggum plugin 就是把這個概念實作在 Claude Code 裡。它的哲學基於幾個關鍵概念：

### 1. 迭代勝過完美（Iteration > Perfection）

不要期待第一次就完美。讓 AI 自己迭代改進，通常會得到更好的結果。

### 2. 失敗是數據（Failures Are Data）

當測試失敗、程式碼報錯時，這些都是「確定性的壞結果」（deterministically bad）——也就是說，這些錯誤是可預測的、可重現的，因此也是可以被修正的。每次失敗都提供了改進的方向。

### 3. 持續性致勝（Persistence Wins）

就像 Ralph Wiggum 一樣，只要不斷嘗試，最終會找到出路。重點不是聰明，而是堅持。

### 4. 操作者的技能很重要（Operator Skill Matters）

寫出好的 prompt，設定清楚的完成條件，是成功的關鍵。工具再強，沒有好的指令也發揮不了作用。

## 實作方式：如何打造一個不會停的 AI

Ralph Wiggum plugin 的實作方式非常巧妙，主要包含三個核心機制：

### 1. Slash Command：啟動無限循環

Plugin 提供了 `/ralph-loop` 指令來啟動迭代循環：

```bash
/ralph-loop "建立一個 REST API。需求：CRUD 操作、輸入驗證、測試覆蓋率 > 80%。完成後輸出 <promise>COMPLETE</promise>" --completion-promise "COMPLETE" --max-iterations 50
```

這個指令會：
1. 把你的 prompt 餵給 Claude
2. Claude 開始工作
3. 當 Claude 想要結束時...（下面說明）

### 2. Stop Hook：攔截退出企圖

這是整個 plugin 最神奇的地方。

通常 Claude 完成任務後會自然結束對話。但 Ralph Wiggum plugin 透過 **Stop Hook** 攔截了這個退出動作：

```
Claude: "好了！我已經完成了..."
Stop Hook: "等等！" *把相同的 prompt 再餵一次*
Claude: "呃...讓我檢查一下..." *發現測試沒過*
Claude: "我來修正這個問題..."
Stop Hook: *繼續等待*
...循環繼續...
```

重點在於：**每次迭代，prompt 都不會改變**。

那 Claude 怎麼知道要改什麼？答案是：透過 **檔案系統** 和 **git history**。

- 第一次迭代：Claude 寫了程式碼，建立了檔案
- 第二次迭代：Claude 看到自己寫的程式碼、測試結果、錯誤訊息
- 第三次迭代：Claude 看到修改歷史、commit 記錄
- ...持續改進...

這是一種 **自我參照的回饋循環**（self-referential feedback loop）。Claude 在讀取自己過去的工作成果，並基於此做出改進。

### 3. Exit Code 控制：設定完成條件

光是無限循環還不夠，我們需要兩個機制來控制何時停止：

#### 機制一：Completion Promise

透過 `--completion-promise` 參數，你可以指定一個「完成承諾」字串。當 Claude 的輸出中出現這個字串時，循環就會結束。

```bash
--completion-promise "COMPLETE"
```

當 Claude 確認所有測試都通過、所有功能都實作完成後，它會主動輸出：

```
<promise>COMPLETE</promise>
```

Stop Hook 檢測到這個字串，就會放行，讓 Claude 真正結束。

#### 機制二：Max Iterations

作為安全機制，你應該總是設定 `--max-iterations`：

```bash
--max-iterations 50
```

這避免了無限循環的風險。如果 50 次迭代後還沒完成，循環會強制停止。

## 如何寫出好的 Ralph Prompt

根據文件和實際經驗，寫出有效的 Ralph prompt 有幾個訣竅：

### ✅ 清楚的完成標準

```
建立一個 Todo API。

完成條件：
- 所有 CRUD endpoints 都能運作
- 有輸入驗證
- 測試通過（覆蓋率 > 80%）
- 有 README 文件說明 API 用法
- 輸出：<promise>COMPLETE</promise>
```

### ✅ 漸進式目標

```
階段 1：使用者認證（JWT, tests）
階段 2：產品目錄（列表/搜尋, tests）
階段 3：購物車（新增/移除, tests）

所有階段完成後輸出 <promise>COMPLETE</promise>
```

### ✅ 自我修正指令

```
實作功能 X，遵循 TDD：
1. 寫失敗的測試
2. 實作功能
3. 執行測試
4. 如果有失敗，debug 並修正
5. 重構（如需要）
6. 重複直到全部通過
7. 輸出：<promise>COMPLETE</promise>
```

### ✅ 逃生艙口

永遠設定 `--max-iterations` 作為安全網，並在 prompt 裡加上：

```
如果 15 次迭代後仍未完成：
- 記錄目前卡住的地方
- 列出嘗試過的方法
- 建議替代方案
```

## 適合使用 Ralph 的場景

根據實際應用經驗，Ralph Wiggum plugin 特別適合：

**✅ 適合的場景：**
- 有明確成功標準的任務（例如：所有測試通過）
- 需要迭代改進的任務（例如：調整參數直到效能達標）
- Greenfield 專案（你可以放心讓它跑）
- 有自動驗證機制的任務（tests, linters）

**❌ 不適合的場景：**
- 需要人類判斷或設計決策的任務
- 一次性操作（例如：資料庫 migration）
- 成功標準不明確的任務
- Production debugging（用針對性的 debug 方式會更好）

## 真實世界的成果

文件裡提到了一些令人印象深刻的案例：

- 在 Y Combinator hackathon 測試時，一夜之間成功產生了 6 個 repositories
- 一個價值 $50k 的合約，只花了 $297 的 API 成本就完成了
- 有人用這個方法花了 3 個月創造了一整個程式語言（叫做 "cursed"）

這些案例的共同點是：**任務明確、可驗證、需要大量迭代**。

## 我的想法

第一次看到這個 plugin 時，我覺得這個概念既瘋狂又天才。

瘋狂在於：我們通常認為 AI 需要人類的引導，需要「適時介入」。但 Ralph Wiggum plugin 反其道而行——**讓 AI 自己跟自己對話，透過檔案系統作為記憶體**。

天才在於：它利用了 AI 的優勢（快速迭代、不會累、可以重複執行）來彌補人類的劣勢（沒耐心、會疲倦、容易放棄）。

但這也讓我思考：**什麼時候應該放手讓 AI 自己跑，什麼時候需要人類介入？**

我的結論是：當任務的「成功」可以被程式化驗證（tests pass、build succeeds、linter happy），那就讓 Ralph 去做。但當需要品味、判斷、創意決策時，人類還是不可或缺的。

Ralph Wiggum plugin 不是要取代人類開發者，而是要解放我們，讓我們可以專注在真正需要人類智慧的地方。

就像 Ralph Wiggum 在卡通裡一樣——雖然看起來笨笨的，但那份純粹的執著，有時候反而能達成別人做不到的事。

## 參考資源

- [Ralph Wiggum Plugin - GitHub](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum)
- [原始技術說明](https://ghuntley.com/ralph/)
- [Ralph Orchestrator](https://github.com/mikeyobrien/ralph-orchestrator)

---

如果你也在用 Claude Code，不妨試試看這個 plugin。記得設定好 `--max-iterations`，然後就放心去喝杯咖啡吧——當你回來時，說不定任務已經完成了。

或者，你會看到 Claude 迭代了 49 次還在努力。這時候你可能需要調整一下 prompt，或者承認這個任務確實需要人類的判斷。

不管如何，這個「不讓你下班」的 plugin，確實讓開發工作多了一些自動化的可能性。而且，能在開發工具裡看到《辛普森家庭》的彩蛋，也是一種樂趣吧？
