from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from PIL import Image as PILImage
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


VISIBLE_ROLES = {"user", "assistant"}
TEXT_ITEM_TYPES = {"input_text", "output_text", "text"}
NON_CONVERSATION_PREFIXES = (
    "# AGENTS.md instructions",
    "<turn_aborted>",
)
IMAGE_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z]:[\\/][^\r\n<>\"|?*]*?\.(?:png|jpe?g|webp|bmp))",
    flags=re.IGNORECASE,
)
CODE_FENCE_RE = re.compile(r"```(?:[^\n]*)\n?(.*?)```", flags=re.DOTALL)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass(frozen=True)
class Message:
    role: str
    text: str
    timestamp: datetime
    source_thread: str
    source_file: Path
    sequence: int
    image_paths: tuple[Path, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export visible Codex conversation messages to PDF.")
    parser.add_argument("--session", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="Codex 对话完整导出")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--analysis-json", type=Path)
    parser.add_argument("--asset-dir", type=Path)
    return parser.parse_args()


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return CONTROL_RE.sub("", value).strip()


def parse_timestamp(raw: object, tz: ZoneInfo) -> datetime:
    if isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(tz)
        except ValueError:
            pass
    return datetime.now(tz)


def content_to_text(content: object) -> str:
    if isinstance(content, str):
        return clean_text(content)
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = str(item.get("type", ""))
        if item_type in TEXT_ITEM_TYPES:
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text)
        elif item_type in {"input_image", "image", "local_image"}:
            path = item.get("path") or item.get("image_url") or item.get("url")
            if isinstance(path, str) and path and not path.startswith("data:"):
                parts.append(f"[图片附件] {path}")
            else:
                parts.append("[图片附件]")
    return clean_text("\n\n".join(parts))


def response_text_only(content: object) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") not in TEXT_ITEM_TYPES:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return clean_text("\n\n".join(parts))


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def decode_data_image(data_url: str, asset_dir: Path) -> Path | None:
    match = re.match(r"data:image/(?P<kind>png|jpeg|jpg|webp|bmp);base64,(?P<data>.+)", data_url, re.DOTALL)
    if not match:
        return None
    try:
        raw = base64.b64decode(match.group("data"), validate=False)
    except Exception:
        return None
    if not raw:
        return None
    suffix = ".jpg" if match.group("kind") in {"jpeg", "jpg"} else f".{match.group('kind')}"
    digest = hashlib.sha256(raw).hexdigest()[:20]
    asset_dir.mkdir(parents=True, exist_ok=True)
    output = asset_dir / f"conversation-image-{digest}{suffix}"
    if not output.exists():
        output.write_bytes(raw)
    return output


def source_thread_id(path: Path) -> str:
    match = re.search(r"(019f[0-9a-f-]{31,})", path.name, flags=re.IGNORECASE)
    return match.group(1) if match else path.stem


def read_messages(path: Path, tz: ZoneInfo, asset_dir: Path | None = None) -> list[Message]:
    messages: list[Message] = []
    fallback_images: dict[str, list[list[str]]] = defaultdict(list)
    fallback_image_bundles: list[list[str]] = []
    thread_id = source_thread_id(path)
    sequence = 0
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for raw_line in handle:
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue

            if record.get("type") == "response_item" and payload.get("type") == "message" and payload.get("role") == "user":
                text = response_text_only(payload.get("content"))
                urls: list[str] = []
                content = payload.get("content")
                if isinstance(content, list):
                    for item in content:
                        if not isinstance(item, dict) or item.get("type") != "input_image":
                            continue
                        url = item.get("image_url")
                        if isinstance(url, str) and url.startswith("data:image/"):
                            urls.append(url)
                if text and urls:
                    fallback_images[normalized_text(text)].append(urls)
                    fallback_image_bundles.append(urls)
                continue

            if record.get("type") != "event_msg":
                continue

            payload_type = payload.get("type")
            if payload_type == "user_message":
                role = "user"
                raw_text = payload.get("message")
            elif payload_type == "agent_message":
                role = "assistant"
                raw_text = payload.get("message")
            else:
                continue

            text = clean_text(raw_text) if isinstance(raw_text, str) else ""
            if not text:
                continue
            if role == "user" and text.startswith(NON_CONVERSATION_PREFIXES):
                continue

            local_images: list[Path] = []
            if role == "user":
                raw_images = payload.get("local_images")
                if isinstance(raw_images, list):
                    for raw_image in raw_images:
                        if isinstance(raw_image, str) and raw_image.strip():
                            local_images.append(Path(raw_image.strip()))
            sequence += 1
            messages.append(
                Message(
                    role=role,
                    text=text,
                    timestamp=parse_timestamp(record.get("timestamp"), tz),
                    source_thread=thread_id,
                    source_file=path,
                    sequence=sequence,
                    image_paths=tuple(local_images),
                )
            )
    if asset_dir is not None and fallback_images:
        enriched: list[Message] = []
        image_bundle_index = 0
        for message in messages:
            if message.role != "user":
                enriched.append(message)
                continue
            local_existing = [candidate for candidate in message.image_paths if candidate.exists()]
            bundles = fallback_images.get(normalized_text(message.text), [])
            best_bundle = max(bundles, key=len, default=[])
            if message.image_paths and image_bundle_index < len(fallback_image_bundles):
                best_bundle = fallback_image_bundles[image_bundle_index]
                image_bundle_index += 1
            decoded: list[Path] = []
            if len(local_existing) < len(best_bundle):
                for data_url in best_bundle:
                    decoded_path = decode_data_image(data_url, asset_dir)
                    if decoded_path is not None:
                        decoded.append(decoded_path)
            enriched.append(replace(message, image_paths=tuple([*message.image_paths, *decoded])))
        messages = enriched
    return messages


