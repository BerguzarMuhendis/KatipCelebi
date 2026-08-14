import logging
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from books.add import AddBookPage
from books.covers import CoverLoader
from books.detail import BookDetail
from books.grid import LibraryPage
from books.openlibrary import COVER_SIZE_THUMB
from books.store import Library
from people.page import PeoplePage
from people.store import Ledger
from settings.page import SettingsPage
from shared import config, texts
from shared.icons import app_icon, dress, logo, redress, with_flag
from shared.logs import point_at as point_log_at
from shared.paths import default_library_dir
from shared.texts import text
from shared.theme import THEMES, apply_theme, theme_preview_pixmap
from stats.goals import Goals
from stats.page import StatsPage

logger = logging.getLogger("katipcelebi")

SIDEBAR_WIDTH = 220


class SetupPage(QWidget):
    """The first questions: where the books go, how it looks, its language."""

    done = pyqtSignal(Path)
    theme_picked = pyqtSignal(str)
    language_picked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder = default_library_dir()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(14)
        layout.addStretch(1)

        self.title = QLabel()
        self.title.setObjectName("pageTitle")
        layout.addWidget(self.title)

        self.explain = QLabel()
        self.explain.setObjectName("pageSubtitle")
        self.explain.setWordWrap(True)
        layout.addWidget(self.explain)

        # The language first: everything under it changes with the answer, so
        # it is the honest thing to ask before the rest can be read.
        lang_row = QHBoxLayout()
        self.language_combo = QComboBox()
        for code, name in texts.available():
            self.language_combo.addItem(with_flag(code, name), code)
        self.language_combo.setCurrentIndex(
            max(0, self.language_combo.findData(texts.current()))
        )
        self.language_combo.activated.connect(
            lambda: self.language_picked.emit(self.language_combo.currentData())
        )
        lang_row.addWidget(self.language_combo)
        lang_row.addStretch(1)
        layout.addLayout(lang_row)

        row = QHBoxLayout()
        self.folder_label = QLabel(str(self.folder))
        self.folder_label.setObjectName("statusLabel")
        row.addWidget(self.folder_label, 1)
        self.browse = QPushButton()
        self.browse.clicked.connect(self._choose)
        row.addWidget(self.browse)
        layout.addLayout(row)

        # Asked here rather than left to be found in Settings later: it is one
        # question, it is the one thing about the app somebody has an opinion
        # about before they have used it, and the answer shows itself.
        theme_row = QHBoxLayout()
        self.theme_heading = QLabel()
        theme_row.addWidget(self.theme_heading)
        self.theme_combo = QComboBox()
        self.theme_combo.setIconSize(QSize(20, 20))
        for name in THEMES:
            self.theme_combo.addItem(theme_preview_pixmap(name), "", name)
        self.theme_combo.setCurrentIndex(
            max(0, self.theme_combo.findData(config.theme()))
        )
        self.theme_combo.activated.connect(
            lambda: self.theme_picked.emit(self.theme_combo.currentData())
        )
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        layout.addLayout(theme_row)

        self.start_button = QPushButton()
        self.start_button.setDefault(True)
        self.start_button.clicked.connect(self._start)
        layout.addWidget(self.start_button)
        layout.addStretch(2)
        self.retranslate()

    def retranslate(self) -> None:
        """Put every label back in the language now in force."""
        self.title.setText(text("setup_title"))
        self.explain.setText(text("setup_explain"))
        self.browse.setText(text("setup_browse"))
        self.theme_heading.setText(text("settings_theme"))
        for index, name in enumerate(THEMES):
            self.theme_combo.setItemText(index, text("theme_" + name.replace("-", "_")))
        self.start_button.setText(text("setup_start"))

    def _choose(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, text("setup_browse"), str(self.folder)
        )
        if chosen:
            self.folder = Path(chosen)
            self.folder_label.setText(chosen)

    def _start(self) -> None:
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.exception("Could not make %s", self.folder)
            self.folder_label.setText(text("setup_folder_missing"))
            return
        self.done.emit(self.folder)


