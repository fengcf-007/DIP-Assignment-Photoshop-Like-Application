import sys
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QFileDialog, QHBoxLayout, QMessageBox, QFrame,
    QApplication, QComboBox, QCheckBox, 
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QCloseEvent


try:
    from Assignment_2.ResizableLabel import ResizableLabel
except ImportError:
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


""" Barcode Reader Panel """
class BarcodeReader(QWidget):
    """ Barcode Reader Panel """
    
    def __init__(self, parent=None, image=None):
        super().__init__()
        self.setWindowFlags(
            Qt.Window 
            | Qt.WindowStaysOnTopHint 
            | Qt.Tool
        )
        self.parent = parent
        self.setWindowTitle("Barcode Reader Panel")
        self.setGeometry(600, 230, 400, 450)
        
        # State variables
        self.canvas_image = image
        self.image = image 
        self.result = None
        
        self.is_paused = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None

        self.init_ui()
        self.process_image(self.image)


    def init_ui(self):
        layout = QVBoxLayout()

    # Image Display
        self.image_label = ResizableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(250)
        self.image_label.setStyleSheet("border: 2px solid #ccc; background-color: white;")
        layout.addWidget(self.image_label)

        self.lbl_tips = QLabel("Tip: Align barcode horizontally in the frame.")
        self.lbl_tips.setStyleSheet("""
            background-color: #e3f2fd; 
            color: #0d47a1; 
            padding: 8px; 
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.lbl_tips.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_tips)
        
    # Buttons control
        controls = QFrame()
        controls.setStyleSheet("background-color: #f0f0f0; border-radius: 8px;")
        ctrl_layout = QVBoxLayout(controls)

    # State display
        self.status_label = QLabel("Idle\n")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.status_label.setAlignment(Qt.AlignCenter)
        ctrl_layout.addWidget(self.status_label)

    # Image source
        h_btn_layout = QVBoxLayout()
        button_style = """
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                color: #333;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:checked {
                background-color: #ddd;
                border: 1px solid #999;
            }
        """
        
        lbl_source = QLabel("Image Source:")
        self.combo_source = QComboBox()
        self.combo_source.setStyleSheet("font-size: 16px")
        self.combo_source.addItems([
            "Canvas", 
            "File Upload", 
            "Camera"
        ])
        self.combo_source.setStyleSheet("""
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
        self.combo_source.currentIndexChanged.connect(self.changed_source)
        
        # Upload Button
        self.btn_upload = QPushButton("Upload Image")
        self.btn_upload.setStyleSheet(button_style)
        self.btn_upload.clicked.connect(self.upload_image)
        self.btn_upload.hide()
        # Capture button
        self.btn_capture = QPushButton("Capture Camera")
        self.btn_capture.clicked.connect(self.toggle_capture)
        self.btn_capture.setStyleSheet("""
            QPushButton { background-color: #ff9800; color: white; font-weight: bold; border: none; padding: 5px; border-radius: 4px; }
            QPushButton:hover { background-color: #f57c00; }
        """)
        self.btn_capture.hide()
        
        
        # Otsu's Thresholding
        self.cb_otsu = QCheckBox("Apply Otsu's Thresholding")
        self.cb_otsu.setChecked(True)
        self.cb_otsu.setStyleSheet("font-size: 13px; color: #333; margin-left: 5px;")
        self.cb_otsu.stateChanged.connect(lambda: self.process_image(self.image))
        
        h_btn_layout.addWidget(lbl_source)
        h_btn_layout.addWidget(self.combo_source)
        h_btn_layout.addWidget(self.btn_upload)
        h_btn_layout.addWidget(self.btn_capture)
        h_btn_layout.addWidget(self.cb_otsu)
        
        ctrl_layout.addStretch()
        ctrl_layout.addLayout(h_btn_layout)
        
        layout.addWidget(controls)

    # Buttons area
        btn_layout = QVBoxLayout()
        # Close button
        self.cancel_btn = QPushButton("Close")
        self.cancel_btn.setShortcut(Qt.Key_Escape)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setFixedWidth(80)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                color: #666; 
                font-size: 14px;
            }
            QPushButton:hover {
                color: #333;
                text-decoration: underline;
            }
        """)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.setAlignment(self.cancel_btn, Qt.AlignCenter)

        # Copy button
        apply_copy_layout = QHBoxLayout()
        self.btn_copy = QPushButton("Copy Data")
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #0366d6; 
                color: white; 
                font-size: 14px; 
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #0366d6;
            }
            QPushButton:hover {
                background-color: #0255b3;
            }
        """)
        apply_copy_layout.addWidget(self.btn_copy)

        # Apply insert button
        self.btn_insert = QPushButton("Insert to Canvas")
        self.btn_insert.clicked.connect(self.insert_to_canvas)
        self.btn_insert.setStyleSheet("""
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
        """)
        apply_copy_layout.addWidget(self.btn_insert)

        btn_layout.addLayout(apply_copy_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.display_image(self.image)


    
    def process_image(self, image):
        """
        Core logic to handle lighting, detection, and drawing yellow boxes.
        """
        if image is None: return
        
        gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.generate_tips(gray_img)
        
        
    #Image enchancement
        gray_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
        if self.cb_otsu.isChecked():
            _, gray_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            try:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                gray_img = clahe.apply(gray_img)
            except Exception:
                pass
        

        # Detect Barcodes
        barcodes = decode(gray_img)
        result_image = image.copy()
        detection_status = "Barcode detecting... \n"
        
        # Process barcode if found
        if barcodes:
            result_image = self.process_barcodes(barcodes, result_image)
            self.display_image(result_image)
            return
        
        # No barcodes found, 
        # Find the pattern that look like barcode
        rect_box = self.detect_candidate_region(image)
        if rect_box is not None:
            # Found  the barcode shape but cant decode
            box = cv2.boxPoints(rect_box)
            box = np.int64(box)
            cv2.drawContours(result_image, [box], -1, (0, 255, 255), 9)
            
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: orange;")
        else:
            # Exalty no barcode found
            detection_status = "No Barcode Detected\n"
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
            self.result = None
        self.status_label.setText(detection_status)
        self.display_image(result_image)

    def detect_candidate_region(self, image):
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Gradient-based detection
        gradX = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
        gradY = cv2.Sobel(gray, ddepth=cv2.CV_32F, dx=0, dy=1, ksize=-1)
        gradient = cv2.subtract(gradX, gradY)
        gradient = cv2.convertScaleAbs(gradient)

        # Thresholding
        blurred = cv2.blur(gradient, (9, 9))
        (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

        # Morphological
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        # Clean up small blobs (Erosion/Dilation)
        closed = cv2.erode(closed, None, iterations=4)
        closed = cv2.dilate(closed, None, iterations=4)

        # 3. Find Contours and Check Aspect Ratio
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return None
            
        c = sorted(contours, key=cv2.contourArea, reverse=True)[0]
        
        rect = cv2.minAreaRect(c)
        (x, y), (w, h), angle = rect
        
        if h > w: 
            w, h = h, w
        if h == 0: return None
        aspect_ratio = w / float(h)

        if aspect_ratio > 1.3:
            return rect
        return None

    def process_barcodes(self, barcodes, img):
        for barcode in barcodes:
            # Decode data
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type
            
            # Detected data
            detection_status = f"Detected barcode: {barcode_type} - \n{barcode_data}"
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
            
            # Bounding box for barcode
            points = barcode.polygon
            if len(points) == 4:
                pts = np.array(points, np.int32)
                pts = pts.reshape((-1, 1, 2))
                
                cv2.polylines(img, [pts], True, (0, 255, 255), 9)
                txt_pos = (min(p.x for p in points), min(p.y for p in points) - 10)
            else:
                # Fallback for non-standard shapes
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 9)
                txt_pos = (x, y - 10)

            # Put text above the barcode
            text = barcode_data
            cv2.putText(img, text, txt_pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 5)
        
        # Display and save the data result
        self.status_label.setText(detection_status)
        self.result = barcode_data if barcodes else ""
        return img

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

    def generate_tips(self, img):
        brightness = np.mean(img)
        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
        
    # Display tips
        tip_text = "Tip: "
        if brightness < 60:
            tip_text += "Image too dark. Turn on flashlight ."
        elif brightness > 220:
            tip_text += "Image too bright. Turn off light."
        elif laplacian_var < 50: # Threshold for blur (adjustable)
            tip_text += "Image is blurry. Hold camera steady."
        else:
            tip_text += "Image looks good. Align barcode horizontally."
        self.lbl_tips.setText(tip_text)



    def changed_source(self):
        self.btn_upload.hide()
        self.btn_capture.hide()
        self.toggle_camera(False)
        if self.is_paused:
            self.toggle_capture()
        
        source = self.combo_source.currentText()
        if source == "Canvas":
            self.image = self.canvas_image
            self.process_image(self.image)
        elif source == "File Upload":
            self.btn_upload.show()
        elif source == "Camera":
            self.toggle_camera(True)
            self.btn_capture.show()
                
    def toggle_camera(self, toggle):
        # Camera opened
        if toggle:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                QMessageBox.warning(self, "Error", "Could not open camera")
                return
            self.timer.start(30)
            return
        
        # Camera closed
        self.timer.stop()
        if self.cap:
            self.cap.release()
        self.display_image(self.image)

    def toggle_capture(self):
        if self.cap is None: return
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            # Capture (Freeze)
            self.timer.stop()
            self.btn_capture.setText("Resume Camera")
            self.btn_capture.setStyleSheet("""
                QPushButton { background-color: #2196f3; color: white; font-weight: bold; border: none; padding: 5px; border-radius: 4px; }
                QPushButton:hover { background-color: #1976d2; }
            """)
        else:
            # Resume
            self.timer.start(30)
            self.btn_capture.setText("Capture Frame")
            self.btn_capture.setStyleSheet("""
                QPushButton { background-color: #ff9800; color: white; font-weight: bold; border: none; padding: 5px; border-radius: 4px; }
                QPushButton:hover { background-color: #f57c00; }
            """)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.image = frame
            self.process_image(frame)

    def upload_image(self):

        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.bmp)")
        if file_path:
            image = cv2.imread(file_path)
            if image is not None:
                self.image = image
                self.process_image(image)

    
    def insert_to_canvas(self):
        """
        Apply the data to insert text in canvas
        """
        self.apply = True
        # If you have logic to send data back to parent:
        if self.result == "":
            QMessageBox.warning(self, "Copy Failed", "No barcode data.")
            return
        self.close()
        self.parent.create_new_layer()
        self.parent.insert_text_tool(self.result)
        
    def copy_to_clipboard(self):
        """
        Copies the detected barcode data to clipboard
        """
        if self.result == "":
            QMessageBox.warning(self, "Copy Failed", "No barcode data.")
            return
        QApplication.clipboard().setText(self.result)
        QMessageBox.information(self, "Copied", f"Barcode data copied to clipboard:\n{self.result}")
   
   
   
    def closeEvent(self, event: QCloseEvent):
        self.timer.stop()
        if self.cap:
            self.cap.release()
            
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()
        
        
        