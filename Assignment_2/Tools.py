import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSizePolicy,
    QDialog, QCheckBox, QLabel, QSlider, QPushButton, QColorDialog
)
from PyQt5.QtGui import (
    QImage, QPixmap, QCloseEvent, QPainter, QPen, QColor, QPainterPath
)
from PyQt5.QtCore import Qt, QRect

from Assignment_2.LayerManager import LayerManager
from Assignment_1.SelectLabel import SelectLabel





#/layer
"""
Sub-window to view image in a separate window.
Support all operations as main window expects zoom in/out
"""
class ImageViewWindow(QMainWindow):
    """
    Sub-window to view image in a separate window.\n
    Support all operations as main window expects zoom in/out
    """
    
    def __init__(self, parent=None, image_index=-1, image_name="", 
                 image_list=[]):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.parent = parent
        
        title = os.path.basename(image_name)
        self.setWindowTitle(title)
        self.resize(400, 400)

        self.current_index = image_index
        self.layer_panel = parent.layer_panel
        self.image_list = image_list
        self.original_image_list = parent.original_image_list
        self.histogram_display = parent.histogram_display
        self.dialog_open = parent.dialog_open
        
    ## Data Initiation
        self.on_focus = False
        self.display_image = None
        self.display_scale_x = 1.0
        self.display_scale_y = 1.0
        self.display_offset = 0.0, 0.0
        
        self.undo_stack = self.parent.undo_stack
        
        self.selected_rect = (0, 0, 0, 0)
        
    ## Inherit Data
        self.pen_color = parent.pen_color
        self.pen_thickness = parent.pen_thickness
        
        self.grid_size = parent.grid_size
        self.grid_thickness = parent.grid_thickness
        self.grid_color = parent.grid_color
        
        self.ruler_thickness = parent.ruler_thickness
        self.ruler_grid = parent.ruler_grid
        
        
    ## Setup UI --------------------------        

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # self.image_label = QLabel()
        self.image_label = SelectLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)

        


    def set_image(self, image):
        if image is None:
            self.image_label.clear()
            return

        self.display_image = image.copy()
        self.update_scaled_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scaled_image()

    def update_scaled_image(self):
        if self.display_image is None:
            return

        image = self.display_image
        if len(image.shape) == 2: 
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
        elif len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        h, w, _ = image.shape
        
        bytes_per_line = image.strides[0]
        qt_image = QImage(
            image.data, 
            w, h, bytes_per_line, 
            QImage.Format_RGBA8888
        ).rgbSwapped()
        pix = QPixmap.fromImage(qt_image)

        label_w = self.image_label.width()
        label_h = self.image_label.height()
        
        # Scale to fit window
        scaled_pix = pix.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pix)

        x_offset = (label_w - scaled_pix.width()) // 2
        y_offset = (label_h - scaled_pix.height()) // 2
        
        self.display_scale_x = scaled_pix.width() / w
        self.display_scale_y = scaled_pix.height() / h
        self.display_offset = (x_offset, y_offset)

        

    def event(self, e):
        if e.type() == 24:  # QEvent.WindowActivate
            self.parent.activateWindow()
            self.parent.raise_()
            
            self.set_current_index_focus()
            if self.histogram_display is not None:
                self.histogram_display.update_histogram()
            return True
        return super().event(e)
    def closeEvent(self, event: QCloseEvent):
        self.parent.view_windows.remove(self)
        event.accept()


    def display_current_image(self, reset_scale=False):
        # Direclty using original function, if same with main canvas
        if self.parent.main_index == self.current_index:
            self.parent.display_current_image(reset_scale)
            return
        # Only update self view window
        _, layers = self.parent.image_list[self.current_index]
        self.set_image(LayerManager.compose_layers(layers))
        self.parent.display_thumbnail_image()
        
        if self.parent.histogram_panel.isVisible():
            self.parent.histogram_panel.update_histogram()

    def update_image_display(self):
        self.parent.update_image_display()
    def set_current_index_focus(self):
        if self.dialog_open: return
        
        self.on_focus = True
        self.parent.current_index = self.current_index

        # Update layer panel
        if self.current_index != self.parent.main_index:
            _, layers = self.parent.image_list[self.parent.current_index]
            self.layer_panel.set_layers(layers)
        
        self.parent.grid_action.setChecked(self.image_label.show_grid)
        self.parent.ruler_action.setChecked(self.image_label.show_ruler)
        
        ## Disable focus on other windows
        self.parent.disabled_selection_mode()
        for i in self.parent.view_windows:
            if i is not self and i.isVisible():
                i.on_focus = False
                i.disabled_selection_mode()
    
    def current_focus_layer_image(self, img=None): 
        return self.parent.current_focus_layer_image(img)
    def get_current_focus_layer(self): 
        return self.parent.get_current_focus_layer()
    
    
    
    def update_button_menu(self):
        self.parent.update_button_menu()
        
    def push_undo_state(self, reset_redo=True):
        self.parent.push_undo_state(reset_redo)
    def push_redo_state(self):
        self.parent.push_redo_state()
    
    
    def enable_selection_mode(self):
        if self.image_label.select_mode:
            self.image_label.enable_selection(False)            
            return

        self.image_label.enable_selection(True)
        self.image_label.enable_moving(False)
    def disabled_selection_mode(self):
        self.image_label.selection_rect = QRect()
        self.selected_rect = (0, 0, 0, 0)
        self.image_label.update()
    def on_selection_made(self, rect: QRect):
        offset_x, offset_y = self.display_offset
        height, width = self.display_image.shape[:2] 
        
        x1 = int((rect.left() - offset_x) / self.display_scale_x)
        y1 = int((rect.top() - offset_y) / self.display_scale_y)
        x2 = int((rect.right() - offset_x) / self.display_scale_x)
        y2 = int((rect.bottom() - offset_y) / self.display_scale_y)

        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min (x2, width)
        y2 = min(y2, height)


        self.selected_rect = (x1, y1, x2, y2)
    def select_all(self):
        if self.display_image is None:
            return

        x1, y1, w, h = self.get_canvas_area_size()

        display_rect = QRect(
            x1, y1, w, h
        )

        self.image_label.selection_rect = display_rect
        # Emit true image-space rectangle
        self.on_selection_made(display_rect)
        self.image_label.update()
    def get_canvas_area_size(self):
        h, w = self.display_image.shape[:2]

        # Map full image to label coordinates for visual rectangle
        scale = self.display_scale_x
        offset_x, offset_y = self.display_offset

        return (offset_x, offset_y, 
                int(w * scale), int(h * scale))
    
    def free_transform(self):
        if self.image_label.selection_rect == QRect():
            self.select_all()

        self.image_label.enable_transform(True)
        self.image_label.update()
        
        



