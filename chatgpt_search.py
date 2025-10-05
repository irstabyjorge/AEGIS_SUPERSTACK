"""ChatGPT conversation search utility.

This script loads exported ChatGPT conversation data (``conversations.json``)
from the official export format and provides fast keyword lookups over every
message. It builds an in-memory inverted index for quick searches across all
messages so you can immediately locate evidence, IP addresses, logs, or any
other keywords of interest.

Usage example::

    python chatgpt_search.py path/to/conversations.json evidence logs

The script also accepts a directory that contains multiple conversation JSON
files. By default it performs AND search (all keywords must appear in the same
message). Use ``--any`` for OR semantics.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple


@dataclass(frozen=True)
class MessageRecord:
    """Represents a single message pulled from the export."""

    conversation_title: str
    message_id: str
    author_role: str
    create_time: float | None
    text: str


def iter_json_files(root: Path) -> Iterator[Path]:
    """Yield all JSON files that might contain conversations."""

    if root.is_file() and root.suffix.lower() == ".json":
        yield root
        return

    if root.is_dir():
        for path in sorted(root.rglob("*.json")):
            yield path


def load_messages(path: Path) -> List[MessageRecord]:
    """Load every textual message from ChatGPT exports found under ``path``."""

    messages: List[MessageRecord] = []
    for json_file in iter_json_files(path):
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:  # pragma: no cover - user feedback path
            raise SystemExit(f"Failed to parse {json_file}: {exc}") from exc

        # Some exports contain a list of conversations, others contain a single
        # conversation object. Normalise to a list.
        conversations: Sequence[Dict[str, object]]
        if isinstance(data, list):
            conversations = [item for item in data if isinstance(item, dict)]
        elif isinstance(data, dict):
            conversations = [data]
        else:  # pragma: no cover - protective branch
            continue

        for conversation in conversations:
            title = str(conversation.get("title", "Untitled"))
            mapping = conversation.get("mapping", {})
            if not isinstance(mapping, dict):
                continue

            for node in mapping.values():
                if not isinstance(node, dict):
                    continue
                message = node.get("message")
                if not isinstance(message, dict):
                    continue

                content = message.get("content")
                if not isinstance(content, dict):
                    continue

                parts = content.get("parts", [])
                text_parts: List[str] = []
                if isinstance(parts, list):
                    for part in parts:
                        if isinstance(part, str):
                            text_parts.append(part)
                        elif isinstance(part, dict):
                            # Some exports store text inside dict parts (e.g. multimodal)
                            text_value = part.get("text")
                            if isinstance(text_value, str):
                                text_parts.append(text_value)
                text = "\n".join(part.strip() for part in text_parts if part.strip())
                if not text:
                    continue

                message_id = str(message.get("id", node.get("id", "")))
                author = message.get("author", {})
                author_role = "unknown"
                if isinstance(author, dict):
                    role = author.get("role")
                    if isinstance(role, str):
                        author_role = role

                create_time = message.get("create_time")
                if not isinstance(create_time, (int, float)):
                    create_time = None

                messages.append(
                    MessageRecord(
                        conversation_title=title,
                        message_id=message_id,
                        author_role=author_role,
                        create_time=create_time,
                        text=text,
                    )
                )
    return messages


def build_index(messages: Sequence[MessageRecord]) -> Dict[str, List[int]]:
    """Build an inverted index mapping tokens to message indices."""

    token_pattern = re.compile(r"[\w-]+", flags=re.UNICODE)
    index: Dict[str, List[int]] = defaultdict(list)
    for idx, message in enumerate(messages):
        tokens = {token.lower() for token in token_pattern.findall(message.text)}
        for token in tokens:
            index[token].append(idx)
    return index


def search_messages(
    messages: Sequence[MessageRecord],
    index: Dict[str, List[int]],
    keywords: Sequence[str],
    match_all: bool,
) -> List[int]:
    """Return sorted message indices that match the query keywords."""

    if not keywords:
        return []

    normalized = [keyword.lower() for keyword in keywords]
    sets: List[set[int]] = []
    for keyword in normalized:
        postings = index.get(keyword)
        if postings is None:
            if match_all:
                return []
            continue
        sets.append(set(postings))

    if not sets:
        return []

    if match_all:
        candidate_indices = set.intersection(*sets)
    else:
        candidate_indices = set.union(*sets)

    # Maintain chronological order based on index position
    return sorted(candidate_indices)


def make_snippets(text: str, keywords: Sequence[str], context: int) -> Iterator[str]:
    """Yield highlighted snippets of ``text`` around the keywords."""

    if not keywords:
        return iter(())

    pattern = re.compile(
        "|".join(re.escape(keyword) for keyword in keywords),
        flags=re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        start = max(match.start() - context, 0)
        end = min(match.end() + context, len(text))
        snippet = text[start:end].replace("\n", " ")
        yield snippet


def format_message(record: MessageRecord, keywords: Sequence[str], context: int) -> str:
    """Format a message record with snippets for display."""

    header = (
        f"Conversation: {record.conversation_title}\n"
        f"Author: {record.author_role} | Message ID: {record.message_id}\n"
    )
    snippets = list(make_snippets(record.text, keywords, context))
    if snippets:
        body = "\n".join(f"  …{snippet}…" for snippet in snippets)
    else:
        trimmed = record.text if len(record.text) <= context * 2 else record.text[: context * 2] + "…"
        body = f"  {trimmed}"
    return header + body


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="Path to conversations.json or a directory containing JSON exports",
    )
    parser.add_argument(
        "keywords",
        nargs="+",
        help="Keywords to search for (case-insensitive token search)",
    )
    parser.add_argument(
        "--any",
        dest="match_all",
        action="store_false",
        default=True,
        help="Match messages that contain any of the keywords instead of all",
    )
    parser.add_argument(
        "--context",
        type=int,
        default=60,
        help="Number of characters to show around each match",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    messages = load_messages(args.path)
    if not messages:
        raise SystemExit("No messages were found in the provided export.")

    index = build_index(messages)
    matches = search_messages(messages, index, args.keywords, args.match_all)
    if not matches:
        print("No messages matched the supplied keywords.")
        return

    for message_idx in matches:
        record = messages[message_idx]
        print(format_message(record, args.keywords, args.context))
        print("-" * 80)


if __name__ == "__main__":
    main()
