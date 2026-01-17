import cv2
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QWidget,
    QPushButton, QSlider, QHBoxLayout, 
    QComboBox, QCheckBox, QRadioButton, 
    QGridLayout, QSizePolicy, QFrame, 
    QToolButton, QButtonGroup, 
    
)
from PyQt5.QtGui import (
    QImage, QPixmap, QCloseEvent
)
from PyQt5.QtCore import Qt

from Assignment_2.LayerManager import LayerManager
from Assignment_2.ResizableLabel import ResizableLabel
    



""" Bit Plane Slicing Tool """
class BitPlaneSlicer(QWidget):
    """
    Bit Plane Slicing Tool
    """
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


#/ #/ #/layer
""" Edge Detection Window Panel """
class EdgeDetectionPanel(QWidget):
    """ Edge Detection Window Panel """
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
""" Thersholding Control Panel """
class ThresholdPanel(QWidget):
    """ Thersholding Control Panel """
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
""" Morphological Control Panel """
class MorphologyPanel(QWidget):
    """ Morphological Control Panel """
    
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


""" Histogram Equalization Control Panel """
class HistogramEqualizationPanel(QWidget):
    """ Histogram Equalization Control Panel """
        
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
        