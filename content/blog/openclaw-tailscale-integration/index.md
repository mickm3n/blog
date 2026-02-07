+++
title = "透過 Tailscale 從任何裝置存取家裡的 OpenClaw"
date = 2026-02-05
description = "在 Mac Mini 上跑 OpenClaw，透過 Tailscale Serve 讓 MacBook 和手機都能安全連上，不用設定防火牆也不用暴露在外網上"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw", "tailscale",]

[extra]
image = "openclaw.webp"
+++

# OpenClaw 簡介

最近很流行養龍蝦。

![](openclaw.webp)

[龍蝦（OpenClaw）](https://github.com/openclaw/openclaw) 是一個跑在個人電腦上的 AI Agent，我覺得厲害的地方是 [Channel](https://docs.openclaw.ai/channels/index) 整合做得很好，支援 Slack、Telegram、WhatsApp、Line 等各種通訊平台，簡單設定完就可以用想要的方式跟 Agent 溝通。我自己是接到個人 Slack 來跟他對話。

因為跑在本機，OpenClaw 可以操作電腦上的各種工具——讀寫檔案、執行指令、瀏覽網頁，權限很大，所以可以當成很強的個人助理來用。但好用跟安全性通常是反向的，權限越大風險也越高，所以邊在探索使用情境的同時也會特別注意安全性的設定。

我的 OpenClaw 跑在家裡的 Mac Mini 上，作為 24 小時運行的個人 AI 助手。但 OpenClaw Gateway 預設綁定在 `localhost`，也就是只能在 Mac Mini 本機上存取 UI。但是我大部分時間都是用 MacBook 在工作，偶爾也想在手機上排查 OpenClaw 的狀態，所以就研究了一下怎麼從其他裝置連上去。

這篇記錄一下 OpenClaw 串接 [Tailscale](https://tailscale.com/) 的設定。

# Tailscale 簡介

Tailscale 是一個基於 [WireGuard](https://www.wireguard.com/) 的 VPN 服務，主要用途是把你的裝置組成一個私有網路（Tailnet）。跟傳統 VPN 不同的是，Tailscale 不需要自己架設 VPN Server，裝置之間是直接點對點連線，延遲很低。

免費方案就可以連接最多 100 個裝置，對個人使用來說綽綽有餘。

## Tailscale Serve

這次主要用到的功能是 [Tailscale Serve](https://tailscale.com/kb/1312/serve)。簡單來說，它可以把你本機的服務透過 Tailnet 以 HTTPS 的方式分享給你的其他裝置。

舉例來說，你的 Mac Mini 上有一個跑在 `http://localhost:18789` 的服務，透過 `tailscale serve` 設定後，你的 MacBook 和手機只要在同一個 Tailnet 裡，就可以用 `https://mac-mini.tail1234.ts.net` 這樣的網址安全存取。

Tailscale Serve 方案解決了以下的問題：

- **不需要開對外 Port**：服務維持綁定在 localhost，不會暴露在外有未預期的存取
- **自動 HTTPS**：Tailscale 會自動處理憑證，不用自己用類似 Let's Encrypt 的方式申請憑證
- **存取控制**：只有 Tailnet 裡的裝置可以連上

而且 OpenClaw 原生就支援 Tailscale Serve 的整合，只需要透過 Config 就能輕鬆設定。

# 設定步驟

## 1. 安裝 Tailscale

在 Mac Mini（OpenClaw 主機）和 MacBook 上都安裝 Tailscale 並登入同一個帳號。

Mac 可以直接從 [Mac App Store](https://apps.apple.com/app/tailscale/id1475387142) 安裝，或用 Homebrew：

```bash
brew install --cask tailscale
```

安裝完後登入，確認兩台裝置都出現在 [Tailscale Admin Console](https://login.tailscale.com/admin/machines) 裡。

## 2. 啟用 HTTPS

Tailscale Serve 需要 HTTPS 憑證，要先在 Admin Console 啟用：

進入 **DNS** 頁面 → 確認 **MagicDNS** 和 **HTTPS Certificates** 都已啟用。

## 3. 設定 OpenClaw

OpenClaw 原生支援 Tailscale Serve 的整合，只需要幾個設定：

```bash
# Gateway 維持綁定在 localhost
openclaw config set gateway.bind loopback

# 啟用 Tailscale Serve 模式
openclaw config set gateway.tailscale.mode serve

# 設定信任的 Proxy（Tailscale Serve 從 localhost 轉發請求）
openclaw config set gateway.trustedProxies '["127.0.0.1"]'
```

設定完後重啟 Gateway：

```bash
openclaw gateway restart
```

OpenClaw 啟動時會自動執行 `tailscale serve`，把 Gateway 的 port 透過 Tailscale 分享出去。

在 `tailscale.mode` 設成 `serve` 的情況下，OpenClaw 預設會啟用 `allowTailscale` 認證，不需要額外設定 Token 或密碼。

## 4. 驗證連線

設定完成後，可以在 Mac Mini 上檢查 Tailscale Serve 的狀態：

```bash
> tailscale serve status
https://xxx.tailxxxxxx.ts.net (tailnet only)
|-- / proxy http://127.0.0.1:18789
```

看到類似這樣的輸出，顯示你的 OpenClaw Gateway port 已經被 Serve 出去。

接著在其他裝置上打開瀏覽器，輸入上述指令得到的 Tailscale 網址就可以看到 OpenClaw 的 UI 了。

## 5. 手機設定

在手機上使用也很簡單：

1. 安裝 Tailscale App
2. 登入同一個帳號
3. 在手機瀏覽器輸入 Mac Mini 的 Tailscale 網址

因為 Tailscale 的認證是基於裝置和帳號的，只要手機加入了 Tailnet，就可以直接存取 OpenClaw UI。
