import os
import cv2
import numpy as np
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QRect

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QLineEdit, 
    QDialogButtonBox, QCheckBox, QRadioButton, QButtonGroup, QHBoxLayout, 
    QFormLayout, QComboBox, QMessageBox
)



"""
Window for scaling All Canvas Image 
"""
class ScaleImageDialog(QDialog):
    """
    Window for scaling All Canvas Image 
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Size")
        self.setFixedSize(400, 260)
        self.parent = parent

        current_layer = self.parent.get_current_focus_layer()
        self.original_width = current_layer.image.shape[1]
        self.original_height = current_layer.image.shape[0]

        self.aspect_ratio = self.original_width / self.original_height if self.original_height != 0 else 1.0


        layout = QVBoxLayout(self)

        # 1. Pixel Dimensions Group
        dim_group = QGroupBox("Pixel Options")
        dim_layout = QGridLayout()
        dim_group.setLayout(dim_layout)

        dim_layout.addWidget(QLabel("Width:"), 0, 0)
        self.width_input = QLineEdit(str(self.original_width))
        self.width_input.setValidator(QIntValidator(1, 100000))
        dim_layout.addWidget(self.width_input, 0, 1)
        dim_layout.addWidget(QLabel("Pixels"), 0, 2)

        dim_layout.addWidget(QLabel("Height:"), 1, 0)
        self.height_input = QLineEdit(str(self.original_height))
        self.height_input.setValidator(QIntValidator(1, 100000))
        dim_layout.addWidget(self.height_input, 1, 1)
        dim_layout.addWidget(QLabel("Pixels"), 1, 2)
        
        layout.addWidget(dim_group)

        # 2. Scaling Options Group
        scale_group = QGroupBox("Scaling Options")
        scale_layout = QGridLayout()
        scale_group.setLayout(scale_layout)

        scale_layout.addWidget(QLabel("Scale:"), 0, 0)
        self.percent_input = QLineEdit("100.00")
        self.percent_input.setValidator(QDoubleValidator(0.1, 10000.0, 2))
        scale_layout.addWidget(self.percent_input, 0, 1)
        scale_layout.addWidget(QLabel("Percent"), 0, 2)

        scale_layout.addWidget(QLabel("Resample:"), 1, 0)
        self.resample_combo = QComboBox()
        self.resample_combo.addItems([
            "Bicubic",
            "Bilinear",
            "Nearest Neighbor",
            "Lanczos"
        ])
        # Default to Bicubic
        self.resample_combo.setCurrentIndex(0) 
        scale_layout.addWidget(self.resample_combo, 1, 1, 1, 2)

        self.constrain_checkbox = QCheckBox("Constrain Proportions")
        self.constrain_checkbox.setChecked(True)
        scale_layout.addWidget(self.constrain_checkbox, 2, 0, 1, 3)

        layout.addWidget(scale_group)

        # 3. Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.apply_changes) # Logic moved here
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # --- Logic Connections ---
        self.updating = False
        self.width_input.textEdited.connect(self.on_width_changed)
        self.height_input.textEdited.connect(self.on_height_changed)
        self.percent_input.textEdited.connect(self.on_percent_changed)

    # --- UI Sync Logic ---
    def on_width_changed(self, text):
        if self.updating or not text: return
        self.updating = True
        try:
            new_w = int(text)
            percent = (new_w / self.original_width) * 100.0
            self.percent_input.setText(f"{percent:.2f}")
            
            if self.constrain_checkbox.isChecked():
                new_h = int(new_w / self.aspect_ratio)
                self.height_input.setText(str(new_h))
        except ValueError: 
            pass
        finally: 
            self.updating = False

    def on_height_changed(self, text):
        if self.updating or not text: return
        self.updating = True
        try:
            new_h = int(text)
            percent = (new_h / self.original_height) * 100.0
            self.percent_input.setText(f"{percent:.2f}")
            
            if self.constrain_checkbox.isChecked():
                new_w = int(new_h * self.aspect_ratio)
                self.width_input.setText(str(new_w))
        except ValueError: 
            pass
        finally: 
            self.updating = False

    def on_percent_changed(self, text):
        if self.updating or not text: return
        self.updating = True
        try:
            percent = float(text)
            factor = percent / 100.0
            
            new_w = int(self.original_width * factor)
            new_h = int(self.original_height * factor)
            self.width_input.setText(str(new_w))
            self.height_input.setText(str(new_h))
        except ValueError: 
            pass
        finally: 
            self.updating = False

    # Apply
    def apply_changes(self):
        # Avoid Invalid input
        try:
            target_w = int(self.width_input.text())
            target_h = int(self.height_input.text())
        except ValueError:
            return

        idx = self.resample_combo.currentIndex()
        if idx == 0: interp = cv2.INTER_CUBIC
        elif idx == 1: interp = cv2.INTER_LINEAR
        elif idx == 2: interp = cv2.INTER_NEAREST
        elif idx == 3: interp = cv2.INTER_LANCZOS4
        else: interp = cv2.INTER_LINEAR

        self.parent.push_undo_state()

        for layer in self.parent.layer_panel.layers:
            if layer.image is not None:
                layer.image = cv2.resize(layer.image, (target_w, target_h), interpolation=interp)

        self.parent.selected_rect = (0, 0, 0, 0)
        self.parent.image_label.selection_rect = QRect()
        self.accept()
        
#/layer
"""
Window for expand / resize Canvas Image From any 9 Anchor Point
"""
class ExpandCanvasDialog(QDialog):
    """
    Window for expand / resize Canvas Image From any 9 Anchor Point
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Expand Canvas Size")
        self.setFixedSize(420, 340)
        self.parent = parent

        current_layer = self.parent.get_current_focus_layer()
        self.current_w = current_layer.image.shape[1]
        self.current_h = current_layer.image.shape[0]



        layout = QVBoxLayout(self)

        info_label = QLabel(f"Current Size: {self.current_w} px × {self.current_h} px")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setFixedHeight(60)
        info_label.setStyleSheet("color: #888888; margin-bottom: 5px;")
        layout.addWidget(info_label)

        # Input
        size_group = QGroupBox("New Size")
        size_layout = QGridLayout()
        size_group.setLayout(size_layout)

        # Input type Select
        self.unit_group = QButtonGroup(self)
        self.pixel_btn = QRadioButton("Pixels")
        self.percent_btn = QRadioButton("Percent")
        self.pixel_btn.setChecked(True)
        self.unit_group.addButton(self.pixel_btn)
        self.unit_group.addButton(self.percent_btn)
        
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(self.pixel_btn)
        unit_layout.addWidget(self.percent_btn)
        size_layout.addLayout(unit_layout, 0, 0, 1, 2)

        # Input box
        size_layout.addWidget(QLabel("Width:"), 1, 0)
        self.width_input = QLineEdit(str(self.current_w))
        size_layout.addWidget(self.width_input, 1, 1)

        size_layout.addWidget(QLabel("Height:"), 2, 0)
        self.height_input = QLineEdit(str(self.current_h))
        size_layout.addWidget(self.height_input, 2, 1)

        layout.addWidget(size_group)


        #  Anchor Grid Area
        anchor_group = QGroupBox("Anchor")
        anchor_layout = QGridLayout()
        anchor_group.setLayout(anchor_layout)
        
        self.anchor_btns = []
        self.anchor_bg = QButtonGroup(self)
        
        # 3x3 Grid
        positions = [
            ("TL", 0, 0), ("TC", 0, 1), ("TR", 0, 2),
            ("CL", 1, 0), ("CC", 1, 1), ("CR", 1, 2),
            ("BL", 2, 0), ("BC", 2, 1), ("BR", 2, 2)
        ]
        
        for name, r, c in positions:
            btn = QRadioButton()
            btn.setStyleSheet("QRadioButton::indicator { width: 15px; height: 15px; }")
            anchor_layout.addWidget(btn, r, c, alignment=Qt.AlignCenter)
            self.anchor_btns.append(btn)
            self.anchor_bg.addButton(btn, r*3 + c)
            
            if name == "CC": # Default Center
                btn.setChecked(True)

        layout.addWidget(anchor_group)


        # Accept button
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # --- Logic Connections ---
        self.pixel_btn.toggled.connect(self.on_unit_changed)
        
    def on_unit_changed(self):
        # Pixels
        if self.pixel_btn.isChecked():
            self.width_input.setText(str(self.current_w))
            self.height_input.setText(str(self.current_h))
        # Percent
        else:
            self.width_input.setText("100")
            self.height_input.setText("100")

    def get_target_size(self):
        try:
            val_w = float(self.width_input.text())
            val_h = float(self.height_input.text())
        except ValueError:
            return self.current_w, self.current_h

        if self.pixel_btn.isChecked():
            return int(val_w), int(val_h)
        else:
            # Calculate percent
            return int(self.current_w * (val_w / 100)), int(self.current_h * (val_h / 100))

    def get_anchor_offset(self, old_w, old_h, new_w, new_h):
        
        # 0 1 2
        # 3 4 5
        # 6 7 8
        idx = self.anchor_bg.checkedId()
        
        # Horizontal Logic
        if idx in [0, 3, 6]:   # Left
            x = 0
        elif idx in [1, 4, 7]: # Center
            x = (new_w - old_w) // 2
        else:                  # Right
            x = new_w - old_w
            
        # Vertical Logic
        if idx in [0, 1, 2]:   # Top
            y = 0
        elif idx in [3, 4, 5]: # Center
            y = (new_h - old_h) // 2
        else:                  # Bottom
            y = new_h - old_h
            
        return x, y

    def apply_changes(self):
        new_w, new_h = self.get_target_size()
        
        if new_w <= 0 or new_h <= 0:
            return

        self.parent.push_undo_state()
        
        old_w, old_h = self.current_w, self.current_h
        dx, dy = self.get_anchor_offset(old_w, old_h, new_w, new_h)
        
        for i, layer in enumerate(self.parent.layer_panel.layers):
            src_img = layer.image
            new_img = np.zeros((new_h, new_w, 4), dtype=np.uint8)
            
            
            sx1 = max(0, -dx)
            sy1 = max(0, -dy)
            sx2 = min(old_w, new_w - dx)
            sy2 = min(old_h, new_h - dy)
            
            # Dest Clip
            dx1 = max(0, dx)
            dy1 = max(0, dy)
            
            w = sx2 - sx1
            h = sy2 - sy1
            
            if w > 0 and h > 0:
                new_img[dy1:dy1+h, dx1:dx1+w] = src_img[sy1:sy1+h, sx1:sx1+w]
            
            layer.set_image(new_img)
        self.parent.display_current_image()
        self.accept()

