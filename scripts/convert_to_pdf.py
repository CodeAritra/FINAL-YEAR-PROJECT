import os
import sys
import re
import subprocess
import pymupdf
from markdown_it import MarkdownIt

def format_latex_math_to_html(text: str) -> str:
    def clean_latex_symbols(formula: str) -> str:
        formula = re.sub(r'\\mathbf\{(.*?)\}', r'<strong>\1</strong>', formula)
        formula = re.sub(r'\\text\{(.*?)\}', r'\1', formula)
        formula = formula.replace('\\times', '×').replace('\\%', '%')
        formula = formula.replace('\\ge', '≥').replace('\\le', '≤')
        formula = formula.replace('\\implies', '⟹').replace('\\land', '∧')
        formula = formula.replace('\\in', '∈').replace('\\sim', '~')
        formula = formula.replace('\\uparrow', '↑').replace('\\downarrow', '↓')
        formula = formula.replace('\\mathbb{I}', '𝕀')
        formula = formula.replace('\\sum', '∑')
        # Subscripts
        formula = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', formula)
        formula = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', formula)
        return formula

    # 1. Clean block math: $$...$$
    def replace_block_math(match):
        formula = match.group(1).strip()
        formula = clean_latex_symbols(formula)
        
        frac_match = re.search(r'\\frac\{(.*?)\}\{(.*?)\}', formula)
        if frac_match:
            num = frac_match.group(1)
            den = frac_match.group(2)
            prefix = formula[:frac_match.start()].strip()
            suffix = formula[frac_match.end():].strip()
            return f'''
<div class="math-box">
  <span class="math-text">{prefix}</span>
  <span class="math-fraction">
    <span class="math-num">{num}</span>
    <span class="math-den">{den}</span>
  </span>
  <span class="math-text">{suffix}</span>
</div>'''
        else:
            return f'''
<div class="math-box">
  <span class="math-text">{formula}</span>
</div>'''

    text = re.sub(r'\$\$(.*?)\$\$', replace_block_math, text, flags=re.DOTALL)

    # 2. Clean inline math: $...$
    def replace_inline_math(match):
        formula = match.group(1).strip()
        formula = clean_latex_symbols(formula)
        return f'<span class="inline-math">{formula}</span>'

    text = re.sub(r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)', replace_inline_math, text)
    return text

def convert_md_to_pdf(input_md_path: str, output_pdf_path: str = None):
    input_md_path = os.path.abspath(input_md_path)
    if output_pdf_path is None:
        output_pdf_path = os.path.splitext(input_md_path)[0] + ".pdf"
    else:
        output_pdf_path = os.path.abspath(output_pdf_path)

    with open(input_md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Extract Document Title from first H1
    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else os.path.basename(input_md_path)

    # Pre-process math
    processed_md = format_latex_math_to_html(md_content)

    # Convert to HTML via MarkdownIt
    md_parser = MarkdownIt('commonmark').enable('table')
    body_html = md_parser.render(processed_md)

    # Academic & Professional report styling
    html_document = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{doc_title}</title>
<style>
  @page {{
    size: A4;
    margin: 11mm 13mm 14mm 13mm;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 8.9pt;
    line-height: 1.39;
    color: #1e293b;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
  }}

  /* Document Title Header Banner */
  h1 {{
    font-size: 16pt;
    font-weight: 700;
    color: #0f172a;
    border-bottom: 2.5px solid #2563eb;
    padding-bottom: 4px;
    margin-top: 0;
    margin-bottom: 8px;
    letter-spacing: -0.3px;
  }}

  /* Section Headings */
  h2 {{
    font-size: 12pt;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 14px;
    margin-bottom: 5px;
    page-break-after: avoid;
  }}

  h3 {{
    font-size: 10.2pt;
    font-weight: 600;
    color: #0f172a;
    margin-top: 10px;
    margin-bottom: 4px;
    page-break-after: avoid;
  }}

  h4 {{
    font-size: 9.1pt;
    font-weight: 600;
    color: #334155;
    margin-top: 7px;
    margin-bottom: 3px;
    page-break-after: avoid;
  }}

  p, ul, ol {{
    margin-top: 2px;
    margin-bottom: 4px;
  }}

  li {{
    margin-bottom: 2px;
  }}

  /* Blockquotes / Callout boxes */
  blockquote {{
    margin: 5px 0;
    padding: 5px 11px;
    background-color: #f0fdf4;
    border-left: 4px solid #16a34a;
    border-radius: 0 4px 4px 0;
    color: #166534;
    font-size: 8.7pt;
  }}

  blockquote p {{
    margin: 2px 0;
  }}

  /* Code & Architectural Diagrams */
  pre {{
    background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 5px 7px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 6.1pt;
    line-height: 1.13;
    overflow-x: auto;
    white-space: pre;
    color: #0f172a;
    page-break-inside: avoid;
    margin: 5px 0;
  }}

  code {{
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 7.7pt;
    background-color: #f1f5f9;
    color: #2563eb;
    padding: 1px 3px;
    border-radius: 3px;
  }}

  pre code {{
    background-color: transparent;
    padding: 0;
    color: inherit;
    font-size: inherit;
  }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0;
    font-size: 7.9pt;
    page-break-inside: avoid;
  }}

  th, td {{
    border: 1px solid #cbd5e1;
    padding: 4px 6px;
    text-align: left;
    vertical-align: top;
  }}

  th {{
    background-color: #f1f5f9;
    font-weight: 600;
    color: #0f172a;
  }}

  tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  hr {{
    border: 0;
    border-top: 1px solid #e2e8f0;
    margin: 10px 0;
  }}

  /* Math Box Styling */
  .math-box {{
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f8fafc;
    border: 1px solid #94a3b8;
    border-radius: 4px;
    padding: 4px 10px;
    margin: 5px auto;
    width: fit-content;
    font-family: "Cambria Math", "Georgia", serif;
    font-size: 8.6pt;
    color: #0f172a;
    page-break-inside: avoid;
  }}

  .math-fraction {{
    display: inline-flex;
    flex-direction: column;
    vertical-align: middle;
    text-align: center;
    margin: 0 4px;
  }}

  .math-num {{
    border-bottom: 1.1px solid #0f172a;
    padding-bottom: 1px;
    font-style: italic;
  }}

  .math-den {{
    padding-top: 1px;
    font-style: italic;
  }}

  .math-text {{
    padding: 0 3px;
    font-weight: 500;
  }}

  .inline-math {{
    font-family: "Cambria Math", "Georgia", serif;
    font-weight: 600;
    color: #1e293b;
    background-color: #f1f5f9;
    padding: 1px 3px;
    border-radius: 3px;
  }}

  strong {{
    color: #0f172a;
    font-weight: 600;
  }}

  sub {{
    font-size: 70%;
    vertical-align: sub;
  }}
