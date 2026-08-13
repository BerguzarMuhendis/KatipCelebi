# Katip Celebi
# Copyright (C) 2026 farukylmz0550
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Shim that re-exports the real SettingsPage implementation.

The heavy implementation lives in `settings.page_impl` so this module can
remain small and stable for imports elsewhere.
"""

from .page_impl import *

__all__ = [name for name in dir() if not name.startswith("_")]

    def _build_seed(self, column) -> None:
        """Where the colours come from. A sentence, not a control.

        Nobody picks this: the app wears the desktop's own accent, the way
        Material You wears the wallpaper on a phone. Saying so is the whole
        job -- otherwise the app just looks like it chose blue by itself.
        Hidden when an Adwaita theme is active, since it does not apply.
        """
        self._colour_heading = self._heading(column, "settings_colour")
        self.colour_label = QLabel()
        self.colour_label.setObjectName("statusLabel")
        self.colour_label.setWordWrap(True)
        column.addWidget(self.colour_label)

    def _about_text(self) -> str:
        """Who wrote this, where it lives, with the source a click away.

        The link is coloured here because Qt colours links from its own
        palette, not from our stylesheet -- so left alone it comes out a blue
        nobody chose, on a page whose every other colour was worked out from
        the desktop's accent.
        """
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

    # ------------------------------------------------------------ showing ---
    def refresh(self) -> None:
        self.folder_label.setText(str(self.main_window.library.folder))
        index = self.theme_combo.findData(config.theme())
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(max(index, 0))
        self.theme_combo.blockSignals(False)
        self.cache_label.setText(text("settings_cache_size").format(mb=cache_size_mb()))
        # The colour section only applies to the built-in Fluent/Contrast themes
        # and not to the custom QSS override, which can use any palette.
        is_built_in = family(config.theme()) in {"default", "contrast"}
        self._colour_heading.setVisible(is_built_in)
        self.colour_label.setVisible(is_built_in)
        if is_built_in:
            self._show_colour()
        # The link is coloured by hand, so it does not follow the
        # stylesheet on its own.
        self.about_label.setText(self._about_text())
        self._show_qss()
        self._update_status()

    # ------------------------------------------------------------- theme ---
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

    # ---------------------------------------------------------- language ---
    def _pick_language(self, *_args) -> None:
        code = self.language_combo.currentData() or texts.BASE
        if not config.set_language(code):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.main_window.library.path),
            )
            return
        # The window redraws every page, this one included, so nothing more is
        # done here -- the combo the user just touched is about to be replaced.
        self.language_changed.emit(code)

    # ------------------------------------------------------------ colour ---
    def _show_colour(self) -> None:
        seed = current_seed()
        key = (
            "settings_colour_from_desktop" if has_a_desktop() else "settings_colour_own"
        )
        self.colour_label.setText(text(key).format(colour=seed))

    # ------------------------------------------------------------ custom QSS -
    def _show_qss(self) -> None:
        from shared.theme import _qss_styles_dir, _qss_user_path

        user = _qss_user_path()
        if user.exists():
            self.qss_label.setText(str(user))
        else:
            default = _qss_styles_dir() / "default.qss"
            self.qss_label.setText(str(default))

    def _update_status(self) -> None:
        # Run the networked update check off the UI thread.
        from shared.settings_helpers import UpdateThread

        # Keep a reference so the thread isn't GC'd.
        self._update_thread = UpdateThread(APP_VERSION)
        self._update_thread.result.connect(
            lambda has, latest, url: self._on_update_result(has, latest, url, show_message=False)
        )
        self._update_thread.start()

    def _check_updates(self) -> None:
        # User-initiated check: run off-thread and show a dialog when done.
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
            # Copy the default to the user's data dir so they can edit it.
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

    # ------------------------------------------------------------- cache ---
    def clear_cache(self) -> None:
        removed = 0
        for path in cover_cache_dir().glob("*"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                # In use, or gone already: neither is worth stopping
                # for.
                continue
        self.refresh()
        QMessageBox.information(
            self,
            text("settings_cache_cleared_title"),
            text("settings_cache_cleared").format(n=removed),
        )

    # ------------------------------------------------------------ folder ---
    def change_folder(self) -> None:
        """Move the library somewhere else.

        Nothing moves unless all of it can.
        """
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
            # That folder holds somebody's library. Never write over it without
            # asking: it is unrecoverable, and the answer is often "open that
            # one".
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
            self._point_at(new_folder)  # open what is there; move nothing
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
            # The books are at the new folder but the note saying so did not
            # save, so the next launch would open the old one and look like the
            # library had been lost. Say it now, while the user is still here.
            QMessageBox.critical(
                self,
                text("settings_move_failed_title"),
                text("settings_move_failed").format(files=str(folder)),
            )
            return
        self.folder_changed.emit()
        self.refresh()
