"""Implementation for the Settings page, split out to reduce file size.
"""
import sys
from html import escape
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from shared import config, texts
from shared.icons import dress, logo, with_flag
from shared.palette import has_a_desktop
from shared.paths import cover_cache_dir
from shared.texts import text
from shared.paths import project_version
from shared.theme import (
    DEFAULT_THEME,
    THEMES,
    colours,
    current_seed,
    family,
    theme_preview_pixmap,
)

APP_VERSION = project_version()

LOGO_SIZE = 72
COPYRIGHT = "Copyright (C) 2026 farukylmz0550"
SOURCE_URL = "https://github.com/farukylmz0550/KatipCelebi"


def cache_size_mb() -> float:
    total = 0
    for path in cover_cache_dir().glob("*"):
        try:
            total += path.stat().st_size
        except OSError:
            continue
    return total / (1024 * 1024)


class SettingsPage(QWidget):
    """Everything about the app rather than about the books."""

    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)
    folder_changed = pyqtSignal()

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._build()
        self.refresh()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(28, 24, 28, 20)
        column.setSpacing(10)

        title = QLabel(text("nav_settings"))
        title.setObjectName("pageTitle")
        column.addWidget(title)

        # --- where the books live
        self._heading(column, "settings_where")
        self.folder_label = QLabel()
        self.folder_label.setObjectName("statusLabel")
        self.folder_label.setWordWrap(True)
        self.folder_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        column.addWidget(self.folder_label)
        self.move_button = dress(QPushButton(text("settings_move")), "settings_move")
        self.move_button.clicked.connect(self.change_folder)
        column.addWidget(self.move_button, 0, Qt.AlignmentFlag.AlignLeft)

        # --- how it looks
        self._heading(column, "settings_theme")
        theme_row = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.setIconSize(QSize(20, 20))
        for name in THEMES:
            self.theme_combo.addItem(
                theme_preview_pixmap(name),
                text("theme_" + name.replace("-", "_")),
                name,
            )
        self.theme_combo.activated.connect(self._pick_theme)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        column.addLayout(theme_row)

        # --- language
        self._heading(column, "settings_language")
        lang_row = QHBoxLayout()
        self.language_combo = QComboBox()
        for code, name in texts.available():
            self.language_combo.addItem(with_flag(code, name), code)
        index = self.language_combo.findData(texts.current())
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.activated.connect(self._pick_language)
        lang_row.addWidget(self.language_combo)
        lang_row.addStretch(1)
        column.addLayout(lang_row)

        self._build_seed(column)

        # --- the covers we have downloaded
        self._heading(column, "settings_cache")
        cache_row = QHBoxLayout()
        self.cache_label = QLabel()
        self.cache_label.setObjectName("statusLabel")
        cache_row.addWidget(self.cache_label)
        self.cache_button = dress(
            QPushButton(text("settings_clear_cache")),
            "settings_clear_cache",
        )
        self.cache_button.clicked.connect(self.clear_cache)
        cache_row.addWidget(self.cache_button)
        cache_row.addStretch(1)
        column.addLayout(cache_row)

        # --- custom style sheet
        self._heading(column, "settings_qss")
        qss_row = QHBoxLayout()
        self.qss_label = QLabel()
        self.qss_label.setObjectName("statusLabel")
        self.qss_label.setWordWrap(True)
        qss_row.addWidget(self.qss_label, 1)
        self.qss_edit_button = QPushButton(text("settings_qss_edit"))
        self.qss_edit_button.clicked.connect(self._open_qss)
        qss_row.addWidget(self.qss_edit_button)
        self.qss_reload_button = QPushButton(text("settings_qss_reload"))
        self.qss_reload_button.clicked.connect(self._reload_qss)
        qss_row.addWidget(self.qss_reload_button)
        column.addLayout(qss_row)

        # --- what this is
        self._heading(column, "settings_about")
        about_row = QHBoxLayout()
        about_row.setSpacing(14)

        mark = QLabel()
        mark.setPixmap(logo(LOGO_SIZE))
        mark.setAlignment(Qt.AlignmentFlag.AlignTop)
        about_row.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)

        self.about_label = QLabel(self._about_text())
        self.about_label.setWordWrap(True)
        self.about_label.setTextFormat(Qt.TextFormat.RichText)
        self.about_label.setOpenExternalLinks(True)
        self.about_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        about_row.addWidget(self.about_label, 1)
        column.addLayout(about_row)

        self.update_label = QLabel()
        self.update_label.setObjectName("statusLabel")
        self.update_label.setWordWrap(True)
        column.addWidget(self.update_label)

        update_row = QHBoxLayout()
        self.update_button = QPushButton(text("settings_check_updates"))
        self.update_button.clicked.connect(self._check_updates)
        update_row.addWidget(self.update_button)
        update_row.addStretch(1)
        column.addLayout(update_row)
        column.addStretch(1)

    def _build_seed(self, column) -> None:
        self._colour_heading = self._heading(column, "settings_colour")
        self.colour_label = QLabel()
        self.colour_label.setObjectName("statusLabel")
        self.colour_label.setWordWrap(True)
        column.addWidget(self.colour_label)

    def _about_text(self) -> str:
        return (
            "<b>{0} {1}</b><br>{2}<br><br>" '<a href="{3}" style="color: {4}">{3}</a>'
        ).format(
            escape(text("app_name")),
            escape(APP_VERSION),
            escape(COPYRIGHT),
            escape(SOURCE_URL),
            colours()["accent"],
        )

    def _heading(self, column, key: str) -> QLabel:
        label = QLabel(text(key))
        label.setObjectName("detailFieldLabel")
        column.addWidget(label)
        return label

    def refresh(self) -> None:
        self.folder_label.setText(str(self.main_window.library.folder))
        index = self.theme_combo.findData(config.theme())
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(max(index, 0))
        self.theme_combo.blockSignals(False)
        self.cache_label.setText(text("settings_cache_size").format(mb=cache_size_mb()))
        is_built_in = family(config.theme()) in {"default", "contrast"}
        self._colour_heading.setVisible(is_built_in)
        self.colour_label.setVisible(is_built_in)
        if is_built_in:
            self._show_colour()
        self.about_label.setText(self._about_text())
        self._show_qss()
        self._update_status()

    def _pick_theme(self, *_args) -> None:
        name = self.theme_combo.currentData() or DEFAULT_THEME
        if not config.set_theme(name):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.main_window.library.path),
            )
            self.refresh()
            return
        self.theme_changed.emit(name)

    def _pick_language(self, *_args) -> None:
        code = self.language_combo.currentData() or texts.BASE
        if not config.set_language(code):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.main_window.library.path),
            )
            return
        self.language_changed.emit(code)

    def _show_colour(self) -> None:
        seed = current_seed()
        key = (
            "settings_colour_from_desktop" if has_a_desktop() else "settings_colour_own"
        )
        self.colour_label.setText(text(key).format(colour=seed))

    def _show_qss(self) -> None:
        from shared.theme import _qss_styles_dir, _qss_user_path

        user = _qss_user_path()
        if user.exists():
            self.qss_label.setText(str(user))
        else:
            default = _qss_styles_dir() / "default.qss"
            self.qss_label.setText(str(default))

    def _update_status(self) -> None:
        from shared.settings_helpers import UpdateThread

        self._update_thread = UpdateThread(APP_VERSION)
        self._update_thread.result.connect(
            lambda has, latest, url: self._on_update_result(has, latest, url, show_message=False)
        )
        self._update_thread.start()

    def _check_updates(self) -> None:
        if getattr(self, "_update_thread", None) and self._update_thread.isRunning():
            return
        self._update_thread = None
        from shared.settings_helpers import UpdateThread

        self._update_thread = UpdateThread(APP_VERSION)
        self._update_thread.result.connect(
            lambda has, latest, url: self._on_update_result(has, latest, url, show_message=True)
        )
        self._update_thread.start()

    def _on_update_result(self, has_update: bool, latest: str, release_url: str, show_message: bool) -> None:
        if has_update:
            self.update_label.setText(
                text("settings_update_available").format(latest=latest, url=release_url)
            )
            if show_message:
                QMessageBox.information(
                    self,
                    text("update_available_title"),
                    text("update_available_message").format(latest=latest, url=release_url),
                )
        else:
            self.update_label.setText(text("settings_update_latest"))
            if show_message:
                QMessageBox.information(
                    self,
                    text("up_to_date_title"),
                    text("up_to_date_message"),
                )

    def _open_qss(self) -> None:
        import subprocess

        from shared.theme import _qss_styles_dir, _qss_user_path

        user = _qss_user_path()
        if not user.exists():
            default = _qss_styles_dir() / "default.qss"
            if default.exists():
                user.parent.mkdir(parents=True, exist_ok=True)
                user.write_text(default.read_text(encoding="utf-8"), encoding="utf-8")
        if sys.platform == "win32":
            subprocess.Popen(["notepad", str(user)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(user)])
        else:
            subprocess.Popen(["xdg-open", str(user)])
        self._show_qss()

    def _reload_qss(self) -> None:
        from PyQt6.QtWidgets import QApplication

        from shared.theme import apply_theme

        apply_theme(QApplication.instance(), config.theme())
        from shared.icons import redress

        redress(self.main_window)

    def clear_cache(self) -> None:
        removed = 0
        for path in cover_cache_dir().glob("*"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        self.refresh()
        QMessageBox.information(
            self,
            text("settings_cache_cleared_title"),
            text("settings_cache_cleared").format(n=removed),
        )

    def change_folder(self) -> None:
        from settings.relocate import files_in, move_library

        current = self.main_window.library.folder
        chosen = QFileDialog.getExistingDirectory(
            self, text("settings_move"), str(current)
        )
        if not chosen:
            return
        new_folder = Path(chosen)
        if new_folder == current:
            return

        already = files_in(new_folder)
        if already:
            reply = QMessageBox.question(
                self,
                text("settings_move_conflict_title"),
                text("settings_move_conflict").format(
                    path=new_folder, files="\n".join(already)
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self._point_at(new_folder)
            return

        result = move_library(current, new_folder)
        if not result.ok:
            QMessageBox.critical(
                self,
                text("settings_move_failed_title"),
                text("settings_move_failed").format(files="\n".join(result.failed)),
            )
            return
        self._point_at(new_folder)

    def _point_at(self, folder: Path) -> None:
        if not config.set_library_dir(folder):
            QMessageBox.critical(
                self,
                text("settings_move_failed_title"),
                text("settings_move_failed").format(files=str(folder)),
            )
            return
        self.folder_changed.emit()
        self.refresh()
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
