import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QGridLayout, QColorDialog,
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox,
    QCheckBox, QGroupBox, QSlider, QSpinBox, QHBoxLayout, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QColor, QCloseEvent



"""
Color Palette Widget
For Pen Color Selection
"""
class ColorPalette(QWidget):
    """For Pen Color Selection"""

    def __init__(self, parent=None, color_callback=None):
        super().__init__(parent)
        self.color_callback = color_callback
        self.parent = parent
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # self.setFixedHeight(80)
        self.layout.setSpacing(1)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.colors = [
            (47,14,23), (105,50,28), (60,65,117), (95,96,55),
            (112,114,46), (62,107,157), (60,89,228), (185,138,173),
            (52,145,190), (190,198,79), (114,194,168), (209,217,163),
            (82,203,255), (156,209,255), (169,246,255), (229,252,255)
        ]

        self.buttons = []
        for i, color in enumerate(self.colors):
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"background-color: rgb({color[2]}, {color[1]}, {color[0]}); border: 1px solid #555;")
            btn.installEventFilter(self)
            btn.color_index = i
            self.layout.addWidget(btn, i // 8, i % 8)
            self.buttons.append(btn)

    def eventFilter(self, source, event):
        if event.type() == event.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.select_color(source.color_index)
            elif event.button() == Qt.RightButton:
                self.customize_color(source.color_index)
        return super().eventFilter(source, event)

    def select_color(self, index):
        color = self.colors[index]
        if self.color_callback:
            self.color_callback(color)

    def customize_color(self, index):
        choice = QColorDialog.getColor(QColor(
            self.colors[index][2],
            self.colors[index][1],
            self.colors[index][0]
        ), self, "Select New Palette Color")

        if choice.isValid():
            bgr = (choice.blue(), choice.green(), choice.red())
            self.colors[index] = bgr
            self.buttons[index].setStyleSheet(
                f"background-color: rgb({bgr[2]}, {bgr[1]}, {bgr[0]}); border: 1px solid #555;"
            )

# --------------------------------------------------------------------------------
"""
#/ #/layer
Window for converting Color Fromat (RGB, GRAY, HSV, HLS, Lab, YCrCb)
"""
class ColorConvertDialog(QDialog):
    """
    Window for converting Color Fromat (RGB, GRAY, HSV, HLS, Lab, YCrCb)
    """
    
    def __init__(self, parent, original_image):
        super().__init__(parent)
        self.setWindowTitle("Color Conversion")
        self.setFixedSize(300, 180)
        self.parent = parent
        
        self.original_layer = []
        for layer in self.parent.layer_panel.layers:
            self.original_layer.append((layer, layer.image.copy()))
        self.original_image = original_image.copy()
        

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Select Color Space:"))
        self.combo = QComboBox()
        self.combo.addItems(["RGB", "GRAY", "HSV", "HLS", "Lab (CIE)", "YCrCb"])
        layout.addWidget(self.combo)

        # Checkbox
        self.preview_checkbox = QCheckBox("Preview Changes")
        self.preview_checkbox.setChecked(True)
        layout.addWidget(self.preview_checkbox)
        
        self.apply_all_checkbox = QCheckBox("Apply to All Layers")
        self.apply_all_checkbox.setChecked(False)
        layout.addWidget(self.apply_all_checkbox)

        # Button Box (OK / Cancel)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.buttons)

        # Connections
        self.combo.currentIndexChanged.connect(lambda: self.preview_color_change(False))
        self.preview_checkbox.stateChanged.connect(lambda: self.preview_color_change(False))
        self.apply_all_checkbox.stateChanged.connect(lambda: self.preview_color_change(False))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)


    def preview_color_change(self, apply=False):
        mode = self.combo.currentText()
        is_preview = self.preview_checkbox.isChecked()
        apply_all = self.apply_all_checkbox.isChecked()

        if not is_preview and not apply:
            self.restore_all_layers()
            self.parent.display_current_image()
            return
        
        if apply_all:
            target = self.original_layer
        else:
            self.restore_all_layers()
            
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        
        # Apply process
        for layer, image in target:
            converted = self.convert_to_mode(image, mode)
            
            current_focus = self.parent.get_focus_window()
            if current_focus.selected_rect != (0, 0, 0, 0):
                x1, y1, x2, y2 = current_focus.selected_rect

                h, w = converted.shape[:2]
                x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
                y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
                
                # Ensure valid region
                if x1 < x2 and y1 < y2:
                    img = image.copy()
                    region = converted[y1:y2, x1:x2]

                    img[y1:y2, x1:x2] = region
                    layer.set_image(img)
                    continue
            layer.set_image(converted)
            
        self.parent.display_current_image()
                

    def restore_all_layers(self):
        """Reverts all layers to the state they were in when dialog opened"""
        for layer, image in self.original_layer:
            layer.set_image(image.copy())
        
    def convert_to_mode(self, img, mode):
        if mode == "RGB": return img.copy()

        # Handle Alpha
        has_alpha = (img.shape[2] == 4)
        if has_alpha:
            b, g, r, a = cv2.split(img)
            bgr_img = cv2.merge([b, g, r])
        else:
            bgr_img = img
        
        # Convert
        res_img = bgr_img
        if mode == "GRAY":
            gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
            res_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif mode == "HSV":
            res_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        elif mode == "HLS":
            res_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HLS)
        elif mode == "Lab (CIE)":
            res_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2Lab)
        elif mode == "YCrCb":
            res_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)

        if has_alpha:
            b, g, r = cv2.split(res_img)
            return cv2.merge([b, g, r, a])
        else:
            return res_img

    def accept(self):
        self.preview_color_change(apply=True)
        super().accept()

    def reject(self):
        self.restore_all_layers()
        self.parent.display_current_image()
        super().reject()
    def closeEvent(self, event: QCloseEvent):
        self.reject()
        event.accept()

    def get_selected_mode(self):
        return self.combo.currentText()

