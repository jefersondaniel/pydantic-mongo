import contextlib
import io
import os
import re
import sys

# This test isn't really nessessary


def extract_python_snippets(content):
    # Regular expression pattern for finding Python code blocks
    pattern = r"```python(.*?)```"
    snippets = re.findall(pattern, content, re.DOTALL)
    return snippets


def evaluate_snippet(snippet):
    # Capture the output of the snippet
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        try:
            exec(snippet, globals())
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            raise Exception(f"{e} {exc_type} {fname} {exc_tb.tb_lineno}")
    return output_buffer.getvalue()


class TestReadme:
    def test_readme(self):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
        readme_contents = open(readme_path, "r").read().strip()
        snippets = extract_python_snippets(readme_contents)
        for snippet in snippets:
            evaluate_snippet(snippet)
