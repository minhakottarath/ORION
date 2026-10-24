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
        Splits markdown or plain text documents into semantically coherent chunks,
        retaining hierarchical section headers.
        """
        chunks = []
        # Split text into major sections using markdown headers (# or ## or ###)
        sections = re.split(r'(?m)^(#{1,4}\s+.+)$', text)
        
        current_section = metadata.get("title", "General Document Overview")
        accumulated_text = ""
        
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

            # Sub-split content if it exceeds max_chunk_words
            words = content.split()
            if not words:
                continue

            if len(words) <= self.max_chunk_words:
                chunk_text = f"[{current_section}]\n{content}"
                chunks.append({
                    "text": chunk_text.strip(),
                    "section": current_section,
                    "word_count": len(words)
                })
            else:
                # Sliding window chunking
                step = max(1, self.max_chunk_words - self.overlap_words)
                for start in range(0, len(words), step):
                    window = words[start:start + self.max_chunk_words]
                    chunk_body = " ".join(window)
                    chunk_text = f"[{current_section} (Part {start // step + 1})]\n{chunk_body}"
                    chunks.append({
                        "text": chunk_text.strip(),
                        "section": current_section,
                        "word_count": len(window)
                    })

        # Enrich each chunk with standard metadata
        total_chunks = len(chunks)
        enriched_chunks = []
        for idx, chunk in enumerate(chunks):
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
                    "equipment_type": metadata.get("equipment_type", "General Industrial"),
                    "safety_level": metadata.get("safety_level", "Standard"),
                    "chunk_index": idx + 1,
                    "total_chunks": total_chunks,
                    "source_type": metadata.get("source_type", "Manual")
                }
            }
            enriched_chunks.append(enriched)

        return enriched_chunks