"""
Grid and Ruler Settings Dialog
"""
class GridSettingsDialog(QDialog):
    """
    Grid and Ruler Settings Dialog
    """
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Grid & Ruler Settings")
        self.setFixedWidth(300)

        ## Store original settings
        self.apply = False
        self.ori_cbg_rid = self.parent.image_label.show_grid
        self.ori_cb_ruler = self.parent.image_label.show_ruler
        self.ori_grid_size = self.parent.grid_size
        self.ori_grid_thickness = self.parent.grid_thickness
        self.ori_grid_color = self.parent.grid_color
        self.ori_ruler_thickness = self.parent.ruler_thickness
        self.ori_ruler_grid = self.parent.ruler_grid
        self.color = self.parent.grid_color
        
        layout = QVBoxLayout()

        # Show/Hide
        self.cb_grid = QCheckBox("Show Grid")
        self.cb_grid.setChecked(self.parent.image_label.show_grid)
        self.cb_grid.stateChanged.connect(self.apply_settings)
        layout.addWidget(self.cb_grid)

        self.cb_ruler = QCheckBox("Show Ruler")
        self.cb_ruler.setChecked(self.parent.image_label.show_ruler)
        self.cb_ruler.stateChanged.connect(self.apply_settings)
        layout.addWidget(self.cb_ruler)

    ## Ruler
        layout.addWidget(QLabel("Ruler Width"))
        self.ruler_width = QSlider(Qt.Horizontal)
        self.ruler_width.setRange(10, 50)
        self.ruler_width.setValue(self.parent.ruler_thickness)
        self.ruler_width.valueChanged.connect(self.apply_settings)
        layout.addWidget(self.ruler_width)
        
        layout.addWidget(QLabel("Ruler Grid Size"))
        self.ruler_size = QSlider(Qt.Horizontal)
        self.ruler_size.setRange(30, 80)
        self.ruler_size.setValue(self.parent.ruler_grid)
        self.ruler_size.valueChanged.connect(self.apply_settings)
        layout.addWidget(self.ruler_size)
        
    ## Grid
        layout.addWidget(QLabel("Grid Size"))
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(5, 200)
        self.spacing_slider.setValue(self.parent.grid_size)
        self.spacing_slider.valueChanged.connect(self.apply_settings)
        layout.addWidget(self.spacing_slider)

        layout.addWidget(QLabel("Grid Line Thickness"))
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setRange(1, 8)
        self.thickness_slider.setValue(self.parent.grid_thickness)
        self.thickness_slider.valueChanged.connect(self.apply_settings)
        layout.addWidget(self.thickness_slider)

        # --- Color button ---
        self.btn_color = QPushButton("Grid Line Color")
        self.btn_color.clicked.connect(self.pick_color)
        layout.addWidget(self.btn_color)

        # --- Apply ---
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self.apply_button_pressed)
        layout.addWidget(btn_apply)

        self.setLayout(layout)

    def pick_color(self):
        color = QColorDialog.getColor(self.parent.grid_color, self)
        if color.isValid():
            self.color = color
            self.apply_settings()


    def apply_settings(self):
        self.parent.image_label.show_grid = self.cb_grid.isChecked()
        self.parent.image_label.show_ruler = self.cb_ruler.isChecked()
        self.parent.image_label.grid_size = self.spacing_slider.value()
        self.parent.image_label.grid_thickness = self.thickness_slider.value()
        self.parent.image_label.grid_color = self.color
        self.parent.image_label.ruler_thickness = self.ruler_width.value()
        self.parent.image_label.ruler_grid = self.ruler_size.value()
        self.parent.image_label.update()

        for i in self.parent.view_windows:
            i.image_label.show_grid = self.cb_grid.isChecked()
            i.image_label.show_ruler = self.cb_ruler.isChecked()
            i.image_label.grid_size = self.spacing_slider.value()
            i.image_label.grid_thickness = self.thickness_slider.value()
            i.image_label.grid_color = self.color
            i.image_label.ruler_thickness = self.ruler_width.value()
            i.image_label.ruler_grid = self.ruler_size.value()
            i.image_label.update()
        
    
    def apply_button_pressed(self):
        self.apply = True
        
        self.parent.grid_size = self.spacing_slider.value()
        self.parent.grid_thickness = self.thickness_slider.value()
        self.parent.grid_color = self.color
        self.parent.ruler_thickness = self.ruler_width.value()
        self.parent.ruler_grid = self.ruler_size.value()
        
        self.close()

    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.apply_defaults()
        event.accept()

    def apply_defaults(self):
        self.parent.image_label.show_grid = self.ori_cbg_rid
        self.parent.image_label.show_ruler = self.ori_cb_ruler
        self.parent.image_label.grid_size = self.ori_grid_size
        self.parent.image_label.grid_color = self.ori_grid_color
        self.parent.image_label.grid_thickness = self.ori_grid_thickness
        self.parent.image_label.ruler_thickness = self.ori_ruler_thickness
        self.parent.image_label.ruler_grid = self.ori_ruler_grid
        self.parent.update()
        
        for i in self.parent.view_windows:
            i.image_label.grid_size = self.ori_grid_size
            i.image_label.grid_thickness = self.ori_grid_thickness
            i.image_label.grid_color = self.ori_grid_color
            i.image_label.show_grid = self.ori_cbg_rid
            i.image_label.show_ruler = self.ori_cb_ruler
            i.image_label.ruler_thickness = self.ori_ruler_thickness
            i.image_label.ruler_grid = self.ori_ruler_grid
            i.image_label.update()

