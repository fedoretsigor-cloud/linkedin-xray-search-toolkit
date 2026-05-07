from io import BytesIO

from src.text_utils import clean_text


MAX_RESUME_BYTES = 8 * 1024 * 1024


def extract_resume_text(upload):
    filename = clean_text(getattr(upload, "filename", "")) or "resume"
    raw = upload.read()
    if not raw:
        raise RuntimeError("Resume file is empty")
    if len(raw) > MAX_RESUME_BYTES:
        raise RuntimeError("Resume file is too large. Please upload a file under 8 MB")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension == "pdf":
        return {
            "filename": filename,
            "text": extract_pdf_text(raw),
        }
    if extension == "docx":
        return {
            "filename": filename,
            "text": extract_docx_text(raw),
        }
    if extension in {"txt", "md"}:
        return {
            "filename": filename,
            "text": decode_text(raw),
        }

    raise RuntimeError("Unsupported resume file type. Please upload PDF or DOCX")


def extract_pdf_text(raw):
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support is not installed. Run pip install -r requirements.txt") from exc

    try:
        reader = PdfReader(BytesIO(raw))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise RuntimeError(f"Could not read PDF resume: {exc}") from exc

    text = clean_text(text)
    if len(text) < 80:
        raise RuntimeError("Could not extract enough text from this PDF resume")
    return text


def extract_docx_text(raw):
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX support is not installed. Run pip install -r requirements.txt") from exc

    try:
        document = Document(BytesIO(raw))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as exc:
        raise RuntimeError(f"Could not read DOCX resume: {exc}") from exc

    text = clean_text(text)
    if len(text) < 80:
        raise RuntimeError("Could not extract enough text from this DOCX resume")
    return text


def decode_text(raw):
    for encoding in ("utf-8", "utf-16", "cp1251", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="ignore")

    text = clean_text(text)
    if len(text) < 80:
        raise RuntimeError("Paste or upload more resume text before analysis")
    return text
