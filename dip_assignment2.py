import sys
import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QSlider, QHBoxLayout, 
    QDialog, QComboBox, QInputDialog, QCheckBox, QRadioButton, 
    QGridLayout, QColorDialog, QListWidget, QMessageBox, 
    QSizePolicy, QSpinBox, QGroupBox, QFrame, QToolButton, 
    QButtonGroup, QAbstractItemView, QListWidgetItem, 
    
)
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QIcon,
    QCloseEvent, QPainterPath, QPalette
)
from PyQt5.QtCore import (
    Qt, QRect, QSize
)
import copy

from dip_assignment1 import SelectLabel
    
### Path of assets folder loaded 
current_path = os.path.dirname(os.path.abspath(__file__))
assets_path = current_path + "\\Assets\\"

    
#/layer
## Create a view window
class ImageViewWindow(QMainWindow):
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
        
        



## Multiple Layer Controller
class LayerState:
    def __init__(self, name, opacity, is_visible, blend_mode, clipping_mask, image_data):
        """
        Restore information of layer
        """
        self.name = name
        self.opacity = opacity
        self.is_visible = is_visible
        self.blend_mode = blend_mode
        self.clipping_mask = clipping_mask
        self.image_data = copy.deepcopy(image_data)
        
class Layer:
    def __init__(self, parent, 
                 name, image_data, visible=True, opacity=1.0, blend_mode="Normal", clipping_mask=False):
        
        self.parent = parent
        self.name = name
        # Ensure image is BGRA (has transparency)
        self.image = image_data.copy()
        if image_data.shape[2] == 3:
            self.image = cv2.cvtColor(image_data, cv2.COLOR_BGR2BGRA)
            
        self.visible = visible
        self.opacity = opacity
        self.blend_mode = blend_mode
        self.clipping_mask = clipping_mask
    
    def set_image(self, img):
        self.image = img.copy()
        if img.shape[2] == 3:
            self.image = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        self.parent.on_image_changed()
        
class LayersPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.layers = [] 
        self.active_layer_index = 0
        self._updating_ui = False 
        
        self.image_buffer = None
        self.image_changed = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

    # Layer Control Button
        top_controls_layout = QHBoxLayout()
        second_controls_layout = QHBoxLayout()
        
    # Add/Del Buttons
        self.btn_add = QPushButton("")
        self.btn_add.setFixedWidth(30)
        self.btn_add.setToolTip("Create new layer")
        self.btn_add.setIcon(QIcon(f"{assets_path}new-blank-page.png"))
        self.btn_add.clicked.connect(self.add_new_layer)
        self.btn_del = QPushButton("")
        self.btn_del.setFixedWidth(30)
        self.btn_del.setToolTip("Delete layer")
        self.btn_del.setIcon(QIcon(f"{assets_path}delete.png"))
        self.btn_del.clicked.connect(self.delete_layer)
        
    # Blend Mode 
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "Normal", "Multiply", "Screen", "Overlay", 
            "Darken", "Lighten", "Difference", "Addition", "Soft Light"
        ])
        self.combo_mode.currentIndexChanged.connect(self.change_blend_mode)
        self.combo_mode.insertSeparator(4)
        self.combo_mode.insertSeparator(7)
        self.combo_mode.setMaxVisibleItems(99)
        
    # Clipping mask
        self.btn_clip = QPushButton("Clip")
        self.btn_clip.setFixedWidth(40)
        self.btn_clip.setCheckable(True)
        self.btn_clip.setToolTip("Create Clipping Mask")
        self.btn_clip.clicked.connect(self.toggle_clipping_mask)
        
    # Opacity Slider
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.sliderReleased.connect(self.change_opacity)
        self.opacity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #666;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #333;
                border: 1px solid #333;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        
        top_controls_layout.addWidget(self.btn_clip)
        top_controls_layout.addWidget(self.combo_mode)
        second_controls_layout.addWidget(self.btn_add)
        second_controls_layout.addWidget(self.btn_del)
        second_controls_layout.addWidget(self.opacity_slider)
        
        layout.addLayout(top_controls_layout)
        layout.addLayout(second_controls_layout)
        

    # Layer List
        layout.addWidget(QLabel("<b>Layers</b>"))
        
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Enable Drag and Drop
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Connect signals
        self.list_widget.currentRowChanged.connect(self.set_active_layer)
        self.list_widget.itemChanged.connect(self.on_item_changed)
        self.list_widget.itemDoubleClicked.connect(self.rename_layer)
        
        layout.addWidget(self.list_widget)

        self.setLayout(layout)



    def set_layers(self, layers_list, reset=False):
        """ Update layers list """
        self.on_image_changed()
        self.layers = layers_list
        self.refresh_list(reset)

    def refresh_list(self, reset=False, index=-1):
        """ Update layer panel list on main canvas """
        self._updating_ui = True 
        self.list_widget.clear()
        
        for i, layer in enumerate(reversed(self.layers)): 
            item = QListWidgetItem("layer")


            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            item.setCheckState(Qt.Checked if layer.visible else Qt.Unchecked)
            

            item.setData(Qt.UserRole, layer)
            icon = self.generate_thumbnail(layer.image)
            item.setIcon(icon)
            
            self.list_widget.addItem(item)
            actual_idx = len(self.layers)-1 - i
            self.update_layer_item(actual_idx, item)
        
        self._updating_ui = False
        self.list_widget.setIconSize(QSize(40, 60))
        
        if self.layers:
            if reset:
                self.list_widget.setCurrentRow(0) 
            else:
                # Remain the current layer index
                index = min(self.active_layer_index, len(self.layers)-1) if index == -1 else index
                self.list_widget.setCurrentRow(len(self.layers)-1 - index)
                
# ---------------------------------

    def add_new_layer(self):
        
        self.parent.push_undo_state()
        h, w = self.layers[0].image.shape[:2]
        
        # Create transparent image
        new_img = LayerManager.create_blank_layer(w, h)
        
        name = f"Layer {len(self.layers) + 1}"
        new_layer = Layer(self, name, new_img)
        
        # Add layer on current position
        self.layers.insert(max(len(self.layers)-1, self.active_layer_index+1), new_layer)
        self.active_layer_index += 1
        self.refresh_list()
        self.update_composite()

    def copy_layer(self):
        """ Copy a same layer """
        self.parent.push_undo_state()
        h, w = self.layers[0].image.shape[:2]
        
        # Copy the current image
        cl = self.layers[self.active_layer_index]
        
        name = f"{cl.name}-copy"
        new_layer = Layer(
            self, name, cl.image, cl.visible, 
            cl.opacity, cl.blend_mode, cl.clipping_mask
        )
        
        # Add layer on current position
        self.layers.insert(max(len(self.layers)-1, self.active_layer_index+1), new_layer)
        self.active_layer_index += 1
        self.refresh_list()
        self.update_composite()
    
    def delete_layer(self):
        if len(self.layers) <= 1: 
            QMessageBox.warning(self, "Error", "Cannot delete all layer.")
            return
        
        # Current row in UI
        self.parent.push_undo_state()
        row = self.list_widget.currentRow()
        if row == -1: return

        # Get the layer object from the item
        item = self.list_widget.item(row)
        layer_to_remove = item.data(Qt.UserRole)
        
        if layer_to_remove in self.layers:
            self.layers.remove(layer_to_remove)
            self.refresh_list()
            self.image_changed = True
            self.parent.display_current_image()

    def clear_layer(self):
        """ Create new transparent blank image to replace it """
        self.parent.push_undo_state()
        h, w = self.layers[0].image.shape[:2]
        
        blank = LayerManager.create_blank_layer(w, h)
        self.layers[self.active_layer_index].set_image(blank)
    
    def write_down(self):
        """
        Write the current content to layer below
        """
        idx = self.active_layer_index
        if idx <= 0: return
        if idx >= len(self.layers): return
        
        self.parent.push_undo_state()
        
        top_layer = self.layers[idx]
        bottom_layer = self.layers[idx - 1]
        
        merged_img = LayerManager.merge_two_layers(
            bottom_layer.image, 
            top_layer.image, 
            top_layer.opacity, 
            top_layer.blend_mode
        )
        
        # Clear current layer, and write the image down
        self.clear_layer()
        bottom_layer.set_image(merged_img)
        
        self.refresh_list()
     
    def merge_down(self):
        """
        Combine current layer with layer below
        """
        idx = self.active_layer_index
        if idx <= 0: return
        if idx >= len(self.layers): return
        
        self.parent.push_undo_state()
        
        top_layer = self.layers[idx]
        bottom_layer = self.layers[idx - 1]
        
        merged_img = LayerManager.merge_two_layers(
            bottom_layer.image, 
            top_layer.image, 
            top_layer.opacity, 
            top_layer.blend_mode
        )
        
        # Write image down, and delete current layer
        bottom_layer.set_image(merged_img)
        self.layers.pop(idx)
        self.active_layer_index = idx - 1
        
        self.refresh_list()
    
    def merge_all_layer(self):
        """
        Combine all layer
        """
        self.parent.push_undo_state()
        
        merge_img = self.update_composite()
        
        name = f"Layer {len(self.layers) + 1}"
        new_layer = Layer(self, name, merge_img)
        
        self.active_layer_index = 0
        self.set_layers([new_layer], True)

    def merge_all_visible_layer(self):
        """
        Combine all layers except of unvisible layer
        """
        self.parent.push_undo_state()
        
        merge_img = self.update_composite()
        
        name = f"Layer {len(self.layers) + 1}"
        new_layer = Layer(self, name, merge_img)
        
        new_layer_list = []
        for l in self.layers:
            if not l.visible:
                new_layer_list.append(l)
        new_layer_list.append(new_layer)
        
        self.set_layers(new_layer_list, True)
    
# ---------------------------------

    def layer_move(self, mode):
        """ Layer moving """
        self.parent.push_undo_state()
        
        idx = self.active_layer_index
        current_layer = self.layers.pop(idx)
        
        # mode = 1 go front, mode = -1 to down
        self.layers.insert(idx + mode, current_layer)
        self.refresh_list(index=idx + mode)

    def layer_move_top(self, mode):
        """ Layer moving to first or last """
        self.parent.push_undo_state()
        
        idx = self.active_layer_index
        current_layer = self.layers.pop(idx)
        
        # Move layer to top
        if mode == 1:
            self.layers.append(current_layer)
            self.refresh_list(reset=True)
        # Move layer to bottom
        elif mode == -1:
            self.layers.insert(0, current_layer)
            self.refresh_list(index=0)
            

