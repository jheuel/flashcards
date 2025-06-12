# /// script
# dependencies = [
#   "genanki",
#   "rich",
# ]
# ///

import re
import os
import subprocess
from pathlib import Path
from datetime import datetime
from textwrap import dedent, indent
from dataclasses import dataclass, field
from typing import List, Optional
import genanki
from rich.console import Console
from rich.logging import RichHandler
import logging

# Configure rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = 1749648272
RE_DECK = re.compile(r"^= ([^\n]*?)\s*\n+([\s\S]*?)(?=\n= |\Z)", re.MULTILINE)
RE_LABEL = re.compile(r"<(.*)>")
RE_NOTE = re.compile(r"^== ([^\n]*?)\s*\n+([\s\S]*?)(?=\n== |\Z)", re.MULTILINE)
CWD = Path.cwd()


@dataclass
class FlashcardNote:
    """Represents a single flashcard note."""

    question: str
    answer: str
    id: str
    question_svg: str = ""
    answer_svg: str = ""

    def __post_init__(self):
        """Clean up question text by removing labels."""
        self.question = RE_LABEL.sub("", self.question).strip()


@dataclass
class FlashcardDeck:
    """Represents a deck of flashcard notes."""

    title: str
    body: str
    id: int
    notes: List[FlashcardNote] = field(default_factory=list)

    def __post_init__(self):
        """Clean up deck title by removing labels."""
        self.title = RE_LABEL.sub("", self.title).strip()


class IDGenerator:
    """Handles ID generation for notes and decks."""

    @staticmethod
    def get_note_id(suffix: Optional[int] = None) -> str:
        """Generate a unique note ID."""
        id_str = datetime.now().strftime("%Y-%m-%d-%H:%M")
        if suffix is not None:
            id_str += f"-{suffix}"
        return id_str

    @staticmethod
    def get_deck_id(suffix: Optional[int] = None) -> int:
        """Generate a unique deck ID."""
        id_str = datetime.now().strftime("%Y%m%d%H%M%S")
        if suffix is not None:
            id_str += str(suffix)
        return int(id_str)


class AnkiNote(genanki.Note):
    """Custom Anki note with GUID generation."""

    @property
    def guid(self):
        return genanki.guid_for(self.fields[0])


