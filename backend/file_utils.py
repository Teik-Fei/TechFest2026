import PyPDF2
import io
from typing import Optional

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file content"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from TXT file content"""
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Try with different encodings
        try:
            return file_content.decode('latin-1')
        except Exception as e:
            raise Exception(f"Error decoding text file: {str(e)}")

def extract_text_from_file(filename: str, file_content: bytes) -> str:
    """
    Extract text from uploaded file based on file extension
    Supports: .pdf, .txt
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename_lower.endswith('.txt'):
        return extract_text_from_txt(file_content)
    else:
        raise Exception(f"Unsupported file type. Only .pdf and .txt files are supported.")

def extract_email_from_text(text: str) -> Optional[str]:
    """Extract email address from text"""
    import re
    email_pattern = r'[\w.-]+@[\w.-]+\.\w+'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def extract_name_from_filename(filename: str) -> str:
    """Extract name from filename by removing extension"""
    import os
    name = os.path.splitext(filename)[0]
    # Clean up common patterns
    name = name.replace('_', ' ').replace('-', ' ')
    return name.strip()