# ---------------------------------

    def set_active_layer(self, ui_row_index):
        """
        Update when changing focusing layer
        """
        if ui_row_index == -1 or self._updating_ui or \
            self.parent.dialog_open: return
        
        item = self.list_widget.item(ui_row_index)
        layer = item.data(Qt.UserRole)
        
        # Find index in backend list
        self.active_layer_index = self.layers.index(layer)
        
        # Update opacity slider without triggering update loop
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(int(layer.opacity * 100))
        self.opacity_slider.blockSignals(False)
        
        # Update clipping mask button
        self.btn_clip.blockSignals(True)
        self.btn_clip.setChecked(layer.clipping_mask)
        # Disable button if it's the bottom layer
        self.btn_clip.setEnabled(self.active_layer_index > 0)
        self.btn_clip.blockSignals(False)
        
        # Update blend mode
        self.combo_mode.blockSignals(True)
        self.combo_mode.setCurrentText(layer.blend_mode)
        self.combo_mode.blockSignals(False)
        

    def change_opacity(self):
        """ Set image alpha """
        if self.active_layer_index != -1 and 0 <= self.active_layer_index < len(self.layers):
            self.parent.push_undo_state()
            self.image_changed = True
            
            idx = self.active_layer_index
            self.layers[idx].opacity = self.opacity_slider.value() / 100.0
            self.parent.display_current_image()
            
            self.update_layer_item(idx)
            
    def change_blend_mode(self):
        """ Set image blend mode """
        if 0 <= self.active_layer_index < len(self.layers):
            idx = self.active_layer_index
            mode = self.combo_mode.currentText()
            
            if self.layers[idx].blend_mode != mode:
                self.parent.push_undo_state()
                self.layers[idx].blend_mode = mode
                self.image_changed = True
                
                self.parent.display_current_image()
                self.update_layer_item(self.active_layer_index)

    def toggle_clipping_mask(self):
        """ Clipping mask """
        if self.active_layer_index >= len(self.layers): return
        if self.active_layer_index == 0: return 

        self.parent.push_undo_state()
        
        layer = self.layers[self.active_layer_index]
        layer.clipping_mask = not layer.clipping_mask
        
        # Update UI state
        self.btn_clip.setChecked(layer.clipping_mask)
        
        self.refresh_list()
        self.image_changed = True
        self.parent.display_current_image()
    
    
    def update_layer_item(self, index, item=None):
        """"
        Update layer information
        """
        if item is None:
            item = self.list_widget.item(self.list_widget.currentRow())
        layer = self.layers[index]
        clipping_mask = "  ↳ " if layer.clipping_mask else ""
        item.setText(f"{clipping_mask}{layer.name} \n({layer.blend_mode}) \n"\
                    f"{int(layer.opacity*100)}%")
    