class TypstModel(genanki.Model):
    """Anki model for Typst-generated flashcards."""

    def __init__(self):
        super().__init__(
            MODEL_ID,
            "Typst Flashcard Model",
            fields=[
                {"name": "ID"},
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": dedent("""
                        <div class="svg-container">
                            {{Question}}
                        </div>
                    """).strip(),
                    "afmt": dedent("""
                        <div class="svg-container">
                            {{FrontSide}}
                        </div>
                        <div class="svg-container">
                            {{Answer}}
                        </div>
                    """).strip(),
                },
            ],
            css=dedent("""
                .svg-container svg {
                    width: 100% !important;
                    height: auto !important;
                    max-width: 100% !important;
                    display: block;
                }
            """).strip(),
        )


class DeckFileProcessor:
    """Handles processing of deck files."""

    def __init__(self, filename: str):
        self.filename = filename
        self.id_generator = IDGenerator()

    def add_missing_ids(self) -> None:
        """Add missing IDs to deck and note headers."""
        logger.info(f"Processing file: {self.filename}")

        with open(self.filename, "r") as f:
            lines = f.read().splitlines()

        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(self._add_label_if_missing(line, i))

        with open(self.filename, "w") as f:
            f.write("\n".join(new_lines) + "\n")

        logger.info("Added missing IDs to file")

    def _add_label_if_missing(self, line: str, index: int) -> str:
        """Add label to line if missing."""
        if not line.startswith("="):
            return line

        if RE_LABEL.search(line):
            return line

        if line.startswith("== "):
            return f"{line} <{self.id_generator.get_note_id(index)}>"

        return f"{line} <{self.id_generator.get_deck_id(index)}>"

    def parse_decks(self) -> List[FlashcardDeck]:
        """Parse deck file and return list of FlashcardDeck objects."""
        logger.info("Parsing decks from file")

        with open(self.filename, "r") as f:
            content = f.read()

        decks = []
        for match in RE_DECK.finditer(content):
            deck = self._parse_single_deck(match)
            decks.append(deck)
            logger.info(f"Parsed deck: {deck.title} with {len(deck.notes)} notes")

        return decks

    def _parse_single_deck(self, match) -> FlashcardDeck:
        """Parse a single deck from regex match."""
        deck_title = match.group(1).strip()
        deck_body = match.group(2).strip()

        # Extract deck ID from label
        label = RE_LABEL.findall(deck_title)
        deck_id = label[0].strip() if label else self.id_generator.get_deck_id()

        try:
            deck_id = int(deck_id)
        except ValueError:
            logger.error(
                f"Invalid deck ID '{deck_id}' in deck '{deck_title}', must be integer"
            )
            raise ValueError(f"Invalid deck ID: {deck_id}")

        # Create deck
        deck = FlashcardDeck(title=deck_title, body=deck_body, id=deck_id)

        # Parse notes
        for i, note_match in enumerate(RE_NOTE.finditer(deck_body)):
            note = self._parse_single_note(note_match, i)
            deck.notes.append(note)

        return deck

    def _parse_single_note(self, match, index: int) -> FlashcardNote:
        """Parse a single note from regex match."""
        question = match.group(1).strip()
        answer = match.group(2).strip()

        # Extract note ID from label
        label = RE_LABEL.findall(question)
        note_id = label[0].strip() if label else self.id_generator.get_note_id(index)

        return FlashcardNote(question=question, answer=answer, id=note_id)


class TypstRenderer:
    """Handles Typst compilation and SVG generation."""

    def __init__(self):
        self.header = dedent(
            """
            #import "/common.typ": *
            #show: style
            #set align(center)
            """
        ).strip()

    def render_decks(self, decks: List[FlashcardDeck]) -> None:
        """Render all decks to SVG format."""
        logger.info("Starting SVG rendering for all decks")

        for deck in decks:
            logger.info(f"Rendering deck: {deck.title}")
            self._render_single_deck(deck)

        logger.info("Completed SVG rendering for all decks")

    def _render_single_deck(self, deck: FlashcardDeck) -> None:
        """Render a single deck to SVG format."""
        output_path = CWD / "build" / deck.title
        os.makedirs(output_path, exist_ok=True)

        for note in deck.notes:
            self._render_note(note, output_path)

    def _render_note(self, note: FlashcardNote, output_path: Path) -> None:
        """Render a single note's question and answer to SVG."""
        # Render question
        question_path = output_path / f"{note.id}_question.typ"
        self._write_typst_file(question_path, note.question, is_question=True)
        self._compile_typst(question_path)

        # Render answer
        answer_path = output_path / f"{note.id}_answer.typ"
        self._write_typst_file(answer_path, note.answer, is_question=False)
        self._compile_typst(answer_path)

        # Read SVG content
        note.question_svg = self._read_svg_file(question_path.with_suffix(".svg"))
        note.answer_svg = self._read_svg_file(answer_path.with_suffix(".svg"))

    def _write_typst_file(self, path: Path, content: str, is_question: bool) -> None:
        """Write Typst file with appropriate formatting."""
        with open(path, "w") as f:
            f.write(self.header + "\n")
            f.write(
                dedent(
                    f"""
                    {"#v(-0.5em)#line(length: 75%, stroke: 0.6pt + black)#v(1em)" if not is_question else ""}

                    #box[
                        #set align(left)
                        {"#set text(size: 1.1em)" if is_question else ""}
                        \n{indent(content, " " * 24)}
                    ]
                    """
                ).strip()
            )

    def _compile_typst(self, source_path: Path) -> None:
        """Compile Typst file to SVG."""
        result = subprocess.run(
            [
                "typst",
                "compile",
                "--root",
                str(CWD),
                str(source_path),
                str(source_path.with_suffix(".svg")),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Typst compilation failed for {source_path}")
            logger.error(f"Error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args)

    def _read_svg_file(self, path: Path) -> str:
        """Read SVG file content."""
        with open(path, "r") as f:
            return f.read()


class AnkiExporter:
    """Handles export to Anki package format."""

    def __init__(self, path: Path):
        self.model = TypstModel()
        self.path = path

    def export_decks(self, decks: List[FlashcardDeck]) -> None:
        """Export all decks to Anki package files."""
        logger.info("Starting Anki package export")

        for deck in decks:
            self._export_single_deck(deck)
            logger.info(f"Exported deck: {deck.title}")

        logger.info("Completed Anki package export")

    def _export_single_deck(self, deck: FlashcardDeck) -> None:
        """Export a single deck to Anki package."""
        anki_deck = genanki.Deck(deck.id, deck.title)

        for note in deck.notes:
            anki_note = AnkiNote(
                model=self.model,
                fields=[
                    note.id,
                    note.question_svg,
                    note.answer_svg,
                ],
            )
            anki_deck.add_note(anki_note)

        package_path = self.path / f"{deck.title}.apkg"
        package_path.parent.mkdir(parents=True, exist_ok=True)
        genanki.Package(anki_deck).write_to_file(package_path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "deck_file",
        type=str,
        help="Path to the Typst deck file (e.g., deck.typ)",
    )
    args = parser.parse_args()
    deck_path = Path(args.deck_file)
    decks_path = deck_path.parent / "decks"
    decks_path.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Starting Anki deck generation process")

        # Process deck file
        processor = DeckFileProcessor(deck_path)
        processor.add_missing_ids()
        decks = processor.parse_decks()

        # Render to SVG
        renderer = TypstRenderer()
        renderer.render_decks(decks)

        # Export to Anki
        exporter = AnkiExporter(decks_path)
        exporter.export_decks(decks)

        logger.info("Anki deck generation completed successfully")

    except Exception as e:
        logger.exception(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    main()
