+++
title = "Harper's LLM Codegen Workflow"
date = 2025-03-03
description = "探索 Harper Reed 的 LLM 工作流，學習如何利用 LLM 開發專案，從創意生成到細節實作，運用互動和工具提升效率。"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "generative-ai",]

+++

創作者：[Harper Reed](https://harper.blog/about/)

文章：[My LLM codegen workflow atm](https://harper.blog/2025/02/16/my-llm-codegen-workflow-atm/)

很精彩的一篇文章！Harper Reed 分享他如何利用 LLM 開發專案的工作流。

作者在利用這個方法後，已經把自己的想做的應用清單都清空了。

如果是全新的專案，他會先透過對話的方式與 LLM 進行 Brainstorming，直到細節被釐清成完整的 Spec。根據這個 Spec，要求推理模型將其拆解成可逐步執行的計劃，並同時產生 Checklist 提供給 LLM 管理進度，也讓人可以掌握進度。最後再與 LLM 一步步地共同去完成實作。

如果是已存在的大型專案，會把執行的範圍從專案縮減成一個要完成的功能，並利用 [Repomix](https://github.com/yamadashy/repomix) 工具提供 LLM 所需的專案相關脈絡。

作者在文章裡也提供了他在每個步驟用到的提示詞，很值得一讀。