class WelcomePage(QWidget):
    """Hello, before the questions start."""

    done = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.addStretch(1)

        mark = QLabel()
        mark.setPixmap(logo(160))
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(mark)
        layout.addSpacing(18)

        title = QLabel(text("app_name"))
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(text("welcome_line"))
        subtitle.setObjectName("pageSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        button = QPushButton(text("welcome_start"))
        button.setDefault(True)
        button.clicked.connect(self.done.emit)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(2)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(text("app_name"))
        self.setWindowIcon(app_icon())
        self.resize(1180, 760)
        self.setMinimumSize(880, 600)

        folder = config.library_dir() or default_library_dir()
        self.library = Library(folder)
        self.ledger = Ledger(folder)
        self.goals = Goals(folder)
        self.covers = CoverLoader()
        self.covers.signals.loaded.connect(self._on_cover)

        self._build()
        if config.setup_done() and config.library_dir():
            self._open_library()
        else:
            self.stack.setCurrentWidget(self.welcome_page)

    # ------------------------------------------------------------ building ---
    def _build(self) -> None:
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome_page = WelcomePage()
        self.welcome_page.done.connect(
            lambda: self.stack.setCurrentWidget(self.setup_page)
        )
        self.stack.addWidget(self.welcome_page)

        self.setup_page = SetupPage()
        self.setup_page.done.connect(self._setup_done)
        self.setup_page.theme_picked.connect(self._pick_setup_theme)
        self.setup_page.language_picked.connect(self._pick_language)
        self.stack.addWidget(self.setup_page)

        self.shell = None
        self._build_shell()

    def _build_shell(self) -> None:
        """The sidebar and the five pages, built fresh.

        Torn down and rebuilt whole when the language changes: every page holds
        its own labels, and re-labelling each by hand is a list to forget one
        from. The library, the ledger and the goals live on the window, not the
        pages, so nothing here touches the user's data -- only the words.
        """
        was_on = 0
        if self.shell is not None:
            was_on = self.pages.currentIndex()
            self.stack.removeWidget(self.shell)
            self.shell.deleteLater()

        shell = QWidget()
        row = QHBoxLayout(shell)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 26, 18, 18)
        side.setSpacing(6)

        brand = QLabel(text("app_name"))
        brand.setObjectName("brandLabel")
        brand.setWordWrap(True)
        side.addWidget(brand)
        side.addSpacing(22)

        self.pages = QStackedWidget()
        self.add_page = AddBookPage(self.library)
        self.add_page.book_added.connect(self._books_changed)
        self.library_page = LibraryPage(self)
        self.library_page.book_opened.connect(self._open_book)
        self.book_page = None
        self._came_from = None
        self.people_page = PeoplePage(self.ledger)
        self.stats_page = StatsPage(self, self.goals)
        self.settings_page = SettingsPage(self)
        self.settings_page.theme_changed.connect(self._change_theme)
        self.settings_page.folder_changed.connect(self._open_library)
        self.settings_page.language_changed.connect(self._pick_language)
        self.pages.addWidget(self._centered_page(self.add_page))
        self.pages.addWidget(self._centered_page(self.library_page))
        self.pages.addWidget(self._centered_page(self.people_page))
        self.pages.addWidget(self._centered_page(self.stats_page))
        self.pages.addWidget(self._centered_page(self.settings_page))

        self.nav_add = self._nav_button(side, "nav_add", 0, checked=True)
        self.nav_library = self._nav_button(side, "nav_library", 1)
        self.nav_people = self._nav_button(side, "nav_people", 2)
        self.nav_stats = self._nav_button(side, "nav_stats", 3)
        self.nav_settings = self._nav_button(side, "nav_settings", 4)
        side.addStretch(1)

        self.folder_label = QLabel()
        self.folder_label.setObjectName("statusLabel")
        side.addWidget(self.folder_label)

        row.addWidget(sidebar)
        row.addWidget(self.pages, 1)
        self.stack.addWidget(shell)
        self.shell = shell
        self.pages.setCurrentIndex(was_on)

    def _centered_page(self, page: QWidget) -> QWidget:
        """Wrap a page in a tighter, symmetric centered host."""
        host = QWidget()
        host.setObjectName("pageCenterHost")
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(0)

        page.setMaximumWidth(1180)
        page.setMinimumWidth(760)
        page.setSizePolicy(
            page.sizePolicy().horizontalPolicy(), page.sizePolicy().verticalPolicy()
        )
        host_layout.addWidget(page, 0, Qt.AlignmentFlag.AlignHCenter)
        return host

    def _nav_button(
        self, layout, key: str, index: int, checked: bool = False
    ) -> QPushButton:
        """A sidebar button.

        It takes the text key, not the text: the icon is looked up by the
        same name, so the two cannot drift apart.
        """
        button = dress(QPushButton(text(key)), key)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setAutoExclusive(True)
        button.setChecked(checked)
        button.clicked.connect(lambda: self.pages.setCurrentIndex(index))
        layout.addWidget(button)
        return button

    # ------------------------------------------------------------ starting ---
    def _pick_setup_theme(self, name: str) -> None:
        """Answer the question while it is being asked.

        The whole window changes under them, which is the only honest preview
        there is.
        """
        config.set_theme(name)
        self._change_theme(name)

    def _pick_language(self, code: str) -> None:
        """Switch language, and redraw the whole app into it at once.

        The setup screen has its own labels and is rebuilt on its own; the
        five pages are rebuilt together. The window's own title and its
        placeholder-cover glyph go through here too -- they belong to no page.
        """
        from shared import texts

        # Caught before the rebuild: _build_shell removes the old shell, which
        # moves the stack off it -- so afterwards there is no telling whether
        # the user was in the app or still on the setup screen.
        in_app = self.stack.currentWidget() is self.shell

        config.set_language(code)
        texts.use(code)
        self.setWindowTitle(text("app_name"))
        self.setup_page.retranslate()
        self._build_shell()
        if in_app:
            self.stack.setCurrentWidget(self.shell)
            self._refresh()

    def _setup_done(self, folder: Path) -> None:
        if not config.set_library_dir(folder):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=folder),
            )
            return
        config.set_setup_done()
        self.library.folder = folder
        self.ledger.folder = folder
        self.goals.folder = folder
        self._open_library()

    def _open_library(self) -> None:
        """Read the books, and put the log beside them."""
        folder = config.library_dir() or self.library.folder
        # Before anything is read: loading is the part most worth having a log
        # of, and this is the first moment we know where to put one.
        point_log_at(folder)
        self.library.folder = folder
        self.ledger.folder = folder
        self.goals.folder = folder
        self.library.load()
        self.ledger.load()
        self.goals.load()
        self.add_page.library = self.library
        self.add_page.refresh_tags()
        self._show_folder()
        if hasattr(self, "settings_page"):
            self.settings_page.refresh()
        self.stack.setCurrentWidget(self.shell)
        self._refresh()
        self._report_damage()

    # ----------------------------------------------------------- the books ---
    def _refresh(self) -> None:
        out = {loan.book_key for loan in self.ledger.loans if loan.is_open}
        self.library_page.rebuild(self.library.books, out)
        self.people_page.refresh()
        self.stats_page.refresh()
        # A book added is a tag the next book can be offered.
        self.add_page.refresh_tags()
        for book in self.library.books:
            self.covers.request(book.key, COVER_SIZE_THUMB)

    def _books_changed(self, _key: str = "") -> None:
        self._refresh()

    def _open_book(self, key: str) -> None:
        """Show one book, on a page of its own inside this window."""
        book = self.library.find(key)
        if book is None:
            return
        self._came_from = self.pages.currentWidget()
        page = BookDetail(book, self.library, self.ledger, self.covers)
        page.saved.connect(self._book_edited)
        # A deleted book cannot have its one card touched up: it has no card
        # any more, and the filters and the figures have all changed under it.
        page.deleted.connect(self._books_changed)
        page.closed.connect(self._close_book)
        self.book_page = page

        # Added before it is shown: setParent() hides a widget, so switching to
        # it first would land on a page that has just been hidden.
        self.pages.addWidget(page)
        self.pages.setCurrentWidget(page)
        self._lock_nav(True)
        page.setFocus()  # so Escape reaches it

    def _close_book(self) -> None:
        """Take the book's page away and go back where we came from."""
        page = getattr(self, "book_page", None)
        if page is None:
            return
        self.book_page = None
        self._lock_nav(False)
        if self._came_from is not None:
            self.pages.setCurrentWidget(self._came_from)
        self.pages.removeWidget(page)
        page.deleteLater()

    def _lock_nav(self, locked: bool) -> None:
        """A book is a page, but it is not one of the five.

        The sidebar cannot take you off it, because leaving is the Back button
        -- a checked nav button pointing at a page you are not on would be
        telling you something untrue.
        """
        for button in (
            self.nav_add,
            self.nav_library,
            self.nav_people,
            self.nav_stats,
            self.nav_settings,
        ):
            button.setEnabled(not locked)

    def _book_edited(self, key: str) -> None:
        book = self.library.find(key)
        card = self.library_page.card_for(key)
        if book is not None and card is not None:
            # Just this card: a rebuild would ask for every cover again.
            card.refresh(book, lent_out=self.ledger.is_lent_out(key))
        self.people_page.refresh()
        # The figures are worked out from the books, so an edited book means
        # a different answer -- and this is the cheapest moment to redraw.
        self.stats_page.refresh()

    def _on_cover(self, key: str, size: str, image) -> None:
        if size == COVER_SIZE_THUMB:
            self.library_page.show_cover(key, image)

    def closeEvent(self, event):
        logger.info("Closing.")
        event.accept()

    def _show_folder(self) -> None:
        """Say where the books are, in the room the sidebar actually has.

        A path is longer than any sidebar, so it is shortened in the middle --
        the two ends are the parts that mean something -- and the whole thing
        is on the tooltip for when the user really wants it.

        Polished first: a widget's font() does not know about the stylesheet
        until Qt has applied it, so measuring before that shortens the path to
        fit a font it is not going to be drawn in -- and the last letter of
        "library.json" went over the edge.
        """
        path = str(self.library.path)
        self.folder_label.ensurePolished()
        metrics = QFontMetrics(self.folder_label.font())
        room = SIDEBAR_WIDTH - 36  # the sidebar's left and right margins
        self.folder_label.setText(
            metrics.elidedText(path, Qt.TextElideMode.ElideMiddle, room)
        )
        self.folder_label.setToolTip(path)

    def _change_theme(self, name: str | None = None) -> None:
        """Re-dress the app, and redraw everything that paints itself.

        The stylesheet (or, under a native theme, the platform style) reaches
        every widget on its own. Three things it cannot reach: the charts and
        the placeholder covers, which paint their own colours, and the button
        icons, which are pictures already painted in a colour that has just
        stopped being right.
        """
        from PyQt6.QtWidgets import QApplication

        apply_theme(
            QApplication.instance(),
            config.theme() if name is None else name,
        )
        redress(self)
        self._refresh()
        self.settings_page.refresh()

    def _report_damage(self) -> None:
        """Say so if the library file could not be read.

        Silence would be the cruel part: the app would look like it had simply
        forgotten every book the user owns, while the file sat right next to it
        under another name.
        """
        rescued = list(self.ledger.rescued)
        if self.library.rescued_to is not None:
            rescued.insert(0, self.library.rescued_to)
        if not rescued:
            return
        QMessageBox.warning(
            self,
            text("damaged_title"),
            text("damaged").format(path="\n".join(str(p) for p in rescued)),
        )
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
