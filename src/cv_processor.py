import base64
import os
import re
from pypdf import PdfReader
from docx import Document

def download_attachment(service, msg_id, attachment_id, filename, save_dir="data/cv"):
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{msg_id}_{filename}")
    attachment = service.users().messages().attachments().get(
        userId='me', messageId=msg_id, id=attachment_id
    ).execute()
    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
    with open(file_path, 'wb') as f:
        f.write(file_data)
    return file_path

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = " ".join([page.extract_text() or "" for page in reader.pages])
        return clean_text(text)
    except Exception:
        return ""

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = " ".join([p.text for p in doc.paragraphs if p.text])
        return clean_text(text)
    except Exception:
        return ""

def extract_cv_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    return ""