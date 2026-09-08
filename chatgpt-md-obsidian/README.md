# chatgpt-md-obsidian

将 macOS 剪贴板中的 ChatGPT 回复清理成适用于 Obsidian 的 Markdown，并写回剪贴板。

公式规则：行内 `\(...\)` 转为 `$...$`，块级 `\[...\]` 转为 `$$...$$`；代码块内部不转换。

## 安装

```bash
cp -R chatgpt-md-obsidian ~/.codex/skills/chatgpt-md-obsidian
```

重启 Codex 或开启新任务，然后说：

```text
使用 $chatgpt-md-obsidian 清理当前剪贴板
```

## 测试与预览

```bash
python3 -m unittest discover -s tests -v
python3 scripts/chatgpt_md.py --stdout
```

脚本仅使用 Python 标准库；剪贴板模式需要 macOS。它不会访问网络，默认会覆盖当前剪贴板。
