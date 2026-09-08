---
name: chatgpt-md-obsidian
description: Clean a ChatGPT response on the macOS clipboard into Obsidian-compatible Markdown. Use specifically when the destination is Obsidian; LaTeX delimiters are normalized to $...$ and $$...$$ outside code fences.
---

# ChatGPT 剪贴板转 Obsidian Markdown

运行确定性脚本，原位清理当前 macOS 剪贴板：

```bash
python3 scripts/chatgpt_md.py
```

脚本优先读取剪贴板的 HTML，以恢复标题、粗体、多层列表、表格、引用、链接、代码块和 LaTeX；无 HTML 时回退到纯文本。它会在代码围栏之外将 `\(...\)` 转为 `$...$`、将 `\[...\]` 转为 `$$...$$`，包括标题、正文和列表中的公式，以适配 Obsidian。

需要预览且不修改剪贴板时使用 `--stdout`。处理提供的文本或测试时使用 `--stdin --stdout`。命令失败时不得声称剪贴板已更新。

剪贴板模式仅适用于 macOS，依赖系统自带的 `pbpaste`、`pbcopy`，通常还会使用 `osascript`。脚本仅使用 Python 标准库。安装与测试方法见 [README.md](README.md)。
