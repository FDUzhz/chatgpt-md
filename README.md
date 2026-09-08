# chatgpt-md

一个面向 macOS 的 Codex Skill：把当前剪贴板里的 ChatGPT 回复转换成干净、可复用的 Markdown，并自动写回剪贴板。

## 版本迭代

### v2.0.0：按编辑器拆分（当前版本）

实际使用表明，不同 Markdown 编辑器对公式定界符的处理并不一致。因此 v2.0.0 将功能拆成两个可独立安装、独立调用的 Skill：

| Skill | 目标编辑器 | 公式处理 |
| --- | --- | --- |
| [`chatgpt-md-obsidian`](chatgpt-md-obsidian/) | Obsidian | `\(...\)` → `$...$`，`\[...\]` → `$$...$$` |
| [`chatgpt-md-typora`](chatgpt-md-typora/) | Typora | 保留 `\(...\)` 与 `\[...\]` |

两者都会对纯文本和 HTML/KaTeX 中恢复出的公式采用对应策略，并且不会改写围栏代码块内部内容。

### v1.1.0：修复公式显示

这一迭代解决了公式出现在标题、正文和列表中时被当作普通文本显示的问题：在代码块之外识别 `\(...\)` 与 `\[...\]`，并转换成 `$...$` 与 `$$...$$`。

### v1.0.0：基础剪贴板清理

首个版本完成 ChatGPT HTML/纯文本到 Markdown 的转换，覆盖标题、粗体、多层列表、代码块、表格、引用、链接、空行和 Unicode 项目符号。

详细变化见 [CHANGELOG.md](CHANGELOG.md)。原来的 `chatgpt-md` 保留为兼容入口，默认行为与 Obsidian 版一致。

它会优先读取浏览器放入剪贴板的 HTML，以保留标题、粗体、列表和多层列表、代码块、Markdown 表格、LaTeX 公式、引用及链接；没有 HTML 时，会保守清理纯文本中的多余空行、Unicode 项目符号、制表符表格和常见 Markdown 间距问题。

## 功能特点

- 保留标题、粗体、斜体、删除线、引用和链接。
- 转换有序列表、无序列表及多层嵌套列表。
- 保留围栏代码块内容，并识别常见语言标记。
- 将 HTML 表格或制表符分隔文本转换为 Markdown 表格。
- 从 KaTeX/MathML 恢复 LaTeX，并兼容标题、正文和列表中的公式。
- 清理多余空行、不可见 Unicode 字符和特殊项目符号。
- 不访问网络，不读取任意文件，仅处理当前剪贴板或标准输入。

## 安装当前版本

克隆仓库：

```bash
git clone https://github.com/FDUzhz/chatgpt-md.git
```

按需安装一个或同时安装两个 Skill：

```bash
mkdir -p ~/.codex/skills
cp -R chatgpt-md/chatgpt-md-obsidian ~/.codex/skills/chatgpt-md-obsidian
cp -R chatgpt-md/chatgpt-md-typora ~/.codex/skills/chatgpt-md-typora
```

重新启动 Codex，或开启一个新任务以刷新 Skill 列表。

处理准备粘贴到 Obsidian 的内容：

```text
使用 $chatgpt-md-obsidian 清理当前剪贴板
```

处理准备粘贴到 Typora 的内容：

```text
使用 $chatgpt-md-typora 清理当前剪贴板
```

## 命令行用法

直接转换当前剪贴板并写回：

```bash
python3 scripts/chatgpt_md.py
```

只预览，不修改剪贴板：

```bash
python3 scripts/chatgpt_md.py --stdout
```

从标准输入清理纯文本：

```bash
pbpaste | python3 scripts/chatgpt_md.py --stdin --stdout
```

从标准输入转换 HTML：

```bash
python3 scripts/chatgpt_md.py --stdin --input-format html --stdout < reply.html
```

兼容入口也可以显式选择公式风格：

```bash
python3 scripts/chatgpt_md.py --math-delimiters dollar
python3 scripts/chatgpt_md.py --math-delimiters backslash
```

运行自带测试：

```bash
python3 -m unittest discover -s tests -v
```

## 说明与边界

- 剪贴板模式仅支持 macOS；stdin/stdout 模式可在其他平台运行。
- 脚本只使用 Python 标准库，无需安装第三方依赖。
- HTML 链接仅保留 `http`、`https`、`mailto` 和相对地址；会丢弃 `javascript:`、`data:`、`file:` 等危险或本地协议。
- 纯文本已丢失的视觉格式（例如网页里的粗体或链接地址）无法可靠恢复；从 ChatGPT 网页复制后直接运行效果最好。
- 转换采取保守策略：不会把普通段落武断地改成标题，也不会改写围栏代码块内部内容。
- LaTeX 优先从 KaTeX/MathML 的 `application/x-tex` annotation 恢复，再按照所选 Skill 输出对应定界符。
- Obsidian 版输出 `$...$` 与 `$$...$$`；Typora 版输出 `\(...\)` 与 `\[...\]`；标题、正文和列表均适用，代码块内部保持原样。

## 安全说明

- 不包含网络请求、遥测或第三方依赖。
- 外部命令固定调用 macOS 系统路径，避免从不可信 `PATH` 加载同名程序。
- HTML 链接使用协议白名单，危险协议不会进入生成的 Markdown 链接。
- 默认行为会覆盖剪贴板；需要先检查结果时，请使用 `--stdout`。

## 项目结构

```text
chatgpt-md/
├── chatgpt-md-obsidian/
│   ├── SKILL.md
│   ├── README.md
│   ├── agents/openai.yaml
│   ├── scripts/chatgpt_md.py
│   └── tests/test_chatgpt_md.py
├── chatgpt-md-typora/
│   ├── SKILL.md
│   ├── README.md
│   ├── agents/openai.yaml
│   ├── scripts/chatgpt_md.py
│   └── tests/test_chatgpt_md.py
├── SKILL.md                 # v1 兼容入口
├── README.md
├── agents/openai.yaml
├── scripts/chatgpt_md.py
└── tests/test_chatgpt_md.py
```
