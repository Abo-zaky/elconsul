from pathlib import Path
import re

html_path = Path('index.html')
css_path = Path('styles.css')
text = html_path.read_text(encoding='utf-8')
pattern = re.compile(r'<([^>]*?)\sstyle="([^"]*)"([^>]*)>')
unique = {}

for match in pattern.finditer(text):
    style = match.group(2).strip()
    if style not in unique:
        unique[style] = f'inline-style-{len(unique)+1}'

css_rules = '\n/* Auto-generated inline style classes */\n'
for style, cls in unique.items():
    css_rules += f'.{cls}{{{style}}}\n'


def repl(match):
    before = match.group(1)
    style = match.group(2).strip()
    after = match.group(3)
    cls = unique[style]
    if 'class="' in before:
        before = re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1).strip()} {cls}"', before)
    else:
        before = before + f' class="{cls}"'
    return f'<{before}{after}>'

new_text = pattern.sub(repl, text)
remaining = len(re.findall(r'style="', new_text))
html_path.write_text(new_text, encoding='utf-8')
with css_path.open('a', encoding='utf-8') as f:
    f.write(css_rules)
print(f'Added {len(unique)} classes to styles.css')
print(f'style occurrences remaining: {remaining}')