def message_identity(message: Message) -> tuple[str, str]:
    normalized = re.sub(r"\s+", " ", message.text).strip()
    return message.role, normalized


def merge_continuation_sessions(message_groups: Sequence[Sequence[Message]]) -> list[Message]:
    """Merge sessions when a continuation file starts by replaying the prior transcript."""
    merged: list[Message] = []
    for group in message_groups:
        current = list(group)
        if not current:
            continue
        if not merged:
            merged.extend(current)
            continue

        prefix = 0
        while (
            prefix < len(merged)
            and prefix < len(current)
            and message_identity(merged[prefix]) == message_identity(current[prefix])
        ):
            prefix += 1

        tail = current[prefix:]
        while tail and merged and message_identity(tail[0]) == message_identity(merged[-1]):
            tail.pop(0)
        merged.extend(tail)
    return merged


def deduplicate(messages: Iterable[Message]) -> list[Message]:
    result: list[Message] = []
    seen: set[tuple[str, str, str]] = set()
    for message in sorted(messages, key=lambda item: (item.timestamp, item.source_file.name, item.sequence)):
        normalized = re.sub(r"\s+", " ", message.text).strip()
        key = (message.role, message.timestamp.isoformat(timespec="seconds"), normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(message)
    return result


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        (Path(r"C:\Windows\Fonts\msyh.ttc"), "MicrosoftYaHei"),
        (Path(r"C:\Windows\Fonts\simhei.ttf"), "SimHei"),
        (Path(r"C:\Windows\Fonts\simsun.ttc"), "SimSun"),
    ]
    regular_name = "Helvetica"
    for path, name in candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            regular_name = name
            break
        except Exception:
            continue

    bold_candidates = [
        (Path(r"C:\Windows\Fonts\msyhbd.ttc"), "MicrosoftYaHei-Bold"),
        (Path(r"C:\Windows\Fonts\simhei.ttf"), "SimHei-Bold"),
    ]
    bold_name = regular_name
    for path, name in bold_candidates:
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            bold_name = name
            break
        except Exception:
            continue
    code_name = regular_name
    code_path = Path(r"C:\Windows\Fonts\simsun.ttc")
    if code_path.exists():
        try:
            pdfmetrics.registerFont(TTFont("NSimSun-Mono", str(code_path), subfontIndex=1))
            code_name = "NSimSun-Mono"
        except Exception:
            pass
    return regular_name, bold_name, code_name


def xml_text(text: str) -> str:
    return html.escape(clean_text(text), quote=False).replace("\n", "<br/>")


