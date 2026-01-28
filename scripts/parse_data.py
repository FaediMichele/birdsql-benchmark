import json
import os


def parse_raw_data(input_file: str, output_file: str) -> None:
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found.")
        return

    records = []

    with open(input_file, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Simple heuristic: Identify records by instance_id pattern or count
    # The patterns are like 'solar_panel_1', 'hulushows_1', etc.
    # We can try to group by 12 lines if the structure is strict.
    # Or we can look for the 'instance_id' pattern.

    # Skip headers if any
    start_idx = 0
    for i, line in enumerate(lines):
        if line.endswith("_1") or "_M_" in line or "_pattern_" in line:
            # heuristic to find start of data
            # But header "instance_id" is not data.
            if line == "instance_id":
                continue
            if "rows)" in line:
                continue

            # This looks like a data line.
            start_idx = i
            break

    data_lines = lines[start_idx:]

    # We assume 12 fields per record based on observation
    # 1. id
    # 2. db
    # 3. query
    # 4. normal query
    # 5. preprocess
    # 6. cleanup
    # 7. sol
    # 8. ext
    # 9. test
    # 10. cat
    # 11. high_level
    # 12. conditions

    chunks = [data_lines[i : i + 12] for i in range(0, len(data_lines), 12)]

    for chunk in chunks:
        if len(chunk) < 12:
            break

        try:
            record = {
                "instance_id": chunk[0],
                "selected_database": chunk[1],
                "query": chunk[2],
                "normal_query": chunk[3],
                "preprocess_sql": json.loads(chunk[4]) if chunk[4].startswith("[") else [],
                "clean_up_sqls": json.loads(chunk[5]) if chunk[5].startswith("[") else [],
                "sol_sql": json.loads(chunk[6]) if chunk[6].startswith("[") else [],
                "external_knowledge": json.loads(chunk[7]) if chunk[7].startswith("[") else [],
                "test_cases": json.loads(chunk[8]) if chunk[8].startswith("[") else [],
                "category": chunk[9],
                "high_level": chunk[10].lower() == "true",
                "conditions": json.loads(chunk[11]) if chunk[11].startswith("{") else {},
            }
            records.append(record)
        except Exception as e:
            print(f"Error parsing chunk starting with {chunk[0]}: {e}")

    with open(output_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"Parsed {len(records)} records to {output_file}")


if __name__ == "__main__":
    parse_raw_data("data/raw_paste.txt", "data/livesqlbench_data.jsonl")
