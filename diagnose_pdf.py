#!/usr/bin/env python3
"""Diagnose PDF chapter detection issues."""

import sys
import re

def diagnose_pdf(pdf_path):
    try:
        import pdfplumber
    except ImportError:
        print("Please install pdfplumber: pip install pdfplumber")
        return
    
    print(f"Diagnosing PDF: {pdf_path}")
    print("=" * 70)
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")
        print()
        
        # Chapter patterns
        patterns = [
            r'^\s*([IVX]+)\s+([A-Z].+)$',
            r'^\s*([IVX]+)\s*$',
            r'^\s*(\d+)\.\s+([A-Z].+)$',
            r'^\s*Chapter\s+(\d+)(?:[:\s]+(.+))?$',
            r'^\s*CHAPTER\s+(\d+)(?:[:\s]+(.+))?$',
        ]
        
        found_chapters = []
        
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not text:
                continue
            
            lines = text.split('\n')
            
            # Check each line
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check against patterns
                for pattern in patterns:
                    match = re.match(pattern, line)
                    if match:
                        title = match.group(0).strip()
                        # Normalize spaces
                        title = re.sub(r'\s{2,}', ' ', title)
                        
                        if len(title) >= 2 and not re.match(r'^[IVX]+$', title):
                            found_chapters.append({
                                'page': page_num + 1,
                                'line': i + 1,
                                'title': title,
                                'raw': line[:80]
                            })
                            break
        
        print(f"Found {len(found_chapters)} chapter markers:")
        print("-" * 70)
        
        for ch in found_chapters:
            print(f"Page {ch['page']}, Line {ch['line']}: {ch['title']}")
            print(f"  Raw: \"{ch['raw']}\"")
            print()
        
        # Also show first few lines of each page for debugging
        print("\nFirst 3 lines of each page:")
        print("-" * 70)
        
        for page_num, page in enumerate(pdf.pages[:20]):  # Limit to first 20 pages
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if not text:
                continue
            
            lines = text.split('\n')
            print(f"\nPage {page_num + 1}:")
            for i, line in enumerate(lines[:3]):
                print(f"  Line {i+1}: {line[:100]}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python diagnose_pdf.py <path_to_pdf>")
    else:
        diagnose_pdf(sys.argv[1])