+++
title = "如何在一台電腦上使用多個 Claude Code Profile"
date = 2026-03-04
description = "透過 Shell 設定檔中的 alias 搭配 CLAUDE_CONFIG_DIR 環境變數，輕鬆在同一台電腦上切換不同的 Claude Code 帳號與設定環境。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "claude-code",]

+++

如果你同時有個人和工作兩個 Claude Code 帳號，或是想為不同專案維護獨立的設定，可以透過一個簡單的 alias 來達成。

# 設定方式

在你的 Shell 設定檔（以 zsh 為例是 `~/.zshrc`，bash 則是 `~/.bashrc`）加入：

```sh
alias claude-work="CLAUDE_CONFIG_DIR=~/.claude-work claude"
```

存檔後重新載入設定（或開新的終端機視窗），然後執行一次 `claude-work` 完成登入。

之後就可以這樣使用：

- `claude` — 使用預設環境（設定存在 `~/.claude`）
- `claude-work` — 使用工作環境（設定存在 `~/.claude-work`）

兩個環境彼此獨立，帳號、設定、對話記錄都不會互相影響。

我自己是在 MacOS 上使用，但照理說 Linux 和 Windows 上的 WSL 應該也都適用。
