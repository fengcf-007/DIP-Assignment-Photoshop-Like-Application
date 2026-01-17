from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt


"""
Resizable QLabel that maintains aspect ratio of the image 
when the window is resized.
"""
class ResizableLabel(QLabel):
    """
    Resizable QLabel that maintains aspect ratio of the image 
    when the window is resized.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)
        self._pixmap = None

    def setPixmap(self, pixmap):
        # Store the original pixmap so we can rescale it later
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        self.update_display()

    def resizeEvent(self, event):
        # Triggered when window is resized
        self.update_display()
        super().resizeEvent(event)

    def update_display(self):
        if self._pixmap:
            # Scale based on the CURRENT label size
            scaled = self._pixmap.scaled(
                self.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
