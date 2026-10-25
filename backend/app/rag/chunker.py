"""
Industrial Semantic Document Chunker
Splits technical manuals, SOPs, and reports while maintaining section headers and context.
"""
import re
from typing import List, Dict, Any

class IndustrialChunker:
    def __init__(self, max_chunk_words: int = 250, overlap_words: int = 40):
        self.max_chunk_words = max_chunk_words
        self.overlap_words = overlap_words

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits markdown, text, or multi-page documents into semantically coherent chunks,
        retaining hierarchical section headers and page numbers.
        """
        raw_chunks = []
        doc_title = metadata.get("title", "General Document Overview")

        # 1. Page-based chunking if structured pages exist (e.g. from PDFs)
        if metadata.get("pages") and isinstance(metadata["pages"], list):
            for p in metadata["pages"]:
                p_num = p.get("page", 1)
                p_text = p.get("text", "").strip()
                if not p_text:
                    continue
                words = p_text.split()
                if len(words) <= self.max_chunk_words:
                    raw_chunks.append({
                        "text": f"[{doc_title} - Page {p_num}]\n{p_text}",
                        "section": f"Page {p_num}",
                        "page": p_num,
                        "word_count": len(words)
                    })
                else:
                    step = max(1, self.max_chunk_words - self.overlap_words)
                    for start in range(0, len(words), step):
                        window = words[start:start + self.max_chunk_words]
                        part_num = (start // step) + 1
                        raw_chunks.append({
                            "text": f"[{doc_title} - Page {p_num} (Part {part_num})]\n{' '.join(window)}",
                            "section": f"Page {p_num} (Part {part_num})",
                            "page": p_num,
                            "word_count": len(window)
                        })
        else:
            # 2. Section-based chunking using markdown headers
            sections = re.split(r'(?m)^(#{1,4}\s+.+)$', text)
            current_section = doc_title
            current_page = None

            i = 0
            while i < len(sections):
                part = sections[i].strip()
                if not part:
                    i += 1
                    continue

                # Check if this part is a header
                if re.match(r'^#{1,4}\s+', part):
                    current_section = part.lstrip('#').strip()
                    i += 1
                    content = sections[i].strip() if i < len(sections) else ""
                    i += 1
                else:
                    content = part
                    i += 1

                # Check for inline page tags like --- PAGE 4 ---
                page_match = re.search(r'---\s*PAGE\s+(\d+)\s*---', content)
                if page_match:
                    current_page = int(page_match.group(1))

                words = content.split()
                if not words:
                    continue

                if len(words) <= self.max_chunk_words:
                    chunk_text = f"[{current_section}]\n{content}"
                    raw_chunks.append({
                        "text": chunk_text.strip(),
                        "section": current_section,
                        "page": current_page,
                        "word_count": len(words)
                    })
                else:
                    step = max(1, self.max_chunk_words - self.overlap_words)
                    for start in range(0, len(words), step):
                        window = words[start:start + self.max_chunk_words]
                        part_num = (start // step) + 1
                        chunk_text = f"[{current_section} (Part {part_num})]\n{' '.join(window)}"
                        raw_chunks.append({
                            "text": chunk_text.strip(),
                            "section": current_section,
                            "page": current_page,
                            "word_count": len(window)
                        })

        # Enrich each chunk with standard metadata
        total_chunks = len(raw_chunks)
        enriched_chunks = []
        for idx, chunk in enumerate(raw_chunks):
            doc_id = metadata.get("doc_id", "DOC")
            chunk_id = f"{doc_id}_chk_{idx + 1}"
            enriched = {
                "id": chunk_id,
                "text": chunk["text"],
                "metadata": {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "file_name": metadata.get("file_name", "unknown"),
                    "title": metadata.get("title", doc_id),
                    "section": chunk["section"],
                    "page": chunk.get("page"),
                    "equipment_type": metadata.get("equipment_type", "General Industrial"),
                    "safety_level": metadata.get("safety_level", "Standard"),
                    "chunk_index": idx + 1,
                    "total_chunks": total_chunks,
                    "source_type": metadata.get("source_type", "Manual")
                }
            }
            enriched_chunks.append(enriched)

        return enriched_chunks
