"""FDX Formatter — Converts screenplay data to Final Draft XML format.

Generates valid Final Draft .fdx XML files from Script and SceneDescriptionCollection.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

from ai_movie_gen_suite.models import SceneDescriptionCollection, Script


class FDXFormatter:
    """Formats screenplay data into Final Draft XML (.fdx) format."""

    def __init__(self, script: Script, scene_descriptions: Optional[SceneDescriptionCollection] = None):
        self.script = script
        self.scene_descriptions = scene_descriptions

    def format(self) -> str:
        """Generate FDX XML string."""
        root = ET.Element("FinalDraft")
        root.set("version", "12.0")

        # Document metadata
        doc = ET.SubElement(root, "Document")
        doc.set("Type", "Screenplay")
        doc.set("Title", self.script.title)
        doc.set("Author", "AI Movie Gen Suite")
        doc.set("Genre", self.script.genre)
        doc.set("Logline", self.script.logline)

        # Body
        body = ET.SubElement(doc, "Body")

        # Add scenes
        for scene in self.script.scenes:
            scene_elem = ET.SubElement(body, "Scene")
            scene_elem.set("ID", scene.scene_id)

            # Scene heading
            heading = ET.SubElement(scene_elem, "SceneHeading")
            heading.text = scene.scene_heading

            # Action lines
            if scene.action:
                action = ET.SubElement(scene_elem, "Action")
                action.text = scene.action

            # Dialogue
            for dialogue in scene.dialogue_lines:
                dialogue_elem = ET.SubElement(scene_elem, "Dialogue")
                character = ET.SubElement(dialogue_elem, "Character")
                character.text = dialogue.character_name
                text = ET.SubElement(dialogue_elem, "Text")
                text.text = dialogue.text

            # Scene description if available
            if self.scene_descriptions:
                desc = self.scene_descriptions.get_description(scene.scene_id)
                if desc:
                    notes = ET.SubElement(scene_elem, "Notes")
                    notes.text = f"Mood: {desc.mood}\nLighting: {desc.lighting}\nCamera: {desc.camera_notes}"

        # Serialize to string
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")
        return xml_str

    def save(self, filepath: str) -> None:
        """Save FDX file to disk."""
        xml_str = self.format()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_str)
