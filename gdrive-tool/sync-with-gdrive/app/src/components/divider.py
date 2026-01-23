from __future__ import annotations
from PySide6.QtWidgets import QFrame, QSizePolicy
from PySide6.QtCore import Qt


class CustomDivider(QFrame):
    """
    Divider dùng được cả ngang & dọc.

    - orientation: "horizontal" | "vertical"
    - thickness: độ dày đường kẻ (px)
    - color: màu divider
    - margins: (left, top, right, bottom)
    """

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        *,
        thickness: int = 1,
        color: str = "#595959",
        parent=None,
    ):
        super().__init__(parent)

        self._orientation = orientation
        self._thickness = max(1, int(thickness))
        self._color = color

        self.setProperty("class", "NAME-divider")

        self.setStyleSheet(
            f"""
        QFrame[class="NAME-divider"] {{
            background-color: {self._color};
        }}
        """
        )

        self.set_orientation(self._orientation)

    def set_orientation(self, orientation: Qt.Orientation) -> None:
        if orientation not in (Qt.Orientation.Horizontal, Qt.Orientation.Vertical):
            orientation = Qt.Orientation.Horizontal

        self._orientation = orientation

        if orientation == Qt.Orientation.Horizontal:
            self.setFixedHeight(self._thickness)
            self.setFixedWidth(16777215)  # QWIDGETSIZE_MAX
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(self._thickness)
            self.setFixedHeight(16777215)  # QWIDGETSIZE_MAX
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
