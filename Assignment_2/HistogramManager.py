import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame
)
from PyQt5.QtGui import (
    QPainter, QColor, QPainterPath, QPalette, QCloseEvent
)
from PyQt5.QtCore import Qt

from Assignment_2.LayerManager import LayerManager





#/layer
"""
Histogram Calculation Utility
"""
class HistogramCalculator:
    """
    Histogram Calculation Utility
    """
    
    @staticmethod
    def compute_histogram(image, mode='RGB'):
        """
        mode: 'RGB' or 'COMBINED'
        returns: dict { 'R':hist, 'G':hist, 'B':hist } or {'COMBINED':hist }
        """
        if image is None:
            return None

        if len(image.shape) == 3:
            b, g, r = cv2.split(image)
        else:
            r = g = b = image

        if mode == 'RGB':
            return {
                "R": cv2.calcHist([r], [0], None, [256], [0, 256]).flatten(),
                "G": cv2.calcHist([g], [0], None, [256], [0, 256]).flatten(),
                "B": cv2.calcHist([b], [0], None, [256], [0, 256]).flatten(),
            }

        elif mode == "COMBINED":
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            return {
                "COMBINED": cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
            }

"""
Widget to display histogram data.
"""
class HistogramWidget(QWidget):
    """
    Widget to display histogram data.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hist_data = {} 
        self.setMinimumHeight(100)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)

    def set_data(self, data):
        self.hist_data = data
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Dark Background
        painter.fillRect(0, 0, w, h, QColor(240, 240, 240))
        
        if not self.hist_data:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        # Determine scaling
        max_val = 1
        for channel in self.hist_data.values():
            if len(channel) > 0:
                max_val = max(max_val, np.max(channel))
        
        if max_val == 0: max_val = 1

        # Colors mapping
        colors = {
            'R': (QColor(255, 100, 100, 255), QColor(255, 0, 0, 60)),
            'G': (QColor(100, 255, 100, 255), QColor(0, 255, 0, 60)),
            'B': (QColor(100, 100, 255, 255), QColor(0, 0, 255, 60)),
            'Gray': (QColor(120, 120, 120, 255), QColor(200, 200, 200, 80))
        }

        # Draw
        for channel_name, data in self.hist_data.items():
            if channel_name not in colors or len(data) != 256: continue

            pen_color, brush_color = colors[channel_name]
            
            path = QPainterPath()
            path.moveTo(0, h)

            x_step = w / 256.0
            
            for i, val in enumerate(data):
                bar_h = (val / max_val) * (h - 5)
                path.lineTo(i * x_step, h - bar_h)

            path.lineTo(w, h)
            path.closeSubpath()

            painter.setPen(Qt.NoPen)
            painter.setBrush(brush_color)
            painter.drawPath(path)
            
            painter.setPen(pen_color)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

"""
Histogram Display Panel in the Main Window
"""
class HistogramPanel(QWidget):
    """
    Histogram Display Panel in the Main Window
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_mode = "RGB" # or "GRAY"
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        
        # Mode Button
        self.mode_btn = QPushButton("Mode: RGB")
        self.mode_btn.setToolTip("Click to toggle between RGB and Grayscale")
        self.mode_btn.clicked.connect(self.toggle_mode)
        layout.addWidget(self.mode_btn)
        

        
        layout.addWidget(QLabel("<b>Original</b>"))
        self.ori_histogram = HistogramWidget(self)
        layout.addWidget(self.ori_histogram)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- Bottom Section: Combined Output ---
        layout.addWidget(QLabel("<b>Modified</b>"))
        self.mod_histogram = HistogramWidget(self)
        layout.addWidget(self.mod_histogram)

        

    def toggle_mode(self):
        if self.current_mode == "RGB":
            self.current_mode = "GRAY"
            self.mode_btn.setText("Mode: Grayscale")
        else:
            self.current_mode = "RGB"
            self.mode_btn.setText("Mode: RGB")
        
        self.update_histogram()

    def update_histogram(self):
        
        # Original Image
        ori_img = self.parent.original_image_list[self.parent.current_index]
        # Current Image
        current_focus = self.parent.get_focus_window()
        mod_img = current_focus.display_image.copy()


        data_orig = self.calc_data(ori_img)
        data_curr = self.calc_data(mod_img)

        self.ori_histogram.set_data(data_orig)
        self.mod_histogram.set_data(data_curr)

    def calc_data(self, img):
        data = {}
        if img is None: 
            return data

        mask = None
        if len(img.shape) == 3:
            channels = img.shape[2]
            if channels == 4:
                a = img[:, :, 3] 
                mask = (a > 0).astype(np.uint8) * 255


        # --- Calculation ---
        if self.current_mode == "RGB":
            if len(img.shape) == 2:
                    hist = cv2.calcHist([img], [0], mask, [256], [0, 256])
                    data['Gray'] = hist.flatten()
            else:

                # 3 or 4-channel image
                if img.shape[2] >= 3:
                    hist_b = cv2.calcHist([img], [0], mask, [256], [0, 256])
                    hist_g = cv2.calcHist([img], [1], mask, [256], [0, 256])
                    hist_r = cv2.calcHist([img], [2], mask, [256], [0, 256])
                    
                    data['B'] = hist_b.flatten()
                    data['G'] = hist_g.flatten()
                    data['R'] = hist_r.flatten()
        
        # Grayscale Mode
        else: 
            gray = img
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
            hist = cv2.calcHist([gray], [0], mask, [256], [0, 256])
            data['Gray'] = hist.flatten()
            
        return data

