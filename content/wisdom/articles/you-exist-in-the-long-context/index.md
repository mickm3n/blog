+++
title = "You Exist In The Long Context"
date = 2024-12-05
description = "探索 Steven Johnson 的新作《The Infernal Machine》，將生成式 AI 融合長短期記憶。透過大 Context Window，賦予沉浸式故事體驗新價值！"

[taxonomies]
categories = [ "閱讀筆記",]
tags = [ "generative-ai",]

+++

創作者：[Steven Johnson](https://adjacentpossible.substack.com/)

文章：[You Exist In The Long Context](https://thelongcontext.com/)

被身為 NotebookLM 傳教士的 Steven Johnson 傳教成功。~Gemini 的 Long Context Window 就是真理。~

文章用一個對話框當作開始，可以經由這個對話框對他的新書《The Infernal Machine》做沉浸式的體驗。

透過導入整本書的內容加上設計好的 Prompt，讀者可以扮演書中的鑑識偵探，一步一步找出事實的真相。生成式 AI 透過與使用者對話，提供彈性即興內容的同時，也能兼顧故事線的正確性。

這讓我想到充滿大量文本的《[柏德之門 3（Baldur's Gate 3）](https://baldursgate3.game/)》。過往製作這種大量文本的遊戲，需要投入大量人力時間對故事的拆分重組及複雜的對話設計。

如今，透過生成式 AI 的發展，只要將故事加上 Prompt 即可達成，且 AI 還能透過對話理解使用者對目前場景的認知，提供不同的指引。

Steven Johnson 把這個進展歸功於 Context Window 的增長。在 LLM 的進展，通常提及模型的參數有多少，但 Context Window 也是一個重要的指標。

作者將模型參數量比擬為長期記憶，而 Context Window 則是短期記憶。長期記憶透過對大量文本的解讀與連結，建立知識的基礎；而短期記憶提供了彈性與個人化。

# Long Context Window 的價值

對於 Long Context Window，最常見的評估方式是大海撈針（Needle-in-a-Haystack (NIAH)），在大文本中埋藏一個特定的資訊，透過問題測試大語言模型能不能回答出特定資訊的答案。

但作者提到 Large Context Window 真正的價值是能看到整片大海，理解前後文的因果關係，透過解析提供新的價值。導入個人的筆記本，它能變成能與你對話的第二大腦；導入企業的決策資料，它能成為熟知企業歷史的專業決策顧問。

一切雖然看似美好，但要達到這樣的成果，高品質的資料還是關鍵。未來資料品質會越來越重要，越來越有價值。

# 窺探 Steven Johnson 的 Prompt

文章的最後也附上 Steven Johnson 產生這個互動式對話的 Prompt：

**（防雷警告！！！會包含推理的劇情）**

```
你是一個互動式推理遊戲的主持人，遊戲內容根據下列文本:{{infernalMachineText}}。

以下是遊戲規則：
你將主持一場以 Charles Crispi 犯罪調查為背景的角色扮演遊戲。
我將扮演開創性的鑑識偵探 Joseph Faurot。
遊戲開始時，由 Fitzgerald 警官帶你到犯罪現場。
讓我自行探索現場並發現玻璃窗上的指紋，不要立即透露這個關鍵線索。

你要：
設置場景和歷史背景
讓我以 Faurot 的視角探索
設計明確的解謎任務 (如尋找玻璃窗上的指紋)
保持劇情符合原文事實

破案方式：
發現玻璃上的指紋
帶到紐約警局總部分析
找到與 Crispi 指紋相符的證據

如果我的行動偏離原有劇情，請巧妙引導回原本時間線，但也給予適度的探索自由。

任務目標：運用科學辦案技巧找出嫌疑犯。

規則：
10 個行動內完成任務
可用 1 次行動請求幫助或詢問歷史/人物背景
除非要求，否則不提供行動選項清單
每回合告知剩餘行動次數
逮捕 Charles Crispi 即獲勝
超過 10 次行動則失敗
遊戲結束後可重新開始
```
