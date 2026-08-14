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

"""The Statistics page: what your reading adds up to."""

from PyQt6.QtCharts import QChart, QChartView, QPieSeries
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from books.reading import READ, READING, WANT_TO_READ, format_duration
from shared import shape
from shared.texts import text
from shared.theme import colour, slice_colours
from stats.goals import Goals
from stats.summary import (
    RECENT_WINDOWS,
    WINDOW_YEAR,
    average_days_to_finish,
    counts_by_status,
    finished_in_month,
    finished_in_year,
    month_goal,
    tag_spread,
    time_spent,
    top_authors,
    top_publishers,
    year_goal,
)


class MetricCard(QFrame):
    """One number, and what it means."""

    def __init__(self, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        column = QVBoxLayout(self)
        column.setContentsMargins(14, 12, 14, 12)
        column.setSpacing(2)

        self.value_label = QLabel("—")
        self.value_label.setObjectName("metricValue")
        column.addWidget(self.value_label)
        caption_label = QLabel(caption)
        caption_label.setObjectName("metricCaption")
        caption_label.setWordWrap(True)
        column.addWidget(caption_label)

    def show_value(self, value: str) -> None:
        self.value_label.setText(value)


def count_label(name: str, value: float) -> str:
    """A wedge that stands for a number of books."""
    return f"{name} ({int(value)})"


def duration_label(name: str, value: float) -> str:
    """A wedge that stands for an amount of time."""
    return f"{name} ({format_duration(value)})"


def pie(title: str, slices: list[tuple[str, float]], label=count_label) -> QChartView:
    """A pie chart, or an empty one when there is nothing yet.

    How a wedge is named is the caller's business: three books and three days
    are both numbers, and only one of them reads properly as "(3)".
    """
    wedges = slice_colours()
    series = QPieSeries()
    for index, (name, count) in enumerate(slices):
        wedge = series.append(label(name, count), count)
        wedge.setBrush(QColor(wedges[index % len(wedges)]))
        # No labels around the pie: a name like "Herman Melville" plus its
        # count does not fit beside a 300px chart, and QtCharts answers that by
        # truncating -- "Herman Melvill...". The legend below has a whole line
        # per entry, down the right-hand side.
        wedge.setLabelVisible(False)

    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.setTitleBrush(colour("text_body"))

    legend = chart.legend()
    legend.setVisible(True)
    legend.setAlignment(Qt.AlignmentFlag.AlignRight)
    # QtCharts paints legend text black whatever the palette says, which on a
    # dark page means invisible. Setting the pen is the only thing that fixes
    # it. QtCharts paints legend text black whatever the palette says, which on
    # a dark page means invisible. Setting the pen is the only thing that fixes
    # it -- and it has to be re-set when the theme changes.
    legend.setLabelColor(colour("text_body"))
    legend.setBorderColor(QColor("transparent"))
    # A filled card like the metric ones: a raised tonal surface, no outline,
    # its corners rounded to the same large radius. The line the chart used to
    # draw around itself was the one thing on the page still edged rather than
    # toned.
    chart.setBackgroundBrush(colour("surface_container_high"))
    chart.setBackgroundPen(QPen(Qt.PenStyle.NoPen))
    chart.setBackgroundRoundness(shape.LARGE)
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setMinimumHeight(220)
    # The view's own frame and white viewport would box the rounded card back
    # in and show at its corners; drop both so the page shows through instead.
    view.setFrameShape(QFrame.Shape.NoFrame)
    view.setBackgroundBrush(QColor("transparent"))
    view.setStyleSheet("background: transparent; border: none;")
    return view


class StatsPage(QWidget):
    """Totals, the top five, and how you are doing against your goals."""

    def __init__(self, main_window, goals: Goals, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.goals = goals
        self._drawn: list = []
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 20)
        outer.setSpacing(12)

        title = QLabel(text("nav_stats"))
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        self.count_label = QLabel()
        self.count_label.setObjectName("pageSubtitle")
        outer.addWidget(self.count_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        self.column = QVBoxLayout(host)
        self.column.setSpacing(14)
        self.scroll.setWidget(host)
        outer.addWidget(self.scroll, 1)

        self._build_metrics()
        self._build_goals()
        self._build_charts()
        self.column.addStretch(1)

    def _build_metrics(self) -> None:
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cards = {
            "read": MetricCard(text("metric_read")),
            "reading": MetricCard(text("metric_reading")),
            "want": MetricCard(text("metric_want")),
            "not_read": MetricCard(text("metric_not_read")),
            "this_month": MetricCard(text("metric_this_month")),
            "this_year": MetricCard(text("metric_this_year")),
            "average": MetricCard(text("metric_average")),
            "total": MetricCard(text("metric_total")),
        }
        for index, card in enumerate(self.cards.values()):
            grid.addWidget(card, index // 4, index % 4)
        holder = QWidget()
        holder.setLayout(grid)
        self.column.addWidget(holder)

    def _build_goals(self) -> None:
        heading = QLabel(text("goals_heading"))
        heading.setObjectName("detailFieldLabel")
        self.column.addWidget(heading)

        self.year_bar, self.year_spin = self._goal_row(
            text("goal_yearly"), self._save_yearly
        )
        self.month_bar, self.month_spin = self._goal_row(
            text("goal_monthly"), self._save_monthly
        )

    def _goal_row(self, caption: str, on_change):
        row = QWidget()
        inner = QHBoxLayout(row)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(8)
        inner.addWidget(QLabel(caption))

        spin = QSpinBox()
        spin.setRange(0, 999)
        spin.setSpecialValueText(text("goal_none"))
        # No Set button: a goal is one number, and a button to confirm one
        # number is a button somebody forgets to press and then wonders why
        # the bar never moved.
        spin.valueChanged.connect(on_change)
        inner.addWidget(spin)

        bar = QProgressBar()
        bar.setTextVisible(True)
        inner.addWidget(bar, 1)
        self.column.addWidget(row)
        return bar, spin

    def _build_charts(self) -> None:
        window_row = QHBoxLayout()
        window_row.addWidget(QLabel(text("chart_time_window")))
        self.window_combo = QComboBox()
        for days in RECENT_WINDOWS:
            self.window_combo.addItem(text(f"window_{days}"), days)
        self.window_combo.currentIndexChanged.connect(self.refresh)
        window_row.addWidget(self.window_combo)
        window_row.addStretch(1)
        self.column.addLayout(window_row)

        # One above the other, not side by side. Three charts across a normal
        # window leave each of them about 300px, and "George Orwell (3)" does
        # not fit next to a pie in 300px -- QtCharts answers that by
        # truncating, so the page read "George Or...". Full width, and the
        # names fit.
        holder = QWidget()
        self.charts_column = QVBoxLayout(holder)
        self.charts_column.setContentsMargins(0, 0, 0, 0)
        self.charts_column.setSpacing(10)
        self.column.addWidget(holder)

    # ------------------------------------------------------------ drawing ---
    def refresh(self) -> None:
        """Redraw every figure from the books as they are right now."""
        books = self.main_window.library.books
        counts = counts_by_status(books)

        self.count_label.setText(text("stats_subtitle").format(n=len(books)))
        today = None  # summary uses today when it is not told otherwise

        self.cards["read"].show_value(str(counts[READ]))
        self.cards["reading"].show_value(str(counts[READING]))
        self.cards["want"].show_value(str(counts[WANT_TO_READ]))
        self.cards["not_read"].show_value(str(counts["not_read"]))
        self.cards["total"].show_value(str(len(books)))

        from datetime import datetime

        now = datetime.now()  # noqa: DTZ005 - wall-clock, like the stamps
        self.cards["this_month"].show_value(
            str(finished_in_month(books, now.year, now.month))
        )
        self.cards["this_year"].show_value(str(finished_in_year(books, now.year)))

        average = average_days_to_finish(books)
        self.cards["average"].show_value(
            text("metric_no_average") if average is None else format_duration(average)
        )

        self._show_goal(
            self.year_bar,
            self.year_spin,
            year_goal(books, self.goals.yearly, today),
        )
        self._show_goal(
            self.month_bar,
            self.month_spin,
            month_goal(books, self.goals.monthly, today),
        )
        self._draw_charts(books)

    def _show_goal(self, bar: QProgressBar, spin: QSpinBox, goal) -> None:
        spin.blockSignals(True)
        # Let the box hold whatever the file says. A goal hand-edited above the
        # ordinary cap would otherwise be clamped for display while the bar
        # showed the true figure, and the next nudge of the spin would save the
        # clamped number back -- quietly rewriting the user's goal.
        if goal.target > spin.maximum():
            spin.setMaximum(goal.target)
        spin.setValue(goal.target)
        spin.blockSignals(False)
        if goal.target <= 0:
            bar.setRange(0, 1)
            bar.setValue(0)
            bar.setFormat(text("goal_not_set"))
            return
        bar.setRange(0, goal.target)
        bar.setValue(min(goal.done, goal.target))
        bar.setFormat(
            text("goal_reached").format(done=goal.done, goal=goal.target)
            if goal.reached
            else text("goal_progress").format(done=goal.done, goal=goal.target)
        )

    def _draw_charts(self, books) -> None:
        # Torn down and rebuilt: a QChart cannot be told to forget its old
        # series without leaving the wedges behind.
        for widget in self._drawn:
            self.charts_column.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self._drawn = []

        if not books:
            # Three blank pies do not say "add some books", and the zeros
            # above have already said everything there is to say.
            self._drawn.append(self._say_nothing_yet(text("stats_empty")))
            self.charts_column.addWidget(self._drawn[0])
            return

        window = self.window_combo.currentData() or WINDOW_YEAR
        spent = time_spent(books, window)
        for title, slices, label, nothing_yet in (
            (
                text("chart_time"),
                spent,
                duration_label,
                text("chart_time_empty"),
            ),
            (text("chart_authors"), top_authors(books), count_label, ""),
            (text("chart_publishers"), top_publishers(books), count_label, ""),
            (text("chart_tags"), tag_spread(books), count_label, ""),
        ):
            if not slices and nothing_yet:
                # An empty pie under a title is a chart that says nothing about
                # why it is empty. This one has a reason worth giving.
                self._drawn.append(self._say_nothing_yet(nothing_yet))
                continue
            self._drawn.append(pie(title, slices, label))
        for widget in self._drawn:
            self.charts_column.addWidget(widget)

    def _say_nothing_yet(self, message: str) -> QLabel:
        label = QLabel(message)
        label.setObjectName("emptyLabel")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    @property
    def _charts(self) -> list:
        """Only the real charts. Some of what is drawn is an explanation."""
        return [w for w in self._drawn if isinstance(w, QChartView)]

    # -------------------------------------------------------------- goals ---
    def _save_yearly(self, target: int) -> None:
        if not self.goals.set_yearly(target):
            self._complain()
        self.refresh()

    def _save_monthly(self, target: int) -> None:
        if not self.goals.set_monthly(target):
            self._complain()
        self.refresh()

    def _complain(self) -> None:
        QMessageBox.critical(
            self,
            text("save_failed_title"),
            text("save_failed").format(path=self.goals.path),
        )
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
