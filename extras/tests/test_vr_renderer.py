"""Tests for the VRRenderer."""

from __future__ import annotations

import pytest
from src.vr_renderer import VRRenderer
from src.ticker import Ticker
from src.panels import TickerPanel, TickerBoard
from src.vr_scene import VRScene


class TestVRRendererCreation:
    """Tests for VRRenderer creation and initialization."""

    def test_create_default_renderer(self):
        renderer = VRRenderer()
        assert renderer.frame_rate == 60.0
        assert renderer.resolution == (1920, 1080)
        assert renderer.is_rendering is False
        assert renderer.scene is None

    def test_create_renderer_with_custom_params(self):
        renderer = VRRenderer(frame_rate=120.0, resolution=(2560, 1440))
        assert renderer.frame_rate == 120.0
        assert renderer.resolution == (2560, 1440)

    def test_create_renderer_with_scene(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        assert renderer.scene == scene


class TestVRRendererSceneManagement:
    """Tests for scene management in VRRenderer."""

    def test_set_scene(self):
        renderer = VRRenderer()
        scene = VRScene(name="Test Scene")
        renderer.set_scene(scene)
        assert renderer.scene == scene

    def test_get_scene(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        assert renderer.scene == scene

    def test_get_scene_not_set(self):
        renderer = VRRenderer()
        assert renderer.scene is None

    def test_set_scene_none(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        renderer.set_scene(None)
        assert renderer.scene is None


class TestVRRendererRendering:
    """Tests for rendering functionality."""

    def test_render_ticker(self):
        ticker = Ticker(symbol="AAPL", price=100.0, change=5.0)
        renderer = VRRenderer()
        result = renderer.render_ticker(ticker)
        assert result["symbol"] == "AAPL"
        assert result["price"] == 100.0
        assert result["change"] == 5.0
        assert result["color"] == (0.0, 1.0, 0.0)  # Green for positive change
        assert result["background_color"] == (0.0, 0.5, 0.0)  # Dark green

    def test_render_ticker_down(self):
        ticker = Ticker(symbol="GOOGL", price=200.0, change=-5.0)
        renderer = VRRenderer()
        result = renderer.render_ticker(ticker)
        assert result["color"] == (1.0, 0.0, 0.0)  # Red for negative change
        assert result["background_color"] == (0.5, 0.0, 0.0)  # Dark red

    def test_render_panel(self):
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker=ticker, position=(1.0, 2.0, 3.0))
        renderer = VRRenderer()
        result = renderer.render_panel(panel)
        assert result["ticker"]["symbol"] == "AAPL"
        assert result["position"] == [1.0, 2.0, 3.0]
        assert result["size"] == [1.0, 0.6, 0.05]

    def test_render_board(self):
        board = TickerBoard(name="Test Board")
        renderer = VRRenderer()
        result = renderer.render_board(board)
        assert result["name"] == "Test Board"
        assert result["panels"] == []

    def test_render_board_with_panels(self):
        board = TickerBoard(name="Test Board")
        ticker = Ticker(symbol="AAPL", price=100.0)
        panel = TickerPanel(ticker=ticker)
        board.add_panel(panel)
        renderer = VRRenderer()
        result = renderer.render_board(board)
        assert len(result["panels"]) == 1
        assert result["panels"][0]["ticker"]["symbol"] == "AAPL"

    def test_render_scene_with_no_scene(self):
        renderer = VRRenderer()
        result = renderer.render_scene()
        assert result == {}

    def test_render_scene_with_scene(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        result = renderer.render_scene()
        assert result["name"] == "Test Scene"
        assert result["is_rendering"] is False
        assert result["frame_rate"] == 60.0
        assert result["resolution"] == [1920, 1080]

    def test_render_scene_with_tickers(self):
        scene = VRScene(name="Test Scene")
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        renderer = VRRenderer(scene=scene)
        result = renderer.render_scene()
        assert len(result["tickers"]) == 1
        assert result["tickers"][0]["symbol"] == "AAPL"

    def test_render_scene_with_boards(self):
        scene = VRScene(name="Test Scene")
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        renderer = VRRenderer(scene=scene)
        result = renderer.render_scene()
        assert "Test Board" in result["boards"]

    def test_render_scene_with_tickers_and_boards(self):
        scene = VRScene(name="Test Scene")
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        renderer = VRRenderer(scene=scene)
        result = renderer.render_scene()
        assert len(result["tickers"]) == 1
        assert "Test Board" in result["boards"]

    def test_start_rendering(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        renderer.start_rendering()
        assert renderer.is_rendering is True

    def test_stop_rendering(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        renderer.start_rendering()
        renderer.stop_rendering()
        assert renderer.is_rendering is False

    def test_start_rendering_multiple_times(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene)
        renderer.start_rendering()
        renderer.start_rendering()  # Should not raise
        assert renderer.is_rendering is True

    def test_stop_rendering_without_start(self):
        renderer = VRRenderer()
        renderer.stop_rendering()  # Should not raise
        assert renderer.is_rendering is False


class TestVRRendererStatus:
    """Tests for renderer status reporting."""

    def test_get_render_status_no_scene(self):
        renderer = VRRenderer()
        status = renderer.get_render_status()
        assert status["is_rendering"] is False
        assert status["frame_rate"] == 60.0
        assert status["resolution"] == [1920, 1080]
        assert status["scene_name"] is None
        assert status["ticker_count"] == 0
        assert status["board_count"] == 0

    def test_get_render_status_with_scene(self):
        scene = VRScene(name="Test Scene")
        scene.add_ticker(Ticker(symbol="AAPL", price=100.0))
        board = TickerBoard(name="Test Board")
        scene.add_board(board)
        renderer = VRRenderer(scene=scene)
        renderer.start_rendering()
        status = renderer.get_render_status()
        assert status["is_rendering"] is True
        assert status["frame_rate"] == 60.0
        assert status["resolution"] == [1920, 1080]
        assert status["scene_name"] == "Test Scene"
        assert status["ticker_count"] == 1
        assert status["board_count"] == 1


class TestVRRendererSerialization:
    """Tests for VRRenderer serialization."""

    def test_renderer_to_dict(self):
        scene = VRScene(name="Test Scene")
        renderer = VRRenderer(scene=scene, frame_rate=120.0, resolution=(2560, 1440))
        data = renderer.render_scene()
        assert data["name"] == "Test Scene"
        assert data["frame_rate"] == 120.0
        assert data["resolution"] == [2560, 1440]
        assert data["is_rendering"] is False

    def test_renderer_equality(self):
        renderer1 = VRRenderer(frame_rate=60.0, resolution=(1920, 1080))
        renderer2 = VRRenderer(frame_rate=60.0, resolution=(1920, 1080))
        assert renderer1 == renderer2

    def test_renderer_inequality(self):
        renderer1 = VRRenderer(frame_rate=60.0, resolution=(1920, 1080))
        renderer2 = VRRenderer(frame_rate=120.0, resolution=(2560, 1440))
        assert renderer1 != renderer2
