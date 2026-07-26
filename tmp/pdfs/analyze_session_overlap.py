from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def read(path: Path):
    result = []
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "response_item":
                continue
            payload = record.get("payload") or {}
            if payload.get("type") != "message" or payload.get("role") not in {"user", "assistant"}:
                continue
            parts = []
            for item in payload.get("content") or []:
                if isinstance(item, dict) and item.get("type") in {"input_text", "output_text", "text"}:
                    parts.append(item.get("text") or "")
            text = "\n\n".join(parts).strip()
            if text:
                norm = re.sub(r"\s+", " ", text).strip()
                result.append((payload.get("role"), norm, record.get("timestamp"), text))
    return result


old = read(Path(sys.argv[1]))
new = read(Path(sys.argv[2]))
prefix = 0
while prefix < min(len(old), len(new)) and old[prefix][:2] == new[prefix][:2]:
    prefix += 1

old_keys = {(role, text) for role, text, *_ in old}
novel = [item for item in new if item[:2] not in old_keys]
print(json.dumps({
    "old_count": len(old),
    "new_count": len(new),
    "matching_prefix": prefix,
    "old_first": old[0][0:3] if old else None,
    "new_first": new[0][0:3] if new else None,
    "old_last": [(r, t[:120], ts) for r, t, ts, _ in old[-5:]],
    "new_last": [(r, t[:120], ts) for r, t, ts, _ in new[-8:]],
    "novel_count": len(novel),
    "novel": [(r, t[:200], ts) for r, t, ts, _ in novel],
}, ensure_ascii=False, indent=2))
