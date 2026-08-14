from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout


class FlowLayout(QLayout):
    """Left to right, wrapping onto the next line when it runs out of room."""

    def __init__(self, parent=None, margin: int = 0, spacing: int = 16):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items: list = []

    # QLayout expects a subclass to say when its contents changed. Miss that
    # and the positions worked out for the previous set of items simply stand:
    # the last card added stays at (0, 0) at its unlaid-out size, drawn on top
    # of the first one. Adding a widget usually reparents it, which posts a
    # layout request by accident and hides the omission -- until the day a
    # widget is re-added that is already a child, and nothing reparents.
    def addItem(self, item):
        self._items.append(item)
        self.invalidate()

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )

    def _arrange(self, rect, test_only: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        area = rect.adjusted(left, top, -right, -bottom)
        x, y, line_height = area.x(), area.y(), 0

        for item in self._items:
            # isHidden(), not isVisible(): a widget is not visible before its
            # window is first shown either, and testing for that stacked every
            # card at (0, 0) on startup.
            if item.widget().isHidden():
                continue
            width = item.sizeHint().width()
            if x + width > area.right() and line_height > 0:
                x = area.x()
                y += line_height + self.spacing()
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x += width + self.spacing()
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
