+++
title = "要最大化 AI Agent 的產出還是得用 YOLO Mode"
date = 2025-10-14
description = "探討 AI Agent 的 YOLO Mode 如何最大化產出，以及在 debug、優化和套件升級等場景的應用，同時分析其風險與降低風險的策略"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "AI", "Agent",]

+++

創作者：[Simon Willison](https://simonwillison.net/about/)

文章：[Designing agentic loops](https://simonwillison.net/2025/Sep/30/designing-agentic-loops/)

Simon Willison 提出要最大化 AI Agent 的產出，還是得要用 YOLO Mode。

需要自動化嘗試大量選項的場景都很適合用 YOLO Mode：
* Debug
* 各類型優化
* 升級套件

但 YOLO Mode 有三個主要的風險：
* 刪除重要的資料
* 資料外洩，如個資或 credential
* 機器被用來當作 proxy 拿來進行攻擊

為了發揮 YOLO Mode 的強大能力，可以考慮以下的方式降低風險：
* 跑在沙盒環境裡如 Docker，或是別人的機器如 GitHub Codespaces。
* 最小化 credential 的使用，如果還是需要，請給予測試環境的 credential 並設置預算上限。

以上 Simon Willison 將之稱為 **Design Agentic Loops**，藉由設計 Agent 的環境使產出最大化，其中還包含提供 agent 完成任務所需的工具、資料與指令等等。
