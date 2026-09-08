---
name: chatgpt-md
description: Clean a ChatGPT response currently on the macOS clipboard into Markdown and write it back to the clipboard. Use when the user wants copied ChatGPT content normalized or converted for Markdown notes, editors, or documentation.
---

# ChatGPT 剪贴板转 Markdown

使用确定性脚本原地转换当前 macOS 剪贴板：

```bash
python3 scripts/chatgpt_md.py
```

脚本优先读取剪贴板的 HTML 格式，以恢复标题、粗体、多层列表、表格、引用、链接、代码块和 LaTeX。若没有 HTML，则回退到纯文本；在代码围栏之外，将 `\\(...\\)` 和 `\\[...\\]` 公式定界符转换为 `$...$` 和 `$$...$$`，并保守清理已有 Markdown。成功后，干净的 Markdown 会替换剪贴板内容，同时向 stderr 输出简短状态。

需要预览且不修改剪贴板时使用 `--stdout`。处理用户提供的文本或测试时使用 `--stdin --stdout`。如果命令失败，不得声称剪贴板已更新。

剪贴板模式需要 macOS，依赖系统自带的 `pbpaste`、`pbcopy`，通常还会使用 `osascript`。脚本仅使用 Python 标准库。安装方法、选项和示例见 [README.md](README.md)。
