---
name: chatgpt-md-typora
description: Clean a ChatGPT response on the macOS clipboard into Typora-compatible Markdown. Use specifically when the destination is Typora; LaTeX delimiters remain \(...\) and \[...\] outside code fences.
---

# ChatGPT 剪贴板转 Typora Markdown

运行确定性脚本，原位清理当前 macOS 剪贴板：

```bash
python3 scripts/chatgpt_md.py
```

脚本优先读取剪贴板的 HTML，以恢复标题、粗体、多层列表、表格、引用、链接、代码块和 LaTeX；无 HTML 时回退到纯文本。它会保留 `\(...\)` 与 `\[...\]` 公式定界符；从 HTML/KaTeX 恢复公式时也输出这一形式，以适配 Typora。代码围栏内容保持原样。

需要预览且不修改剪贴板时使用 `--stdout`。处理提供的文本或测试时使用 `--stdin --stdout`。命令失败时不得声称剪贴板已更新。

剪贴板模式仅适用于 macOS，依赖系统自带的 `pbpaste`、`pbcopy`，通常还会使用 `osascript`。脚本仅使用 Python 标准库。安装与测试方法见 [README.md](README.md)。
