#!/usr/bin/env python3
"""Debug PDF chapter detection."""
import sys
import re

def debug_pdf(pdf_path):
    try:
        import pdfplumber
    except ImportError:
        print("pip install pdfplumber")
        return
    
    print(f"Debugging: {pdf_path}")
    print("=" * 70)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages[:20]):  # 只看前20页
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not text:
                continue
            
            lines = text.split('\n')
            
            # 检查前5行是否有章节标题
            has_chapter = False
            for i, line in enumerate(lines[:5]):
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否匹配章节模式
                if re.match(r'^\s*[IVX]+\s+', line) or re.match(r'^\s*[IVX]+\s*$', line):
                    has_chapter = True
                    print(f"\nPage {page_num + 1}:")
                    print(f"  Line {i+1}: \"{line}\"")
                    print(f"  Length: {len(line)}")
                    print(f"  Hex: {line.encode().hex()}")
            
            # 如果检测到章节，显示前5行
            if has_chapter:
                print(f"  All lines:")
                for i, line in enumerate(lines[:5]):
                    print(f"    {i+1}: \"{line.strip()[:60]}\"")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf.py <pdf>")
    else:
        debug_pdf(sys.argv[1])