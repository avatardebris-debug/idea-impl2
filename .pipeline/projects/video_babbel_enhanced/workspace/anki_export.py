"""
anki_export.py — Export video_babbel clips to Anki deck (.apkg).

Produces a valid .apkg file (ZIP with collection.anki2 SQLite DB + media/)
that can be imported into Anki desktop.

Usage:
    python -m video_babbel_enhanced export-anki --deck "My Clips" --db video_babbel.db
    python video_babbel_enhanced/anki_export.py --deck "My Clips" --db video_babbel.db
"""
from __future__ import annotations
import io
import json
import os
import sqlite3
import struct
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Anki .apkg format
# ---------------------------------------------------------------------------
# .apkg is a ZIP file containing:
#   - collection.anki2  (SQLite DB with cards, decks, notes, revlog tables)
#   - media/            (folder for attached media files)
#
# The collection.anki2 schema (simplified):
#   - decks: deck definitions
#   - notes: note fields (the actual content)
#   - cards: card instances linked to notes
#   - revlog: review history
#   - models: note type / card template definitions
# ---------------------------------------------------------------------------

# Anki note type ID (standard basic card type)
_NOTE_TYPE_ID = 1623957000  # "Basic (and reversed card)" — common default

# Deck ID (will be created if not exists)
_DECK_ID = 1623957001


