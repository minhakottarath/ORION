"""
Heterogeneous Document Loader
Parses SOPs, manuals, incident reports, and telemetry logs into unified text representations.
"""
import json
import csv
from pathlib import Path
from typing import Dict, Any, Tuple

class DocumentLoader:
    @staticmethod
    def load_file(file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """
        Loads a document file and extracts text and metadata.
        Returns: (raw_text, metadata_dict)
        """
        suffix = file_path.suffix.lower()
        file_name = file_path.name
        doc_id = file_path.stem.upper()
        
        metadata = {
            "doc_id": doc_id,
            "file_name": file_name,
            "source_type": "Unknown",
            "title": file_path.stem.replace("_", " ").title(),
            "equipment_type": "General Industrial",
            "safety_level": "Standard"
        }

        # Infer industrial metadata from filename conventions
        if "sop" in file_name.lower():
            metadata["source_type"] = "Standard Operating Procedure (SOP)"
            metadata["safety_level"] = "Level 2 Industrial Hazard"
            metadata["equipment_type"] = "Hydraulic & Power Unit"
            metadata["equipment_id"] = "HPU-SERIES-900"
        elif "manual" in file_name.lower() or "t800" in file_name.lower():
            metadata["source_type"] = "Technical Manual"
            metadata["safety_level"] = "Critical Machinery"
            metadata["equipment_type"] = "Gas Turbine Generator"
            metadata["equipment_id"] = "TITAN-800"
        elif "incident" in file_name.lower():
            metadata["source_type"] = "Incident Report"
            metadata["safety_level"] = "Post-Incident CAPA"
            metadata["equipment_type"] = "Centrifugal Pump"
            metadata["equipment_id"] = "BFP-02B"
        elif "log" in file_name.lower() or "telemetry" in file_name.lower():
            metadata["source_type"] = "Telemetry Log"
            metadata["safety_level"] = "Electrical Safety"
            metadata["equipment_type"] = "Variable Frequency Drive"
            metadata["equipment_id"] = "VFD-MCC4"

        if suffix in [".md", ".txt"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return content, metadata

        elif suffix == ".json":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            
            # Format JSON logs into clear diagnostic prose
            text_lines = [f"# Log Record: {data.get('log_batch_id', doc_id)}"]
            if "equipment_type" in data:
                text_lines.append(f"**Equipment:** {data.get('equipment_type')} ({data.get('equipment_id', 'N/A')})")
                metadata["equipment_type"] = data.get("equipment_type")
            if "facility" in data:
                text_lines.append(f"**Facility Location:** {data.get('facility')}")
            
            if "telemetry_events" in data:
                text_lines.append("\n## Telemetry Events & Fault Codes")
                for evt in data["telemetry_events"]:
                    text_lines.append(f"### Fault Code: {evt.get('code')} - {evt.get('description')}")
                    text_lines.append(f"- Severity: {evt.get('severity')}")
                    text_lines.append(f"- Telemetry Readings: {json.dumps(evt.get('telemetry', {}), indent=2)}")
                    text_lines.append(f"- Diagnostic Note: {evt.get('diagnostic_note', 'None')}")

            if "recommended_troubleshooting_sequence" in data:
                text_lines.append("\n## Recommended Troubleshooting Sequence")
                for step in data["recommended_troubleshooting_sequence"]:
                    text_lines.append(f"- {step}")

            return "\n".join(text_lines), metadata

        elif suffix == ".csv":
            text_lines = [f"# Data Sheet: {doc_id}"]
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    text_lines.append(f"Columns: {', '.join(headers)}")
                for row in reader:
                    text_lines.append(f"Record: {', '.join(row)}")
            return "\n".join(text_lines), metadata

        elif suffix == ".pdf":
            # Text extraction from PDF with page preservation
            try:
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                metadata["source_type"] = "PDF Technical Document"
                pages_data = []
                text_parts = []
                for idx, page in enumerate(reader.pages):
                    page_num = idx + 1
                    page_text = page.extract_text() or ""
                    clean_page_text = page_text.strip()
                    if clean_page_text:
                        pages_data.append({"page": page_num, "text": clean_page_text})
                        text_parts.append(f"\n--- PAGE {page_num} ---\n{clean_page_text}")
                
                metadata["total_pages"] = len(reader.pages)
                metadata["pages"] = pages_data
                combined_text = "\n".join(text_parts) if text_parts else "No readable text extracted from PDF."
                return combined_text, metadata
            except Exception as e:
                print(f"[DocumentLoader] Error reading PDF {file_name}: {e}")
                return f"[Document Error: Could not extract text from {file_name}]", metadata

        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(), metadata
