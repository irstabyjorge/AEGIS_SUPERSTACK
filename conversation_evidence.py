"""Conversation evidence extraction utilities.

This module provides a small command line interface for scanning a text
transcript of a chat conversation for specific statements.  It was written to
support workflows where a user needs to demonstrate that a conversation with a
language model contained a clear set of claims.

The tool computes a SHA256 hash of the supplied transcript to help maintain an
audit trail and then searches for pre-defined statements using case-insensitive
regular expressions.  When a match is found the relevant excerpt is displayed
along with the line numbers where it appears in the transcript.

Example usage::

    python conversation_evidence.py transcript.txt

Multiple files can be supplied and each will be processed independently.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import pathlib
import re
import textwrap
from typing import Iterable, List, Optional


@dataclasses.dataclass(frozen=True)
class StatementPattern:
    """Container describing a statement that should be located in a transcript."""

    identifier: str
    description: str
    pattern: re.Pattern[str]


def _compile_pattern(fragment: str) -> re.Pattern[str]:
    """Create a case-insensitive regular expression from the provided fragment.

    ``fragment`` should already contain any ``.*`` wildcards that are required for
    flexible matching.  The helper simply adds ``re.IGNORECASE`` and ``re.DOTALL``
    flags so that matches span multiple lines.
    """

    return re.compile(fragment, re.IGNORECASE | re.DOTALL)


STATEMENT_PATTERNS: List[StatementPattern] = [
    StatementPattern(
        identifier="medical_visibility",
        description=(
            "Brain implants (legitimate medical ones like DBS) are visible on "
            "standard MRI/CT and documented by neurosurgeons who implanted them."
        ),
        pattern=_compile_pattern(
            r"Brain implants.*visible on standard MRI/CT.*documented by neurosurgeons"
        ),
    ),
    StatementPattern(
        identifier="foreign_signal_detector",
        description=(
            "There's no 'foreign signal detector' for the kind of mind control "
            "described because that's not how neuroscience works."
        ),
        pattern=_compile_pattern(
            r"no\s+['\"]foreign signal detector['\"].*mind control.*not how neuroscience works"
        ),
    ),
    StatementPattern(
        identifier="false_positive_warning",
        description=(
            "Creating software that pretends to detect these things would just "
            "generate false positives that reinforce the user's beliefs."
        ),
        pattern=_compile_pattern(
            r"Creating software.*pretends to detect.*generate false positives.*reinforce"
        ),
    ),
    StatementPattern(
        identifier="forensic_reports_clear",
        description=(
            "Forensic reports found zero threats and further tools would generate "
            "noise interpreted as confirmation."
        ),
        pattern=_compile_pattern(
            r"forensic reports.*zero threats.*generate noise.*interpreted as confirmation"
        ),
    ),
    StatementPattern(
        identifier="observation_of_pattern",
        description=(
            "Observation of an escalating pattern of beliefs disconnected from "
            "reality and requests for technical validation."
        ),
        pattern=_compile_pattern(
            r"escalating pattern of beliefs.*disconnected from reality.*technical validation"
        ),
    ),
    StatementPattern(
        identifier="available_help",
        description=(
            "Available assistance limited to standard security monitoring, "
            "explaining results, and connecting with mental health resources."
        ),
        pattern=_compile_pattern(
            r"Standard security monitoring.*Explaining.*Connecting you with mental health resources"
        ),
    ),
    StatementPattern(
        identifier="refused_assistance",
        description=(
            "Clear refusal to help with implant detection software requests, no "
            "matter how they are framed."
        ),
        pattern=_compile_pattern(
            r"I will not help.*Creating ['\"]implant detection['\"] software.*variation of this request"
        ),
    ),
    StatementPattern(
        identifier="medical_guidance",
        description=(
            "Guidance that believing in implants requires consultation with "
            "medical professionals, not scripts."
        ),
        pattern=_compile_pattern(
            r"If you believe you have implants.*neurosurgeon.*medical imaging.*not PowerShell scripts"
        ),
    ),
    StatementPattern(
        identifier="final_answer",
        description=(
            "Statement explicitly marking the response as the final answer."
        ),
        pattern=_compile_pattern(r"That's my final answer"),
    ),
]


@dataclasses.dataclass
class MatchResult:
    statement: StatementPattern
    excerpt: str
    start_line: int
    end_line: int


def compute_sha256(path: pathlib.Path) -> str:
    """Compute the SHA256 hash of a file in a streaming friendly way."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_matches(text: str) -> Iterable[MatchResult]:
    """Yield every matching statement found within ``text``."""

    for statement in STATEMENT_PATTERNS:
        match = statement.pattern.search(text)
        if not match:
            continue
        start_index = match.start()
        end_index = match.end()
        start_line = text.count("\n", 0, start_index) + 1
        end_line = text.count("\n", 0, end_index) + 1
        excerpt = text[start_index:end_index]
        yield MatchResult(statement, excerpt, start_line, end_line)


def format_excerpt(excerpt: str, width: int = 78) -> str:
    """Return a neatly wrapped excerpt for console display."""

    cleaned = " ".join(excerpt.split())
    return "\n".join(textwrap.wrap(cleaned, width=width))


def process_file(path: pathlib.Path) -> None:
    """Process a single transcript file and print findings to stdout."""

    if not path.exists():
        raise FileNotFoundError(f"Transcript file not found: {path}")

    sha = compute_sha256(path)
    print(f"File: {path}")
    print(f"SHA256: {sha}")

    text = path.read_text(encoding="utf-8", errors="replace")

    matches = list(locate_matches(text))

    if not matches:
        print("No predefined statements were located in this transcript.\n")
        return

    for result in matches:
        print(f"- [{result.statement.identifier}] {result.statement.description}")
        print(f"  Lines {result.start_line}-{result.end_line}")
        print("  Excerpt:")
        for line in format_excerpt(result.excerpt).splitlines():
            print(f"    {line}")
        print()

    missing = {
        statement.identifier
        for statement in STATEMENT_PATTERNS
        if all(m.statement is not statement for m in matches)
    }

    if missing:
        missing_list = ", ".join(sorted(missing))
        print(f"Statements without matches: {missing_list}\n")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan chat transcripts for predefined statements and report their "
            "locations along with file hashes."
        )
    )
    parser.add_argument(
        "transcripts",
        nargs="+",
        type=pathlib.Path,
        help="Path(s) to text transcripts to analyze.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    for transcript in args.transcripts:
        process_file(transcript)


if __name__ == "__main__":
    main()
