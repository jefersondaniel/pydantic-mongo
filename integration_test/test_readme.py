import contextlib
import io
import os
import re

def extract_python_snippets(content):
    # Regular expression pattern for finding Python code blocks
    pattern = r'```python(.*?)```'
    snippets = re.findall(pattern, content, re.DOTALL)

    return snippets

def evaluate_snippet(snippet):
    # Capture the output of the snippet
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        exec(snippet, globals())
    return output_buffer.getvalue()


class TestReadme:
    def test_readme(self):
        readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
        readme_contents = open(readme_path, "r").read().strip()
        snippets = extract_python_snippets(readme_contents)
        for snippet in snippets:
            evaluate_snippet(snippet)
