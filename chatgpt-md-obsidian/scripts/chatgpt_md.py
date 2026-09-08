#!/usr/bin/env python3
"""Convert a copied ChatGPT response to clean Markdown on macOS."""

from __future__ import annotations

import argparse
import html
from html.parser import HTMLParser
import os
import re
import subprocess
import sys
from typing import Optional
from urllib.parse import urlsplit


BULLETS = "•◦▪▫●○■□►▸‣⁃"
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "main", "aside"}
OSASCRIPT = "/usr/bin/osascript"
PBCOPY = "/usr/bin/pbcopy"
PBPASTE = "/usr/bin/pbpaste"
DEFAULT_MATH_DELIMITERS = "dollar"


def _safe_href(value: Optional[str]) -> Optional[str]:
    """Keep ordinary web/mail/relative links and reject executable URL schemes."""
    if not value or re.search(r"[\x00-\x1f\x7f]", value):
        return None
    value = value.strip()
    scheme = urlsplit(value).scheme.lower()
    if scheme and scheme not in {"http", "https", "mailto"}:
        return None
    return value.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def _escape_cell(value: str) -> str:
    return value.strip().replace("|", r"\|").replace("\n", "<br>")


class MarkdownHTMLParser(HTMLParser):
    """Small, dependency-free HTML-to-Markdown converter tuned for copied chat."""

    def __init__(self, math_delimiters: str = DEFAULT_MATH_DELIMITERS) -> None:
        super().__init__(convert_charrefs=True)
        self.math_delimiters = math_delimiters
        self.out: list[str] = []
        self.href_stack: list[Optional[str]] = []
        self.list_stack: list[dict[str, object]] = []
        self.in_pre = 0
        self.inline_code = 0
        self.quote_depth = 0
        self.table: Optional[dict[str, object]] = None
        self.capture_tex = 0
        self.tex_parts: list[str] = []
        self.math_display_stack: list[bool] = []
        self.suppress_math = 0

    def emit(self, value: str) -> None:
        self.out.append(value)

    def newline(self, count: int = 1) -> None:
        current = "".join(self.out)
        have = len(current) - len(current.rstrip("\n"))
        if have < count:
            self.emit("\n" * (count - have))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        a = dict(attrs)
        classes = set((a.get("class") or "").split())

        if tag in {"math", "span"} and (tag == "math" or any("katex" in c for c in classes)):
            display = a.get("display") == "block" or "katex-display" in classes
            self.math_display_stack.append(display)
            self.suppress_math += 1
        if tag == "annotation" and a.get("encoding") == "application/x-tex":
            self.capture_tex += 1
            self.tex_parts = []
            self.suppress_math = max(0, self.suppress_math - 1)
            return
        if self.suppress_math:
            return

        if tag in BLOCK_TAGS:
            self.newline(1 if self.quote_depth else 2)
            if self.quote_depth:
                self.emit("> " * self.quote_depth)
        elif re.fullmatch(r"h[1-6]", tag):
            self.newline(2)
            self.emit("#" * int(tag[1]) + " ")
        elif tag == "br":
            self.newline()
        elif tag in {"strong", "b"}:
            self.emit("**")
        elif tag in {"em", "i"}:
            self.emit("*")
        elif tag == "del" or tag == "s":
            self.emit("~~")
        elif tag == "a":
            self.href_stack.append(_safe_href(a.get("href")))
            self.emit("[")
        elif tag == "blockquote":
            self.quote_depth += 1
            self.newline(2)
        elif tag in {"ul", "ol"}:
            self.list_stack.append({"tag": tag, "index": 0})
            self.newline()
        elif tag == "li":
            self.newline()
            depth = max(0, len(self.list_stack) - 1)
            marker = "- "
            if self.list_stack and self.list_stack[-1]["tag"] == "ol":
                self.list_stack[-1]["index"] = int(self.list_stack[-1]["index"]) + 1
                marker = f"{self.list_stack[-1]['index']}. "
            prefix = "> " * self.quote_depth
            self.emit(prefix + "  " * depth + marker)
        elif tag == "pre":
            self.newline(2)
            language = ""
            m = re.search(r"(?:language-|lang-)([\w+-]+)", a.get("class") or "")
            if m:
                language = m.group(1)
            self.emit("```" + language + "\n")
            self.in_pre += 1
        elif tag == "code" and not self.in_pre:
            self.inline_code += 1
            self.emit("`")
        elif tag == "table":
            self.table = {"rows": [], "row": None, "cell": None, "header": False}
        elif tag == "tr" and self.table is not None:
            self.table["row"] = []
        elif tag in {"th", "td"} and self.table is not None:
            self.table["cell"] = []
            if tag == "th":
                self.table["header"] = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "annotation" and self.capture_tex:
            tex = html.unescape("".join(self.tex_parts)).strip()
            display = any(self.math_display_stack)
            if self.math_delimiters == "dollar":
                self.emit(("\n$$\n" + tex + "\n$$\n") if display else ("$" + tex + "$"))
            else:
                self.emit(("\n\\[\n" + tex + "\n\\]\n") if display else ("\\(" + tex + "\\)"))
            self.capture_tex -= 1
            self.suppress_math += 1
            return
        if tag in {"math", "span"} and self.math_display_stack:
            self.math_display_stack.pop()
            self.suppress_math = max(0, self.suppress_math - 1)
            return
        if self.suppress_math:
            return

        if tag in BLOCK_TAGS:
            self.newline(1 if self.quote_depth else 2)
        elif re.fullmatch(r"h[1-6]", tag):
            self.newline(2)
        elif tag in {"strong", "b"}:
            self.emit("**")
        elif tag in {"em", "i"}:
            self.emit("*")
        elif tag in {"del", "s"}:
            self.emit("~~")
        elif tag == "a":
            href = self.href_stack.pop() if self.href_stack else None
            self.emit("](" + href + ")" if href else "]")
        elif tag == "blockquote":
            self.quote_depth = max(0, self.quote_depth - 1)
            self.newline(2)
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self.newline(2 if not self.list_stack else 1)
        elif tag == "pre":
            self.in_pre = max(0, self.in_pre - 1)
            self.newline()
            self.emit("```\n")
        elif tag == "code" and not self.in_pre:
            self.inline_code = max(0, self.inline_code - 1)
            self.emit("`")
        elif tag in {"th", "td"} and self.table is not None:
            cell = "".join(self.table.get("cell") or [])
            row = self.table.get("row")
            if isinstance(row, list):
                row.append(_escape_cell(cell))
            self.table["cell"] = None
        elif tag == "tr" and self.table is not None:
            row = self.table.get("row")
            if isinstance(row, list) and row:
                rows = self.table["rows"]
                assert isinstance(rows, list)
                rows.append(row)
            self.table["row"] = None
        elif tag == "table" and self.table is not None:
            rows = self.table["rows"]
            assert isinstance(rows, list)
            if rows:
                width = max(len(row) for row in rows)
                rows = [row + [""] * (width - len(row)) for row in rows]
                self.newline(2)
                self.emit("| " + " | ".join(rows[0]) + " |\n")
                self.emit("| " + " | ".join(["---"] * width) + " |\n")
                for row in rows[1:]:
                    self.emit("| " + " | ".join(row) + " |\n")
                self.newline(2)
            self.table = None

    def handle_data(self, data: str) -> None:
        if self.capture_tex:
            self.tex_parts.append(data)
            return
        if self.suppress_math:
            return
        if self.table is not None and isinstance(self.table.get("cell"), list):
            self.table["cell"].append(data)
            return
        if self.in_pre:
            self.emit(data)
            return
        value = re.sub(r"[ \t\r\n]+", " ", data.replace("\xa0", " "))
        if value == " ":
            current = "".join(self.out)
            if not current or current.endswith((" ", "\n")):
                return
        self.emit(value)