</style>
</head>
<body>
{body_html}
</body>
</html>
'''

    temp_html_path = os.path.splitext(output_pdf_path)[0] + "_temp.html"
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_document)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    raw_pdf_path = os.path.splitext(output_pdf_path)[0] + "_raw.pdf"

    cmd = [
        chrome_path,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={raw_pdf_path}",
        temp_html_path
    ]

    print(f"1. Compiling HTML to PDF via {os.path.basename(chrome_path)}...")
    subprocess.run(cmd, check=True)

    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)

    # 2. Add professional running header and footer with PyMuPDF
    print("2. Stamping running headers and footers with PyMuPDF...")
    doc = pymupdf.open(raw_pdf_path)
    total_pages = len(doc)

    short_title = doc_title.split(":")[0].strip() if ":" in doc_title else doc_title

    for i, page in enumerate(doc):
        # Header (pages 2+)
        if i > 0:
            header_rect = pymupdf.Rect(35, 12, page.rect.width - 35, 26)
            header_text = f"{short_title} — Research Methodology & Evaluation Paradigm"
            page.insert_textbox(
                header_rect,
                header_text,
                fontsize=7.2,
                color=(0.45, 0.5, 0.55),
                fontname="helv",
                align=pymupdf.TEXT_ALIGN_RIGHT
            )
            # Header line
            page.draw_line(pymupdf.Point(35, 27), pymupdf.Point(page.rect.width - 35, 27), color=(0.85, 0.88, 0.92), width=0.5)

        # Footer (all pages)
        footer_rect = pymupdf.Rect(35, page.rect.height - 24, page.rect.width - 35, page.rect.height - 10)
        footer_text = f"Page {i + 1} of {total_pages}"
        page.insert_textbox(
            footer_rect,
            footer_text,
            fontsize=7.8,
            color=(0.4, 0.45, 0.5),
            fontname="helv",
            align=pymupdf.TEXT_ALIGN_CENTER
        )
        # Footer line
        page.draw_line(pymupdf.Point(35, page.rect.height - 26), pymupdf.Point(page.rect.width - 35, page.rect.height - 26), color=(0.85, 0.88, 0.92), width=0.5)

    doc.save(output_pdf_path)
    doc.close()

    if os.path.exists(raw_pdf_path):
        os.remove(raw_pdf_path)

    print(f"Success! Final PDF generated: {output_pdf_path}")
    print(f"Total Pages: {total_pages} | File Size: {os.path.getsize(output_pdf_path):,} bytes")

if __name__ == '__main__':
    target_md = sys.argv[1] if len(sys.argv) > 1 else 'learning.md'
    target_pdf = sys.argv[2] if len(sys.argv) > 2 else None
    convert_md_to_pdf(target_md, target_pdf)