def split_markdown(text: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    cursor = 0
    for match in CODE_FENCE_RE.finditer(text):
        if match.start() > cursor:
            parts.append(("text", text[cursor : match.start()]))
        parts.append(("code", match.group(1)))
        cursor = match.end()
    if cursor < len(text):
        parts.append(("text", text[cursor:]))
    return [(kind, value.strip("\n")) for kind, value in parts if value.strip()]


def extract_image_paths(text: str) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for match in IMAGE_PATH_RE.finditer(text):
        raw = match.group("path").strip().rstrip("`').,;：，；")
        normalized = str(Path(raw)).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        candidate = Path(raw)
        if candidate.exists() and candidate.is_file():
            found.append(candidate)
    return found


def message_image_paths(message: Message) -> list[Path]:
    candidates = [*message.image_paths, *extract_image_paths(message.text)]
    found: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            found.append(candidate)
    return found


def scaled_image(path: Path, max_width: float, max_height: float) -> Image | None:
    try:
        with PILImage.open(path) as image:
            width, height = image.size
        if width <= 0 or height <= 0:
            return None
        scale = min(max_width / width, max_height / height, 1.0)
        return Image(str(path), width=width * scale, height=height * scale)
    except Exception:
        return None


def make_styles(font_name: str, bold_font_name: str, code_font_name: str) -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ExportTitle",
            parent=styles["Title"],
            fontName=bold_font_name,
            fontSize=19,
            leading=27,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#102A43"),
            spaceAfter=12 * mm,
            wordWrap="CJK",
        ),
        "subtitle": ParagraphStyle(
            "ExportSubtitle",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#486581"),
            wordWrap="CJK",
        ),
        "heading": ParagraphStyle(
            "ExportHeading",
            parent=styles["Heading1"],
            fontName=bold_font_name,
            fontSize=15,
            leading=21,
            textColor=colors.HexColor("#243B53"),
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
            wordWrap="CJK",
        ),
        "meta": ParagraphStyle(
            "ExportMeta",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=8.4,
            leading=12,
            textColor=colors.HexColor("#627D98"),
            spaceAfter=1.8 * mm,
            wordWrap="CJK",
        ),
        "user_label": ParagraphStyle(
            "UserLabel",
            parent=styles["Heading3"],
            fontName=bold_font_name,
            fontSize=11.2,
            leading=15,
            textColor=colors.HexColor("#0B5CAB"),
            spaceBefore=5 * mm,
            spaceAfter=1.4 * mm,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "assistant_label": ParagraphStyle(
            "AssistantLabel",
            parent=styles["Heading3"],
            fontName=bold_font_name,
            fontSize=11.2,
            leading=15,
            textColor=colors.HexColor("#176B4D"),
            spaceBefore=5 * mm,
            spaceAfter=1.4 * mm,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "user_body": ParagraphStyle(
            "UserBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9.6,
            leading=15,
            textColor=colors.HexColor("#102A43"),
            backColor=colors.HexColor("#EAF4FF"),
            borderColor=colors.HexColor("#B9D9F5"),
            borderWidth=0.5,
            borderPadding=7,
            borderRadius=4,
            spaceAfter=2.5 * mm,
            wordWrap="CJK",
            splitLongWords=True,
        ),
        "assistant_body": ParagraphStyle(
            "AssistantBody",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9.6,
            leading=15,
            textColor=colors.HexColor("#102A43"),
            backColor=colors.HexColor("#EDF8F3"),
            borderColor=colors.HexColor("#B8DFC9"),
            borderWidth=0.5,
            borderPadding=7,
            borderRadius=4,
            spaceAfter=2.5 * mm,
            wordWrap="CJK",
            splitLongWords=True,
        ),
        "code": ParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontName=code_font_name,
            fontSize=7.5,
            leading=10.5,
            textColor=colors.HexColor("#102A43"),
            backColor=colors.HexColor("#F3F6F8"),
            borderColor=colors.HexColor("#CBD5E1"),
            borderWidth=0.5,
            borderPadding=6,
            leftIndent=2 * mm,
            rightIndent=2 * mm,
            spaceBefore=1.5 * mm,
            spaceAfter=2.5 * mm,
            wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "ImageCaption",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=7.2,
            leading=10,
            textColor=colors.HexColor("#627D98"),
            alignment=TA_CENTER,
            spaceBefore=1 * mm,
            spaceAfter=3 * mm,
            wordWrap="CJK",
        ),
        "note": ParagraphStyle(
            "ExportNote",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=9.2,
            leading=15,
            textColor=colors.HexColor("#334E68"),
            backColor=colors.HexColor("#F5F7FA"),
            borderColor=colors.HexColor("#D9E2EC"),
            borderWidth=0.5,
            borderPadding=8,
            wordWrap="CJK",
        ),
    }


def page_decorator(font_name: str, title: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 7.5)
        canvas.setFillColor(colors.HexColor("#829AB1"))
        canvas.drawString(20 * mm, A4[1] - 12 * mm, title)
        canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"第 {doc.page} 页")
        canvas.setStrokeColor(colors.HexColor("#D9E2EC"))
        canvas.setLineWidth(0.4)
        canvas.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
        canvas.restoreState()

    return draw


def append_text_segment(story: list, kind: str, value: str, styles: dict, role: str) -> None:
    if kind == "code":
        story.append(Preformatted(clean_text(value), styles["code"], maxLineLength=96))
        return

    body_style = styles["user_body"] if role == "user" else styles["assistant_body"]
    blocks = re.split(r"\n{2,}", value)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            story.append(Paragraph(xml_text(block[2:].strip()), styles["heading"]))
        else:
            story.append(Paragraph(xml_text(block), body_style))


