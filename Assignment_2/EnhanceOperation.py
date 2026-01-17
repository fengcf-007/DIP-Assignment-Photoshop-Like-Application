import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, 
    QCheckBox, QSpinBox, QGroupBox, QGridLayout, QSizePolicy, QFrame
)
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QCloseEvent
)
from PyQt5.QtCore import Qt

from Assignment_2.LayerManager import LayerManager
from Assignment_2.ResizableLabel import ResizableLabel


""" Image Enhancement Filters Operation """
class ImageEnhancer:
    """
    Image Enhancement Filters Operation
    """

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

""" Window Panel for Image Enhancement Filters """
class EnhancePanel(QWidget):
    """
    Window Panel for Image Enhancement Filters
    """
    
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


""" Window Panel for Power Law (Gamma) Transformation """
class PowerLawPanel(QWidget):
    """
    Window Panel for Power Law (Gamma) Transformation
    """
    
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
        


""" Graph Widget for Piecewise Linear Transformation """
class TransferGraph(QWidget):
    """
    Graph Widget for Piecewise Linear Transformation
    """
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
""" Window Panel for Piecewise Linear Transformation """
class PiecewisePanel(QWidget):
    """
    Window Panel for Piecewise Linear Transformation
    """
    
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
   