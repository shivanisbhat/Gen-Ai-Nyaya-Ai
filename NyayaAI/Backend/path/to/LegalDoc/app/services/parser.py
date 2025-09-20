import pdfplumber
import re
from typing import List, Dict

def extract_text_from_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text.append(page_text)
    return "\n".join(text)

def chunk_into_clauses(text: str, max_chars: int = 1200) -> List[Dict]:
    """
    Enhanced chunking for legal documents that handles various section patterns
    """
    section_patterns = [
        r'^\*\*[A-Z\s]+\*\*$',  # **SECTION HEADERS**
        r'^[A-Z\s]{3,}:$',      # SECTION HEADERS:
        r'^\d+\.\s+[A-Z]',      # 1. Numbered sections
        r'^Clause\s+\d+',       # Clause 1
        r'^Article\s+\d+',      # Article 1
        r'^Section\s+\d+',      # Section 1
        r'^WHEREAS\b',          # WHEREAS clauses
        r'^NOW\s+THEREFORE',    # NOW THEREFORE
        r'^IN\s+WITNESS\s+WHEREOF', # IN WITNESS WHEREOF
        r'^BY\s+AND\s+BETWEEN', # BY AND BETWEEN
    ]
    
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    chunk_id = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        is_section_start = any(re.match(pattern, para, re.IGNORECASE | re.MULTILINE) 
                              for pattern in section_patterns)
        
        if is_section_start and current_chunk.strip():
            chunks.append({
                "id": f"section_{chunk_id}", 
                "text": current_chunk.strip()
            })
            chunk_id += 1
            current_chunk = para + "\n\n"
        else:
            if len(current_chunk) + len(para) > max_chars and current_chunk.strip():
                chunks.append({
                    "id": f"section_{chunk_id}", 
                    "text": current_chunk.strip()
                })
                chunk_id += 1
                current_chunk = para + "\n\n"
            else:
                current_chunk += para + "\n\n"
    
    if current_chunk.strip():
        chunks.append({
            "id": f"section_{chunk_id}", 
            "text": current_chunk.strip()
        })
    
    if len(chunks) <= 1 and len(text) > max_chars:
        return simple_chunk_fallback(text, max_chars)
    
    return chunks

def simple_chunk_fallback(text: str, max_chars: int) -> List[Dict]:
    """Fallback chunking when no clear sections are found"""
    words = text.split()
    chunks = []
    current_chunk = ""
    chunk_id = 0
    
    for word in words:
        if len(current_chunk) + len(word) + 1 > max_chars:
            if current_chunk.strip():
                chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": current_chunk.strip()
                })
                chunk_id += 1
                current_chunk = word + " "
        else:
            current_chunk += word + " "
    
    if current_chunk.strip():
        chunks.append({
            "id": f"chunk_{chunk_id}",
            "text": current_chunk.strip()
        })
    
    return chunks