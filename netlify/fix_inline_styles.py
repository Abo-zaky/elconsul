#!/usr/bin/env python3
"""
Remove inline style attributes from index.html and add equivalent CSS classes.
"""
from pathlib import Path
import re

def main():
    html_path = Path('index.html')
    css_path = Path('styles.css')
    
    # Read HTML
    html_text = html_path.read_text(encoding='utf-8')
    print(f"Read {len(html_text)} chars from index.html")
    
    # Find all inline style attributes
    pattern = re.compile(r'<([^>]*?)\s+style="([^"]*)"([^>]*)>', re.DOTALL)
    matches = list(pattern.finditer(html_text))
    print(f"Found {len(matches)} inline style attributes")
    
    # Collect unique style values
    unique_styles = sorted(set(m.group(2).strip() for m in matches))
    print(f"Unique style values: {len(unique_styles)}")
    print("\nTop 10 unique styles:")
    for style in unique_styles[:10]:
        print(f"  {style}")
    
    # Map each unique style to a class name
    style_to_class = {}
    css_rules = []
    for idx, style in enumerate(unique_styles, 1):
        class_name = f'inline-{idx}'
        style_to_class[style] = class_name
        css_rules.append(f'.{class_name} {{ {style} }}')
    
    # Replace style attributes with class attributes
    def replace_style(match):
        before = match.group(1)
        style = match.group(2).strip()
        after = match.group(3)
        class_name = style_to_class[style]
        
        # Check if element already has a class attribute
        class_match = re.search(r'class="([^"]*)"', before)
        if class_match:
            existing_classes = class_match.group(1).strip()
            before = re.sub(r'class="[^"]*"', 
                          f'class="{existing_classes} {class_name}"', 
                          before)
        else:
            before = before + f' class="{class_name}"'
        
        return f'<{before}{after}>'
    
    new_html = pattern.sub(replace_style, html_text)
    remaining = len(re.findall(r'\sstyle="', new_html))
    print(f"\nRemaining style attributes in new HTML: {remaining}")
    
    # Read existing CSS
    css_text = css_path.read_text(encoding='utf-8')
    
    # Append new CSS rules
    new_css = css_text + '\n\n/* Auto-generated classes from inline styles */\n' + '\n'.join(css_rules)
    
    # Write back (overwrite original files)
    html_path.write_text(new_html, encoding='utf-8')
    css_path.write_text(new_css, encoding='utf-8')
    
    print("\nDone! Updated index.html and styles.css")

if __name__ == '__main__':
    main()
