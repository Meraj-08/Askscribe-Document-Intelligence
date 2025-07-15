import os
import mimetypes
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Get file type from filename"""
    if '.' not in filename:
        return 'unknown'
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension if extension in ALLOWED_EXTENSIONS else 'unknown'

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_file_upload(file):
    """Validate uploaded file"""
    errors = []
    
    if not file or file.filename == '':
        errors.append("No file selected")
        return errors
    
    if not allowed_file(file.filename):
        errors.append(f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Check file size (this is approximate, actual size check happens after save)
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > MAX_FILE_SIZE:
            errors.append(f"File too large. Maximum size: {format_file_size(MAX_FILE_SIZE)}")
    
    return errors

def safe_filename(filename):
    """Generate safe filename"""
    return secure_filename(filename)

def get_mime_type(filename):
    """Get MIME type for file"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'

def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def highlight_keywords(text, keywords):
    """Highlight keywords in text (simple version)"""
    if not keywords:
        return text
    
    highlighted = text
    for keyword in keywords:
        if keyword.lower() in text.lower():
            # Simple replacement (case-insensitive)
            import re
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            highlighted = pattern.sub(f"**{keyword}**", highlighted)
    
    return highlighted

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Remove special characters
    text = text.replace('\x00', '')  # Remove null characters
    text = text.replace('\ufffd', '')  # Remove replacement characters
    
    return text.strip()

def extract_document_metadata(file_path):
    """Extract basic metadata from document"""
    metadata = {}
    
    try:
        stat = os.stat(file_path)
        metadata['size'] = stat.st_size
        metadata['created'] = stat.st_ctime
        metadata['modified'] = stat.st_mtime
        
        # Get MIME type
        metadata['mime_type'] = get_mime_type(file_path)
        
    except Exception as e:
        metadata['error'] = str(e)
    
    return metadata

def chunk_text_simple(text, chunk_size=1000, overlap=200):
    """Simple text chunking function"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            
            break_point = max(last_period, last_newline)
            if break_point > start + chunk_size // 2:
                chunk = text[start:break_point + 1]
                end = break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
        
        if start >= len(text):
            break
    
    return [chunk for chunk in chunks if len(chunk.strip()) > 50]
