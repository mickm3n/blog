+++
title = "透過 Tailscale 從任何裝置存取家裡的 OpenClaw"
date = 2026-02-05
description = "在 Mac Mini 上跑 OpenClaw，透過 Tailscale Serve 讓 MacBook 和手機都能安全連上，不用設定防火牆也不用暴露在公網上"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "openclaw", "tailscale",]

[extra]
image = ""
+++

# OpenClaw 簡介

最近養龍蝦很紅。[OpenClaw](https://github.com/openclaw/openclaw) 是一個跑在個人電腦上的 AI Agent，我覺得最厲害的地方是 Channel 整合做得很好，支援 Slack、Telegram、WhatsApp 等各種通訊平台，設定完就可以隨時跟 Agent 溝通。我自己是接到個人 Slack，有事情就丟訊息給它。

因為跑在本機，OpenClaw 可以操作你電腦上的各種工具——讀寫檔案、執行指令、瀏覽網頁，權限很大，所以可以當成很強的個人助理來用。但好用跟安全性通常是反向的，權限越大風險也越高，所以使用的同時也會特別注意安全性的設定。

這篇就是關於網路層面的安全性設定。

# 動機

我的 OpenClaw 跑在家裡的 Mac Mini 上，平常作為 24 小時運行的個人 AI 助手。但 OpenClaw Gateway 預設綁定在 `localhost`，也就是只能在 Mac Mini 本機上存取 UI。問題是我大部分時間都是用 MacBook 在工作，偶爾也想在手機上跟 OpenClaw 互動，所以就研究了一下怎麼從其他裝置連上去。

最後選擇了 [Tailscale](https://tailscale.com/)，設定過程比想像中簡單很多。

# Tailscale 簡介

Tailscale 是一個基於 [WireGuard](https://www.wireguard.com/) 的 VPN 服務，主要用途是把你的裝置組成一個私有網路（Tailnet）。跟傳統 VPN 不同的是，Tailscale 不需要自己架設 VPN Server，裝置之間是直接點對點連線，延遲很低。

免費方案就可以連接最多 100 個裝置，對個人使用來說綽綽有餘。

## Tailscale Serve

這次主要用到的功能是 [Tailscale Serve](https://tailscale.com/kb/1312/serve)。簡單來說，它可以把你本機的服務透過 Tailnet 以 HTTPS 的方式分享給你的其他裝置。

舉例來說，你的 Mac Mini 上有一個跑在 `http://localhost:18789` 的服務，透過 `tailscale serve` 設定後，你的 MacBook 和手機只要在同一個 Tailnet 裡，就可以用 `https://mac-mini.tail1234.ts.net` 這樣的網址安全存取。

重點是：

- **不需要開 Port**：服務維持綁定在 localhost，不需要修改防火牆規則
- **自動 HTTPS**：Tailscale 自動處理憑證，不用自己搞 Let's Encrypt
- **存取控制**：只有你 Tailnet 裡的裝置可以連上，不會暴露在公網上
- **身份識別**：Tailscale 會在 HTTP Header 帶上使用者的身份資訊，服務端可以用來做認證

# 為什麼用 Tailscale 整合 OpenClaw？

要從其他裝置存取 OpenClaw，有幾種常見的做法：

1. **改綁定到 LAN IP**：直接把 Gateway 綁定到區網 IP，同個 Wi-Fi 下的裝置就可以連上。但安全性較低，同網路的人都可以存取，而且離開家就連不上了。
2. **SSH Tunnel**：每次要用的時候手動建 SSH Tunnel。安全，但每次都要操作一次比較麻煩，手機上也不太方便。
3. **反向代理（Nginx / Caddy）**：自己架設反向代理加上 HTTPS，需要有公網 IP 或 DDNS，設定相對複雜。
4. **Tailscale Serve**：設定簡單、自動 HTTPS、只有自己的裝置可以存取，而且 OpenClaw 原生支援。

對我這種「跑在家裡、只有自己要用」的情境來說，Tailscale Serve 是最省事的選擇。

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

進入 **DNS** 頁面 → 啟用 **MagicDNS**（通常預設已經開了）→ 啟用 **HTTPS Certificates**。

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

### 關於認證

在 `tailscale.mode` 設成 `serve` 的情況下，OpenClaw 預設會啟用 `allowTailscale` 認證。這代表 Tailscale 會在轉發請求時帶上使用者的身份資訊（透過 `Tailscale-User-Login` 等 Header），OpenClaw 會自動驗證這些資訊，不需要額外設定 Token 或密碼。

所以 `openclaw config set gateway.auth.mode token` 和 `openclaw doctor --generate-gateway-token` **對於 Tailscale Serve 存取來說不是必要的**。不過如果你同時也想在 Mac Mini 本機上直接透過 `localhost` 使用 CLI 或 API（不經過 Tailscale），那設定一個 Token 作為 fallback 認證方式還是有用的。

如果你確定只會透過 Tailscale 存取，最精簡的設定只需要三個指令：

```bash
openclaw config set gateway.bind loopback
openclaw config set gateway.tailscale.mode serve
openclaw config set gateway.trustedProxies '["127.0.0.1"]'
```

## 4. 驗證連線

設定完成後，可以先檢查 Tailscale Serve 的狀態：

```bash
tailscale serve status
```

應該會看到類似這樣的輸出，顯示你的 OpenClaw Gateway port 已經被 Serve 出去。

接著在 MacBook 上打開瀏覽器，輸入 Mac Mini 的 Tailscale 網址（在 Admin Console 或 `tailscale status` 可以查到），應該就可以看到 OpenClaw 的 UI 了。

## 5. 手機設定

在手機上使用也很簡單：

1. 安裝 Tailscale App（[iOS](https://apps.apple.com/app/tailscale/id1470499037) / [Android](https://play.google.com/store/apps/details?id=com.tailscale.ipn)）
2. 登入同一個帳號
3. 在手機瀏覽器輸入 Mac Mini 的 Tailscale 網址

因為 Tailscale 的認證是基於裝置和帳號的，只要手機加入了 Tailnet，就可以直接存取 OpenClaw UI，不需要額外輸入密碼或 Token。

如果想要更方便，可以把網址加到手機桌面當作 Web App 使用。

# 小結

整個設定過程大概十分鐘內就可以完成，最核心的就是三行 OpenClaw 設定加上安裝 Tailscale。對於像我一樣把 OpenClaw 跑在家裡固定主機、但想從其他裝置存取的人來說，Tailscale Serve 是目前我找到最簡單也最安全的方案。
