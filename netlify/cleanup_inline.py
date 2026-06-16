from pathlib import Path
import re

html_path = Path('index.html')
css_path = Path('styles.css')
text = html_path.read_text(encoding='utf-8')

# find all style attributes, preserving the full value
pattern = re.compile(r'<([^>]*?)\sstyle="([^"]*)"([^>]*)>', re.DOTALL)
styles = []
for match in pattern.finditer(text):
    styles.append(match.group(2).strip())
uniq_styles = sorted(set(styles))
print('total style attrs:', len(styles))
print('unique style values:', len(uniq_styles))
for i, s in enumerate(uniq_styles[:100], 1):
    print(i, s)

# create CSS class names from unique style values
css_lines = ['\n/* Auto-generated inline style classes */']
style_to_class = {}
for idx, style in enumerate(uniq_styles, 1):
    cls = f'inline-style-{idx}'
    style_to_class[style] = cls
    css_lines.append(f'.{cls} {{ {style} }}')

# Replace inline style with class attribute.

def repl(match):
    before, style, after = match.group(1), match.group(2).strip(), match.group(3)
    cls = style_to_class[style]
    if 'class="' in before:
        before = re.sub(r'class="([^"]*)"', lambda m: f'class="{m.group(1).strip()} {cls}"', before)
    else:
        before = before + f' class="{cls}"'
    return f'<{before}{after}>'

new_text = pattern.sub(repl, text)
remaining = len(re.findall(r'style="', new_text))
print('style occurrences remaining in new text:', remaining)

# Write new files for review, not overwriting original yet
Path('index.cleaned.html').write_text(new_text, encoding='utf-8')
Path('styles.inline.css').write_text('\n'.join(css_lines) + '\n', encoding='utf-8')
print('Generated index.cleaned.html and styles.inline.css')
