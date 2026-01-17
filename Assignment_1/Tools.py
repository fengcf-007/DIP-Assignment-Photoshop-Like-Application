import os
import cv2
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QComboBox, QSlider, QCheckBox, QDialogButtonBox,
    QFileDialog, QLineEdit, QSpinBox, QColorDialog
)
from PyQt5.QtCore import Qt




"""
Window for Combine 2 or more Image
"""
class ImageStitchDialog(QDialog):
    """
    Window for Combine 2 or more Image
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combine / Stitch Images")
        self.setFixedSize(400, 300)

        self.image_paths = []
        self.direction = "Horizontal"
        self.spacing = 0

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Images to Combine:"))
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Images")
        remove_btn = QPushButton("Remove Selected")
        add_btn.clicked.connect(self.add_images)
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        # Direction
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Horizontal", "Vertical"])
        dir_layout.addWidget(self.direction_combo)
        layout.addLayout(dir_layout)

        # Spacing
        layout.addWidget(QLabel("Spacing (pixels):"))
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(0, 100)
        self.spacing_slider.setValue(0)
        layout.addWidget(self.spacing_slider)

        # Preview
        self.preview_checkbox = QCheckBox("Show Preview")
        layout.addWidget(self.preview_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.bmp)")
        if files:
            self.image_paths.extend(files)
            self.refresh_list()

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.image_paths.remove(item.text())
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.image_paths)

    def get_settings(self):
        return {
            "paths": self.image_paths,
            "direction": self.direction_combo.currentText(),
            "spacing": self.spacing_slider.value(),
            "preview": self.preview_checkbox.isChecked(),
        }
        

"""
Window for insert text
"""
class TextInsertDialog(QDialog):
    """
    Window for insert text
    """
    
    def __init__(self, parent=None, text=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Text")
        self.setMinimumWidth(300)
        self.color = (0, 0, 0)
        self.font_scale = 1
        self.thickness = 2
        self.position = (50, 50)

        layout = QVBoxLayout()

    # --- Text input
        layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text...")
        if text is not None:
            self.text_input.setText(text)
        layout.addWidget(self.text_input)

    # --- Font size
        layout.addWidget(QLabel("Font size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 10)
        self.size_spin.setValue(2)
        layout.addWidget(self.size_spin)

    # --- Thickness
        layout.addWidget(QLabel("Thickness:"))
        self.thick_spin = QSpinBox()
        self.thick_spin.setRange(1, 10)
        self.thick_spin.setValue(2)
        layout.addWidget(self.thick_spin)

    # --- Color picker
        color_layout = QHBoxLayout()
        self.color_label = QLabel("Color: ")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 20)
        self.color_preview.setStyleSheet(f"background-color: rgb{self.color}; border:1px solid gray;")

        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        layout.addLayout(color_layout)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = (color.red(), color.green(), color.blue())
            self.color_preview.setStyleSheet(
                f"background-color: rgb{self.color}; border:1px solid gray;"
            )

    def get_values(self):
        return {
            "text": self.text_input.text(),
            "font_scale": self.size_spin.value(),
            "thickness": self.thick_spin.value(),
            "color": self.color,
            "position": self.position
        }