def build_pdf(
    messages: Sequence[Message],
    output: Path,
    title: str,
    tz_name: str,
    font_name: str,
    bold_font_name: str,
    code_font_name: str,
) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles(font_name, bold_font_name, code_font_name)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Codex conversation exporter",
        subject="Visible user and assistant conversation transcript",
    )

    user_count = sum(item.role == "user" for item in messages)
    assistant_count = sum(item.role == "assistant" for item in messages)
    image_paths: list[Path] = []
    for item in messages:
        image_paths.extend(message_image_paths(item))
    unique_images = list(dict.fromkeys(image_paths))

    start_time = messages[0].timestamp if messages else datetime.now(ZoneInfo(tz_name))
    end_time = messages[-1].timestamp if messages else start_time
    generated_at = datetime.now(ZoneInfo(tz_name))

    story: list = [
        Spacer(1, 18 * mm),
        Paragraph(html.escape(title), styles["title"]),
        Paragraph(
            f"对话时间：{start_time:%Y-%m-%d %H:%M:%S} - {end_time:%Y-%m-%d %H:%M:%S}<br/>"
            f"导出时间：{generated_at:%Y-%m-%d %H:%M:%S} ({html.escape(tz_name)})",
            styles["subtitle"],
        ),
        Spacer(1, 10 * mm),
        Paragraph(
            "导出范围：当前连续任务中可见的用户消息和助手消息，按时间顺序排列。"
            "内部推理、系统/开发者隐藏指令、工具调用与原始工具输出未纳入正文。"
            "用户消息里出现的附件路径按原文保留；本机仍可访问的图片会在对应消息后嵌入。",
            styles["note"],
        ),
        Spacer(1, 7 * mm),
        Paragraph(
            f"消息总数：{len(messages)}（用户 {user_count}，助手 {assistant_count}）<br/>"
            f"来源任务数：{len({m.source_thread for m in messages})}<br/>"
            f"嵌入图片数：{len(unique_images)}",
            styles["meta"],
        ),
        PageBreak(),
        Paragraph("完整对话", styles["heading"]),
    ]

    embedded_images: set[str] = set()
    for index, message in enumerate(messages, start=1):
        label = "用户" if message.role == "user" else "助手"
        label_style = styles["user_label"] if message.role == "user" else styles["assistant_label"]
        story.append(
            Paragraph(
                f"{label} · 消息 {index}　"
                f"<font size='8' color='#829AB1'>{message.timestamp:%Y-%m-%d %H:%M:%S}</font>",
                label_style,
            )
        )
        story.append(
            Paragraph(
                f"来源任务：{html.escape(message.source_thread)}",
                styles["meta"],
            )
        )
        for kind, value in split_markdown(message.text):
            append_text_segment(story, kind, value, styles, message.role)

        for image_path in message_image_paths(message):
            image_key = str(image_path.resolve()).lower()
            if image_key in embedded_images:
                continue
            flowable = scaled_image(image_path, max_width=165 * mm, max_height=175 * mm)
            if flowable is None:
                continue
            embedded_images.add(image_key)
            story.append(Spacer(1, 2 * mm))
            story.append(flowable)
            story.append(Paragraph(xml_text(str(image_path)), styles["caption"]))

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.35,
                color=colors.HexColor("#D9E2EC"),
                spaceBefore=2 * mm,
                spaceAfter=1 * mm,
            )
        )

    doc.build(
        story,
        onFirstPage=page_decorator(font_name, title),
        onLaterPages=page_decorator(font_name, title),
    )
    reader = PdfReader(str(output))
    return {
        "output": str(output),
        "page_count": len(reader.pages),
        "message_count": len(messages),
        "user_count": user_count,
        "assistant_count": assistant_count,
        "embedded_image_count": len(embedded_images),
        "source_threads": sorted({message.source_thread for message in messages}),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "font": font_name,
        "bold_font": bold_font_name,
        "code_font": code_font_name,
    }


def main() -> None:
    args = parse_args()
    tz = ZoneInfo(args.timezone)
    message_groups: list[list[Message]] = []
    source_stats: list[dict[str, object]] = []
    for session in args.session:
        messages = read_messages(session, tz, args.asset_dir)
        message_groups.append(messages)
        source_stats.append(
            {
                "path": str(session),
                "message_count": len(messages),
                "user_count": sum(item.role == "user" for item in messages),
                "assistant_count": sum(item.role == "assistant" for item in messages),
            }
        )

    messages = deduplicate(merge_continuation_sessions(message_groups))
    if not messages:
        raise SystemExit("No visible user/assistant messages found.")

    font_name, bold_font_name, code_font_name = register_fonts()
    result = build_pdf(
        messages=messages,
        output=args.output,
        title=args.title,
        tz_name=args.timezone,
        font_name=font_name,
        bold_font_name=bold_font_name,
        code_font_name=code_font_name,
    )
    result["sources"] = source_stats

    if args.analysis_json:
        args.analysis_json.parent.mkdir(parents=True, exist_ok=True)
        args.analysis_json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
