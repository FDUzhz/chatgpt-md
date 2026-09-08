# chatgpt-md

一个面向 macOS 的 Codex Skill：把当前剪贴板里的 ChatGPT 回复转换成干净、可复用的 Markdown，并自动写回剪贴板。

它会优先读取浏览器放入剪贴板的 HTML，以保留标题、粗体、列表和多层列表、代码块、Markdown 表格、LaTeX 公式、引用及链接；没有 HTML 时，会保守清理纯文本中的多余空行、Unicode 项目符号、制表符表格和常见 Markdown 间距问题。

## 功能特点

- 保留标题、粗体、斜体、删除线、引用和链接。
- 转换有序列表、无序列表及多层嵌套列表。
- 保留围栏代码块内容，并识别常见语言标记。
- 将 HTML 表格或制表符分隔文本转换为 Markdown 表格。
- 从 KaTeX/MathML 恢复 LaTeX，并兼容标题、正文和列表中的公式。
- 清理多余空行、不可见 Unicode 字符和特殊项目符号。
- 不访问网络，不读取任意文件，仅处理当前剪贴板或标准输入。

## 安装

将整个目录复制到 Codex Skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R chatgpt-md ~/.codex/skills/chatgpt-md
```

也可以直接从 GitHub 安装：

```bash
git clone https://github.com/FDUzhz/chatgpt-md.git ~/.codex/skills/chatgpt-md
```

重新启动 Codex，或开启一个新任务以刷新 Skill 列表。之后可以说：

```text
使用 $chatgpt-md 清理当前剪贴板
```

也可以不安装，直接在本目录运行脚本。

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
- LaTeX 优先从 KaTeX/MathML 的 `application/x-tex` annotation 恢复；行内公式输出 `$...$`，块级公式输出 `$$...$$`。
- ChatGPT 纯文本中的 `\\(...\\)` 与 `\\[...\\]` 也会分别规范为 `$...$` 与 `$$...$$`，包括标题、正文和列表中的公式；代码块内部保持原样。

## 安全说明

- 不包含网络请求、遥测或第三方依赖。
- 外部命令固定调用 macOS 系统路径，避免从不可信 `PATH` 加载同名程序。
- HTML 链接使用协议白名单，危险协议不会进入生成的 Markdown 链接。
- 默认行为会覆盖剪贴板；需要先检查结果时，请使用 `--stdout`。

## 项目结构

```text
chatgpt-md/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── scripts/chatgpt_md.py
└── tests/test_chatgpt_md.py
```
