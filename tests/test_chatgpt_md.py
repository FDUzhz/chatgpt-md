import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "chatgpt_md.py"
SPEC = importlib.util.spec_from_file_location("chatgpt_md", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


class ConversionTests(unittest.TestCase):
    def test_plain_markdown_cleanup_preserves_code(self):
        source = "##标题\n\n\n• 第一项\n  ◦ 子项\n\n```python\n• x\n\n\nprint(x)\n```"
        expected = "## 标题\n\n- 第一项\n  - 子项\n\n```python\n• x\n\n\nprint(x)\n```\n"
        self.assertEqual(mod.clean_markdown(source), expected)

    def test_tab_separated_table(self):
        source = "名称\t值\nAlpha\t1\nBeta\t2"
        self.assertEqual(mod.clean_markdown(source), "| 名称 | 值 |\n| --- | --- |\n| Alpha | 1 |\n| Beta | 2 |\n")

    def test_html_features(self):
        source = """
        <h2>结论</h2><p><strong>重要</strong>，见 <a href="https://example.com">来源</a>。</p>
        <blockquote><p>引用内容</p></blockquote>
        <ul><li>一<ul><li>二</li></ul></li></ul>
        <pre><code class="language-python">print(&quot;ok&quot;)\n</code></pre>
        <table><tr><th>名称</th><th>值</th></tr><tr><td>A</td><td>1</td></tr></table>
        """
        result = mod.html_to_markdown(source)
        self.assertIn("## 结论", result)
        self.assertIn("**重要**", result)
        self.assertIn("[来源](https://example.com)", result)
        self.assertIn("> 引用内容", result)
        self.assertIn("- 一\n  - 二", result)
        self.assertIn('```\nprint("ok")', result)
        self.assertIn("| 名称 | 值 |", result)

    def test_katex_annotation(self):
        source = '<span class="katex"><math><semantics><annotation encoding="application/x-tex">E=mc^2</annotation></semantics></math></span>'
        self.assertIn("$E=mc^2$", mod.html_to_markdown(source))

    def test_dangerous_link_scheme_is_removed(self):
        result = mod.html_to_markdown('<a href="javascript:alert(1)">不要点击</a>')
        self.assertEqual(result, "[不要点击]\n")

    def test_safe_link_is_kept_and_escaped(self):
        result = mod.html_to_markdown('<a href="https://example.com/a path_(x)">来源</a>')
        self.assertEqual(result, "[来源](https://example.com/a%20path_%28x%29)\n")

    def test_inline_latex_in_heading_body_and_list(self):
        source = (
            "# 2. \\(h_{\\theta_e}(x)\\): 第 \\(e\\) 个专家\n\n"
            "正文中的 \\(x_i^2\\) 应显示为公式。\n\n"
            "• \\(h_{\\theta_e}(x)\\)：专家输出"
        )
        expected = (
            "# 2. $h_{\\theta_e}(x)$: 第 $e$ 个专家\n\n"
            "正文中的 $x_i^2$ 应显示为公式。\n\n"
            "- $h_{\\theta_e}(x)$：专家输出\n"
        )
        self.assertEqual(mod.clean_markdown(source), expected)

    def test_display_latex_delimiters(self):
        source = "推导如下：\n\\[\nE = mc^2\n\\]\n结束。"
        self.assertEqual(mod.clean_markdown(source), "推导如下：\n\n$$\nE = mc^2\n$$\n\n结束。\n")

    def test_latex_delimiters_inside_code_are_unchanged(self):
        source = "```text\n\\(not_math\\)\n```"
        self.assertEqual(mod.clean_markdown(source), source + "\n")


if __name__ == "__main__":
    unittest.main()
