+++
title = "如何在一台電腦上使用多個 Claude Code Profile"
date = 2026-03-04
description = "透過 Shell 設定檔中的 alias 搭配 CLAUDE_CONFIG_DIR 環境變數，輕鬆在同一台電腦上切換不同的 Claude Code 帳號與設定環境。"

[taxonomies]
categories = [ "經驗分享",]
tags = [ "claude-code", "developer-tools",]

+++

如果你同時有個人和工作兩個 Claude Code 帳號，或是想為不同專案維護獨立的設定，可以透過一個簡單的 alias 來達成。

# 設定方式

在你的 Shell 設定檔（以 zsh 為例是 `~/.zshrc`，bash 則是 `~/.bashrc`）加入：

```sh
alias claude-work="CLAUDE_CONFIG_DIR=~/.claude-work command claude"
```

存檔後重新載入設定（或開新的終端機視窗），然後執行一次 `claude-work` 完成登入。

之後就可以這樣使用：

- `claude` — 使用預設環境（設定存在 `~/.claude`）
- `claude-work` — 使用工作環境（設定存在 `~/.claude-work`）

兩個環境彼此獨立，帳號、設定、對話記錄都不會互相影響。

# 為什麼要用 `command claude`？

你可能會好奇，直接寫 `claude` 不就好了？

如果只設 `claude-work` 這一個 alias，`claude` 本身是執行檔，確實不需要 `command`。

但很常見的做法是**同時把 `claude` 也做成 alias**，綁到個人帳號：

```sh
alias claude="CLAUDE_CONFIG_DIR=~/.claude command claude"
alias claude-work="CLAUDE_CONFIG_DIR=~/.claude-work command claude"
```

這時候如果 `claude-work` 裡寫的是 `claude`（沒有 `command`），執行流程會變成：

1. `claude-work` 展開 → `CLAUDE_CONFIG_DIR=~/.claude-work claude`
2. `claude` 觸發 alias → `CLAUDE_CONFIG_DIR=~/.claude claude`（還把剛設的 env var 覆蓋掉了！）
3. `claude` 再次觸發 alias → 無限遞迴

`command` 是 Shell 內建指令，作用是**直接呼叫同名的執行檔，略過所有 alias 和 shell function**。兩個 alias 裡都加上 `command`，就能確保呼叫的是實際的二進位執行檔，不會互相干擾。

# 環境相容性

這個方法有一些前提：

**支援的作業系統：**
- macOS
- Linux
- Windows 上的 WSL（Windows Subsystem for Linux）

**支援的 Shell：**

`VARIABLE=value command` 這個語法，加上 `alias` 和 `command` 內建指令，都是 POSIX 標準的一部分，在大多數常見的 Shell 都能使用：

| Shell | 是否支援 |
|-------|----------|
| zsh   | ✅        |
| bash  | ✅        |
| dash  | ✅        |
| ksh   | ✅        |
| fish  | ❌        |

**fish shell** 的語法不相容 POSIX，需要用不同的方式設定：

```fish
function claude-work
    set -x CLAUDE_CONFIG_DIR ~/.claude-work
    command claude $argv
end
```

Windows 原生的 PowerShell 或 cmd.exe 也不適用這個方法，需要另外處理。
