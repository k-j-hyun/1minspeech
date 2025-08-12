import PyPDF2
from docx import Document
import os

def extract_text_from_file(file_path):
    """파일 확장자에 따른 텍스트 추출"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_pdf_content(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_docx_content(file_path)
    elif ext == '.txt':
        return extract_txt_content(file_path)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")

def extract_pdf_content(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_docx_content(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_txt_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()