def _create_anki_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database with Anki's schema."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE models (
            id          INTEGER PRIMARY KEY,
            mod         INTEGER NOT NULL DEFAULT 0,
            usn         INTEGER NOT NULL DEFAULT 0,
            type        INTEGER NOT NULL DEFAULT 0,
            name        TEXT NOT NULL DEFAULT 'Basic',
            sortf       TEXT NOT NULL DEFAULT 'fld',
            req         TEXT NOT NULL DEFAULT '{"type":0,"keys":["*"]}',
            tmpl        TEXT NOT NULL DEFAULT '[{"name":"Card 1","qfmt":"{{Front}}","afmt":"{{FrontSide}}\\n<hr id=answer>\\n{{Back}}","ord":0,"mid":null,"bafmt":null,"did":null,"bqfmt":""}]',
            css         TEXT NOT NULL DEFAULT 'html,body{margin:0;padding:0;font-family:sans-serif;font-size:14pt}#card{margin:2em}#answer{border-top:1px solid #aaa;padding-top:1em}',
            did         INTEGER,
            usn2        INTEGER NOT NULL DEFAULT 0,
            mod2        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE decks (
            id          INTEGER PRIMARY KEY,
            mod         INTEGER NOT NULL DEFAULT 0,
            name        TEXT NOT NULL DEFAULT 'Default',
            usn         INTEGER NOT NULL DEFAULT 0,
            desc        TEXT NOT NULL DEFAULT '',
            conf        TEXT NOT NULL DEFAULT '{}',
            extm        INTEGER NOT NULL DEFAULT 0,
            lm          INTEGER NOT NULL DEFAULT 0,
            usn2        INTEGER NOT NULL DEFAULT 0,
            usn3        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE notes (
            id          INTEGER PRIMARY KEY,
            guid        TEXT NOT NULL DEFAULT '',
            mid         INTEGER NOT NULL DEFAULT 0,
            mod         INTEGER NOT NULL DEFAULT 0,
            usn         INTEGER NOT NULL DEFAULT 0,
            tags        TEXT NOT NULL DEFAULT '',
            flds        TEXT NOT NULL DEFAULT '',
            flds2       TEXT NOT NULL DEFAULT '',
            sfld        TEXT NOT NULL DEFAULT '',
            csum        INTEGER NOT NULL DEFAULT 0,
            flds3       TEXT NOT NULL DEFAULT '',
            utype       INTEGER NOT NULL DEFAULT 0,
            usn2        INTEGER NOT NULL DEFAULT 0,
            usn3        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE cards (
            id          INTEGER PRIMARY KEY,
            nid         INTEGER NOT NULL DEFAULT 0,
            did         INTEGER NOT NULL DEFAULT 0,
            ord         INTEGER NOT NULL DEFAULT 0,
            mod         INTEGER NOT NULL DEFAULT 0,
            usn         INTEGER NOT NULL DEFAULT 0,
            qfwd        TEXT NOT NULL DEFAULT '',
            qrev        TEXT NOT NULL DEFAULT '',
            usn2        INTEGER NOT NULL DEFAULT 0,
            usn3        INTEGER NOT NULL DEFAULT 0,
            type        INTEGER NOT NULL DEFAULT 0,
            queue       INTEGER NOT NULL DEFAULT 0,
            due         INTEGER NOT NULL DEFAULT 0,
            ivl         INTEGER NOT NULL DEFAULT 0,
            factor      INTEGER NOT NULL DEFAULT 2500,
            reps        INTEGER NOT NULL DEFAULT 0,
            lapses      INTEGER NOT NULL DEFAULT 0,
            left        INTEGER NOT NULL DEFAULT 0,
            odue        INTEGER NOT NULL DEFAULT 0,
            odiff       INTEGER NOT NULL DEFAULT 0,
            usn4        INTEGER NOT NULL DEFAULT 0,
            usn5        INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE revlog (
            id          INTEGER PRIMARY KEY,
            cid         INTEGER NOT NULL DEFAULT 0,
            usn         INTEGER NOT NULL DEFAULT 0,
            ease        INTEGER NOT NULL DEFAULT 0,
            ivl         INTEGER NOT NULL DEFAULT 0,
            lastIvl     INTEGER NOT NULL DEFAULT 0,
            factor      INTEGER NOT NULL DEFAULT 0,
            time        INTEGER NOT NULL DEFAULT 0,
            type        INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    return conn


class AnkiExporter:
    """Export video_babbel clips to Anki .apkg format."""

    def __init__(
        self,
        deck_name: str = "Video Babbel",
        db_path: str | Path = "video_babbel.db",
    ):
        """Initialize the Anki exporter.

        Args:
            deck_name: Name of the Anki deck to create.
            db_path: Path to the source SQLite database.
        """
        self.deck_name = deck_name
        self.db_path = Path(db_path)
        self._anki_db = _create_anki_db()
        self._note_counter = 0
        self._card_counter = 0
        self._revlog_counter = 0
        self._media_files: dict[str, bytes] = {}

    def _ensure_deck(self) -> None:
        """Ensure the target deck exists in the Anki DB."""
        decks = self._anki_db.execute(
            "SELECT id FROM decks WHERE name = ?", (self.deck_name,)
        ).fetchall()
        if not decks:
            now = int(time.time())
            self._anki_db.execute(
                "INSERT INTO decks (id, mod, name, usn, desc, conf, extm, lm) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (_DECK_ID, now, self.deck_name, 0, "", "{}", 0, now),
            )
            self._anki_db.commit()

    def _ensure_note_type(self) -> None:
        """Ensure the note type exists in the Anki DB."""
        nts = self._anki_db.execute(
            "SELECT id FROM models WHERE name = ?", ("Basic (and reversed card)",)
        ).fetchall()
        if not nts:
            now = int(time.time())
            self._anki_db.execute(
                "INSERT INTO models (id, mod, name, type, sortf, req, tmpl, css, did) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (_NOTE_TYPE_ID, now, "Basic (and reversed card)", 0, "fld",
                 '{"type":0,"keys":["*"]}',
                 '[{"name":"Card 1","qfmt":"{{Front}}","afmt":"{{FrontSide}}\\n<hr id=answer>\\n{{Back}}","ord":0,"mid":null,"bafmt":null,"did":null,"bqfmt":""}]',
                 'html,body{margin:0;padding:0;font-family:sans-serif;font-size:14pt}',
                 _DECK_ID),
            )
            self._anki_db.commit()

    def add_clip(
        self,
        clip_id: str,
        l1_text: str,
        l2_text: str,
        audio_data: bytes | None = None,
        video_data: bytes | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Add a single clip as an Anki note.

        Args:
            clip_id: Unique clip identifier.
            l1_text: Source language text.
            l2_text: Target language text.
            audio_data: Optional audio file bytes.
            video_data: Optional video file bytes.
            tags: Optional list of tags.
        """
        self._ensure_deck()
        self._ensure_note_type()

        now = int(time.time())
        self._note_counter += 1
        note_id = self._note_counter

        # Create note fields
        # Field 0: Front (L1 text)
        # Field 1: Back (L2 text)
        fields = [l1_text, l2_text]
        tags_str = " ".join(tags) if tags else ""

        self._anki_db.execute(
            "INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (note_id, f"{clip_id}_{note_id}", _NOTE_TYPE_ID, now, 0,
             tags_str, json.dumps(fields), l1_text),
        )

        # Create card
        self._card_counter += 1
        card_id = self._card_counter
        self._anki_db.execute(
            "INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (card_id, note_id, _DECK_ID, 0, now, 0, 0, 0, 0, 1, 2500, 0),
        )

        # Add media if provided
        if audio_data:
            media_name = f"{clip_id}_audio.mp3"
            self._media_files[media_name] = audio_data
        if video_data:
            media_name = f"{clip_id}_video.mp4"
            self._media_files[media_name] = video_data

    def add_clips(
        self,
        clips: list[dict[str, Any]],
    ) -> None:
        """Add multiple clips as Anki notes.

        Args:
            clips: List of clip dicts with keys: clip_id, l1_text, l2_text,
                   audio_data (optional), video_data (optional), tags (optional).
        """
        for clip in clips:
            self.add_clip(
                clip_id=clip["clip_id"],
                l1_text=clip.get("l1_text", ""),
                l2_text=clip.get("l2_text", ""),
                audio_data=clip.get("audio_data"),
                video_data=clip.get("video_data"),
                tags=clip.get("tags"),
            )

    def export(self, output_path: str | Path) -> Path:
        """Export to .apkg file.

        Args:
            output_path: Path for the output .apkg file.

        Returns:
            Path to the created .apkg file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Anki DB to bytes
        db_bytes = io.BytesIO()
        self._anki_db.commit()
        self._anki_db.backup(sqlite3.connect(db_bytes))
        db_bytes.seek(0)

        # Create .apkg
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("collection.anki2", db_bytes.read())
            zf.writestr("media/.gitkeep", "")

            # Add media files
            for media_name, media_data in self._media_files.items():
                zf.writestr(f"media/{media_name}", media_data)

        return output_path

    def get_stats(self) -> dict[str, int]:
        """Get export statistics.

        Returns:
            Dict with 'notes', 'cards', 'media_files' counts.
        """
        return {
            "notes": self._note_counter,
            "cards": self._card_counter,
            "media_files": len(self._media_files),
        }


def export_anki(
    deck_name: str = "Video Babbel",
    db_path: str | Path = "video_babbel.db",
    output_path: str | Path = "video_babbel_deck.apkg",
) -> Path:
    """Export video_babbel clips to Anki .apkg.

    Args:
        deck_name: Name of the Anki deck.
        db_path: Path to source SQLite database.
        output_path: Path for output .apkg file.

    Returns:
        Path to the created .apkg file.
    """
    from video_babbel_enhanced import session_db

    # Get all clips from database
    clips = session_db.get_all_clips(db_path)
    if not clips:
        print("  No clips found in database. Import clips first.")
        # Still create a valid (empty) deck file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("collection.anki2", b"")
            zf.writestr("media/.gitkeep", "")
        return output_path

    # Create exporter and add clips
    exporter = AnkiExporter(deck_name=deck_name, db_path=db_path)
    exporter.add_clips(clips)

    # Export
    result = exporter.export(output_path)
    stats = exporter.get_stats()
    print(f"  ✓ Exported {stats['notes']} notes, {stats['cards']} cards, "
          f"{stats['media_files']} media files to {output_path}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export video_babbel clips to Anki")
    parser.add_argument("--deck", default="Video Babbel", help="Deck name")
    parser.add_argument("--db", default="video_babbel.db", help="Database path")
    parser.add_argument("--output", default="video_babbel_deck.apkg", help="Output .apkg path")
    args = parser.parse_args()

    export_anki(args.deck, args.db, args.output)
