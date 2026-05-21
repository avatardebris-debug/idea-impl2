"""PDF generator for audiobook metadata."""

import io
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


def generate_pdf(metadata: dict, output_path: str) -> str:
    """Generate a PDF from audiobook metadata.

    The PDF contains:
    - Cover art page (if cover art is available)
    - Metadata page (title, author, narrator, duration)
    - Chapter listing page (if chapters are available)

    Args:
        metadata: Dict from extract_metadata().
        output_path: Path to write the output PDF.

    Returns:
        The output_path that was written.

    Raises:
        PDFGenerationError: If PDF generation fails.
    """
    if not metadata:
        raise PDFGenerationError("metadata cannot be empty")
    if not output_path:
        raise PDFGenerationError("output_path cannot be empty")

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter

        # Page 1: Cover art
        cover = metadata.get("cover_art_bytes")
        if cover:
            cover_stream = io.BytesIO(cover)
            img = ImageReader(cover_stream)
            img_width, img_height = img.getSize()
            # Scale to fit page with margins
            margin = inch
            avail_w = width - 2 * margin
            avail_h = height - 2 * margin
            scale = min(avail_w / img_width, avail_h / img_height)
            draw_w = img_width * scale
            draw_h = img_height * scale
            x = (width - draw_w) / 2
            y = (height - draw_h) / 2
            c.drawImage(img, x, y, width=draw_w, height=draw_h)
            c.showPage()

        # Page 2: Metadata
        title = metadata.get("title", "Unknown Title")
        author = metadata.get("author", "Unknown Author")
        narrator = metadata.get("narrator", "Unknown Narrator")
        duration = metadata.get("duration", 0)

        y_pos = height - inch
        c.setFont("Helvetica-Bold", 24)
        c.drawString(inch, y_pos, title)
        y_pos -= 0.5 * inch
        c.setFont("Helvetica", 14)
        c.drawString(inch, y_pos, f"Author: {author}")
        y_pos -= 0.3 * inch
        c.drawString(inch, y_pos, f"Narrator: {narrator}")
        y_pos -= 0.3 * inch
        c.drawString(inch, y_pos, f"Duration: {format_duration(duration)}")
        c.showPage()

        # Page 3: Chapters (if available)
        chapters = metadata.get("chapters", [])
        if chapters:
            y_pos = height - inch
            c.setFont("Helvetica-Bold", 18)
            c.drawString(inch, y_pos, "Chapters")
            y_pos -= 0.4 * inch
            c.setFont("Helvetica", 12)
            for i, chapter in enumerate(chapters, 1):
                c.drawString(inch, y_pos, f"{i}. {chapter}")
                y_pos -= 0.3 * inch
                if y_pos < inch:
                    c.showPage()
                    y_pos = height - inch

        c.save()
        return output_path

    except Exception as e:
        raise PDFGenerationError(f"Failed to generate PDF: {e}")


def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS."""
    if not seconds:
        return "00:00:00"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