#/layer
"""
Window for translate image
"""
class TranslateDialog(QDialog):
    """
    Window for translate image
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Translate (Move)")
        self.setFixedSize(320, 260)
        self.parent = parent



        layout = QVBoxLayout(self)

    # Mode selection
        mode_group = QGroupBox("Measurement Unit")
        mode_layout = QHBoxLayout()
        mode_group.setLayout(mode_layout)

        self.unit_group = QButtonGroup(self)
        self.pixel_btn = QRadioButton("Pixels")
        self.percent_btn = QRadioButton("Percent")
        self.pixel_btn.setChecked(True)
        
        self.unit_group.addButton(self.pixel_btn)
        self.unit_group.addButton(self.percent_btn)

        mode_layout.addWidget(self.pixel_btn)
        mode_layout.addWidget(self.percent_btn)
        layout.addWidget(mode_group)



    # Value Input 
        offset_group = QGroupBox("Offset")
        offset_layout = QGridLayout()
        offset_group.setLayout(offset_layout)

        self.validator = QDoubleValidator()

        # X Input
        offset_layout.addWidget(QLabel("Horizontal (X):"), 0, 0)
        self.x_input = QLineEdit("0")
        self.x_input.setValidator(self.validator)
        offset_layout.addWidget(self.x_input, 0, 1)

        # Y Input
        offset_layout.addWidget(QLabel("Vertical (Y):"), 1, 0)
        self.y_input = QLineEdit("0")
        self.y_input.setValidator(self.validator)
        offset_layout.addWidget(self.y_input, 1, 1)
        
        layout.addWidget(offset_group)


    # Options checkbox
        options_layout = QVBoxLayout()
        
        self.apply_all_chk = QCheckBox("Apply to All Layers")
        self.apply_all_chk.setChecked(False)
        options_layout.addWidget(self.apply_all_chk)
        
        self.wrap_chk = QCheckBox("Wrap Around (Seamless)")
        self.wrap_chk.setToolTip("Pixels moving off one edge appear on the opposite edge")
        options_layout.addWidget(self.wrap_chk)
        
        layout.addLayout(options_layout)

    # Apply buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_offset_pixels(self, w, h):
        try:
            val_x = float(self.x_input.text())
            val_y = float(self.y_input.text())
        except ValueError:
            return 0, 0

        if self.pixel_btn.isChecked():
            return int(val_x), int(val_y)
        else:
            dx = int(w * (val_x / 100.0))
            dy = int(h * (val_y / 100.0))
            return dx, dy

    def apply_changes(self):
        if self.apply_all_chk.isChecked():
            targets = self.parent.layer_panel.layers
        else:
            current = self.parent.get_current_focus_layer()
            targets = [current] if current else []

        if not targets:
            return

        self.parent.push_undo_state()

        # 2. Process Targets
        for layer in targets:
            img = layer.image
            h, w = img.shape[:2]
            
            dx, dy = self.get_offset_pixels(w, h)
            if dx == 0 and dy == 0:
                continue

            M = np.float32([[1, 0, dx], [0, 1, dy]])

            # Wrap Mode
            if self.wrap_chk.isChecked():
                res_img = np.roll(img, dy, axis=0)
                res_img = np.roll(res_img, dx, axis=1)
                layer.image = res_img
            # Normal mode
            else:
                layer.image = cv2.warpAffine(
                    img, M, (w, h), 
                    borderMode=cv2.BORDER_CONSTANT, 
                    borderValue=(0, 0, 0, 0)
                )
               
               
        self.parent.selected_rect = (0, 0, 0, 0)
        self.parent.image_label.selection_rect = QRect()
        
        self.parent.display_current_image()
        self.accept()

#/layer
"""
View image details Information
"""
class ImageDetailsDialog(QDialog):
    """
    View image details Information
    """
    def __init__(self, parent=None, path=None):
        super().__init__(parent)
        self.setWindowTitle("Image Detail")
        self.setFixedSize(380, 280)
        self.parent = parent

        layout = QVBoxLayout(self)

        # Gather Data
        # 1. File Info
        file_path = path
        if not file_path:
            file_name = "Untitled (Unsaved)"
            file_loc = "N/A"
            file_size_str = "N/A"
            file_fmt = "N/A"
        else:
            file_name = os.path.basename(file_path)
            file_loc = os.path.dirname(file_path)
            # Disk Size
            try:
                size_bytes = os.path.getsize(file_path)
                file_size_str = f"{size_bytes / 1024:.2f} KB"
            except:
                file_size_str = "Unknown"
            file_fmt = os.path.splitext(file_path)[1].lstrip('.').upper()

        # 2. Canvas Info (The Composite Image)
        if parent.display_image is not None:
            comp_h, comp_w = parent.display_image.shape[:2]
            # RAM Usage (Composite)
            ram_bytes = parent.display_image.nbytes
            ram_str = f"{ram_bytes / (1024*1024):.2f} MB"
            
            channels = 1 if len(parent.display_image.shape) == 2 else parent.display_image.shape[2]
            dtype = str(parent.display_image.dtype)
        else:
            comp_h, comp_w = 0, 0
            ram_str = "0 MB"
            channels = 0
            dtype = "N/A"

    

        # --- UI CONSTRUCTION ---

        # GROUP 1: File Information
        file_group = QGroupBox("File Information")
        file_form = QFormLayout()
        
        file_form.addRow("Name:", QLabel(file_name))
        
        # Truncate path if too long
        path_lbl = QLabel(file_loc)
        path_lbl.setWordWrap(True) 
        file_form.addRow("Location:", path_lbl)
        
        file_form.addRow("Disk Size:", QLabel(file_size_str))
        file_form.addRow("Format:", QLabel(file_fmt))
        
        file_group.setLayout(file_form)
        layout.addWidget(file_group)

        # GROUP 2: Canvas / Memory Information
        img_group = QGroupBox("Canvas Data")
        img_form = QFormLayout()
        
        img_form.addRow("Dimensions:", QLabel(f"{comp_w} × {comp_h} px"))
        img_form.addRow("Channels:", QLabel(str(channels)))
        img_form.addRow("Data Type:", QLabel(dtype))
        img_form.addRow("Memory (RAM):", QLabel(ram_str))
        
        img_group.setLayout(img_form)
        layout.addWidget(img_group)

        

        # Close Button
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)


#/ #/layer
"""
Window for crop image (By pixels or percent)
"""
class CropDialog(QDialog):
    """
    Window for crop image (By pixels or percent)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Canvas")
        self.setFixedSize(360, 380)
        self.parent = parent

        # Get initial dimensions from active layer or default
        current_layer = self.parent.get_current_focus_layer()
        self.orig_w = current_layer.image.shape[1]
        self.orig_h = current_layer.image.shape[0]



        layout = QVBoxLayout(self)

        # --- 1. Unit Selection ---
        unit_group = QGroupBox("Units")
        unit_layout = QHBoxLayout()
        unit_group.setLayout(unit_layout)

        self.unit_bg = QButtonGroup(self)
        self.btn_px = QRadioButton("Pixels")
        self.btn_pct = QRadioButton("Percent")
        self.btn_px.setChecked(True)
        
        self.unit_bg.addButton(self.btn_px)
        self.unit_bg.addButton(self.btn_pct)

        unit_layout.addWidget(self.btn_px)
        unit_layout.addWidget(self.btn_pct)
        layout.addWidget(unit_group)

        # --- 2. Margins Input ---
        margin_group = QGroupBox("Crop Margins")
        grid = QGridLayout()
        margin_group.setLayout(grid)

        self.inputs = {}
        labels = ["Top", "Bottom", "Left", "Right"]
        
        # Layout: 
        #      Top
        # Left     Right
        #     Bottom

        positions = [(0, 1), (2, 1), (1, 0), (1, 2)]

        for lbl, pos in zip(labels, positions):
            l_widget = QLabel(f"{lbl}:")
            l_widget.setAlignment(Qt.AlignCenter)
            
            inp = QLineEdit("0")
            inp.setAlignment(Qt.AlignCenter)
            if self.btn_px.isChecked():
                inp.setValidator(QIntValidator(0, 10000))
            
            grid.addWidget(l_widget, pos[0]*2, pos[1])     # Label
            grid.addWidget(inp, pos[0]*2 + 1, pos[1])      # Input
            
            self.inputs[lbl.lower()] = inp
            inp.textChanged.connect(self.update_info_label)

        layout.addWidget(margin_group)

        # --- 3. Result Info ---
        info_group = QGroupBox("Result")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_mod_label = QLabel()
        self.info_mod_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.info_label)
        info_layout.addWidget(self.info_mod_label)
        
        layout.addWidget(info_group)
        self.update_info_label()

        # --- 4. Buttons ---
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.btn_px.toggled.connect(self.on_unit_changed)

    def on_unit_changed(self):
        is_px = self.btn_px.isChecked()
        
        for key, inp in self.inputs.items():
            try:
                val = float(inp.text())
            except ValueError:
                val = 0
            
        # Percent -> Pixel
            if is_px:
                base = self.orig_w if key in ['left', 'right'] else self.orig_h
                new_val = int(base * (val / 100.0))
                inp.setValidator(QIntValidator(0, base))
        # Pixel -> Percent
            else:
                base = self.orig_w if key in ['left', 'right'] else self.orig_h
                new_val = (val / base) * 100.0
                inp.setValidator(QDoubleValidator(0.0, 100.0, 2))
                
            inp.setText(f"{new_val:.2f}" if not is_px else str(new_val))

    def get_margins_in_pixels(self):
        vals = {}
        for key, inp in self.inputs.items():
            try:
                v = float(inp.text())
            except ValueError:
                v = 0
            vals[key] = v

        if self.btn_pct.isChecked():
            top = int(self.orig_h * (vals['top'] / 100.0))
            bottom = int(self.orig_h * (vals['bottom'] / 100.0))
            left = int(self.orig_w * (vals['left'] / 100.0))
            right = int(self.orig_w * (vals['right'] / 100.0))
        else:
            top = int(vals['top'])
            bottom = int(vals['bottom'])
            left = int(vals['left'])
            right = int(vals['right'])
            
        return top, bottom, left, right

    def update_info_label(self):
        t, b, l, r = self.get_margins_in_pixels()
        
        new_w = self.orig_w - l - r
        new_h = self.orig_h - t - b
        
        if new_w > 0 and new_h > 0:
            color = "black" 
        else: 
            color = "red"
        
        self.info_label.setText(
            f"Original: {self.orig_w} × {self.orig_h}\n"
        )
        self.info_mod_label.setStyleSheet(f"color: {color}; font-weight:bold;")
        self.info_mod_label.setText(
            f"New Size: {new_w} × {new_h}"
        )


    def apply_changes(self):
        t, b, l, r = self.get_margins_in_pixels()
        
        new_w = self.orig_w - l - r
        new_h = self.orig_h - t - b
        if new_w <= 0 or new_h <= 0:
            QMessageBox.warning(self, "Error", "Size cannot be negative")
            return

        

        self.parent.push_undo_state()
        
        
        for layer in self.parent.layer_panel.layers:
            img = layer.image
            cropped = img[t : self.orig_h - b, l : self.orig_w - r]
            layer.image = cropped.copy()

        self.parent.selected_rect = (0, 0, 0, 0)
        self.parent.image_label.selection_rect = QRect()

        self.parent.display_current_image(reset_scale=True)
        self.accept()


