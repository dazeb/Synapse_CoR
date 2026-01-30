#!/usr/bin/env python3
"""
github_blob_parser.py
Parses GitHub blob page HTML and extracts file content as clean Markdown.
Used by fetch-github-file.sh
"""

import sys
import json
import re

def main():
    content = sys.stdin.read()
    
    # Find embedded JSON data
    match = re.search(
        r'<script type="application/json" data-target="react-app\.embeddedData">(.*?)</script>',
        content,
        re.DOTALL
    )
    if not match:
        print('Error: Could not find embedded data in GitHub page', file=sys.stderr)
        sys.exit(1)
    
    try:
        data = json.loads(match.group(1))
        payload = data.get('payload', {})
        blob = payload.get('blob', {})
        rich_text = blob.get('richText', '')
        
        if not rich_text:
            # Try rawLines for non-markdown files (scripts, etc.)
            raw_lines = blob.get('rawLines')
            if raw_lines:
                print('\n'.join(raw_lines))
                sys.exit(0)
            print('Error: No content found in blob', file=sys.stderr)
            sys.exit(1)
        
        # Convert HTML to Markdown
        try:
            import html2text
        except ImportError:
            print('Error: html2text not installed. Run: pip install html2text', file=sys.stderr)
            sys.exit(1)
        
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.body_width = 0
        h.unicode_snob = True
        
        markdown = h.handle(rich_text)
        
        # === POST-PROCESSING FOR CLEANER OUTPUT ===
        
        # Fix horizontal rules: '* * *' -> '---'
        markdown = re.sub(r'^\* \* \*$', '---', markdown, flags=re.MULTILINE)
        
        # Fix escaped hyphens: '\-' -> '-'
        markdown = re.sub(r'\\-', '-', markdown)
        
        # Fix spaces before punctuation after bold/italic: '**text** ,' -> '**text**,'
        markdown = re.sub(r'\*\*([^*]+)\*\* ([,.:;!?])', r'**\1**\2', markdown)
        markdown = re.sub(r'\*([^*]+)\* ([,.:;!?])', r'*\1*\2', markdown)
        
        # Fix spaces after bold at start of definitions: '**Triggers** :' -> '**Triggers**:'
        markdown = re.sub(r'\*\*([^*]+)\*\* :', r'**\1**:', markdown)
        
        # Fix extra spaces after bold/italic
        markdown = re.sub(r'\*\*([^*]+)\*\*  +', r'**\1** ', markdown)
        
        # Convert indented code blocks to fenced code blocks
        # html2text outputs code blocks as 4-space indented text
        lines = markdown.split('\n')
        in_code_block = False
        result_lines = []
        code_buffer = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            if not in_code_block:
                # Not in a code block - check if this starts one
                # A code block starts with 4+ space indent on non-empty line
                # Look ahead to see if it's a real code block (multiple lines)
                if indent >= 4 and stripped:
                    is_code_block = False
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        next_stripped = next_line.lstrip()
                        next_indent = len(next_line) - len(next_stripped)
                        if next_indent >= 4 or next_line.strip() == '':
                            is_code_block = True
                    
                    if is_code_block:
                        in_code_block = True
                        result_lines.append('```')
                        code_buffer.append(line[4:])
                    else:
                        # Single indented line - not a code block, keep as-is
                        result_lines.append(line)
                else:
                    result_lines.append(line)
            else:
                # In a code block - continue until we hit unindented content
                if indent >= 4 or line.strip() == '':
                    if line.strip() == '':
                        code_buffer.append('')
                    else:
                        code_buffer.append(line[4:])
                else:
                    # End of code block
                    # Remove trailing empty lines from code buffer
                    while code_buffer and code_buffer[-1] == '':
                        code_buffer.pop()
                    result_lines.extend(code_buffer)
                    result_lines.append('```')
                    code_buffer = []
                    in_code_block = False
                    result_lines.append(line)
            
            i += 1
        
        # Handle file ending in code block
        if in_code_block:
            while code_buffer and code_buffer[-1] == '':
                code_buffer.pop()
            result_lines.extend(code_buffer)
            result_lines.append('```')
        
        markdown = '\n'.join(result_lines)
        
        # Clean up excessive blank lines (3+ -> 2)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove trailing whitespace from lines
        markdown = '\n'.join(line.rstrip() for line in markdown.split('\n'))
        
        # Ensure file ends with single newline
        markdown = markdown.strip() + '\n'
        
        print(markdown, end='')
        
    except json.JSONDecodeError as e:
        print(f'Error: Failed to parse JSON: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()