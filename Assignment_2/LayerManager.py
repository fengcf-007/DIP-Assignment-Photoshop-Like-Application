import os
import copy
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QComboBox, QSlider, QAbstractItemView,
    QListWidgetItem, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QImage, QPixmap, QCloseEvent

# from main import assets_path
## Path of assets folder loaded 
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
assets_path = parent_path + "\\Assets\\"


## Multiple Layer Controller
"""
Layer Information for Store Undo/Redo
"""
class LayerState:
    def __init__(self, name, opacity, is_visible, blend_mode, clipping_mask, image_data):
        """
        Layer Information
        """
        self.name = name
        self.opacity = opacity
        self.is_visible = is_visible
        self.blend_mode = blend_mode
        self.clipping_mask = clipping_mask
        self.image_data = copy.deepcopy(image_data)

"""
Single Layer Information Object
"""
class Layer:
    """
    Single Layer Information Object
    """
    
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

"""
Layer Panel UI for managing and display multiple layers
"""
class LayersPanel(QWidget):
    """
    Layer Panel UI for managing and display multiple layers
    """

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

"""
Handle Layer Operations \n
Create, Merge, Blend Modes
"""
class LayerManager:
    """
    Handle Layer Operations \n
    Create, Merge, Blend Modes
    """
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


