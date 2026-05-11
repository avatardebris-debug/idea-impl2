"""Unit tests for ExportEngine: registration, dispatch, default/custom paths, errors."""

import pytest
from multi_format_export_engine.export_engine import ExportEngine
from multi_format_export_engine.models import Manuscript


class MockExporter:
    """Minimal mock exporter that records calls."""

    def __init__(self):
        self.calls = []

    def export(self, manuscript, output_path="output.epub", **options):
        self.calls.append({
            "manuscript": manuscript,
            "output_path": output_path,
            "options": options,
        })
        return output_path


class TestExportEngine:
    def test_initial_state(self):
        engine = ExportEngine()
        assert engine._exporters == {}

    def test_register_exporter(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        assert "epub" in engine._exporters
        assert engine._exporters["epub"] is exporter

    def test_register_multiple_exporters(self):
        engine = ExportEngine()
        epub = MockExporter()
        pdf = MockExporter()
        engine.register_exporter("epub", epub)
        engine.register_exporter("pdf", pdf)
        assert len(engine._exporters) == 2
        assert "epub" in engine._exporters
        assert "pdf" in engine._exporters

    def test_register_overwrites(self):
        engine = ExportEngine()
        e1 = MockExporter()
        e2 = MockExporter()
        engine.register_exporter("epub", e1)
        engine.register_exporter("epub", e2)
        assert engine._exporters["epub"] is e2

    def test_register_case_insensitive(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("EPUB", exporter)
        assert "epub" in engine._exporters

    def test_export_calls_registered_exporter(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Test Book")
        engine.export("epub", manuscript)
        assert len(exporter.calls) == 1
        assert exporter.calls[0]["manuscript"] is manuscript

    def test_export_default_output_path(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="My Book")
        engine.export("epub", manuscript)
        # Default path uses manuscript title
        assert exporter.calls[0]["output_path"] == "My_Book.epub"

    def test_export_default_path_with_spaces(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("pdf", exporter)
        manuscript = Manuscript(title="My Cool Book")
        engine.export("pdf", manuscript)
        assert exporter.calls[0]["output_path"] == "My_Cool_Book.pdf"

    def test_export_custom_output_path(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Test")
        engine.export("epub", manuscript, output_path="custom.epub")
        assert exporter.calls[0]["output_path"] == "custom.epub"

    def test_export_passes_options(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("pdf", exporter)
        manuscript = Manuscript(title="Test")
        engine.export("pdf", manuscript, margins={"top": "2in"}, font_size=12)
        assert exporter.calls[0]["options"]["margins"] == {"top": "2in"}
        assert exporter.calls[0]["options"]["font_size"] == 12

    def test_export_unsupported_format_raises(self):
        engine = ExportEngine()
        manuscript = Manuscript(title="Test")
        with pytest.raises(ValueError, match="Unsupported format 'docx'"):
            engine.export("docx", manuscript)

    def test_export_unsupported_format_lists_available(self):
        engine = ExportEngine()
        engine.register_exporter("epub", MockExporter())
        manuscript = Manuscript(title="Test")
        with pytest.raises(ValueError, match="Available formats: \\['epub'\\]"):
            engine.export("pdf", manuscript)

    def test_export_format_case_insensitive(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Test")
        engine.export("EPUB", manuscript)
        assert len(exporter.calls) == 1

    def test_export_returns_output_path(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Test")
        result = engine.export("epub", manuscript, output_path="out.epub")
        assert result == "out.epub"

    def test_export_without_output_path_uses_title(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Hello World")
        result = engine.export("epub", manuscript)
        assert result == "Hello_World.epub"

    def test_export_without_output_path_uses_default_name(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="")
        result = engine.export("epub", manuscript)
        # Empty title produces empty base name, so result is ".epub"
        assert result == ".epub"

    def test_export_with_empty_manuscript(self):
        engine = ExportEngine()
        exporter = MockExporter()
        engine.register_exporter("epub", exporter)
        manuscript = Manuscript(title="Empty")
        engine.export("epub", manuscript)
        assert len(exporter.calls) == 1
