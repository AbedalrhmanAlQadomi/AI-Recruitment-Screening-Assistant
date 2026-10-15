import base64
import os

def load_processed_ids(filepath="data/processed-fake-cv/processed_ids.txt"):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_id(msg_id, filepath="data/processed-fake-cv/processed_ids.txt"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{msg_id}\n")

def search_emails(service, job_keyword=None):
    query = "has:attachment (filename:pdf OR filename:docx)"
    if job_keyword:
        query += f' "{job_keyword}"'
    results = service.users().messages().list(userId='me', q=query).execute()
    return results.get('messages', [])

def parse_email_message(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
    
    sender = headers.get('from', '')
    subject = headers.get('subject', '')
    body = ""
    attachments = []
    
    def process_parts(parts):
        nonlocal body, attachments
        for part in parts:
            filename = part.get('filename', '')
            body_data = part.get('body', {})
            mime = part.get('mimeType', '')
            
            if filename and (filename.lower().endswith('.pdf') or filename.lower().endswith('.docx')):
                attachments.append({
                    'filename': filename,
                    'attachment_id': body_data.get('attachmentId')
                })
            elif mime == 'text/plain' and 'data' in body_data:
                body += base64.urlsafe_b64decode(body_data['data']).decode('utf-8', errors='ignore')
            
            if 'parts' in part:
                process_parts(part['parts'])

    payload = msg.get('payload', {})
    if 'parts' in payload:
        process_parts(payload['parts'])
    elif 'data' in payload.get('body', {}):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

    return {
        'id': msg_id,
        'sender': sender,
        'subject': subject,
        'body': body.strip(),
        'attachments': attachments
    }