"""
Histogram Display Window
"""
class HistogramWindow(QMainWindow):
    """
    Histogram Display Window
    """
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        self.parent = parent
        self.setWindowTitle("Real-Time Histogram Comparison")
        self.resize(460, 200)
        self.current_mode = "RGB"
        
        
        
        central = QWidget()
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # --- Controls ---
        top_bar = QHBoxLayout()
        self.toggle_btn = QPushButton("Mode: RGB")
        self.toggle_btn.clicked.connect(self.toggle_mode)
        top_bar.addWidget(self.toggle_btn)
        main_layout.addLayout(top_bar)

        # --- Display Area (Side by Side) ---
        hbox = QHBoxLayout()
        
        # Left: Original
        ori_vbox = QVBoxLayout()
        ori_label = QLabel("Original ")
        ori_label.setAlignment(Qt.AlignCenter)
        ori_label.setFixedHeight(30)
        self.hist_orig = HistogramWidget(self)
        ori_vbox.addWidget(ori_label)
        ori_vbox.addWidget(self.hist_orig)
        
        # Right: Modified
        mod_vbox = QVBoxLayout()
        mod_label = QLabel("Modified ")
        mod_label.setAlignment(Qt.AlignCenter)
        mod_label.setFixedHeight(30)
        self.hist_curr = HistogramWidget(self)
        mod_vbox.addWidget(mod_label)
        mod_vbox.addWidget(self.hist_curr)

        hbox.addLayout(ori_vbox)
        
        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        hbox.addWidget(line)
        
        hbox.addLayout(mod_vbox)
        
        main_layout.addLayout(hbox)

        # Initial Update
        self.update_histogram()

    def toggle_mode(self):
        if self.current_mode == "RGB":
            self.current_mode = "GRAY"
            self.toggle_btn.setText("Mode: Grayscale")
        else:
            self.current_mode = "RGB"
            self.toggle_btn.setText("Mode: RGB")

        self.update_histogram()

    def update_histogram(self):

        ori_img = self.parent.original_image_list[self.parent.current_index]
        # Current Image
        _, layers = self.parent.image_list[self.parent.current_index]
        mod_img = LayerManager.compose_layers(layers)

        # 2. Calculate Data (Using robust method)
        data_orig = self.calc_data(ori_img)
        data_curr = self.calc_data(mod_img)

        # 3. Update Widgets
        self.hist_orig.set_data(data_orig)
        self.hist_curr.set_data(data_curr)

    def calc_data(self, img):
        """Calculates histogram arrays robustly."""
        data = {}
        
        # Safety Checks
        if img is None: return data
        if not isinstance(img, np.ndarray): return data
        if img.size == 0: return data

        # Mask logic for Transparency
        mask = None
        if len(img.shape) == 3 and img.shape[2] == 4:
            # BGRA -> Use Alpha as mask
            try:
                a = img[:, :, 3]
                mask = (a > 0).astype(np.uint8) * 255
            except Exception:
                mask = None

        # Calculation
        if self.current_mode == "RGB":
            # Handle Grayscale image in RGB mode
            if len(img.shape) == 2:
                 try:
                    hist = cv2.calcHist([img], [0], mask, [256], [0, 256])
                    data['Gray'] = hist.flatten()
                 except cv2.error: pass
            
            # Handle Color image
            elif len(img.shape) == 3 and img.shape[2] >= 3:
                try:
                    hist_b = cv2.calcHist([img], [0], mask, [256], [0, 256])
                    hist_g = cv2.calcHist([img], [1], mask, [256], [0, 256])
                    hist_r = cv2.calcHist([img], [2], mask, [256], [0, 256])
                    
                    data['B'] = hist_b.flatten()
                    data['G'] = hist_g.flatten()
                    data['R'] = hist_r.flatten()
                except cv2.error:
                    return data
        
        else: # Grayscale Mode
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
                
            try:
                hist = cv2.calcHist([gray], [0], mask, [256], [0, 256])
                data['Gray'] = hist.flatten()
            except cv2.error:
                return data
            
        return data

    def closeEvent(self, event: QCloseEvent):
        self.parent.histogram_display = None
        event.accept()

