"""Library page: a wall of covers and the search/filter UI.

Extracted from `books.grid` to reduce monolith size.
"""
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from books import tags
from books.card import BookCard
from books.excel import EXPORT_DEFAULT_NAME, export_library
from books.filters import (
    LENT_ANY,
    LENT_HOME,
    LENT_OUT,
    SEARCH_ALL,
    SEARCH_FIELDS,
    SIGNED_ANY,
    SIGNED_NO,
    SIGNED_YES,
    SORT_RATING,
    SORT_TITLE,
    SORT_YEAR,
    Filters,
    arrange,
)
from books.model import Book
from books.reading import STATUS_ANY, STATUSES
from shared.icons import dress
from shared.texts import text

from books.flowlayout import FlowLayout


class LibraryPage(QWidget):
    """Every book, and the search box over them."""

    book_opened = QWidget().pyqtSignal if False else None  # placeholder for type

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.cards: dict[str, BookCard] = {}
        self._books: list[Book] = []
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        self.title_label = QLabel(text("nav_library"))
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchField")
        self.search_edit.setPlaceholderText(text("search_hint"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.refresh_view)
        search_row.addWidget(self.search_edit, 1)
        self.search_field_combo = QComboBox()
        for field in SEARCH_FIELDS:
            self.search_field_combo.addItem(text("search_in_" + field), field)
        self.search_field_combo.currentIndexChanged.connect(self.refresh_view)
        search_row.addWidget(self.search_field_combo)
        layout.addLayout(search_row)

        self.advanced_toggle = QPushButton(text("advanced_search") + " ▸")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setFlat(True)
        self.advanced_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.advanced_toggle.toggled.connect(self._toggle_advanced_search)
        layout.addWidget(self.advanced_toggle, 0, Qt.AlignmentFlag.AlignLeft)

        self.advanced_panel = QWidget()
        self.advanced_panel.setVisible(False)
        advanced_inner = QVBoxLayout(self.advanced_panel)
        advanced_inner.setContentsMargins(0, 0, 0, 0)
        advanced_inner.setSpacing(6)
        advanced_inner.addWidget(self._filter_row())
        layout.addWidget(self.advanced_panel)

        self.count_label = QLabel()
        self.count_label.setObjectName("pageSubtitle")
        layout.addWidget(self.count_label)

        self.empty_label = QLabel()
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_host = QWidget()
        policy = self.grid_host.sizePolicy()
        policy.setHeightForWidth(True)
        self.grid_host.setSizePolicy(policy)
        self.flow = FlowLayout(self.grid_host, margin=4)
        self.scroll.setWidget(self.grid_host)
        layout.addWidget(self.scroll, 1)

    def _filter_row(self) -> QWidget:
        host = QWidget()
        host.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        policy = host.sizePolicy()
        policy.setHeightForWidth(True)
        host.setSizePolicy(policy)
        row = FlowLayout(host, margin=0, spacing=10)

        def group(*widgets) -> None:
            box = QWidget()
            inner = QHBoxLayout(box)
            inner.setContentsMargins(0, 0, 0, 0)
            inner.setSpacing(6)
            for widget in widgets:
                inner.addWidget(widget)
            row.addWidget(box)

        self.rating_combo = QComboBox()
        self.rating_combo.addItem(text("filter_rating_any"), 0)
        for n in (5, 4, 3, 2, 1):
            self.rating_combo.addItem(text("filter_rating_min").format(n=n), n)
        self.rating_combo.currentIndexChanged.connect(self.refresh_view)
        group(QLabel(text("filter_rating")), self.rating_combo)

        self.signed_combo = QComboBox()
        for label, value in (
            ("filter_signed_any", SIGNED_ANY),
            ("filter_signed_yes", SIGNED_YES),
            ("filter_signed_no", SIGNED_NO),
        ):
            self.signed_combo.addItem(text(label), value)
        self.signed_combo.currentIndexChanged.connect(self.refresh_view)
        group(QLabel(text("filter_signed")), self.signed_combo)

        self.lent_combo = QComboBox()
        for label, value in (
            ("filter_lent_any", LENT_ANY),
            ("filter_lent_home", LENT_HOME),
            ("filter_lent_out", LENT_OUT),
        ):
            self.lent_combo.addItem(text(label), value)
        self.lent_combo.currentIndexChanged.connect(self.refresh_view)
        group(QLabel(text("filter_lent")), self.lent_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItem(text("filter_status_any"), STATUS_ANY)
        for status in STATUSES:
            self.status_combo.addItem(text("status_" + status), status)
        self.status_combo.currentIndexChanged.connect(self.refresh_view)
        group(QLabel(text("filter_status")), self.status_combo)

        self.tag_combo = QComboBox()
        self.tag_combo.setMinimumWidth(130)
        self.tag_combo.currentIndexChanged.connect(self.refresh_view)
        group(QLabel(text("filter_tag")), self.tag_combo)

        self.sort_combo = QComboBox()
        for label, value in (
            ("sort_by_title", SORT_TITLE),
            ("sort_by_rating", SORT_RATING),
            ("sort_by_year", SORT_YEAR),
        ):
            self.sort_combo.addItem(text(label), value)
        self.sort_combo.currentIndexChanged.connect(self.refresh_view)
        self.sort_dir_button = QPushButton(text("sort_ascending"))
        self.sort_dir_button.setCheckable(True)
        self.sort_dir_button.toggled.connect(self._sort_dir_changed)
        group(QLabel(text("sort_by")), self.sort_combo, self.sort_dir_button)

        self.clear_button = QPushButton(text("clear_filters"))
        self.clear_button.clicked.connect(self.clear_filters)
        self.export_button = dress(QPushButton(text("export_button")), "export_button")
        self.export_button.clicked.connect(self._export)
        row.addWidget(self.export_button)
        row.addWidget(self.clear_button)
        return host

    def _toggle_advanced_search(self, expanded: bool) -> None:
        self.advanced_panel.setVisible(expanded)
        label = text("advanced_search")
        self.advanced_toggle.setText(f"{label} {'▾' if expanded else '▸'}")

    def _sort_dir_changed(self, descending: bool) -> None:
        self.sort_dir_button.setText(
            text("sort_descending" if descending else "sort_ascending")
        )
        self.refresh_view()

    def filters(self) -> Filters:
        return Filters(
            query=self.search_edit.text(),
            search_field=self.search_field_combo.currentData() or SEARCH_ALL,
            min_rating=self.rating_combo.currentData() or 0,
            signed=self.signed_combo.currentData() or SIGNED_ANY,
            lent=self.lent_combo.currentData() or LENT_ANY,
            status=self.status_combo.currentData() or STATUS_ANY,
            tag=self.tag_combo.currentData() or "",
        )

    def _controls(self) -> tuple:
        return (
            self.search_edit,
            self.search_field_combo,
            self.rating_combo,
            self.signed_combo,
            self.lent_combo,
            self.status_combo,
            self.tag_combo,
            self.sort_combo,
            self.sort_dir_button,
        )

    def clear_filters(self) -> None:
        for widget in self._controls():
            widget.blockSignals(True)
        self.search_edit.clear()
        self.search_field_combo.setCurrentIndex(0)
        self.rating_combo.setCurrentIndex(0)
        self.signed_combo.setCurrentIndex(0)
        self.lent_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.tag_combo.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.sort_dir_button.setChecked(False)
        for widget in self._controls():
            widget.blockSignals(False)
        self.sort_dir_button.setText(text("sort_ascending"))
        self.refresh_view()

    def _export(self) -> None:
        books = self.main_window.library.books
        if not books:
            QMessageBox.information(
                self, text("export_empty_title"), text("export_empty")
            )
            return
        suggested = str(Path.home() / EXPORT_DEFAULT_NAME)
        chosen, _ = QFileDialog.getSaveFileName(
            self, text("export_button"), suggested, "Excel (*.xlsx)"
        )
        if not chosen:
            return
        path = Path(chosen)
        if export_library(books, self.main_window.ledger, path):
            QMessageBox.information(
                self,
                text("export_done_title"),
                text("export_done").format(n=len(books), path=path),
            )
        else:
            QMessageBox.critical(
                self,
                text("export_failed_title"),
                text("export_failed").format(path=path),
            )

    # ------------------------------------------------------------ contents ---
    def rebuild(self, books: list[Book], lent_keys: set = frozenset()) -> None:
        while self.flow.count():
            self.flow.takeAt(0)
        for card in self.cards.values():
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()

        self._books = list(books)
        self._fill_tag_filter()
        for book in books:
            card = BookCard(book, lent_out=book.key in lent_keys)
            card.clicked.connect(self.book_opened.emit)
            self.cards[book.key] = card
        self.refresh_view()

    def _fill_tag_filter(self) -> None:
        chosen = self.tag_combo.currentData()
        self.tag_combo.blockSignals(True)
        self.tag_combo.clear()
        self.tag_combo.addItem(text("filter_tag_any"), "")
        for tag in tags.tags_in_use(self._books):
            self.tag_combo.addItem(tags.display(tag), tag)
        index = self.tag_combo.findData(chosen) if chosen else 0
        self.tag_combo.setCurrentIndex(max(index, 0))
        self.tag_combo.blockSignals(False)

    def card_for(self, key: str):
        return self.cards.get(key)

    def show_cover(self, key: str, image: QImage) -> None:
        card = self.cards.get(key)
        if card is not None:
            card.set_cover(image)

    def refresh_view(self, *_args) -> None:
        filters = self.filters()
        mode = self.sort_combo.currentData() or SORT_TITLE
        descending = self.sort_dir_button.isChecked()

        ledger = self.main_window.ledger
        keep = [b for b in self._books if filters.allows(b, ledger.is_lent_out(b.key))]
        kept_keys = {b.key for b in keep}

        while self.flow.count():
            self.flow.takeAt(0)
        for book in arrange(keep, mode, descending):
            card = self.cards[book.key]
            self.flow.addWidget(card)
            card.setVisible(True)
        for key, card in self.cards.items():
            if key not in kept_keys:
                card.setVisible(False)

        shown, total = len(keep), len(self.cards)
        if not total:
            self.empty_label.setText(text("empty_library"))
            self.empty_label.show()
            self.scroll.hide()
        elif not shown:
            self.empty_label.setText(text("no_results"))
            self.empty_label.show()
            self.scroll.hide()
        else:
            self.empty_label.hide()
            self.scroll.show()

        if shown != total:
            self.count_label.setText(
                text("book_count_filtered").format(shown=shown, n=total)
            )
        else:
            self.count_label.setText(text("book_count").format(n=total))

    def visible_titles(self) -> list[str]:
        return sorted(c.book.title for c in self.cards.values() if not c.isHidden())
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
