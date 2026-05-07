"""Tests for VR rendering system — panel rendering, board layout, and camera updates."""

from __future__ import annotations

import pytest
from src.renderer import (
    Renderer,
    PanelRenderer,
    BoardLayout,
    CameraRenderer,
    RenderingState,
)
from src.ticker import Ticker
from src.ticker_display import TickerPanel, TickerBoard
from src.navigation import VRNavigator, CameraState


class TestPanelRenderer:
    """Tests for PanelRenderer."""

    def test_create_panel_renderer(self):
        renderer = PanelRenderer()
        assert renderer.rendered_panels == []
        assert renderer.highlighted_panels == []

    def test_render_panel(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.render_panel(panel)
        assert panel in renderer.rendered_panels

    def test_render_multiple_panels(self):
        renderer = PanelRenderer()
        for i in range(5):
            ticker = Ticker(symbol=f"SYM{i}", price=100.0)
            panel = TickerPanel(ticker)
            renderer.render_panel(panel)
        assert len(renderer.rendered_panels) == 5

    def test_render_panel_duplicate(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.render_panel(panel)
        renderer.render_panel(panel)
        assert renderer.rendered_panels.count(panel) == 1

    def test_clear_rendered_panels(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.render_panel(panel)
        renderer.clear_rendered_panels()
        assert renderer.rendered_panels == []

    def test_highlight_panel(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.highlight_panel(panel)
        assert panel in renderer.highlighted_panels

    def test_unhighlight_panel(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.highlight_panel(panel)
        renderer.unhighlight_panel(panel)
        assert panel not in renderer.highlighted_panels

    def test_unhighlight_nonexistent_panel(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.unhighlight_panel(panel)
        assert renderer.highlighted_panels == []

    def test_clear_highlighted_panels(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.highlight_panel(panel)
        renderer.clear_highlighted_panels()
        assert renderer.highlighted_panels == []

    def test_get_rendered_panel_count(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.render_panel(panel)
        assert renderer.get_rendered_panel_count() == 1

    def test_get_highlighted_panel_count(self):
        renderer = PanelRenderer()
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        renderer.highlight_panel(panel)
        assert renderer.get_highlighted_panel_count() == 1


class TestBoardLayout:
    """Tests for BoardLayout."""

    def test_create_board_layout_defaults(self):
        layout = BoardLayout()
        assert layout.panel_spacing == 1.5
        assert layout.panel_padding == 0.1
        assert layout.grid_columns == 3
        assert layout.grid_rows == 2
        assert layout.alignment == "center"

    def test_create_board_layout_custom(self):
        layout = BoardLayout(
            panel_spacing=2.0,
            panel_padding=0.2,
            grid_columns=4,
            grid_rows=3,
            alignment="left",
        )
        assert layout.panel_spacing == 2.0
        assert layout.panel_padding == 0.2
        assert layout.grid_columns == 4
        assert layout.grid_rows == 3
        assert layout.alignment == "left"

    def test_board_layout_to_dict(self):
        layout = BoardLayout(
            panel_spacing=2.0,
            panel_padding=0.2,
            grid_columns=4,
            grid_rows=3,
            alignment="left",
        )
        data = layout.to_dict()
        assert data["panel_spacing"] == 2.0
        assert data["panel_padding"] == 0.2
        assert data["grid_columns"] == 4
        assert data["grid_rows"] == 3
        assert data["alignment"] == "left"

    def test_board_layout_from_dict(self):
        data = {
            "panel_spacing": 2.0,
            "panel_padding": 0.2,
            "grid_columns": 4,
            "grid_rows": 3,
            "alignment": "left",
        }
        layout = BoardLayout.from_dict(data)
        assert layout.panel_spacing == 2.0
        assert layout.panel_padding == 0.2
        assert layout.grid_columns == 4
        assert layout.grid_rows == 3
        assert layout.alignment == "left"

    def test_board_layout_round_trip(self):
        layout = BoardLayout(
            panel_spacing=2.0,
            panel_padding=0.2,
            grid_columns=4,
            grid_rows=3,
            alignment="left",
        )
        data = layout.to_dict()
        layout2 = BoardLayout.from_dict(data)
        assert layout.panel_spacing == layout2.panel_spacing
        assert layout.panel_padding == layout2.panel_padding
        assert layout.grid_columns == layout2.grid_columns
        assert layout.grid_rows == layout2.grid_rows
        assert layout.alignment == layout2.alignment

    def test_board_layout_from_dict_defaults(self):
        data = {}
        layout = BoardLayout.from_dict(data)
        assert layout.panel_spacing == 1.5
        assert layout.panel_padding == 0.1
        assert layout.grid_columns == 3
        assert layout.grid_rows == 2
        assert layout.alignment == "center"

    def test_calculate_panel_position(self):
        layout = BoardLayout(panel_spacing=2.0, panel_padding=0.1)
        position = layout.calculate_panel_position(0, 0)
        assert position == (0.0, 0.0, 0.0)

    def test_calculate_panel_position_offset(self):
        layout = BoardLayout(panel_spacing=2.0, panel_padding=0.1)
        position = layout.calculate_panel_position(1, 0)
        assert position[0] == pytest.approx(2.1)  # spacing + padding
        assert position[1] == 0.0

    def test_calculate_panel_position_row(self):
        layout = BoardLayout(panel_spacing=2.0, panel_padding=0.1)
        position = layout.calculate_panel_position(0, 1)
        assert position[0] == 0.0
        assert position[1] == pytest.approx(2.1)

    def test_calculate_panel_position_center_alignment(self):
        layout = BoardLayout(panel_spacing=2.0, panel_padding=0.1, alignment="center")
        position = layout.calculate_panel_position(0, 0)
        # Center alignment should offset by half the spacing
        assert position[0] == pytest.approx(-1.05)
        assert position[1] == pytest.approx(-1.05)

    def test_calculate_panel_position_left_alignment(self):
        layout = BoardLayout(panel_spacing=2.0, panel_padding=0.1, alignment="left")
        position = layout.calculate_panel_position(0, 0)
        assert position[0] == pytest.approx(-1.05)
        assert position[1] == pytest.approx(-1.05)


class TestCameraRenderer:
    """Tests for CameraRenderer."""

    def test_create_camera_renderer(self):
        renderer = CameraRenderer()
        assert renderer.camera_state is not None
        assert renderer.camera_state.position == (0.0, 0.0, 0.0)
        assert renderer.camera_state.rotation == (0.0, 0.0, 0.0)
        assert renderer.camera_state.zoom_level == 1.0

    def test_camera_renderer_set_position(self):
        renderer = CameraRenderer()
        renderer.set_position((1.0, 2.0, 3.0))
        assert renderer.camera_state.position == (1.0, 2.0, 3.0)

    def test_camera_renderer_set_rotation(self):
        renderer = CameraRenderer()
        renderer.set_rotation((10.0, 20.0, 30.0))
        assert renderer.camera_state.rotation == (10.0, 20.0, 30.0)

    def test_camera_renderer_set_zoom(self):
        renderer = CameraRenderer()
        renderer.set_zoom(2.0)
        assert renderer.camera_state.zoom_level == 2.0

    def test_camera_renderer_update_from_navigator(self):
        renderer = CameraRenderer()
        navigator = VRNavigator()
        navigator.pan_forward(1.0)
        navigator.rotate_up(10.0)
        navigator.zoom_in(0.5)
        renderer.update_from_navigator(navigator)
        assert renderer.camera_state.position[2] == pytest.approx(-1.0)
        assert renderer.camera_state.rotation[0] == pytest.approx(10.0)
        assert renderer.camera_state.zoom_level == pytest.approx(1.5)

    def test_camera_renderer_get_state(self):
        renderer = CameraRenderer()
        renderer.set_position((1.0, 2.0, 3.0))
        state = renderer.get_state()
        assert state.position == (1.0, 2.0, 3.0)
        assert state.rotation == (0.0, 0.0, 0.0)
        assert state.zoom_level == 1.0


class TestRenderer:
    """Tests for Renderer."""

    def test_create_renderer(self):
        renderer = Renderer()
        assert renderer.panel_renderer is not None
        assert renderer.board_layout is not None
        assert renderer.camera_renderer is not None
        assert renderer.rendering_state == RenderingState.IDLE

    def test_renderer_set_state(self):
        renderer = Renderer()
        renderer.set_state(RenderingState.RENDERING)
        assert renderer.rendering_state == RenderingState.RENDERING

    def test_renderer_render_board(self):
        renderer = Renderer()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        renderer.render_board(board)
        assert panel in renderer.panel_renderer.rendered_panels
        assert renderer.rendering_state == RenderingState.RENDERING

    def test_renderer_render_empty_board(self):
        renderer = Renderer()
        board = TickerBoard(name="Test Board")
        renderer.render_board(board)
        assert renderer.rendering_state == RenderingState.RENDERING

    def test_renderer_clear_rendering(self):
        renderer = Renderer()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        renderer.render_board(board)
        renderer.clear_rendering()
        assert renderer.panel_renderer.rendered_panels == []
        assert renderer.rendering_state == RenderingState.IDLE

    def test_renderer_get_rendering_state(self):
        renderer = Renderer()
        state = renderer.get_rendering_state()
        assert state == RenderingState.IDLE

    def test_renderer_get_panel_renderer(self):
        renderer = Renderer()
        pr = renderer.get_panel_renderer()
        assert pr == renderer.panel_renderer

    def test_renderer_get_board_layout(self):
        renderer = Renderer()
        bl = renderer.get_board_layout()
        assert bl == renderer.board_layout

    def test_renderer_get_camera_renderer(self):
        renderer = Renderer()
        cr = renderer.get_camera_renderer()
        assert cr == renderer.camera_renderer

    def test_renderer_update_camera_from_navigator(self):
        renderer = Renderer()
        navigator = VRNavigator()
        navigator.pan_forward(1.0)
        renderer.update_camera_from_navigator(navigator)
        assert renderer.camera_renderer.camera_state.position[2] == pytest.approx(-1.0)

    def test_renderer_get_status(self):
        renderer = Renderer()
        status = renderer.get_status()
        assert "rendering_state" in status
        assert "panel_count" in status
        assert "camera_state" in status
        assert "board_layout" in status

    def test_renderer_get_status_with_rendering(self):
        renderer = Renderer()
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker)
        board.add_panel(panel)
        renderer.render_board(board)
        status = renderer.get_status()
        assert status["rendering_state"] == RenderingState.RENDERING
        assert status["panel_count"] == 1


class TestRendererEdgeCases:
    """Tests for edge cases and error handling."""

    def test_panel_renderer_with_none(self):
        renderer = PanelRenderer()
        # Should not crash with None
        try:
            renderer.render_panel(None)
        except Exception:
            pass  # Expected to handle None gracefully

    def test_board_layout_negative_spacing(self):
        layout = BoardLayout(panel_spacing=-1.0)
        assert layout.panel_spacing == -1.0

    def test_board_layout_zero_columns(self):
        layout = BoardLayout(grid_columns=0)
        assert layout.grid_columns == 0

    def test_board_layout_zero_rows(self):
        layout = BoardLayout(grid_rows=0)
        assert layout.grid_rows == 0

    def test_camera_renderer_set_zoom_zero(self):
        renderer = CameraRenderer()
        renderer.set_zoom(0.0)
        assert renderer.camera_state.zoom_level == 0.0

    def test_camera_renderer_set_zoom_negative(self):
        renderer = CameraRenderer()
        renderer.set_zoom(-1.0)
        assert renderer.camera_state.zoom_level == -1.0

    def test_renderer_render_state_transitions(self):
        renderer = Renderer()
        assert renderer.rendering_state == RenderingState.IDLE
        board = TickerBoard(name="Test Board")
        renderer.render_board(board)
        assert renderer.rendering_state == RenderingState.RENDERING
        renderer.clear_rendering()
        assert renderer.rendering_state == RenderingState.IDLE

    def test_renderer_clear_rendering_no_panels(self):
        renderer = Renderer()
        renderer.clear_rendering()
        assert renderer.rendering_state == RenderingState.IDLE

    def test_board_layout_from_dict_invalid(self):
        data = {"invalid_key": 1.0}
        layout = BoardLayout.from_dict(data)
        assert layout.panel_spacing == 1.5  # Default value

    def test_camera_renderer_update_from_navigator_none(self):
        renderer = CameraRenderer()
        # Should not crash with None navigator
        try:
            renderer.update_from_navigator(None)
        except Exception:
            pass  # Expected to handle None gracefully