# ---------------------------------

    def generate_thumbnail(self, image, size=50):
        """
        Creates thumbnail by QIcon
        """
        if image is None: return QIcon()
        
        h, w = image.shape[:2]
        
        scale = size / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        if new_w <= 0 or new_h <= 0: return QIcon()

        small_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

        # Craete checkbox bg
        bg = np.full((new_h, new_w, 3), 204, dtype=np.uint8)
        check_size = 10
        y_idx = np.arange(new_h)[:, None]
        x_idx = np.arange(new_w)[None, :]
        mask = ((y_idx // check_size) + (x_idx // check_size)) % 2 == 0
        bg[mask] = 255 


        if small_img.shape[2] == 4:
            # Split
            b, g, r, a = cv2.split(small_img)
            fg = cv2.merge([b, g, r])
            
            alpha = a.astype(float) / 255.0
            alpha = cv2.merge([alpha, alpha, alpha])
            
            fg_float = fg.astype(float)
            bg_float = bg.astype(float)
            
            comp = (fg_float * alpha) + (bg_float * (1.0 - alpha))
            comp = comp.astype(np.uint8)
            
            comp = cv2.cvtColor(comp, cv2.COLOR_BGR2RGB)
        else:
            comp = cv2.cvtColor(small_img, cv2.COLOR_BGR2RGB)


        h_c, w_c, _ = comp.shape
        qimg = QImage(comp.data, w_c, h_c, comp.strides[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        
        return QIcon(pix)

    def update_current_thumbnail(self):
        """
        Update thumbnail layer
        """
        if self._updating_ui: return
        
        idx = self.active_layer_index
        item = self.list_widget.item(idx)
        _, layers = self.parent.image_list[self.parent.current_index]
        if not layers: return
        
        layer = layers[idx]
        img = layer.image
        
        thumbnail = self.generate_thumbnail(img)
        
        item.setIcon(thumbnail)
    
    def rename_layer(self, item=None):
        """
        Rename 
        """
        if item is None:
            item = self.list_widget.item(self.list_widget.currentRow())

        layer = item.data(Qt.UserRole)
        if not layer: return

        # 2. Open Input Dialog
        old_name = layer.name
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Layer", 
            "Enter new layer name:", 
            text=old_name
        )

        # 3. Apply Change
        if ok and new_name:
            self.parent.push_undo_state()
            
            layer.name = new_name
            
            self.update_layer_item(self.active_layer_index, item)


# ---------------------------------

    def on_item_changed(self, item):
        """Visiblity of layer"""
        if self._updating_ui or self.parent.dialog_open: return
        
        layer = item.data(Qt.UserRole)
        is_visible = (item.checkState() == Qt.Checked)
        self.parent.push_undo_state()
        
        if layer.visible != is_visible:
            layer.visible = is_visible
            self.on_image_changed()
            self.parent.display_current_image()




    def on_image_changed(self):
        self.image_changed = True

    def update_composite(self):
        """
        Get result of composite layer
        """
        if not self.layers: return
        
        if self.image_changed or self.image_buffer is None:
            self.image_buffer = LayerManager.compose_layers(self.layers)
            result_bgr = self.image_buffer.copy()
            self.image_changed = False
        else:
            result_bgr = self.image_buffer.copy()
        
        return result_bgr
    
    def update_parent_list(self):
        name, layers = self.parent.image_list[self.parent.current_index]
        self.parent.image_list[self.parent.current_index] = (
            name, self.layers
        )
    
class LayerManager:
    def create_blank_layer(width, height):
        """
        Full empty transparent canvas
        """
        img = np.zeros((height, width, 4), dtype=np.uint8)
        return img

    def merge_two_layers(base_img, overlay_img, opacity, mode="Normal"):
        """
        Combine two layer with applying blend effect 
        """
        h, w = base_img.shape[:2]
        if overlay_img.shape[:2] != (h, w):
            overlay_img = cv2.resize(overlay_img, (w, h), interpolation=cv2.INTER_LANCZOS4)

        if base_img.shape[2] == 3: 
            base_img = cv2.cvtColor(base_img, cv2.COLOR_BGR2BGRA)
        if overlay_img.shape[2] == 3: 
            overlay_img = cv2.cvtColor(overlay_img, cv2.COLOR_BGR2BGRA)

        # Normaliase
        bg_float = base_img.astype(float) / 255.0
        fg_float = overlay_img.astype(float) / 255.0

        # Separate Alpha
        bg_rgb = bg_float[:, :, :3]
        bg_a = bg_float[:, :, 3]
        
        fg_rgb = fg_float[:, :, :3]
        fg_a = fg_float[:, :, 3] * opacity 

        # Apply blend effect
        blended_rgb = LayerManager.blend_pixel_math(bg_rgb, fg_rgb, mode)

        # Porter-Duff 'Over' Composite Math
        # OutAlpha = TopAlpha + BottomAlpha * (1 - TopAlpha)
        out_a = fg_a + bg_a * (1.0 - fg_a)
        
        
        # Pre-multiply alpha
        fg_pre = blended_rgb * cv2.merge([fg_a, fg_a, fg_a])
        bg_pre = bg_rgb * cv2.merge([bg_a, bg_a, bg_a])
        
        # Composite
        out_rgb_pre = fg_pre + bg_pre * (1.0 - cv2.merge([fg_a, fg_a, fg_a]))
        
        # Normalize (Un-multiply alpha)
        safe_a = cv2.merge([out_a, out_a, out_a])
        mask_zero = (safe_a == 0)
        safe_a[mask_zero] = 1.0
        
        out_rgb = out_rgb_pre / safe_a
        out_rgb[mask_zero] = 0

        # Merge 
        out = cv2.merge([
            out_rgb[:, :, 0], 
            out_rgb[:, :, 1], 
            out_rgb[:, :, 2], 
            out_a
        ])

        return np.clip(out * 255.0, 0, 255).astype(np.uint8)
    
    def blend_pixel_math(bg, fg, mode):
        """
        Blend mode effect calculation
        """
        EPS = 1e-7

        if mode == "Normal":
            return fg
        
        elif mode == "Multiply":
            return bg * fg
        
        elif mode == "Screen":
            return 1.0 - (1.0 - bg) * (1.0 - fg)
        
        elif mode == "Overlay":
            mask = bg < 0.5
            result = np.empty_like(bg)
            result[mask] = 2 * bg[mask] * fg[mask]
            result[~mask] = 1 - 2 * (1 - bg[~mask]) * (1 - fg[~mask])
            return result
            
        elif mode == "Darken":
            return np.minimum(bg, fg)
            
        elif mode == "Lighten":
            return np.maximum(bg, fg)
            
        elif mode == "Difference":
            return np.abs(bg - fg)
            
        elif mode == "Addition":
            return np.clip(bg + fg, 0.0, 1.0)
            
        elif mode == "Soft Light":
            return (1 - 2 * fg) * (bg ** 2) + (2 * fg * bg)

        return fg


    def compose_layers(layers):
        """
        Composite result of all layers
        """
        
        base_height, base_width = layers[0].image.shape[:2]
    
        grid_size = 20       
        light_color = 255   
        dark_color = 204   

        y_indices = np.arange(base_height)[:, None]
        x_indices = np.arange(base_width)[None, :]
        checker_mask = ((y_indices // grid_size) + (x_indices // grid_size)) % 2 == 0

        # Initialize composite with dark color, then fill light spots
        composite = np.full((base_height, base_width, 3), dark_color, dtype=np.uint8)
        composite[checker_mask] = (light_color, light_color, light_color)
        
        for i, layer in enumerate(layers):
            if not layer.visible: continue
            if layer.opacity == 0: continue
            overlay = layer.image
            opacity = layer.opacity
            mode = layer.blend_mode
            
            b, g, r, a = cv2.split(overlay)
            bgr_img = cv2.merge([b, g, r])
            
            
        ## Clipping mask
            if layer.clipping_mask:
                # Find base layer
                base_idx = i - 1
                while base_idx >= 0 and layers[base_idx].clipping_mask:
                    base_idx -= 1
                    
                if base_idx < 0: continue
                
                base_layer = layers[base_idx]
                if not base_layer.visible: continue
                if base_layer.opacity == 0: continue
                
                # Apply the base layer by base layer
                base_a = base_layer.image[:, :, 3]
                factor = base_a.astype(float) / 255.0
                a = (a.astype(float) * factor * base_layer.opacity).astype(np.uint8)
                
            
            
            
            ## Check if is empty canvas
            if np.max(a) == 0: 
                continue
            # Resize layer if it doesn't match canvas
            if overlay.shape[:2] != composite.shape[:2]:
                overlay = cv2.resize(overlay, (base_width, base_height))

            
            # Applying layer blending mode
            fg_float = bgr_img.astype(float) / 255.0
            bg_float = composite.astype(float) / 255.0
            blended_img = LayerManager.blend_pixel_math(bg_float, fg_float, mode)
            
            
            # Apply Opacity to Alpha Channel
            alpha_factor = (a / 255.0) * opacity
            alpha_mask = cv2.merge([alpha_factor, alpha_factor, alpha_factor])
            
            
            # Perform blending
            output = (blended_img * alpha_mask) + (bg_float * (1.0 - alpha_mask))
            composite = np.clip(output * 255.0, 0, 255).astype(np.uint8)
            
        return composite




## Grid and Ruler Settings Dialog
class GridSettingsDialog(QDialog):
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


## Pen thickness Preview
class PenPreviewWidget(QWidget):
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



#/layer
## Histogram Panel
class HistogramCalculator:
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
class HistogramWidget(QWidget):
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

class HistogramPanel(QWidget):
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

class HistogramWindow(QMainWindow):
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



#/layer
## Image Enhancement Filter
class ImageEnhancer:

## Blur --------------------------------------
    def apply_blur(image, ksize=3):
        return cv2.blur(image, (ksize, ksize))

    def apply_gaussian(image, ksize=3):
        if ksize % 2 == 0:
            ksize += 1
        return cv2.GaussianBlur(image, (ksize, ksize), 0)

    def apply_motion_blur(image, size, angle):
        # Ensure size is odd
        if size % 2 == 0: size += 1
        
        kernel = np.zeros((size, size))
        kernel[int((size-1)/2), :] = np.ones(size)
        
        M = cv2.getRotationMatrix2D((size/2, size/2), angle, 1)
        kernel = cv2.warpAffine(kernel, M, (size, size))
        
        kernel = kernel / size
        return cv2.filter2D(image, -1, kernel)

    def apply_radial_blur(image, strength, cx_percent=50, cy_percent=50):
        
        h, w = image.shape[:2]
        center_x = int(((cx_percent+50) / 100.0) * w)
        center_y = int(((cy_percent+50) / 100.0) * h)
        
        grow_img = image.astype(np.float32)
        accumulate = image.astype(np.float32)
        
        factor = 1.0 + (0.002 * strength) 
        for i in range(strength):
            M = cv2.getRotationMatrix2D((center_x, center_y), 0, factor)
            
            grow_img = cv2.warpAffine(grow_img, M, (w, h))
            accumulate = cv2.add(accumulate, grow_img)

        result = accumulate / (strength + 1)
        
        return result.astype(np.uint8)
    

## Sharpen--------------------------------------
    def apply_sharpen(image, intensity=1):
        intensity /= 10.0
        blur = cv2.GaussianBlur(image, (0, 0), 3)

        sharpened = cv2.addWeighted(
            image, 
            1 + intensity, blur, 
            -intensity, 0
        )

        return sharpened

    def apply_sharpen_edge(image):
        kernel = np.array(
            [[-1, -1, -1], 
            [-1,  9, -1], 
            [-1, -1, -1]]
        )
        return cv2.filter2D(image, -1, kernel)

    def apply_usm(image, amount, radius, threshold):
        # Ensure radius is odd
        ksize = (radius * 2) + 1
        
        blurred = cv2.GaussianBlur(image, (ksize, ksize), 0)
        
        # Unsharp Mask (Original - Blurred)
        img_float = image.astype(np.float32)
        blur_float = blurred.astype(np.float32)
        
        amount_float = amount / 10.0
        sharpened = img_float + (img_float - blur_float) * amount_float
        
        if threshold > 0:
            low_contrast_mask = np.abs(img_float - blur_float) < threshold
            sharpened[low_contrast_mask] = img_float[low_contrast_mask]
            
        sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
        return sharpened


## Noise --------------------------------------
    def apply_add_noise(image, strength, size):
        if strength == 0:
            return image

        h, w = image.shape[:2]
        noise_h = max(1, h // size)
        noise_w = max(1, w // size)
        
        if len(image.shape) == 3:
            noise = np.random.normal(0, strength, (noise_h, noise_w, 3))
        else:
            noise = np.random.normal(0, strength, (noise_h, noise_w))

        # Resize
        if size > 1:
            noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_NEAREST)

        img_float = image.astype(np.float32)
        noisy_img = cv2.add(img_float, noise.astype(np.float32))
        
        result = np.clip(noisy_img, 0, 255).astype(np.uint8)
        return result
    
    def apply_denoise(image, strength=15):
        return cv2.bilateralFilter(image, 9, strength, strength)

    def apply_median_blur(image, kernel_size):
        if kernel_size % 2 == 0:
            kernel_size += 1
        if kernel_size < 3:
            kernel_size = 3
            
        return cv2.medianBlur(image, kernel_size)

## Edge --------------------------------------
    def apply_edge_enhance(image, level=1):
        kernel = np.array([
            [-level, -level, -level],
            [-level, 8*level+1, -level],
            [-level, -level, -level]
        ])
        return cv2.filter2D(image, -1, kernel)
    
## Style --------------------------------------
    def apply_diffuse(image, scale):
        if scale == 0: 
            return image

        h, w = image.shape[:2]
        # Generate random number
        rand_x = np.random.randint(-scale, scale + 1, (h, w))
        rand_y = np.random.randint(-scale, scale + 1, (h, w))

        # Create coordinate grid
        grid_x, grid_y = np.meshgrid(np.arange(w), np.arange(h))

        # Add noise 
        map_x = grid_x + rand_x
        map_y = grid_y + rand_y

        map_x = np.clip(map_x, 0, w - 1).astype(np.float32)
        map_y = np.clip(map_y, 0, h - 1).astype(np.float32)

        result = cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_NEAREST)
        return result

    def apply_solarize(image, threshold):
        # Apply image inverse for certain pixel > threshold
        result = image.copy()
        mask = result >= threshold

        result[mask] = 255 - result[mask]
        return result
    
    
## Other --------------------------------------
    def apply_beautify(image, smooth=15, sharp=1.0):
        smooth_img = cv2.bilateralFilter(image, 9, smooth, smooth)
        beautified = ImageEnhancer.apply_sharpen(smooth_img, sharp/10)
        return beautified

class EnhancePanel(QWidget):
    def __init__(self, parent, method, hsize=140):
        super().__init__()
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        
        self.parent = parent
        self.setWindowTitle(f"{method} Filters Controller")
        self.setMinimumSize(490, hsize)
        self.apply = False

        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()



        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Filter Label -----------------------
        self.method = method
        # self.filter_label = QLabel(f"{method} ")
        # self.filter_label.setStyleSheet("font-size: 18px")
        # self.layout.addWidget(self.filter_label)
        # [
        #     Blur, Blur More, Gaussian Blur,
        #     Sharpen, Sharpen Edge, Unsharp Mask (USM)
        #     Add Noise, Noise Removal, Median
        #     Edge Enhance
        #     Diffuse, Solarize
        #     Beautify
        # ]

        # dynamic slider area
        self.slider_area = QVBoxLayout()
        self.layout.addLayout(self.slider_area)

        self.layout.addStretch()
        
        # apply button
        apply_area = QHBoxLayout()
        apply_area.addStretch()
        
        self.cb_preview = QCheckBox("Preview ")
        self.cb_preview.setChecked(True)
        self.cb_all_layer = QCheckBox("Apply to All Layers")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        apply_area.addWidget(self.cb_preview)
        apply_area.addWidget(self.cb_all_layer)
        
        self.apply_btn = QPushButton("Apply ")
        self.apply_btn.setMaximumWidth(300)
        self.apply_btn.setMaximumHeight(100)
        self.apply_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px")
        self.apply_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)
        
        apply_area.addWidget(self.apply_btn)
        self.layout.addLayout(apply_area)

        self.build_sliders()

    def build_sliders(self):
        def _():
            filter_name = self.method
            self.sliders = {}  # store values dynamically

            def add_slider(name, minv, maxv, default, apply=True):
                label = QLabel(f"{name}: {default}")
                slider = QSlider(Qt.Horizontal)
                slider.setRange(minv, maxv)
                slider.setValue(default)
                slider.sliderReleased.connect(lambda l=label, s=slider: self.preview(l, name, s, True))
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
                """
                )
                
                self.slider_area.addWidget(label)
                self.slider_area.addWidget(slider)
                self.sliders[name] = slider
                
                if apply:
                    self.preview(label, name, default, apply)

        # 2. Setup Container Group
        self.slider_group = QGroupBox(self.method)
        self.slider_grid = QGridLayout()
        self.slider_group.setLayout(self.slider_grid)
        self.slider_area.addWidget(self.slider_group)

        self.sliders = {} 
        self.row_index = 0

        filter_name = self.method

        # 3. Define the Helper
        def add_slider(name, minv, maxv, default):
            # --- Widgets ---
            label = QLabel(f"{name}:")
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(minv, maxv)
            slider.setValue(default)
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    border: 1px solid #bbb;
                    background: white;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::sub-page:horizontal {
                    background: #666;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #333;
                    border: 1px solid #333;
                    width: 14px;
                    height: 14px;
                    margin: -5px 0;
                    border-radius: 7px;
                }
            """)

            spin = QSpinBox()
            spin.setRange(minv, maxv)
            spin.setValue(default)
            spin.setFixedWidth(60)
            
            
            slider.valueChanged.connect(lambda v: spin.blockSignals(True) or spin.setValue(v) or spin.blockSignals(False))
            spin.valueChanged.connect(lambda v: slider.blockSignals(True) or slider.setValue(v) or slider.blockSignals(False))
            
            slider.sliderReleased.connect(self.preview)
            spin.valueChanged.connect(self.preview)

            self.slider_grid.addWidget(label, self.row_index, 0)
            self.slider_grid.addWidget(slider, self.row_index, 1)
            self.slider_grid.addWidget(spin, self.row_index, 2)

            self.sliders[name] = slider
            self.row_index += 1

    # -------- Filter-specific sliders --------
    ## Blur filters
        if filter_name == "Blur":
            add_slider("Strength", 1, 45, 5)
        elif filter_name == "Blur More":
            add_slider("Strength", 1, 100, 35)
        elif filter_name == "Gaussian Blur":
            add_slider("Strength", 1, 75, 5)
        elif filter_name == "Motion Blur":
            add_slider("Size", 3, 50, 9)
            add_slider("Angle", 0, 180, 0) 
        elif filter_name == "Radial Blur":
            add_slider("Center X", -50, 50, 0) 
            add_slider("Center Y", -50, 50, 0)
            add_slider("Strength", 1, 20, 3)

    ## Sharpen filters
        elif filter_name == "Sharpen":
            add_slider("Intensity", 1, 70, 2)
        elif filter_name == "Sharpen Edge":
            label = QLabel("Fixed (3x3) sharpening matrix")
            self.slider_area.addWidget(label)
            self.preview(None, "", 0)
        elif filter_name == "Unsharp Mask (USM)":
            add_slider("Amount", 1, 50, 15) 
            add_slider("Radius", 1, 20, 2) 
            add_slider("Threshold", 0, 50, 0) 

    ## Noise filters
        elif filter_name == "Add Noise":
            add_slider("Strength", 0, 100, 30)
            add_slider("Size", 1, 10, 1)  
        elif filter_name == "Noise Removal":
            add_slider("Strength", 1, 100, 15)
        elif filter_name == "Median":
            add_slider("Radian Size", 3, 25, 3)

    ## Edge filter
        elif filter_name == "Edge Enhance":
            add_slider("Strength", 1, 10, 1)
            
    ## Style
        elif filter_name == "Diffuse":
            add_slider("Scale", 1, 20, 5) 
        elif filter_name == "Solarize":
            add_slider("Threshold", 0, 255, 128)
    
    
    ## Other filters
        elif filter_name == "Beautify":
            add_slider("Smoothness", 5, 40, 15)
            add_slider("Sharpness", 0, 100, 1)
        
        self.preview()

        

    
    
    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked(): 
            self.restore_layers()
            return
        if not self.cb_all_layer.isChecked():
            self.restore_layers()

        self.apply_on_layer()
            
    def preview(self):
        # if label is not None:
        #     value = slider
        #     if isinstance(slider, QSlider):
        #         value = slider.value()
        #     label.setText(f"{name}: {value}")


        if self.cb_preview.isChecked():
            self.apply_on_layer()
        
    def apply_filter(self, img):
        """
        Image Process 
        """
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        b, g, r, a = cv2.split(img)
        bgr = cv2.merge([b, g, r])
        
        
        vals = {n: s.value() for n, s in self.sliders.items()}
        result = bgr
        result_a = a
        method = self.method
        
    ## Blur
        if method == "Blur" or method == "Blur More":
            result = ImageEnhancer.apply_blur(bgr, vals["Strength"])
            result_a = ImageEnhancer.apply_blur(a, vals["Strength"])
        elif method == "Gaussian Blur":
            result = ImageEnhancer.apply_gaussian(bgr, vals["Strength"])
            result_a = ImageEnhancer.apply_gaussian(a, vals["Strength"])
        elif method == "Motion Blur":
            result = ImageEnhancer.apply_motion_blur(
                bgr, vals["Size"], vals["Angle"]
            )
            result_a = ImageEnhancer.apply_motion_blur(
                a, vals["Size"], vals["Angle"]
            )
        elif method == "Radial Blur":
            result = ImageEnhancer.apply_radial_blur(
                bgr, vals["Strength"], vals["Center X"], vals["Center Y"]
            )
            result_a = ImageEnhancer.apply_radial_blur(
                a, vals["Strength"], vals["Center X"], vals["Center Y"]
            )

    # Sharpen
        elif method == "Sharpen":
            result = ImageEnhancer.apply_sharpen(bgr, vals["Intensity"])
            result_a = ImageEnhancer.apply_sharpen(a, vals["Intensity"])
        elif method == "Sharpen Edge":
            pass
        elif method == "Unsharp Mask (USM)":
            result = ImageEnhancer.apply_usm(
                 bgr, vals["Amount"], vals["Radius"], vals["Threshold"]
             )
            result_a = ImageEnhancer.apply_usm(
                 a, vals["Amount"], vals["Radius"], vals["Threshold"]
             )
    
    # Noise
        elif method == "Add Noise":
            result = ImageEnhancer.apply_add_noise(
                bgr, vals["Strength"], vals["Size"]
            )
            # result_a = ImageEnhancer.apply_add_noise(
            #     a, vals["Strength"], vals["Size"]
            # )
        elif method == "Noise Removal":
            result = ImageEnhancer.apply_denoise(bgr, vals["Strength"])
            result_a = ImageEnhancer.apply_denoise(a, vals["Strength"])
        elif method == "Median":
            k_size = vals["Radian Size"]
            if k_size % 2 == 0: k_size += 1
            
            result = ImageEnhancer.apply_median_blur(bgr, k_size)
            result_a = ImageEnhancer.apply_median_blur(a, k_size)
        
        
    # Edge
        elif method == "Edge Enhance":
            result = ImageEnhancer.apply_edge_enhance(bgr, vals["Strength"])
        
    # Style
        elif method == "Diffuse":
            result = ImageEnhancer.apply_diffuse(bgr, vals["Scale"])
            result_a = ImageEnhancer.apply_diffuse(a, vals["Scale"])
        elif method == "Solarize":
            result = ImageEnhancer.apply_solarize(bgr, vals["Threshold"])
    
    
    # Other
        elif method == "Beautify":
            result = ImageEnhancer.apply_beautify(
                bgr,smooth=vals["Smoothness"],sharp=vals["Sharpness"]
            )

        
        return cv2.merge([*cv2.split(result), result_a])
        
        
    
    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
            
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            result = self.apply_filter(image)
            
            region = self.parent.get_result_by_roi(
                image, result, current_focus.selected_rect
            )
            layer.set_image(region)
        self.parent.display_current_image()
        
    

    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        if self.apply: 
            return

        self.apply = True
        self.apply_on_layer()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        self.close()
        
    def closeEvent(self, event: QCloseEvent):
        if self.apply: 
            event.accept()
            return
        
        self.parent.undo_stack[self.parent.current_index].pop()
        self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()



## Bit Plane Slicing
class BitPlaneSlicer(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        
        self.parent = parent
        self.setWindowTitle("Bit Plane Display")
        self.setMinimumSize(300, 200)
        
        self.buttons = [] # To store the button objects


        # Main Layout
        main_layout = QVBoxLayout()
        title = QLabel("Select Bit Planes to Display")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        main_layout.addStretch()
        
        
        # Grid Layout for the 4x2 buttons
        grid_layout = QGridLayout()
        grid_layout.setAlignment(Qt.AlignCenter)
        
        counter = 0
        for i in range(2):     
            for j in range(4): 
                btn = QRadioButton(f"Bit {counter}")
                
                btn.setAutoExclusive(False) 
                grid_layout.addWidget(btn, i, j)
                self.buttons.append(btn)
                counter += 1

        main_layout.addLayout(grid_layout)
        main_layout.addStretch()
        
        # Action Button
        self.reset_all_btn = QPushButton("Clear All")
        self.reset_all_btn.clicked.connect(self.reset_all)
        main_layout.addWidget(self.reset_all_btn)
        
        self.show_btn = QPushButton("Display Bit Planes")
        self.show_btn.clicked.connect(self.display_bit_planes)
        main_layout.addWidget(self.show_btn)
        
        self.opencv_grid_btn = QPushButton("Display with OpenCV")
        self.opencv_grid_btn.clicked.connect(self.display_opencv_grid)
        main_layout.addWidget(self.opencv_grid_btn)

        self.setLayout(main_layout)

    def reset_all(self):
        for btn in self.buttons:
            btn.setChecked(False)
    
    def display_bit_planes(self):
        current_focus = self.parent.get_focus_window()
        image = current_focus.display_image.copy()
        if len(image.shape) == 3:
            self.img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            self.img = image
        
        
        selected_bits = []
        for idx, btn in enumerate(self.buttons):
            if btn.isChecked():
                selected_bits.append(idx)
        if not selected_bits:
            selected_bits = list(range(8))

        count = len(selected_bits)
        
        cols = 4
        rows = (count // 4) + (1 if count % 4 > 0 else 0)
        if count < 4:
            cols = count
            rows = 1

        plt.figure(figsize=(12, 6))
        for plot_idx, bit_level in enumerate(selected_bits):
            # plane = np.zeros_like(self.img)
            
            # for i in range(self.img.shape[0]):
            #     for j in range(self.img.shape[1]):
            #         pixel_value = self.img[i, j]
            #         # Check if the specified bit is set
            #         if (pixel_value >> bit_level) & 1:
            #             plane[i, j] = 255
            #         else:
            #             plane[i, j] = 0
            
            plane = cv2.bitwise_and(self.img, 2**bit_level)
            
            # Threshold to make it visible (0 or 255)
            mask = plane > 0
            display_img = np.zeros_like(self.img)
            display_img[mask] = 255
            
            plt.subplot(rows, cols, plot_idx + 1)
            plt.title(f"Bit {bit_level}")
            plt.imshow(plane, cmap='gray')
            plt.xticks([])
            plt.yticks([])

        plt.tight_layout()
        plt.show()
        
        
    
    def display_opencv_grid(self):
        current_focus = self.parent.get_focus_window()
        image = current_focus.display_image.copy()
        if len(image.shape) == 3:
            self.img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            self.img = image
            
        
        selected_bits = [i for i, btn in enumerate(self.buttons) if btn.isChecked()]
        if not selected_bits:
            selected_bits = list(range(8))

        processed_images = []
        h, w = self.img.shape[:2]
        
        for bit_level in selected_bits:
            # Bitwise Slicing
            plane = cv2.bitwise_and(self.img, 2**bit_level)
            
            # Threshold to make it visible (0 or 255)
            mask = plane > 0
            display_slice = np.zeros_like(self.img)
            display_slice[mask] = 255

            labeled_slice = display_slice.copy()
            cv2.putText(labeled_slice, f"Bit {bit_level}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255), 2)
            
            cv2.rectangle(labeled_slice, (0,0), (w-1, h-1), (255), 12)
            
            processed_images.append(labeled_slice)

        MAX_COLS = 4
        rows_needed = (len(processed_images) + MAX_COLS - 1) // MAX_COLS
        
        blank_image = np.zeros((h, w), dtype=np.uint8)

        horizontal_rows = []
        
        for r in range(rows_needed):
            start_idx = r * MAX_COLS
            end_idx = start_idx + MAX_COLS
            row_imgs = processed_images[start_idx:end_idx]
            
            while len(row_imgs) < MAX_COLS:
                row_imgs.append(blank_image)
            
            h_concat = cv2.hconcat(row_imgs)
            horizontal_rows.append(h_concat)

        # Stitch all rows vertically
        if horizontal_rows:
            final_grid = cv2.vconcat(horizontal_rows)
            
            grid_h, grid_w = final_grid.shape[:2]
            
            MAX_DISPLAY_HEIGHT = 800
            MAX_DISPLAY_WIDTH = 1000
            if grid_h > MAX_DISPLAY_HEIGHT:
                scale_factor = min(MAX_DISPLAY_HEIGHT / grid_h, MAX_DISPLAY_WIDTH / grid_w)
                final_grid = cv2.resize(final_grid, None, fx=scale_factor, fy=scale_factor)

            cv2.imshow("Combined Bit Planes", final_grid)
            cv2.waitKey(1)


#/ #/
## Edge Detection Window
class ResizableLabel(QLabel):
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
#/ #/ #/layer
class EdgeDetectionPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        
        self.parent = parent
        self.apply = False
        self.cb_preview = QCheckBox("Preview")
        
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)
        
        

        self.setWindowTitle("Edge Detection Control Panel")
        self.setGeometry(200, 200, 500, 700)

    # Main Layout ------------------
        main_layout = QHBoxLayout()
        main_layout.addStretch()

        self.image_label = ResizableLabel("Image Display")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 400)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: white;")
        self.image_label.setScaledContents(False)

        main_layout.addWidget(self.image_label)


        controls_frame = QFrame()
        controls_frame.setFixedWidth(320)
        controls_layout = QVBoxLayout(controls_frame)

        # Algorithm Selector
        algo_layout = QVBoxLayout()
        algo_label = QLabel("Select Technique:")
        algo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        algo_layout.addWidget(algo_label)

        self.algo_grid_layout = QGridLayout()
        self.algo_grid_layout.setSpacing(5)


        self.algo_group = QButtonGroup(self)
        self.algo_group.setExclusive(True)
        tool_btn_style = """
            QToolButton {
                background-color: #e1e1e1;
                color: #333;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: #d4d4d4;
            }
            QToolButton:checked {
                background-color: #555;
                color: white;
                font-weight: bold;
            }
        """
        

        algos = ["Canny", "Roberts", "Sobel", "Prewitt", "Laplacian"]
        row, col = 0, 0
        for i, algo_name in enumerate(algos):
            btn = QToolButton()
            btn.setText(algo_name)
            btn.setCheckable(True) 
            btn.setStyleSheet(tool_btn_style)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(40) 
            
            self.algo_group.addButton(btn, i)
            self.algo_grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1


        # Add grid to the main layout
        algo_layout.addLayout(self.algo_grid_layout)
        controls_layout.addLayout(algo_layout)
        self.algo_group.button(0).setChecked(True)
        self.algo_group.buttonClicked.connect(self.on_algo_changed)


        # --- Sliders Container ---
        self.slider_layout = QVBoxLayout()
        slider_style = """
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
        """
        
        # Slider 1 (Used for Threshold 1 or Kernel Size)
        self.lbl_param1 = QLabel("Threshold 1:")
        self.lbl_param1.setStyleSheet("color: #444; font-weight: bold;")
        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setRange(0, 255)
        self.slider1.setValue(100)
        self.slider1.setMaximumSize(1000, 20)
        self.slider1.setStyleSheet(slider_style)
        self.slider1.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider1.sliderReleased.connect(self.preview)
        
        # Slider 2 (Used for Threshold 2 in Canny)
        self.lbl_param2 = QLabel("Threshold 2:")
        self.lbl_param2.setStyleSheet("color: #444; font-weight: bold;")
        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setRange(0, 255)
        self.slider2.setValue(200)
        self.slider2.setMaximumSize(1000, 20)
        self.slider2.setStyleSheet(slider_style)
        self.slider2.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider2.sliderReleased.connect(self.preview)

        # Color Inverse checkbox
        self.cb_inverse = QCheckBox("Color Inverse")
        self.cb_inverse.setChecked(True)
        self.cb_inverse.stateChanged.connect(lambda: self.preview(main_canvas=False))
        self.cb_inverse.stateChanged.connect(self.preview)
        # Gray Color checkbox
        self.cb_gray_color = QCheckBox("Gray Color")
        self.cb_gray_color.stateChanged.connect(lambda: self.preview(main_canvas=False))
        self.cb_gray_color.stateChanged.connect(self.preview)

        self.slider_layout.addSpacing(20)
        self.slider_layout.addWidget(self.lbl_param1)
        self.slider_layout.addWidget(self.slider1)
        self.slider_layout.addWidget(self.lbl_param2)
        self.slider_layout.addWidget(self.slider2)
        self.slider_layout.addWidget(self.cb_inverse)
        self.slider_layout.addWidget(self.cb_gray_color)
        
        self.cb_preview = QCheckBox("Preview")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        self.cb_all_layer = QCheckBox("Apply to All Layers")
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_btn_pressed)
        self.apply_btn.setShortcut(Qt.Key_Return)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)
        
        controls_layout.addLayout(self.slider_layout)
        controls_layout.addStretch()
        controls_layout.addStretch()
        controls_layout.addWidget(self.cb_preview)
        controls_layout.addWidget(self.cb_all_layer)
        controls_layout.addWidget(self.cancel_btn)
        controls_layout.addWidget(self.apply_btn)
        
        main_layout.addStretch()
        main_layout.addWidget(controls_frame)

        self.setLayout(main_layout)
        self.update_ui_controls() # Set initial state

    def get_current_method_name(self):
        btn = self.algo_group.checkedButton()
        if btn:
            return btn.text()
        return "Canny"

    def on_algo_changed(self, btn):
        self.update_ui_controls()
    
    def update_ui_controls(self):
        method = self.get_current_method_name()

        if method == "Canny":
            self.lbl_param1.setText("Threshold 1 (Min Val):")
            self.slider1.show()
            self.slider1.setRange(0, 255)
            self.slider1.setValue(100)
            
            self.lbl_param2.setText("Threshold 2 (Max Val):")
            self.lbl_param2.show()
            self.slider2.show()
            self.slider2.setValue(200)
        
        elif method == "Roberts":
            self.lbl_param2.setText("Threshold: ")
            self.lbl_param2.show()
            self.slider2.show()
            self.slider2.setValue(50)
            
        elif method == "Sobel" or method == "Prewitt" \
            or method == "Laplacian":
            self.lbl_param1.setText("Kernel Size (1, 3, 5, 7):")
            self.slider1.show()
            self.slider1.setValue(3)
            self.slider1.setRange(1, 7) # Kernel must be odd
            
            self.lbl_param2.hide()
            self.slider2.hide()
        
        self.preview()


    def process_image(self, image):
        """
        Image Process 
        """
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        b, g, r, a  = cv2.split(image)
        bgr         = cv2.merge([b, g, r])
        img_blur    = cv2.GaussianBlur(bgr, (3,3), 0)

        result = None
        method = self.get_current_method_name()
        if method == "Canny":
            t1 = self.slider1.value()
            t2 = self.slider2.value()
            # Update label text 
            self.lbl_param1.setText(f"Threshold 1: {t1}")
            self.lbl_param2.setText(f"Threshold 2: {t2}")
            
            result = cv2.Canny(img_blur, t1, t2)

        elif method == "Sobel":
            k_size = self.slider1.value()
            # Ensure kernel is odd (1, 3, 5, 7)
            if k_size % 2 == 0: k_size += 1
            self.lbl_param1.setText(f"Kernel Size: {k_size}x{k_size}")

            # Gradient X and Y
            sobelx    = cv2.Sobel(img_blur, cv2.CV_64F, 1, 0, ksize=k_size)
            sobely    = cv2.Sobel(img_blur, cv2.CV_64F, 0, 1, ksize=k_size)
            # sobelxy = cv2.Sobel(img_blur, cv2.CV_64F, 1, 1, ksize=k_size)
            
            # Combine
            magnitude = cv2.magnitude(sobelx, sobely)
            # result = sobelxy
            result    = cv2.convertScaleAbs(magnitude)

        elif method == "Prewitt":
            self.lbl_param1.setText("Fixed Prewitt Kernel (3x3)")
            self.slider1.hide()
            
            kernelx   = np.array([[1,1,1],[0,0,0],[-1,-1,-1]])
            kernely   = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
            
            prewittx  = cv2.filter2D(img_blur, -1, kernelx)
            prewitty  = cv2.filter2D(img_blur, -1, kernely)
            
            # Combine approx
            result    = cv2.addWeighted(prewittx, 0.5, prewitty, 0.5, 0)

        elif method == "Laplacian":
            self.lbl_param1.setText("Fixed Filter Kernel (3x3)")
            self.slider1.hide() 
            
            laplacian   = cv2.Laplacian(img_blur, cv2.CV_64F)
            
            result      = cv2.convertScaleAbs(laplacian)
        
        elif method == "Roberts":
            self.lbl_param1.setText("Fixed Filter Kernel (2x2)")
            self.slider1.hide() 
            t = self.slider2.value()
            self.lbl_param2.setText(f"Threshold: {t}")
            
            img = bgr.copy()
            if len(img.shape) == 3:
                gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray_image = img
            
            # Apply Roberts Cross kernels
            kernel_x = np.array([[1, 0], [0, -1]])
            kernel_y = np.array([[0, 1], [-1, 0]])
                                
            # Convolve the image with the kernels
            horizontal_edges    = cv2.filter2D(gray_image, -1, kernel_x)
            vertical_edges      = cv2.filter2D(gray_image, -1, kernel_y)
            
            # Ensure both arrays have the same data type
            horizontal_edges    = np.float32(horizontal_edges)
            vertical_edges      = np.float32(vertical_edges)
            gradient_magnitude  = cv2.magnitude(horizontal_edges, vertical_edges)
            
            threshold   = t
            _, result   = cv2.threshold(gradient_magnitude, threshold, 255, cv2.THRESH_BINARY)
            result      = result.astype(np.uint8)
            
            
        # Convert to gray if there are color
        if self.cb_gray_color.isChecked():
            if len(result.shape) == 3:
                result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        # Makesure it's color form
        if len(result.shape) == 2:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
                
                
        if self.cb_inverse.isChecked():
            img = result.copy()
            result = 255 - img
        
        return cv2.merge([*cv2.split(result), a])
#/
    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()
            
    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            self.display_image(region)
            return

        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()
    
#/
    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape


        bytes_per_line = img.strides[0]
        q_img = QImage(
            img.data, 
            w, h, bytes_per_line, 
            QImage.Format_RGBA8888
            ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img.copy())

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
    
    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            """ Process """
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
            
    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()




#/ #/ #/layer
## Thersholding Image
class ThresholdPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowStaysOnTopHint 
            | Qt.Tool
        )
        self.parent = parent
        self.setWindowTitle("Thresholding Control Panel")
        self.setGeometry(300, 300, 500, 650)
        
        self.apply = False
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
            
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)


        
        self.init_ui()
        self.preview(False)
        self.preview()

    def init_ui(self):
        layout = QVBoxLayout()

        self.image_label = ResizableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(350)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: white;")
        layout.addWidget(self.image_label)

        controls = QFrame()
        controls.setStyleSheet("background-color: #f0f0f0; border-radius: 8px;")
        ctrl_layout = QVBoxLayout(controls)

        # Combo Box for Threshold Type
        lbl_type = QLabel("Threshold Type:")
        self.combo_type = QComboBox()
        self.combo_type.setStyleSheet("font-size: 16px")
        self.combo_type.addItems(["Binary (Black/White)", "Binary Inverse", "Truncate", "To Zero", "To Zero Inverse"])
        self.combo_type.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
                color: #333;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 2px solid #999;
                border-bottom: 2px solid #999;
                width: 8px;
                height: 8px;
                margin-right: 10px;
                transform: rotate(-45deg);
            }
        """)
        self.combo_type.currentIndexChanged.connect(lambda: self.preview(False))
        self.combo_type.currentIndexChanged.connect(self.preview)
        
        # Slider
        self.lbl_val = QLabel("Threshold Value: 127")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 255)
        self.slider.setValue(127)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #666;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #333;
                border: 1px solid #333;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        self.slider.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider.sliderReleased.connect(self.preview)

        # Otsu Checkbox
        self.cb_otsu = QCheckBox("Use Otsu's Binarization (Auto)")
        self.cb_otsu.setToolTip("Automatically calculates the best threshold value")
        self.cb_otsu.stateChanged.connect(self.toggle_otsu)

        self.cb_preview = QCheckBox("Preview")
        self.cb_all_layer = QCheckBox("Apply to All Layer")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        
        ctrl_layout.addWidget(lbl_type)
        ctrl_layout.addWidget(self.combo_type)
        ctrl_layout.addSpacing(10)
        ctrl_layout.addWidget(self.lbl_val)
        ctrl_layout.addWidget(self.slider)
        ctrl_layout.addWidget(self.cb_otsu)
        ctrl_layout.addWidget(self.cb_preview)
        ctrl_layout.addWidget(self.cb_all_layer)

        layout.addWidget(controls)

        # 3. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFixedWidth(360)
        self.apply_btn.setShortcut(Qt.Key_Return)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)


    def toggle_otsu(self):
        is_otsu = self.cb_otsu.isChecked()
        self.slider.setEnabled(not is_otsu)
        self.lbl_val.setText("Threshold Value: Auto" if is_otsu else f"Threshold Value: {self.slider.value()}")
        self.preview()

    def get_threshold_type(self):
        idx = self.combo_type.currentIndex()
        if idx == 0: return cv2.THRESH_BINARY
        if idx == 1: return cv2.THRESH_BINARY_INV
        if idx == 2: return cv2.THRESH_TRUNC
        if idx == 3: return cv2.THRESH_TOZERO
        if idx == 4: return cv2.THRESH_TOZERO_INV
        return cv2.THRESH_BINARY

    def process_image(self, image):
        a = None
        bgr_img = image.copy()
        gray_img = image.copy()
        
        if len(image.shape) == 3 and image.shape[2] == 4:
            b, g, r, a = cv2.split(image)
            bgr_img = cv2.merge([b, g, r])
        if len(image.shape) == 3:
            gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
            
            
        thresh_type = self.get_threshold_type()
        
        if self.cb_otsu.isChecked():
            # Otsu requires the flag + 0 as value
            thresh_val, result = cv2.threshold(gray_img, 0, 255, thresh_type | cv2.THRESH_OTSU)
            self.lbl_val.setText(f"Threshold Value: {int(thresh_val)} (Auto)")
        else:
            thresh_val = self.slider.value()
            self.lbl_val.setText(f"Threshold Value: {thresh_val}")
            _, result = cv2.threshold(gray_img, thresh_val, 255, thresh_type)
            
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        
        return cv2.merge([*cv2.split(result), a]) if a is not None else result

#/       
    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()
#/       
    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            self.display_image(region)
            return
        
        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()
        
#/
    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
#/
    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape
        
            
        bytes_per_line = img.strides[0]
        q_img = QImage(
            img.data, 
            w, h, bytes_per_line, 
            QImage.Format_RGBA8888
        ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img.copy())
        
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)


    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()


#/ #/ #/layer
## Power Law Tansformation
class PowerLawPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowStaysOnTopHint 
            | Qt.Tool
        )
        
        self.parent = parent
        self.setWindowTitle("Power Law (Gamma) Transformation")
        self.setGeometry(250, 250, 500, 600)
        
        self.apply = False
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)
        
        

        self.init_ui()
        self.preview() 

    def init_ui(self):
        layout = QVBoxLayout()

    # Image Preview
        self.image_label = ResizableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(350)
        self.image_label.setStyleSheet("background-color: white; border: 1px solid #555;")
        layout.addWidget(self.image_label)

    # Controls Area
        controls = QFrame()
        ctrl_layout = QVBoxLayout(controls)

        # Slider Gamma
        self.lbl_gamma = QLabel("Gamma: 1.00")
        self.lbl_gamma.setStyleSheet("color: #444; font-weight: bold;")
        self.slider_gamma = QSlider(Qt.Horizontal)
        self.slider_gamma.setRange(1, 500) 
        self.slider_gamma.setValue(100)
        self.slider_gamma.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider_gamma.sliderReleased.connect(self.preview)
        self.slider_gamma.setStyleSheet("""
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
        
        # Reset Button
        self.btn_reset = QPushButton("Reset gamma")
        self.btn_reset.setFixedWidth(100)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)
        self.btn_reset.clicked.connect(lambda: self.slider_gamma.setValue(100))
        self.btn_reset.clicked.connect(self.preview)

        # Preview button
        self.cb_preview = QCheckBox("Preview")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        self.cb_all_layer = QCheckBox("Apply to All Layer")
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)

        ctrl_layout.addWidget(self.lbl_gamma)
        ctrl_layout.addWidget(self.slider_gamma)
        ctrl_layout.addWidget(self.btn_reset)
        ctrl_layout.addWidget(self.cb_preview)
        ctrl_layout.addWidget(self.cb_all_layer)

        layout.addWidget(controls)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply to Canvas")
        self.apply_btn.setFixedWidth(360)
        self.apply_btn.setShortcut(Qt.Key_Return)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        