"""
Pen thickness Preview
"""
class PenPreviewWidget(QWidget):
    """
    Pen Thickness Preview Widget
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 60)
        self.thickness = 1.0
        self.color = (0, 0, 0) 
        
        # Style the background
        self.setStyleSheet("""
            background-color: gray; 
            border: 4px solid #ccc; border-radius: 8px;
        
        """)
        
    def update_preview(self, thickness, color):
        self.thickness = thickness
        self.color = color
        self.update()  # Triggers paintEvent

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Convert BGR (OpenCV) to RGB (Qt)
        b, g, r = self.color
        color = QColor(r, g, b)

        # Create Pen
        pen = QPen(color)
        pen.setWidthF(np.clip(self.thickness * 0.4, 1, 70))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        # Draw a Sine Wave Curve
        path = QPainterPath()
        start_y = h / 2
        path.moveTo(20, start_y)

        # Create a smooth curve
        # Control points for a cubic bezier (looks like a sine wave)
        # Point 1 (Start), Point 2 (Control 1), Point 3 (Control 2), Point 4 (End)
        path.cubicTo(w * 0.33, start_y - h * 0.4,  # Control 1 (Up)
                     w * 0.66, start_y + h * 0.4,  # Control 2 (Down)
                     w - 20, start_y)              # End Point

        painter.drawPath(path)

