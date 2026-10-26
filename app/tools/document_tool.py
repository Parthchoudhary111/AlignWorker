import os
from typing import Dict, Any
from pypdf import PdfReader

class DocumentTool:
    """Tool for reading and parsing document files (PDF, TXT) from the filesystem."""

    @staticmethod
    def read_document(file_path: str) -> Dict[str, Any]:
        """Reads a PDF or text file and extracts full text content."""
        if not os.path.isabs(file_path):
            # Resolve relative to sample_data or project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            potential = os.path.join(base_dir, "sample_data", file_path)
            if os.path.exists(potential):
                file_path = potential
            else:
                file_path = os.path.join(base_dir, file_path)

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            if file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                text_content = []
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_content.append(f"--- Page {idx + 1} ---\n{page_text}")
                full_text = "\n".join(text_content)
                return {
                    "success": True,
                    "file_path": file_path,
                    "pages": len(reader.pages),
                    "content": full_text
                }
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"success": True, "file_path": file_path, "content": content}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse document: {str(e)}"}
