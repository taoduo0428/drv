from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("analysis", type=Path)
    args = parser.parse_args()

    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    reader = PdfReader(str(args.pdf))
    extracted_pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(extracted_pages)

    required = [
        "认真仔细帮我审核完成",
        "CODEX_A_SERVER_OK",
        "我是插件卡在登录页",
        "我现在好了，你能不能把这个对话全部内容导出来",
        "这次不是 Cockpit 并发不足",
    ]
    forbidden = [
        "# AGENTS.md instructions",
        "<turn_aborted>",
        "encrypted_content",
        "internal_chat_message_metadata_passthrough",
        "custom_tool_call",
    ]

    result = {
        "pdf": str(args.pdf),
        "file_size_bytes": args.pdf.stat().st_size,
        "page_count": len(reader.pages),
        "expected_page_count": analysis["page_count"],
        "extracted_character_count": len(text),
        "required_phrases": {phrase: phrase in text for phrase in required},
        "forbidden_phrases": {phrase: phrase in text for phrase in forbidden},
        "message_count": analysis["message_count"],
        "user_count": analysis["user_count"],
        "assistant_count": analysis["assistant_count"],
        "embedded_image_count": analysis["embedded_image_count"],
    }

    errors = []
    if result["page_count"] != result["expected_page_count"]:
        errors.append("page count mismatch")
    if result["file_size_bytes"] < 100_000:
        errors.append("PDF file unexpectedly small")
    if result["extracted_character_count"] < 50_000:
        errors.append("extracted text unexpectedly short")
    if not all(result["required_phrases"].values()):
        errors.append("required phrase missing")
    if any(result["forbidden_phrases"].values()):
        errors.append("internal-only phrase leaked into PDF")
    if result["embedded_image_count"] != 10:
        errors.append("expected 10 embedded conversation images")

    result["ok"] = not errors
    result["errors"] = errors
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
