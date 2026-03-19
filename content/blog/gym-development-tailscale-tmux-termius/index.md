+++
title = "AI 負責寫 Code，工程師去重訓：用 Tailscale + tmux + Termius 實現健身房開發"
date = 2026-03-19
description = "用 AI 開發的比例越來越高，等 AI 跑的空檔正好能配合組間休息。紀錄用 Tailscale + tmux + Termius 在健身房用手機遠端開發的完整設定流程。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "claude-code", "tailscale", "productivity",]

+++

# 等 AI 的空檔，拿來重訓

用 AI 輔助開發的比例越來越高，特別是嚴謹度需求較低的個人專案，往往連每行程式碼都不太需要仔細審視，更多時候是給好 Prompt、確認方向，然後等 AI 跑完。

這段等待的時間，讓我想到了重訓時的組間休息。

兩者的節奏其實蠻像的：一段高度專注（設定 Prompt、審視輸出 / 扛起槓鈴）、然後一段等待與恢復（等 AI 產生 / 休息 90 秒）。如果能把這兩件事的節奏搭在一起，理論上就能在不降低訓練品質的前提下，順帶推進開發。

於是近期的一個小目標，就是建立一個能在健身房用手機開發的工作流。

# 之前踩過的坑

## Omnara

最早有試過 [Omnara](https://omnara.com)，這是一個讓你用手機操控 Claude Code 的服務。但後來的體驗不太順——要先在電腦上建立好 Claude Code Session 才能操作，而且 Claude Code 本身更新很快，Omnara 的 UI 常常沒能跟上，用起來要嘛破版、要嘛缺功能，就慢慢沒在用了。

## Claude Code Remote Control

後來 Claude Code 推出了 [Remote Control](https://docs.anthropic.com/en/docs/claude-code/remote-development) 功能，當下蠻期待的，試了一次在健身房遠端開發。結果遇到需要允許較高權限的指令時，畫面就卡在那邊不動，什麼反應都沒有。這種「不知道它在等什麼」的狀態在健身房特別難處理，最後只好放棄那次的開發，心裡默默記下來等它穩定一點再試。

目前版本的穩定性還差了點，之後有機會再看看。

# Tailscale + tmux + Termius

一直有聽說這組合很強，但聽起來要裝三個東西就覺得很麻煩，一直沒有行動。直到今天重訓前，臨時起意試著設定看看，結果花了大概十分鐘就全部搞定，才覺得當初是高估了它的複雜度。

（另外因為之前在設定龍蝦時就已經建立過 Tailscale 的網路了，這部分的時間沒有算進去。如果還沒用過 Tailscale，可以先看[這篇](@/blog/openclaw-tailscale-integration/index.md)的 Tailscale 設定部分。）

# 這三個工具是什麼

## Tailscale：建立安全的私人網路

[Tailscale](https://tailscale.com/) 是一個基於 WireGuard 的 VPN 服務，可以把你的裝置組成一個私有網路（Tailnet）。只要裝置都在同一個 Tailnet 裡，就可以用固定的私有 IP 互相連線，不需要設定防火牆、不需要暴露在公開網路上。

免費方案支援最多 100 個裝置，個人使用完全夠用。

## tmux：讓 Session 在背景持續運行

[tmux](https://github.com/tmux/tmux) 是 Terminal 的 session 管理工具。它讓你可以把 Terminal 工作階段跑在背景，就算 SSH 連線斷了、手機鎖屏了，遠端的 Claude Code 依然繼續執行，下次連回來只需要 `tmux attach` 就能接回原本的狀態。

這對健身房開發特別重要——健身時手機不可能一直保持連線，有了 tmux 才不怕中斷。

## Termius：手機上的 SSH Client

[Termius](https://termius.com/) 是手機上的 Terminal 應用程式，支援 iOS 和 Android，介面設計對觸控蠻友好的，也支援儲存 SSH 連線設定，不用每次都手動輸入 IP 和帳號密碼。

三個工具加在一起：Tailscale 負責讓手機找得到電腦、tmux 讓 Claude Code 在背景持續跑、Termius 讓手機能操作 Terminal——這樣就完整了。

# 設定步驟

## 電腦端（Mac Mini）

### 1. 安裝 Tailscale

```bash
brew install --cask tailscale
```

安裝完後開啟 Tailscale，登入帳號，確認 Mac Mini 出現在 [Tailscale Admin Console](https://login.tailscale.com/admin/machines)。

### 2. 啟用 SSH

macOS 預設沒有開 SSH，需要手動啟用：

**系統設定** → **一般** → **共享** → 開啟 **遠端登入**

確認有勾選允許你的帳號存取。

### 3. 安裝 tmux

```bash
brew install tmux
```

### 4. 確認 Tailscale IP

在 Mac Mini 上執行：

```bash
tailscale ip -4
```

記下這個 IP（格式類似 `100.x.x.x`），等一下在 Termius 設定 SSH 連線時會用到。

---

## 手機端

### 1. 安裝並設定 Tailscale

在 App Store 或 Google Play 安裝 [Tailscale](https://tailscale.com/download)，登入**同一個帳號**，確認 Mac Mini 的名稱出現在裝置列表裡。

### 2. 安裝 Termius

在 App Store 或 Google Play 安裝 [Termius](https://termius.com/)。

### 3. 在 Termius 新增 SSH Host

開啟 Termius，新增一個 Host：

- **Hostname**：填入剛才的 Tailscale IP（`100.x.x.x`）
- **Username**：Mac Mini 的使用者名稱
- **Password**：密碼，或設定 SSH Key（建議）

存好之後點進去連線，如果成功看到 Terminal 畫面就設定完成。

---

# 實際使用流程

**重訓前在電腦上：**

```bash
tmux new -s dev   # 建立名為 dev 的 session
claude            # 啟動 Claude Code
```

**在健身房用手機：**

1. 確認 Tailscale 已開啟
2. 開啟 Termius，連線到 Mac Mini
3. 執行 `tmux attach -t dev` 接回 session
4. 看到 Claude Code 的畫面，就可以開始操作了

組間休息時給 Claude Code 一個任務，下一組做完回來再看看輸出、給下一步的指示，節奏搭起來其實意外地順。

---

# 加碼：RealVNC（處理需要畫面的操作）

有一個邊緣案例：如果 Claude Code 的 Session 過期、需要重新登入，純 Terminal 操作就有點麻煩。這種需要 GUI 的情況，可以透過 [RealVNC](https://www.realvnc.com/) 直接遠端控制桌面。

**電腦端：** 安裝 [RealVNC Server](https://www.realvnc.com/en/connect/download/vnc/)（或直接用 macOS 內建的螢幕共享），搭配 Tailscale 限制只能從 Tailnet 連入。

**手機端：** 安裝 [RealVNC Viewer](https://www.realvnc.com/en/connect/download/viewer/)，輸入 Mac Mini 的 Tailscale IP 連線。

這樣就算遇到需要滑鼠點擊的操作，也能在手機上直接處理，不會卡住。

# 心得

這套流程比我想像中好設定很多，主要是因為每個工具都只做一件事、而且都做得很好：Tailscale 讓網路連線這件事幾乎沒有摩擦力、tmux 讓我不用擔心中斷、Termius 的 UI 在手機上也很好操作。

現在的問題只剩下——重訓時真的能專心重訓，還是會一直想去看 Claude Code 跑出了什麼。
