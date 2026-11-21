import json
from pathlib import Path

json_path = Path(r"e:\DATN\LoRa_TinyML_Hopping\docs\2412.01609v1.json")
out_dir = Path(r"e:\DATN\LoRa_TinyML_Hopping\docs\tables")
out_dir.mkdir(parents=True, exist_ok=True)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

tables = data.get("tables", [])
print(f"Total tables detected: {len(tables)}")

for idx, tbl in enumerate(tables):
    grid = tbl.get("data", {}).get("grid", [])
    if not grid:
        continue
    
    # Extract markdown representation of table
    md_lines = []
    headers = [cell.get("text", "").replace("\n", " ").strip() for cell in grid[0]]
    md_lines.append("| " + " | ".join(headers) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for row in grid[1:]:
        row_cells = [cell.get("text", "").replace("\n", " ").strip() for cell in row]
        # Pad or trim if length mismatch
        if len(row_cells) < len(headers):
            row_cells += [""] * (len(headers) - len(row_cells))
        elif len(row_cells) > len(headers):
            row_cells = row_cells[:len(headers)]
        md_lines.append("| " + " | ".join(row_cells) + " |")
    
    table_content = "\n".join(md_lines)
    
    caption_text = f"Table {idx+1}"
    captions = tbl.get("captions", [])
    if captions:
        caption_text = " - ".join([str(c) for c in captions])
        
    out_file = out_dir / f"table_{idx+1}.md"
    with open(out_file, "w", encoding="utf-8") as out_f:
        out_f.write(f"### {caption_text}\n\n")
        out_f.write(table_content + "\n")
    
    print(f"Exported: {out_file.name} ({len(grid)} rows, {len(headers)} cols)")
