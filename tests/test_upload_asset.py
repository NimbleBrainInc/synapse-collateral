"""Unit tests for upload_asset — up-front image validation."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from mcp_collateral.workspace import Workspace

# 1x1 red PNG
VALID_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAj"
    "CB0C8AAAAASUVORK5CYII="
)

# 1x1 white JPEG
VALID_JPG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHR"
    "ofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgy"
    "IRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMj"
    "L/wAARCAABAAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL"
    "/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0f"
    "AkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1"
    "dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1N"
    "XW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiigD//2Q=="
)


@pytest.fixture()
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Workspace:
    monkeypatch.setattr("mcp_collateral.store.BASE_DIR", tmp_path)
    monkeypatch.setattr("mcp_collateral.store.ASSETS_DIR", tmp_path / "assets")
    monkeypatch.setattr("mcp_collateral.store.FONTS_DIR", tmp_path / "fonts")
    monkeypatch.setattr("mcp_collateral.store.TEMPLATES_DIR", tmp_path / "templates")
    monkeypatch.setattr("mcp_collateral.store.DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr("mcp_collateral.store.COMPILE_DIR", tmp_path / "_compile")

    from mcp_collateral import store

    store._ensure_dirs()
    return Workspace()


class TestUploadAssetValidation:
    """Image bytes are decoded at upload; corruption fails here."""

    def test_valid_png_accepted(self, workspace: Workspace) -> None:
        result = workspace.upload_asset(VALID_PNG_B64, "logo.png")
        assert result["filename"] == "logo.png"
        assert Path(result["path"]).exists()

    def test_valid_jpg_accepted(self, workspace: Workspace) -> None:
        result = workspace.upload_asset(VALID_JPG_B64, "photo.jpg")
        assert result["filename"] == "photo.jpg"
        assert Path(result["path"]).exists()

    def test_truncated_png_rejected(self, workspace: Workspace) -> None:
        raw = base64.b64decode(VALID_PNG_B64)
        truncated = base64.b64encode(raw[:30]).decode()
        with pytest.raises(ValueError, match="image validation"):
            workspace.upload_asset(truncated, "bad.png")

    def test_corrupt_deflate_png_rejected(self, workspace: Workspace) -> None:
        """The actual failure mode from the original bug: corrupt IDAT."""
        raw = bytearray(base64.b64decode(VALID_PNG_B64))
        idx = raw.find(b"IDAT")
        # Flip bytes inside the deflate payload
        for i in range(idx + 4, idx + 12):
            raw[i] ^= 0xFF
        corrupt = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(ValueError, match="image validation"):
            workspace.upload_asset(corrupt, "corrupt.png")

    def test_garbage_bytes_rejected_for_image_ext(self, workspace: Workspace) -> None:
        garbage = base64.b64encode(b"not an image at all").decode()
        with pytest.raises(ValueError, match="image validation"):
            workspace.upload_asset(garbage, "fake.png")

    def test_corrupt_bytes_do_not_reach_disk(self, workspace: Workspace) -> None:
        """Rejected assets must not leave partial state."""
        garbage = base64.b64encode(b"junk").decode()
        with pytest.raises(ValueError):
            workspace.upload_asset(garbage, "fake.jpg")
        assert workspace.list_assets() == []

    def test_valid_svg_accepted(self, workspace: Workspace) -> None:
        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
        encoded = base64.b64encode(svg).decode()
        result = workspace.upload_asset(encoded, "icon.svg")
        assert result["filename"] == "icon.svg"

    def test_malformed_svg_rejected(self, workspace: Workspace) -> None:
        encoded = base64.b64encode(b"<svg><unclosed").decode()
        with pytest.raises(ValueError, match="well-formed SVG"):
            workspace.upload_asset(encoded, "bad.svg")

    def test_non_image_extension_passes_through(self, workspace: Workspace) -> None:
        """Non-image assets aren't validated as images."""
        encoded = base64.b64encode(b"arbitrary blob").decode()
        result = workspace.upload_asset(encoded, "data.bin")
        assert result["filename"] == "data.bin"