#/
    def process_image(self, image):
        """
        Process
        """
        val   = self.slider_gamma.value()
        gamma = val / 100.0
        # Avoid division by zero
        if gamma == 0: 
            gamma = 0.01
        self.lbl_gamma.setText(f"Gamma: {gamma:.2f}")
            
            
        table = np.array(
            [((i / 255.0) ** gamma) * 255 
                for i in np.arange(0, 256)]
        ).astype("uint8")
        
        
        ## Only apply for rgb channels 
        if len(image.shape) == 3 and image.shape[2] == 4:
            b, g, r, a = cv2.split(image)
            bgr = cv2.merge([b, g, r])
            result = cv2.LUT(bgr, table)
            
            return cv2.merge([*cv2.split(result), a])
        else:
            return cv2.LUT(image, table)

    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()

    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            self.display_image(region)
            return

        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()
#/
    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape
        
        bytes_per_line = img.strides[0]

        q_img = QImage(
                img.data, 
                w, h, bytes_per_line, 
                QImage.Format_RGBA8888
            ).rgbSwapped()
        
        pixmap = QPixmap.fromImage(q_img.copy())
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            """ Process """
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
            
    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()
        
    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()
        
        
#/ #/ #/layer
## Piecewise Linear Tansformation
class TransferGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(255, 255)
        self.setStyleSheet("background-color: white; border: 1px solid black;")
        self.r1, self.s1 = 70, 0
        self.r2, self.s2 = 140, 255

    def update_points(self, r1, s1, r2, s2):
        self.r1, self.s1 = r1, s1
        self.r2, self.s2 = r2, s2
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Grid
        painter.setPen(QPen(QColor(220, 220, 220), 1, Qt.DotLine))
        painter.drawLine(0, 255, 255, 0) # Identity line reference
        
        
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        
        # Point 1: (0,0) to (r1, s1)
        painter.drawLine(0, 255 - 0, self.r1, 255 - self.s1)
        # Point 2: (r1, s1) to (r2, s2)
        painter.drawLine(self.r1, 255 - self.s1, self.r2, 255 - self.s2)
        # Point 3: (r2, s2) to (255, 255)
        painter.drawLine(self.r2, 255 - self.s2, 255, 255 - 255)
        
        # Draw Dots
        painter.setBrush(QColor(255, 0, 0))
        painter.drawEllipse(self.r1 - 3, (255 - self.s1) - 3, 6, 6)
        painter.drawEllipse(self.r2 - 3, (255 - self.s2) - 3, 6, 6)
        painter.end()
class PiecewisePanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowStaysOnTopHint 
            | Qt.Tool
        )
        
        self.parent = parent
        self.setWindowTitle("Piecewise Linear Transformation")
        self.setGeometry(200, 200, 700, 600)
        self.apply = False
        
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)
        
        
        
        self.init_ui()
        self.preview(False)
        self.preview()

    def init_ui(self):
        # 1. Main Layout Setup
        main_layout = QHBoxLayout()
        main_layout.addStretch()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- LEFT: Image Preview ---
        # left_layout = QVBoxLayout()
        self.image_label = ResizableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(400) 
        self.image_label.setStyleSheet("border: 1px solid #444; background-color: white;")
        self.image_label.setScaledContents(False)
        main_layout.addWidget(self.image_label)

        # --- RIGHT: Controls & Graph ---
        right_frame = QFrame()
        right_frame.setFixedWidth(340)
        right_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5; 
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(15, 15, 15, 15)

        # 1. The Graph
        lbl_graph = QLabel("TRANSFORMATION GRAPH")
        lbl_graph.setStyleSheet("font-weight: bold; font-size: 11px; color: #666; letter-spacing: 1px;")
        lbl_graph.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(lbl_graph)
        
        graph_container = QWidget()
        graph_container.setFixedHeight(280)
        graph_container.setStyleSheet("background-color: white; border-radius: 4px;")
        graph_layout = QHBoxLayout(graph_container)
        graph_layout.setContentsMargins(5, 5, 5, 5)
        
        self.graph = TransferGraph()
        graph_layout.addWidget(self.graph)
        right_layout.addWidget(graph_container)
        
        right_layout.addSpacing(15)

        # 2. Sliders
        # Define Slider Stylesheet
        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #666;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #333;
                border: 1px solid #333;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """
        
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        
        # Label Style
        lbl_style = "color: #333; font-weight: 500;"

        # R1 (Input 1)
        self.lbl_r1 = QLabel("r1 (In 1): 70")
        self.lbl_r1.setStyleSheet(lbl_style)
        self.slider_r1 = QSlider(Qt.Horizontal)
        self.slider_r1.setRange(0, 254)
        self.slider_r1.setValue(70)
        self.slider_r1.setStyleSheet(slider_style)

        # S1 (Output 1)
        self.lbl_s1 = QLabel("s1 (Out 1): 0")
        self.lbl_s1.setStyleSheet(lbl_style)
        self.slider_s1 = QSlider(Qt.Horizontal)
        self.slider_s1.setRange(0, 255)
        self.slider_s1.setValue(0)
        self.slider_s1.setStyleSheet(slider_style)

        # R2 (Input 2)
        self.lbl_r2 = QLabel("r2 (In 2): 140")
        self.lbl_r2.setStyleSheet(lbl_style)
        self.slider_r2 = QSlider(Qt.Horizontal)
        self.slider_r2.setRange(1, 255)
        self.slider_r2.setValue(140)
        self.slider_r2.setStyleSheet(slider_style)

        # S2 (Output 2)
        self.lbl_s2 = QLabel("s2 (Out 2): 255")
        self.lbl_s2.setStyleSheet(lbl_style)
        self.slider_s2 = QSlider(Qt.Horizontal)
        self.slider_s2.setRange(0, 255)
        self.slider_s2.setValue(255)
        self.slider_s2.setStyleSheet(slider_style)

        # Connect signals
        self.slider_r1.valueChanged.connect(self.check_constraints)
        self.slider_s1.valueChanged.connect(self.check_constraints)
        self.slider_r2.valueChanged.connect(self.check_constraints)
        self.slider_s2.valueChanged.connect(self.check_constraints)
        self.slider_r1.sliderReleased.connect(self.preview)
        self.slider_s1.sliderReleased.connect(self.preview)
        self.slider_r2.sliderReleased.connect(self.preview)
        self.slider_s2.sliderReleased.connect(self.preview)

        grid.addWidget(self.lbl_r1, 0, 0)
        grid.addWidget(self.slider_r1, 1, 0)
        grid.addWidget(self.lbl_s1, 2, 0)
        grid.addWidget(self.slider_s1, 3, 0)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #ddd; max-height: 1px;")
        grid.addWidget(line, 4, 0)
        
        grid.addWidget(self.lbl_r2, 5, 0)
        grid.addWidget(self.slider_r2, 6, 0)
        grid.addWidget(self.lbl_s2, 7, 0)
        grid.addWidget(self.slider_s2, 8, 0)

        right_layout.addLayout(grid)
        right_layout.addStretch()

        # 3. Apply Buttons
        self.cb_preview = QCheckBox("Preview")
        self.cb_preview.setStyleSheet("margin-bottom: 10px; color: #333;")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        self.cb_all_layer = QCheckBox("Apply to All Layer")
        self.cb_all_layer.setStyleSheet("margin-bottom: 10px; color: #333;")
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        
        # Reset Button (Secondary style)
        self.btn_reset = QPushButton("Reset Identity")
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                color: #333;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #eee;
                border-color: #bbb;
            }
        """)
        self.btn_reset.clicked.connect(self.reset_values)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFixedWidth(160)
        self.apply_btn.setShortcut(Qt.Key_Return)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        
        right_layout.addWidget(self.cb_preview)
        right_layout.addWidget(self.cb_all_layer)
        right_layout.addWidget(self.btn_reset)
        right_layout.addLayout(btn_layout)


        main_layout.addStretch()
        main_layout.addWidget(right_frame)
        self.setLayout(main_layout)
        
        self.setFocusPolicy(Qt.StrongFocus)


    def reset_values(self):
        self.slider_r1.setValue(0)
        self.slider_s1.setValue(0)
        self.slider_r2.setValue(255)
        self.slider_s2.setValue(255)
    
        if self.cb_preview.isChecked():
            self.preview()

    def check_constraints(self):
        r1 = self.slider_r1.value()
        r2 = self.slider_r2.value()

        # Logic: r1 cannot pass r2
        if r1 >= r2:
            if self.sender() == self.slider_r1:
                self.slider_r2.setValue(r1 + 1)
            else:
                self.slider_r1.setValue(r2 - 1)
        
        # Update text labels
        self.lbl_r1.setText(f"r1 (In): {self.slider_r1.value()}")
        self.lbl_s1.setText(f"s1 (Out): {self.slider_s1.value()}")
        self.lbl_r2.setText(f"r2 (In): {self.slider_r2.value()}")
        self.lbl_s2.setText(f"s2 (Out): {self.slider_s2.value()}")

        # Update Graph and Image
        self.graph.update_points(
            self.slider_r1.value(), self.slider_s1.value(),
            self.slider_r2.value(), self.slider_s2.value()
        )
        self.preview(main_canvas=False)

    def process_image(self, image):
        r1, s1 = self.slider_r1.value(), self.slider_s1.value()
        r2, s2 = self.slider_r2.value(), self.slider_s2.value()
        
        lut = np.zeros(256, dtype=np.uint8)

        # Segment 1: 0 -> r1
        for i in range(r1):
            lut[i] = (s1 / max(r1, 1)) * i
            
        # Segment 2: r1 -> r2
        for i in range(r1, r2):
            slope = (s2 - s1) / max((r2 - r1), 1)
            lut[i] = slope * (i - r1) + s1
            
        # Segment 3: r2 -> 255
        for i in range(r2, 256):
            slope = (255 - s2) / max((255 - r2), 1)
            lut[i] = slope * (i - r2) + s2

        # Apply LUT
        return cv2.LUT(image, lut)
    
#/ 
    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()
#/ 
    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            self.display_image(region)
            return

        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()
            
        
#/
    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape
            
            
        bytes_per_line = img.strides[0]
        q_img = QImage(
                img.data, 
                w, h, bytes_per_line, 
                QImage.Format_RGBA8888
            ).rgbSwapped()
         
        pixmap = QPixmap.fromImage(q_img.copy())
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
#/
    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            """ Process """
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
     
     
    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
       
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
    
    
#/ #/ #/layer
## Erosion effect
class MorphologyPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowStaysOnTopHint 
            | Qt.Tool
        )
        self.parent = parent
        self.setWindowTitle("Morphological Control Panel")
        self.setGeometry(200, 200, 500, 700)
        self.apply = False
        
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)
        
        
        
        self.init_ui()
        # Default to Erosion (Index 0)
        self.op_group.button(0).setChecked(True)
        self.preview()

    def init_ui(self):
       
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.addStretch()

       
        self.image_label = ResizableLabel("Image Display")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setStyleSheet("border: 1px solid #444; background-color: white;")
        self.image_label.setScaledContents(False)
        
        main_layout.addWidget(self.image_label) 

    # Controls Panel -----------------------------------
        controls_frame = QFrame()
        controls_frame.setFixedWidth(320)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5; 
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        # Operation Selector (Grid of Buttons)
        op_label = QLabel("OPERATIONS")
        op_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #666; letter-spacing: 1px;")
        controls_layout.addWidget(op_label)

        self.op_grid_layout = QGridLayout()
        self.op_grid_layout.setSpacing(5)

        self.op_group = QButtonGroup(self)
        self.op_group.setExclusive(True)

        
        # Normal: Light Grey | Checked: Dark Grey | Hover: Slightly darker
        tool_btn_style = """
            QToolButton {
                background-color: #e1e1e1;
                color: #333;
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }
            QToolButton:hover {
                background-color: #d4d4d4;
            }
            QToolButton:checked {
                background-color: #555;
                color: white;
                font-weight: bold;
            }
        """

        ops = ["Erosion", "Dilation", "Opening", "Closing"]
        row, col = 0, 0
        for i, op_name in enumerate(ops):
            btn = QToolButton()
            btn.setText(op_name)
            btn.setCheckable(True) 
            btn.setStyleSheet(tool_btn_style)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(35) 
            
            self.op_group.addButton(btn, i)
            self.op_grid_layout.addWidget(btn, row, col)
            
            # Button Click triggers preview
            btn.clicked.connect(lambda: self.preview(main_canvas=False))
            btn.clicked.connect(self.preview)

            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        controls_layout.addLayout(self.op_grid_layout)
        
        # Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ddd; max-height: 1px;")
        controls_layout.addSpacing(15)
        controls_layout.addWidget(line)
        controls_layout.addSpacing(15)

        slider_layout = QVBoxLayout()
        # Shared Slider Style
        slider_style = """
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
        """

        
        lbl_shape = QLabel("Kernel Shape")
        lbl_shape.setStyleSheet("color: #444; font-weight: bold;")
        
        self.combo_shape = QComboBox()
        self.combo_shape.addItems(["Rectangle", "Cross", "Ellipse"])
        self.combo_shape.setStyleSheet("""
            QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
                color: #333;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.combo_shape.currentIndexChanged.connect(lambda: self.preview(False))
        self.combo_shape.currentIndexChanged.connect(self.preview)
        
        slider_layout.addWidget(lbl_shape)
        slider_layout.addWidget(self.combo_shape)
        slider_layout.addSpacing(15)

        # Kernel Size Slider
        self.lbl_ksize = QLabel("Kernel Size: 3x3")
        self.slider_ksize = QSlider(Qt.Horizontal)
        self.slider_ksize.setRange(1, 7)
        self.slider_ksize.setValue(3)
        self.slider_ksize.setStyleSheet(slider_style)
        self.slider_ksize.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider_ksize.sliderReleased.connect(self.preview)
        
        slider_layout.addWidget(self.lbl_ksize)
        slider_layout.addWidget(self.slider_ksize)
        slider_layout.addSpacing(10)
        
        # Iterations Slider
        self.lbl_iter = QLabel("Iterations: 1")
        self.slider_iter = QSlider(Qt.Horizontal)
        self.slider_iter.setRange(1, 10)
        self.slider_iter.setValue(1)
        self.slider_iter.setStyleSheet(slider_style)
        self.slider_iter.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider_iter.sliderReleased.connect(self.preview)

        slider_layout.addWidget(self.lbl_iter)
        slider_layout.addWidget(self.slider_iter)

        controls_layout.addLayout(slider_layout)
        controls_layout.addStretch() 

    # Action Buttons --------------------------------
        
        # Preview Checkbox
        self.cb_preview = QCheckBox("Preview")
        self.cb_preview.setChecked(False)
        self.cb_preview.setStyleSheet("font-size: 13px; margin-bottom: 10px; color: #333;")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        
        # Apply all Checkbox
        self.cb_all_layer = QCheckBox("Apply to All Layer")
        self.cb_all_layer.setChecked(False)
        self.cb_all_layer.setStyleSheet("font-size: 13px; margin-bottom: 10px; color: #333;")
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        
        # Cancel Button - Styled as clickable text (Transparent)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.clicked.connect(self.close)

        # Apply Button - Styled as a large rounded green button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)
        self.apply_btn.setShortcut(Qt.Key_Return)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)

        controls_layout.addWidget(self.cb_preview)
        controls_layout.addWidget(self.cb_all_layer)
        controls_layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
        controls_layout.addWidget(self.apply_btn)

        # Add Controls to Main Layout
        main_layout.addStretch()
        main_layout.addWidget(controls_frame)

        self.setLayout(main_layout)

    def process_image(self, image):
        # Get Selected Operation
        op_id = self.op_group.checkedId()
        if op_id == -1: op_id = 0

        shape_idx = self.combo_shape.currentIndex()
        
        k_val = self.slider_ksize.value()
        if k_val % 2 == 0: k_val += 1
        self.lbl_ksize.setText(f"Kernel Size: {k_val}x{k_val}")
        
        iters = self.slider_iter.value()
        self.lbl_iter.setText(f"Iterations: {iters} times")

        # 2. Define Kernel
        morph_shape = cv2.MORPH_RECT
        if shape_idx == 1: morph_shape = cv2.MORPH_CROSS
        elif shape_idx == 2: morph_shape = cv2.MORPH_ELLIPSE
        
        kernel = cv2.getStructuringElement(morph_shape, (k_val, k_val))
        img = image.copy()
        
        # Erosion
        if op_id == 0:
            result = cv2.erode(img, kernel, iterations=iters)
        # Dilation
        elif op_id == 1:
            result = cv2.dilate(img, kernel, iterations=iters)
        # Opening
        elif op_id == 2:
            result = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=iters)
        # Closing
        elif op_id == 3:
            result = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel, iterations=iters)
        else:
            result = img

        return result

    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()

    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            self.display_image(region)
            return

        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()