def html_to_markdown(source: str, math_delimiters: str = DEFAULT_MATH_DELIMITERS) -> str:
    parser = MarkdownHTMLParser(math_delimiters=math_delimiters)
    parser.feed(source)
    parser.close()
    return clean_markdown("".join(parser.out), math_delimiters=math_delimiters)


def _tabular_runs(lines: list[str]) -> list[str]:
    result: list[str] = []
    i = 0
    while i < len(lines):
        if "\t" not in lines[i]:
            result.append(lines[i])
            i += 1
            continue
        run: list[list[str]] = []
        while i < len(lines) and "\t" in lines[i]:
            run.append([_escape_cell(c) for c in lines[i].split("\t")])
            i += 1
        if len(run) >= 2:
            width = max(len(row) for row in run)
            run = [row + [""] * (width - len(row)) for row in run]
            result.append("| " + " | ".join(run[0]) + " |")
            result.append("| " + " | ".join(["---"] * width) + " |")
            result.extend("| " + " | ".join(row) + " |" for row in run[1:])
        else:
            result.append("  ".join(run[0]))
    return result


def _normalize_latex_delimiters(segment: str, math_delimiters: str) -> str:
    """Normalize ChatGPT TeX delimiters for the selected Markdown editor."""
    if math_delimiters == "backslash":
        return segment
    segment = re.sub(
        r"\\\[(.*?)\\\]",
        lambda match: "\n$$\n" + match.group(1).strip() + "\n$$\n",
        segment,
        flags=re.S,
    )
    return re.sub(
        r"\\\(([^\n]*?)\\\)",
        lambda match: "$" + match.group(1).strip() + "$",
        segment,
    )