"""
#/ #/layer
Window for color edit (Hue, Saturation, Brightness)
"""
class ColorAdjustDialog(QDialog):
    """
    Window for color edit (Hue, Saturation, Brightness)
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Adjust Color & Saturation")
        self.setFixedSize(500, 180)
        self.parent = parent
        
        self.original_layer = []
        for layer in self.parent.layer_panel.layers:
            self.original_layer.append((layer, layer.image.copy()))
        current_layer = self.parent.get_current_focus_layer()
        if current_layer:
            self.original_image = current_layer.image.copy()
        
        
        
        main_layout = QVBoxLayout(self)
        
        # Group Box for Controls
        group = QGroupBox("Control Panel")
        grid = QGridLayout()
        group.setLayout(grid)
        
        # -- Helpers to build rows --
        self.hue_slider, self.hue_spin = self.create_slider_row(grid, 0, "Hue:", -180, 180)
        self.sat_slider, self.sat_spin = self.create_slider_row(grid, 1, "Saturation:", -100, 100)
        self.val_slider, self.val_spin = self.create_slider_row(grid, 2, "Lightness:", -100, 100)

        main_layout.addWidget(group)

        # -- Options --
        options_layout = QHBoxLayout()
        self.preview_checkbox = QCheckBox("Preview")
        self.preview_checkbox.setChecked(True)
        
        self.apply_all_checkbox = QCheckBox("Apply to All Layers")
        self.apply_all_checkbox.setChecked(False)

        options_layout.addWidget(self.preview_checkbox)
        options_layout.addWidget(self.apply_all_checkbox)
        main_layout.addLayout(options_layout)

        # -- Buttons --
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(self.button_box)

        # 3. Connections
        # Connect Sliders and Spins
        self.connect_slider_spin(self.hue_slider, self.hue_spin)
        self.connect_slider_spin(self.sat_slider, self.sat_spin)
        self.connect_slider_spin(self.val_slider, self.val_spin)

        # Connect Logic
        self.preview_checkbox.stateChanged.connect(lambda: self.preview_update(False))
        self.apply_all_checkbox.stateChanged.connect(lambda: self.preview_update(False))
        
        self.button_box.accepted.connect(self.apply_changes)
        self.button_box.rejected.connect(self.cancel_changes)

    def create_slider_row(self, layout, row, label_text, min_val, max_val):
        label = QLabel(label_text)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(0)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #888;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #444;
                border: 1px solid #444;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(0)
        spin.setFixedWidth(60)

        layout.addWidget(label, row, 0)
        layout.addWidget(slider, row, 1)
        layout.addWidget(spin, row, 2)
        
        return slider, spin
    def connect_slider_spin(self, slider, spin):
        slider.valueChanged.connect(lambda v: spin.setValue(v))
        spin.valueChanged.connect(lambda v: slider.setValue(v))
        # slider.valueChanged.connect(self.preview_update)
        slider.sliderReleased.connect(self.preview_update)
        
    def process_image(self, img, h_shift, s_shift, v_shift):
        has_alpha = False
        if img.shape[2] == 4:
            has_alpha = True
            b, g, r, a = cv2.split(img)
            bgr = cv2.merge([b, g, r])
        else:
            bgr = img

        # 2. Convert to HSV
        # Use int16 to prevent overflow during addition
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.int16)

        # 3. Apply Shifts
        # Hue is circular (0-180 in OpenCV)
        hsv[:, :, 0] = (hsv[:, :, 0] + h_shift) % 180
        
        # Saturation (0-255) - Clip
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] + s_shift, 0, 255)
        
        # Value/Brightness (0-255) - Clip
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] + v_shift, 0, 255)

        # 4. Convert back to BGR
        hsv = hsv.astype(np.uint8)
        bgr_result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # 5. Merge Alpha
        if has_alpha:
            b_new, g_new, r_new = cv2.split(bgr_result)
            return cv2.merge([b_new, g_new, r_new, a])
        else:
            return bgr_result
    
    def preview_update(self, apply=False):
        if self.original_image is None: return

        # Get Values
        h_shift = self.hue_slider.value()
        s_shift = self.sat_slider.value()
        v_shift = self.val_slider.value()
        
        is_preview = self.preview_checkbox.isChecked()
        apply_all = self.apply_all_checkbox.isChecked()

        if not is_preview and not apply:
            self.restore_all_layers()
            self.parent.display_current_image()
            return

        # Define targets
        if apply_all:
            targets = self.original_layer
        else:
            self.restore_all_layers()
            
            current_layer = self.parent.get_current_focus_layer()
            targets = [(current_layer, self.original_image)]



        # Processing
        for layer, original_img in targets:
            processed_img = self.process_image(original_img, h_shift, s_shift, v_shift)
            
            # Handle Selection Clipping (Only apply to selected area)
            current_focus = self.parent.get_focus_window()
            if current_focus.selected_rect != (0, 0, 0, 0):
                x1, y1, x2, y2 = current_focus.selected_rect
                h, w = processed_img.shape[:2]
                
                # Bounds check
                x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
                y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

                if x1 < x2 and y1 < y2:
                    # Create composite: Original image + Processed Region
                    region = original_img.copy()
                    region[y1:y2, x1:x2] = processed_img[y1:y2, x1:x2]
                    processed_img = region
            layer.set_image(processed_img)

        self.parent.display_current_image()
    
    
    
    def restore_all_layers(self):
        for layer, original_img in self.original_layer:
            layer.image = original_img.copy()
    
    def apply_changes(self):
        self.preview_update(apply=True)
        self.accept()
    def cancel_changes(self):
        self.restore_all_layers()
        self.reject()
    def closeEvent(self, event: QCloseEvent):
        self.cancel_changes()
        event.accept()

"""
#/ #/layer
Window for color edit (Brightness, Intensity, Contrast)
"""
class ColorIntensityAdjustDialog(QDialog):
    """
    Window for color edit (Brightness, Intensity, Contrast)
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Adjust Color Intensity & Contrast")
        self.setFixedSize(500, 180)
        self.parent = parent

        self.original_layer = []
        for layer in self.parent.layer_panel.layers:
            self.original_layer.append((layer, layer.image.copy()))
        current_layer = self.parent.get_current_focus_layer()
        self.original_image = current_layer.image.copy()



        main_layout = QVBoxLayout(self)
        
        # Controls Group
        group = QGroupBox("Adjustments")
        grid = QGridLayout()
        group.setLayout(grid)
        
        self.bright_slider, self.bright_spin = self.create_slider_row(grid, 0, "Brightness:", -100, 100)
        self.contrast_slider, self.contrast_spin = self.create_slider_row(grid, 1, "Contrast:", -100, 100)
        self.vib_slider, self.vib_spin = self.create_slider_row(grid, 2, "Intensity:", -100, 100)

        main_layout.addWidget(group)

        # Options
        options_layout = QHBoxLayout()
        self.preview_checkbox = QCheckBox("Preview")
        self.preview_checkbox.setChecked(True)
        
        self.apply_all_checkbox = QCheckBox("Apply to All Layers")
        self.apply_all_checkbox.setChecked(False)

        options_layout.addWidget(self.preview_checkbox)
        options_layout.addWidget(self.apply_all_checkbox)
        main_layout.addLayout(options_layout)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(self.button_box)

        # signal
        self.connect_slider_spin(self.bright_slider, self.bright_spin)
        self.connect_slider_spin(self.contrast_slider, self.contrast_spin)
        self.connect_slider_spin(self.vib_slider, self.vib_spin)

        self.preview_checkbox.stateChanged.connect(lambda: self.preview_update(False))
        self.apply_all_checkbox.stateChanged.connect(lambda: self.preview_update(False))
        
        self.button_box.accepted.connect(self.apply_changes)
        self.button_box.rejected.connect(self.cancel_changes)
        
        
    def create_slider_row(self, layout, row, label_text, min_val, max_val):
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(0)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #888;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #444;
                border: 1px solid #444;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(0)
        spin.setFixedWidth(60)

        layout.addWidget(label, row, 0)
        layout.addWidget(slider, row, 1)
        layout.addWidget(spin, row, 2)
        return slider, spin

    def connect_slider_spin(self, slider, spin):
        slider.valueChanged.connect(lambda v: spin.setValue(v))
        spin.valueChanged.connect(lambda v: slider.setValue(v))
        slider.sliderReleased.connect(self.preview_update)
        
    def preview_update(self, apply=False):
        if self.original_image is None: return
        
        is_preview = self.preview_checkbox.isChecked()
        apply_all = self.apply_all_checkbox.isChecked()
        
        if not is_preview and not apply:
            self.restore_all_layers()
            self.parent.display_current_image()
            return


        bright = self.bright_slider.value()
        contrast = self.contrast_slider.value()
        vibrance = self.vib_slider.value()
    # Get target layer
        if apply_all:
            targets = self.original_layer
        else:
            self.restore_all_layers()
            
            current_layer = self.parent.get_current_focus_layer()
            targets = [(current_layer, self.original_image)]



        # Processing 
        for layer, original_img in targets:
            processed = self.process_image(original_img, bright, contrast, vibrance)
            
            # Handle Selection Clipping
            current_focus = self.parent.get_focus_window()
            if current_focus.selected_rect != (0, 0, 0, 0):
                x1, y1, x2, y2 = current_focus.selected_rect
                h, w = processed.shape[:2]
                
                x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
                y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

                if x1 < x2 and y1 < y2:
                    region = original_img.copy()
                    region[y1:y2, x1:x2] = processed[y1:y2, x1:x2]
                    processed = region
            layer.set_image(processed)

        self.parent.display_current_image()

    def process_image(self, img, bright, contrast, vibrance):
        b, g, r, a = cv2.split(img)
        bgr_image = cv2.merge([b, g, r])

    # Brightness
        if bright != 0:
            hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV).astype(np.int16)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + bright, 0, 255)
            hsv = hsv.astype(np.uint8)
            bgr_image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # Convert for Contrast and Vibrance
        bgr_float = bgr_image.astype(np.float32)

    # Contrast
        if contrast != 0:
            factor = 1.0 + (contrast / 100.0)
            bgr_float = (bgr_float - 127.5) * factor + 127.5
            bgr_float = np.clip(bgr_float, 0, 255)

    # Vibrance
        if vibrance != 0:
            gray = cv2.cvtColor(bgr_float.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
            gray_3c = cv2.merge([gray, gray, gray])
            
            factor = 1.0 + (vibrance / 100.0)
            bgr_float = gray_3c + (bgr_float - gray_3c) * factor
            bgr_float = np.clip(bgr_float, 0, 255)

        # Merge result
        result_bgr = bgr_float.astype(np.uint8)
        
        b_new, g_new, r_new = cv2.split(result_bgr)
        return cv2.merge([b_new, g_new, r_new, a])

    def restore_all_layers(self):
        for layer, original_img in self.original_layer:
            layer.image = original_img.copy()
        


    def apply_changes(self):
        self.preview_update(apply=True)
        self.accept()

    def cancel_changes(self):
        self.restore_all_layers()
        self.parent.display_current_image()
        self.reject()
    def closeEvent(self, event: QCloseEvent):
        self.cancel_changes()
        event.accept()