#/ 
    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape


        bytes_per_line = img.strides[0]
        q_img = QImage(
            img.data, 
            w, h, bytes_per_line, 
            QImage.Format_RGBA8888
            ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img.copy())

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)


    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            """ Process """
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
     
    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()
    
    def closeEvent(self, event: QCloseEvent):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()


#/layer
## Histogram 
class HistogramEqualizationPanel(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Window 
            | Qt.WindowType.WindowStaysOnTopHint 
            | Qt.WindowType.Tool
        )
        
        self.parent = parent
        self.setWindowTitle("Histogram Equalization Control Panel")
        self.setGeometry(200, 200, 950, 600)
        self.apply = False
        
        # Origianal layer
        self.original_layer = []
        _, layers = self.parent.image_list[self.parent.current_index]
        for layer in layers:
            self.original_layer.append((layer, layer.image.copy()))
        # Original current layer image
        self.original_image = self.parent.current_focus_layer_image()
        # Original composite image
        self.original_composite_image  = LayerManager.compose_layers(layers)
        
        
        
        self.init_ui()
        self.algo_group.button(0).setChecked(True)
        self.toggle_sliders(0) 
        
        self.preview_btn_pressed()
    
    def init_ui(self):
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        main_layout.addStretch()
        
        # Image Display ------------------
        self.image_label = ResizableLabel("Image Display")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(400)
        self.image_label.setStyleSheet("border: 1px solid #444; background-color: white;")
        
        main_layout.addWidget(self.image_label)

        # Controls -------------------------
        controls_frame = QFrame()
        controls_frame.setFixedWidth(320)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5; 
                border-radius: 4px;
                border: 1px solid #ddd;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(15, 15, 15, 15)

        # Histogram ---------------------------
        lbl_hist = QLabel("HISTOGRAM PREVIEW")
        lbl_hist.setStyleSheet("font-weight: bold; font-size: 11px; color: #666; letter-spacing: 1px;")
        controls_layout.addWidget(lbl_hist)
        
        self.hist_plot_label = QLabel()
        self.hist_plot_label.setFixedHeight(100)
        self.hist_plot_label.setStyleSheet("background-color: #222; border: 1px solid #555; border-radius: 4px;")
        self.hist_plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.hist_plot_label)
        controls_layout.addSpacing(15)

        lbl_method = QLabel("METHOD")
        lbl_method.setStyleSheet("font-weight: bold; font-size: 11px; color: #666; letter-spacing: 1px;")
        controls_layout.addWidget(lbl_method)
        
        self.algo_grid = QGridLayout()
        self.algo_grid.setSpacing(5)
        self.algo_group = QButtonGroup(self)
        self.algo_group.setExclusive(True)

        tool_btn_style = """
            QToolButton {
                background-color: #e1e1e1;
                color: #333;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                padding: 8px;
            }
            QToolButton:hover {
                background-color: #d4d4d4;
            }
            QToolButton:checked {
                background-color: #555;
                color: white;
                font-weight: bold;
            }
        """
        algos = ["Global Equalization", "CLAHE (Adaptive)"]
        for i, name in enumerate(algos):
            btn = QToolButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.setStyleSheet(tool_btn_style)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            
            self.algo_group.addButton(btn, i)
            self.algo_grid.addWidget(btn, i, 0) 
            
            btn.clicked.connect(lambda _, idx=i: self.on_algo_changed(idx))
        
        controls_layout.addLayout(self.algo_grid)
        controls_layout.addSpacing(15)

        self.slider_container = QWidget()
        self.slider_layout = QVBoxLayout(self.slider_container)
        self.slider_layout.setContentsMargins(0,0,0,0)

        slider_style = """
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #666;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #333;
                border: 1px solid #333;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """

        # Clip Limit Slider
        self.lbl_clip = QLabel("Clip Limit: 2.0")
        self.lbl_clip.setStyleSheet("color: #333; font-weight: 500;")
        self.slider_clip = QSlider(Qt.Orientation.Horizontal)
        self.slider_clip.setRange(1, 100) 
        self.slider_clip.setValue(20)
        self.slider_clip.setStyleSheet(slider_style)
        self.slider_clip.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider_clip.sliderReleased.connect(self.preview)
        
        self.slider_layout.addWidget(self.lbl_clip)
        self.slider_layout.addWidget(self.slider_clip)
        self.slider_layout.addSpacing(10)
        
        # Grid Size Slider
        self.lbl_grid = QLabel("Tile Grid Size: 8x8")
        self.lbl_grid.setStyleSheet("color: #333; font-weight: 500;")
        self.slider_grid = QSlider(Qt.Orientation.Horizontal)
        self.slider_grid.setRange(1, 32)
        self.slider_grid.setValue(8)
        self.slider_grid.setStyleSheet(slider_style)
        self.slider_grid.valueChanged.connect(lambda: self.preview(main_canvas=False))
        self.slider_grid.sliderReleased.connect(self.preview)

        self.slider_layout.addWidget(self.lbl_grid)
        self.slider_layout.addWidget(self.slider_grid)

        controls_layout.addWidget(self.slider_container)
        controls_layout.addStretch()

    # Action Buttons --------------------
        # preview 
        self.cb_preview = QCheckBox("Preview")
        self.cb_preview.setChecked(False)
        self.cb_preview.setStyleSheet("font-size: 13px; margin-bottom: 10px; color: #444;")
        self.cb_preview.stateChanged.connect(self.preview_btn_pressed)
        
        # Apply all layer
        self.cb_all_layer = QCheckBox("Apply tto All Layer")
        self.cb_all_layer.setChecked(False)
        self.cb_all_layer.setStyleSheet("font-size: 13px; margin-bottom: 10px; color: #444;")
        self.cb_all_layer.stateChanged.connect(self.preview_btn_pressed)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)
        self.cancel_btn.clicked.connect(self.close)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2da44e; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #2da44e;
            }
            QPushButton:hover {
                background-color: #2c974b;
            }
            QPushButton:pressed {
                background-color: #298e46;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_btn_pressed)

        controls_layout.addWidget(self.cb_preview)
        controls_layout.addWidget(self.cb_all_layer)
        controls_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.apply_btn)

        main_layout.addStretch()
        main_layout.addWidget(controls_frame)
        self.setLayout(main_layout)
        
    def on_algo_changed(self, idx):
        self.toggle_sliders(idx)
        self.preview(False)
        self.preview()

    def toggle_sliders(self, idx):
        # Method Clahe
        if idx == 1:
            self.slider_container.setVisible(True)
        else:
        # Method Global
            self.slider_container.setVisible(False)

    def draw_histogram(self, image):
        if image is None: return

        h, w = 100, 300
        hist_img = np.zeros((h, w, 3), dtype=np.uint8)
        
        colors = []
        if len(image.shape) == 2:
            colors = [((255, 255, 255), image)] 
        else:
            # Split BGR
            if image.shape[2] == 3:
                b, g, r = cv2.split(image)
            else:
                b, g, r, _ = cv2.split(image)
                
            colors = [((255, 0, 0), b), ((0, 255, 0), g), ((0, 0, 255), r)]

        for color, channel in colors:
            # Calculate histogram
            hist = cv2.calcHist([channel], [0], None, [256], [0, 256])
            cv2.normalize(hist, hist, 0, h, cv2.NORM_MINMAX)
            
            # Draw lines
            pts = np.int32(np.column_stack((np.arange(256) * (w / 256), h - hist)))
            cv2.polylines(hist_img, [pts], False, color, 1)

        # Display on QLabel
        bytes_per_line = 3 * w
        q_img = QImage(hist_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.hist_plot_label.setPixmap(QPixmap.fromImage(q_img))

    def process_image(self, image):
        method_idx = self.algo_group.checkedId()
        if method_idx == -1: method_idx = 0

        img = image.copy()
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                _, _, _, a = cv2.split(img)
            
            ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            channels = list(cv2.split(ycrcb))
            to_process = channels[0]
        else:
            to_process = img


        # Method Global Histogram Equalization -----------
        if method_idx == 0:
            processed_channel = cv2.equalizeHist(to_process)
            
        # Mehod CLAHE -------------------------------
        elif method_idx == 1:
            clip_limit = self.slider_clip.value() / 10.0
            grid_size = self.slider_grid.value()
            
            self.lbl_clip.setText(f"Clip Limit: {clip_limit:.1f}")
            self.lbl_grid.setText(f"Tile Grid Size: {grid_size}x{grid_size}")

            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
            processed_channel = clahe.apply(to_process)
        else:
            processed_channel = to_process

        # --- RECONSTRUCT ---
        if len(img.shape) == 3:
            channels[0] = processed_channel
            merged = cv2.merge(channels)
            result = cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)
        else:
            result = processed_channel
            
        if len(image.shape) == 3 and image.shape[2] == 4:
            return cv2.merge([*cv2.split(result), a])
        else:
            return result

    def preview(self, main_canvas=True):
        """
        Update preview image on Control Panel, or (Main canvas preview)
        """
        
        # Only update result on control panel (process single image for speed)
        if not self.cb_preview.isChecked() or not main_canvas:
            
            if self.cb_all_layer.isChecked():
                image = self.original_composite_image.copy()
            else: image = self.original_image.copy()

            result = self.process_image(image)
            if result is None: return
            
            current_focus = self.parent.get_focus_window()
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)

            self.display_image(region)
            self.draw_histogram(region)
            return

        if not main_canvas: return
        # Apply on main canvas (result by layer)
        self.apply_on_layer()
        self.parent.display_current_image()

    def preview_btn_pressed(self):
        if not self.cb_preview.isChecked():
            self.restore_layers()
        self.preview(False)
        self.preview()

    def display_image(self, img):
        if img is None: return
        if img.dtype != np.uint8:
            img = cv2.convertScaleAbs(img)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
        elif len(img.shape) == 3:
            if img.shape[2] == 3:     
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        h, w, _ = img.shape
            
        bytes_per_line = img.strides[0]
        q_img = QImage(
            img.data, 
            w, h, bytes_per_line, 
            QImage.Format_RGBA8888
        ).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img.copy())
        
        # Scale to fit label
        scaled = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)
    
    def apply_on_layer(self):
        """
        Apply the result in layer system
        """
        # Apply on main canvas (result by layer)
        if self.cb_all_layer.isChecked():
            target = self.original_layer
        else:
            current_layer = self.parent.get_current_focus_layer()
            target = [(current_layer, self.original_image)]
        
        # Apply process
        current_focus = self.parent.get_focus_window()
        for layer, image in target:
            """ Process """
            result = self.process_image(image)
            
            region = self.parent.get_result_by_roi(image, result, current_focus.selected_rect)
            layer.set_image(region)
            
    def restore_layers(self):
        """
        Reverts layers to their state before the dialog opened
        """
        for layer, ori_img in self.original_layer:
            layer.set_image(ori_img.copy())
        self.parent.display_current_image()
        
    def apply_btn_pressed(self):
        self.apply = True
        
        self.apply_on_layer()
                   
        self.parent.display_current_image()
        self.close()

    def closeEvent(self, event):
        if not self.apply:
            self.parent.undo_stack[self.parent.current_index].pop()
            self.restore_layers()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()
        