def _clean_noncode(segment: str, math_delimiters: str) -> str:
    segment = segment.replace("\r\n", "\n").replace("\r", "\n")
    segment = segment.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
    segment = _normalize_latex_delimiters(segment, math_delimiters)
    lines = segment.split("\n")
    cleaned: list[str] = []
    bullet_re = re.compile(rf"^(\s*)[{re.escape(BULLETS)}]\s+")
    heading_re = re.compile(r"^(\s*)(#{1,6})\s*(.+?)\s*#*\s*$")
    quote_re = re.compile(r"^(\s*)[❯›]\s+")
    for line in lines:
        line = line.rstrip()
        line = bullet_re.sub(lambda m: m.group(1).replace("\t", "  ") + "- ", line)
        line = quote_re.sub(lambda m: m.group(1) + "> ", line)
        line = re.sub(r"^(\s*)[–—]\s+", r"\1- ", line)
        line = re.sub(r"^(\s*)(\d+)[.)]\s+", r"\1\2. ", line)
        match = heading_re.match(line)
        if match:
            line = f"{match.group(1)}{match.group(2)} {match.group(3)}"
        cleaned.append(line)
    cleaned = _tabular_runs(cleaned)
    text = "\n".join(cleaned)
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")


def clean_markdown(source: str, math_delimiters: str = DEFAULT_MATH_DELIMITERS) -> str:
    """Clean prose while preserving fenced code exactly."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"(^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$)", source, flags=re.M | re.S)
    output: list[str] = []
    for index, part in enumerate(parts):
        if index % 2:
            output.append(part.strip("\n"))
        else:
            output.append(_clean_noncode(part, math_delimiters))
    text = "\n\n".join(part for part in output if part).strip()
    return text + ("\n" if text else "")


def read_clipboard_html() -> Optional[str]:
    if not os.path.isfile(OSASCRIPT):
        return None
    command = ["osascript", "-e", "try", "-e", "the clipboard as «class HTML»", "-e", "on error", "-e", 'return ""', "-e", "end try"]
    command[0] = OSASCRIPT
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    value = proc.stdout.strip()
    return value if proc.returncode == 0 and re.search(r"<[a-zA-Z][^>]*>", value) else None


def read_clipboard_plain() -> str:
    if not os.path.isfile(PBPASTE):
        raise RuntimeError("找不到 pbpaste；剪贴板模式需要 macOS")
    proc = subprocess.run([PBPASTE], capture_output=True, text=True, check=True)
    return proc.stdout


def write_clipboard(value: str) -> None:
    if not os.path.isfile(PBCOPY):
        raise RuntimeError("找不到 pbcopy；剪贴板模式需要 macOS")
    subprocess.run([PBCOPY], input=value, text=True, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdin", action="store_true", help="read input from stdin instead of the clipboard")
    parser.add_argument("--stdout", action="store_true", help="print result instead of replacing the clipboard")
    parser.add_argument("--input-format", choices=("auto", "plain", "html"), default="auto")
    parser.add_argument(
        "--math-delimiters",
        choices=("dollar", "backslash"),
        default=DEFAULT_MATH_DELIMITERS,
        help="emit $/$$ (Obsidian) or preserve \\(...\\)/\\[...\\] (Typora)",
    )
    args = parser.parse_args()

    try:
        if args.stdin:
            source = sys.stdin.read()
            is_html = args.input_format == "html" or (args.input_format == "auto" and bool(re.search(r"<[a-zA-Z][^>]*>", source)))
        else:
            clipboard_html = read_clipboard_html() if args.input_format != "plain" else None
            source = clipboard_html if clipboard_html is not None else read_clipboard_plain()
            is_html = clipboard_html is not None
        result = (
            html_to_markdown(source, math_delimiters=args.math_delimiters)
            if is_html
            else clean_markdown(source, math_delimiters=args.math_delimiters)
        )
        if args.stdout:
            sys.stdout.write(result)
        else:
            write_clipboard(result)
            print(f"已将 {len(result)} 个字符的 Markdown 写回剪贴板。", file=sys.stderr)
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"chatgpt-md: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
