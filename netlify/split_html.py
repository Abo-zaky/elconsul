from pathlib import Path
p = Path('Untitled-1.html')
text = p.read_text(encoding='utf-8')
start = text.find('<style>')
end = text.find('</style>', start)
if start == -1 or end == -1:
    raise SystemExit('style block not found')
end += len('</style>')
body = text[end:]
split = body.find('<script>')
if split == -1:
    raise SystemExit('main script tag not found')
html_head = text[:start]
style_content = text[start + len('<style>'):end - len('</style>')]
body_content = body[:split]
script_content = body[split + len('<script>'):]
if script_content.endswith('</script>'):
    script_content = script_content[:-len('</script>')]
new_index = html_head + '<link rel="stylesheet" href="styles.css">\n' + body_content + '<script defer src="app.js"></script>\n</body></html>'
Path('index.html').write_text(new_index, encoding='utf-8')
Path('styles.css').write_text(style_content, encoding='utf-8')
Path('app.js').write_text(script_content, encoding='utf-8')
print('ok')
