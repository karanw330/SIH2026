import os, io, re
from pypdf import PdfReader
from docx import Document

class DocumentSearchTool:
    name = "document_search"

    def extract_text(self, file_source, file_type: str) -> str:
        text = ""
        try:
            if file_type == "txt":
                text = file_source.decode("utf-8", errors="ignore") if isinstance(file_source, bytes) else open(file_source, encoding="utf-8").read()
            elif file_type == "pdf":
                reader = PdfReader(io.BytesIO(file_source) if isinstance(file_source, bytes) else file_source)
                for page in reader.pages:
                    if page.extract_text(): text += page.extract_text() + "\n"
            elif file_type == "docx":
                doc = Document(io.BytesIO(file_source) if isinstance(file_source, bytes) else file_source)
                for p in doc.paragraphs: text += p.text + "\n"
        except Exception as e:
            text = f"Error reading document: {str(e)}"
        return text

    def execute(self, query: str, document_text: str) -> str:
        if not document_text.strip(): return "No document text loaded."
        paragraphs = [p.strip() for p in document_text.split("\n") if len(p.strip()) > 20]
        keywords = set(re.findall(r'\w+', query.lower())) - {"what", "is", "the", "in", "to", "and"}
        
        scored = [(sum(1 for kw in keywords if kw in p.lower()), p) for p in paragraphs]
        scored = [item for item in scored if item[0] > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return "\n---\n".join([item[1] for item in scored[:2]]) if scored else document_text[:1000]