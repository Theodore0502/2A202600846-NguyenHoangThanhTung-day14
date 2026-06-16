from __future__ import annotations

def parse_policy_markdown(markdown_text: str) -> list[dict]:
    chunks = []
    current_h2 = ""
    current_h3 = ""
    current_content = []
    
    lines = markdown_text.splitlines()
    
    def save_chunk():
        if not current_h2 and not current_h3 and not current_content:
            return
        
        content_str = "\n".join(current_content).strip()
        if not content_str and not current_h3:
            return
        
        citation = current_h3 if current_h3 else current_h2
        if not citation:
            citation = "General"
            
        rendered_text = f"{current_h2}\n{current_h3}\n{content_str}".strip()
        
        chunks.append({
            "section_h2": current_h2.replace("## ", "").strip(),
            "section_h3": current_h3.replace("### ", "").strip() if current_h3 else "",
            "citation": citation.replace("### ", "").replace("## ", "").strip(),
            "rendered_text": rendered_text
        })

    for line in lines:
        if line.startswith("## "):
            save_chunk()
            current_h2 = line
            current_h3 = ""
            current_content = []
        elif line.startswith("### "):
            save_chunk()
            current_h3 = line
            current_content = []
        else:
            current_content.append(line)
            
    save_chunk()
    return chunks
