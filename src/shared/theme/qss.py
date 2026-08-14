"""QSS loading and token substitution for the theme package."""
from pathlib import Path as _Path
import sys
from shared import palette
from shared.paths import app_data_dir

from typing import Dict

from PyQt6.QtGui import QColor

from shared.theme.core import _shades  # type: ignore


def _qss_styles_dir() -> _Path:
    """The directory that ships with the app, containing default.qss."""
    bundled = getattr(sys, "_MEIPASS", None)
    if bundled:
        return _Path(bundled) / "assets" / "styles"
    return _Path(__file__).resolve().parent.parent.parent / "assets" / "styles"


def _qss_user_path() -> _Path:
    """The user's custom QSS file in the app data directory."""
    return app_data_dir() / "custom.qss"


def load_custom_qss() -> str:
    """Load the user's custom QSS, falling back to the shipped default.

    Priority:  custom.qss in app data  >  assets/styles/default.qss  >  ""
    The file is read as UTF-8 and a %(key)s substitution is performed so the
    QSS can reference the app's accent colour, background, etc.
    """
    user = _qss_user_path()
    default = _qss_styles_dir() / "default.qss"

    path = user if user.exists() else default
    if not path.exists():
        return ""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # Substitute %(var)s tokens with live values from the current palette.
    tokens: Dict[str, str] = {
        "accent": _shades.get("accent", "#0078d7"),
        "accent_text": _shades.get("accent_text", "#ffffff"),
        "window": _shades.get("window", "#f0f0f0"),
        "text": _shades.get("text", "#000000"),
        "text_soft": _shades.get("text_soft", "#606060"),
        "border": _shades.get("border", "#c0c0c0"),
        "sidebar": _shades.get("sidebar", "#e8e8e8"),
        "danger": _shades.get("danger", "#c42b1c"),
        "cover": _shades.get("cover", "#ffffff"),
        "star": _shades.get("star", "#e6a800"),
    }
    try:
        return raw % tokens
    except (KeyError, TypeError):
        return raw


def apply_custom_qss(app) -> None:
    qss = load_custom_qss()
    if qss:
        app.setStyleSheet(qss)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
