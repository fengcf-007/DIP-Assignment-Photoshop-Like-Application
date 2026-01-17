import sys
import cv2
import numpy as np
import time
import datetime
import sqlite3
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QWidget, QGroupBox, QTextEdit,
                            QFileDialog, QAction, QMenuBar, QStatusBar,
                            QMessageBox, QTabWidget, QCheckBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSplitter, QComboBox,
                            QLineEdit, QProgressBar)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QPalette


class QRHistoryDB:
    def __init__(self, db_name='qr_history.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
    
    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                qr_data TEXT,
                data_type TEXT,
                confidence REAL,
                scan_count INTEGER DEFAULT 1
            )
        ''')
        self.conn.commit()
    
    def add_scan(self, qr_data, confidence=1.0):
        data_type = self._detect_data_type(qr_data)
        
        cursor = self.conn.execute('''
            SELECT id, scan_count FROM scan_history 
            WHERE qr_data = ? AND DATE(timestamp) = DATE('now')
            ORDER BY timestamp DESC LIMIT 1
        ''', (qr_data,))
        row = cursor.fetchone()
        
        if row:
            scan_id, count = row
            self.conn.execute('''
                UPDATE scan_history 
                SET timestamp = CURRENT_TIMESTAMP, scan_count = ?, confidence = ?
                WHERE id = ?
            ''', (count + 1, confidence, scan_id))
        else:
            self.conn.execute('''
                INSERT INTO scan_history (qr_data, data_type, confidence)
                VALUES (?, ?, ?)
            ''', (qr_data, data_type, confidence))
        
        self.conn.commit()
    
    def _detect_data_type(self, data):
        if data == "Partial QR Code Detected":
            return 'partial'
        elif data.startswith(('http://', 'https://', 'www.')):
            return 'url'
        elif data.startswith('WIFI:'):
            return 'wifi'
        elif data.startswith('BEGIN:VCARD'):
            return 'contact'
        elif data.startswith('mailto:'):
            return 'email'
        elif data.startswith('tel:'):
            return 'phone'
        elif '@' in data and '.' in data and len(data) < 100:
            return 'email'
        else:
            return 'text'
    
    def get_recent_scans(self, limit=50):
        cursor = self.conn.execute('''
            SELECT timestamp, qr_data, data_type, confidence, scan_count
            FROM scan_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        result = cursor.fetchall()
        return result if result else []
    
    def get_scan_statistics(self):
        cursor = self.conn.execute('''
            SELECT 
                COUNT(*) as total_scans,
                COUNT(DISTINCT qr_data) as unique_codes,
                SUM(CASE WHEN data_type != 'partial' THEN 1 ELSE 0 END) as successful_scans,
                COUNT(CASE WHEN data_type = 'url' THEN 1 END) as url_count,
                COUNT(CASE WHEN data_type = 'wifi' THEN 1 END) as wifi_count,
                COUNT(CASE WHEN data_type = 'contact' THEN 1 END) as contact_count,
                COUNT(CASE WHEN data_type = 'text' THEN 1 END) as text_count
            FROM scan_history
        ''')
        result = cursor.fetchone()
        if result:
            return [0 if x is None else x for x in result]
        return [0, 0, 0, 0, 0, 0, 0]
    
    def clear_history(self):
        self.conn.execute('DELETE FROM scan_history')
        self.conn.commit()
    
    def close(self):
        self.conn.close()

class EnhancedQRDetector:
    def __init__(self):
        self.qr_detector = cv2.QRCodeDetector()
        self.detected_data = None
        self.bbox = None
        self.detection_confidence = 0
        self.last_detection_time = 0
        self.enhance_contrast = True
        self.detect_partial = True
    
    def simple_enhance(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        min_val = np.min(gray)
        max_val = np.max(gray)
        if max_val > min_val:
            gray = ((gray - min_val) * 255 / (max_val - min_val)).astype(np.uint8)
        
        kernel = np.array([[0, -1, 0],
                          [-1, 5, -1],
                          [0, -1, 0]])
        gray = cv2.filter2D(gray, -1, kernel)
        
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    
    def detect_square_patterns(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        squares = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:
                continue
            
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:
                if cv2.isContourConvex(approx):
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = float(w) / h
                    if 0.8 <= aspect_ratio <= 1.2:
                        squares.append(approx)
        
        return squares
    
    def detect_and_decode(self, frame):
        self.detected_data = None
        self.bbox = None
        
        try:
            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            if bbox is not None and data:
                self.detected_data = data
                self.bbox = bbox.astype(int)
                self.detection_confidence = 1.0
                self.last_detection_time = time.time()
                return True
            
            if self.enhance_contrast:
                enhanced = self.simple_enhance(frame)
                data, bbox, _ = self.qr_detector.detectAndDecode(enhanced)
                if bbox is not None and data:
                    self.detected_data = data
                    self.bbox = bbox.astype(int)
                    self.detection_confidence = 0.8
                    self.last_detection_time = time.time()
                    return True
            
            if self.detect_partial:
                squares = self.detect_square_patterns(frame)
                if squares:
                    largest_square = max(squares, key=cv2.contourArea)
                    self.bbox = largest_square.reshape(4, 1, 2).astype(int)
                    self.detected_data = "Partial QR Code Detected"
                    self.detection_confidence = 0.5
                    self.last_detection_time = time.time()
                    return True
                    
        except Exception as e:
            print(f"QR detection error: {e}")
        
        return False
    
    def draw_bounding_box(self, frame):
        if self.bbox is not None:
            n = len(self.bbox)
            for i in range(n):
                cv2.line(frame,
                        tuple(self.bbox[i][0]),
                        tuple(self.bbox[(i+1) % n][0]),
                        (0, 0, 255), 3)
            
            for corner in self.bbox:
                x, y = corner[0]
                cv2.circle(frame, (x, y), 8, (0, 255, 0), -1)
            
            if self.detection_confidence > 0:
                center_x = int(np.mean(self.bbox[:, 0, 0]))
                center_y = int(np.mean(self.bbox[:, 0, 1]))
                confidence_text = f"{self.detection_confidence*100:.0f}%"
                confidence_color = (0, 255, 0) if self.detection_confidence > 0.7 else (0, 165, 255) if self.detection_confidence > 0.4 else (0, 0, 255)
                cv2.putText(frame, confidence_text,
                           (center_x - 20, center_y + 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, confidence_color, 2)
        
        return frame

class RobustCamera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.last_frame = None
        
    def initialize_camera(self):
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            return True
        
        return False
    
    def read_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return self.last_frame
        
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return self.last_frame
            
            self.last_frame = frame
            return frame
            
        except Exception as e:
            print(f"Error reading frame: {e}")
            return self.last_frame
    
    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.last_frame = None

class QRScannerApp(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.qr_detector = EnhancedQRDetector()
        self.camera = RobustCamera()
        self.history_db = QRHistoryDB()
        self.timer = QTimer()
        self.detection_count = 0
        self.frame_count = 0
        self.is_camera_running = False
        self.current_frame = None
        self.last_scan_time = 0
        self.scan_delay = 2.0
        self.fps_history = []
        
        self.setup_ui()
        self.setup_menus()
        self.setup_connections()
        
        self.setWindowTitle("QR Code Scanner")
        self.setGeometry(100, 100, 1200, 700)
        self.apply_dark_theme()
        self.statusBar().showMessage("Ready to scan QR codes")
        self.refresh_history()
    
    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(dark_palette)
        
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #353535;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QTextEdit {
                background-color: #252525;
                border: 1px solid #555;
                color: #FFFFFF;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                padding: 5px;
            }
            QTableWidget {
                background-color: #252525;
                border: 1px solid #555;
                color: #FFFFFF;
                gridline-color: #555;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2A82DA;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #353535;
                color: #FFFFFF;
                padding: 5px;
                border: 1px solid #555;
                font-weight: bold;
            }
            QPushButton {
                padding: 8px;
                font-weight: bold;
                border-radius: 4px;
                min-width: 120px;
                border: 1px solid #555;
            }
            QPushButton:hover {
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #2A82DA;
            }
            QCheckBox {
                color: #FFFFFF;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #454545;
                color: #FFFFFF;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #2A82DA;
            }
            QTabBar::tab:hover {
                background-color: #555;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2A82DA;
                border-radius: 3px;
            }
        """)
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        self.setup_scanner_tab()
        self.setup_history_tab()
        self.setup_statistics_tab()
    
    def setup_scanner_tab(self):
        scanner_tab = QWidget()
        scanner_layout = QHBoxLayout()
        scanner_tab.setLayout(scanner_layout)
        
        left_panel = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setText("Camera Feed\nClick 'Start Camera' to begin")
        self.video_label.setStyleSheet("""
            QLabel {
                border: 3px solid #2A82DA;
                background-color: #000000;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        left_panel.addWidget(self.video_label)
        
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Camera")
        self.stop_btn = QPushButton("Stop Camera")
        self.capture_btn = QPushButton("Capture Frame")
        self.upload_btn = QPushButton("Upload Image")
        self.batch_btn = QPushButton("Batch Scan")
        self.start_btn.setStyleSheet("background-color: #2E7D32; color: white;")
        self.stop_btn.setStyleSheet("background-color: #C62828; color: white;")
        self.capture_btn.setStyleSheet("background-color: #1565C0; color: white;")
        self.upload_btn.setStyleSheet("background-color: #EF6C00; color: white;")
        self.batch_btn.setStyleSheet("background-color: #7B1FA2; color: white;")
        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.batch_btn.setEnabled(True)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.capture_btn)
        control_layout.addWidget(self.upload_btn)
        control_layout.addWidget(self.batch_btn)
        control_layout.addStretch()
        left_panel.addLayout(control_layout)
        
        settings_layout = QHBoxLayout()
        self.contrast_cb = QCheckBox("Enhance Contrast")
        self.partial_cb = QCheckBox("Detect Partial QR Codes")
        self.contrast_cb.setChecked(True)
        self.partial_cb.setChecked(True)
        settings_layout.addWidget(self.contrast_cb)
        settings_layout.addWidget(self.partial_cb)
        settings_layout.addStretch()
        left_panel.addLayout(settings_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_panel.addWidget(self.progress_bar)
        
        right_panel = QVBoxLayout()
        status_group = QGroupBox("Detection Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 5px; color: #2A82DA;")
        self.detection_count_label = QLabel("Detections: 0")
        self.detection_count_label.setStyleSheet("font-size: 12px; padding: 3px;")
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("font-size: 12px; padding: 3px;")
        self.confidence_label = QLabel("Confidence: 0%")
        self.confidence_label.setStyleSheet("font-size: 12px; padding: 3px;")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.detection_count_label)
        status_layout.addWidget(self.fps_label)
        status_layout.addWidget(self.confidence_label)
        status_layout.addStretch()
        status_group.setLayout(status_layout)
        right_panel.addWidget(status_group)
        
        data_group = QGroupBox("QR Code Data")
        data_layout = QVBoxLayout()
        self.data_text = QTextEdit()
        self.data_text.setReadOnly(True)
        self.data_text.setMaximumHeight(200)
        action_layout = QHBoxLayout()
        self.open_url_btn = QPushButton("Open URL")
        self.copy_btn = QPushButton("Copy Data")
        self.clear_btn = QPushButton("Clear")
        self.open_url_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.open_url_btn.setStyleSheet("background-color: #0288D1; color: white;")
        self.copy_btn.setStyleSheet("background-color: #7B1FA2; color: white;")
        self.clear_btn.setStyleSheet("background-color: #757575; color: white;")
        action_layout.addWidget(self.open_url_btn)
        action_layout.addWidget(self.copy_btn)
        action_layout.addWidget(self.clear_btn)
        data_layout.addWidget(self.data_text)
        data_layout.addLayout(action_layout)
        data_group.setLayout(data_layout)
        right_panel.addWidget(data_group)
        
        tips_group = QGroupBox("Tips for Better Detection")
        tips_layout = QVBoxLayout()
        tips_content = """
        • Lighting: Use even, indirect light
        • Position: Hold QR code parallel to camera
        • Distance: Move closer for small codes
        • Steadiness: Hold camera steady
        • Angle: Try different angles if not detected
        • Cleanliness: Ensure QR code is not damaged
        • Background: Use high contrast backgrounds
        
        Features:
        • Real-time camera scanning
        • Image upload functionality
        • Batch processing
        • Scan history tracking
        • Statistics and analytics
        """
        tips_label = QLabel(tips_content)
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet("font-size: 11px; padding: 5px; line-height: 1.4;")
        tips_layout.addWidget(tips_label)
        tips_group.setLayout(tips_layout)
        right_panel.addWidget(tips_group)
        right_panel.addStretch()
        
        scanner_layout.addLayout(left_panel, 2)
        scanner_layout.addLayout(right_panel, 1)
        self.tab_widget.addTab(scanner_tab, "QR Scanner")
    
    def setup_history_tab(self):
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_tab.setLayout(history_layout)
        
        history_controls = QHBoxLayout()
        self.refresh_history_btn = QPushButton("Refresh")
        self.export_history_btn = QPushButton("Export to CSV")
        self.clear_history_btn = QPushButton("Clear History")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Scans", "URLs", "WiFi", "Contacts", "Text", "Partial"])
        self.refresh_history_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.export_history_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.clear_history_btn.setStyleSheet("background-color: #F44336; color: white;")
        history_controls.addWidget(self.refresh_history_btn)
        history_controls.addWidget(self.export_history_btn)
        history_controls.addWidget(self.clear_history_btn)
        history_controls.addWidget(QLabel("Filter:"))
        history_controls.addWidget(self.filter_combo)
        history_controls.addStretch()
        history_layout.addLayout(history_controls)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Timestamp", "QR Data", "Type", "Confidence", "Scan Count"
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        history_layout.addWidget(self.history_table)
        self.tab_widget.addTab(history_tab, "Scan History")
    
    def setup_statistics_tab(self):
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        stats_tab.setLayout(stats_layout)
        
        stats_controls = QHBoxLayout()
        self.refresh_stats_btn = QPushButton("Refresh Stats")
        self.refresh_stats_btn.setStyleSheet("background-color: #2196F3; color: white;")
        stats_controls.addWidget(self.refresh_stats_btn)
        stats_controls.addStretch()
        stats_layout.addLayout(stats_controls)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(300)
        self.recent_activity_text = QTextEdit()
        self.recent_activity_text.setReadOnly(True)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.stats_text)
        splitter.addWidget(self.recent_activity_text)
        splitter.setSizes([200, 400])
        stats_layout.addWidget(splitter)
        self.tab_widget.addTab(stats_tab, "Statistics")
    
    def setup_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        load_action = QAction("Load Image...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.upload_image)
        file_menu.addAction(load_action)
        save_action = QAction("Save Capture...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.capture_frame)
        file_menu.addAction(save_action)
        batch_action = QAction("Batch Scan...", self)
        batch_action.setShortcut("Ctrl+B")
        batch_action.triggered.connect(self.batch_scan)
        file_menu.addAction(batch_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menubar.addMenu("View")
        scanner_action = QAction("QR Scanner", self)
        scanner_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(scanner_action)
        history_action = QAction("Scan History", self)
        history_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(history_action)
        stats_action = QAction("Statistics", self)
        stats_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(stats_action)
        
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_connections(self):
        self.start_btn.clicked.connect(self.start_camera)
        self.stop_btn.clicked.connect(self.stop_camera)
        self.capture_btn.clicked.connect(self.capture_frame)
        self.upload_btn.clicked.connect(self.upload_image)
        self.batch_btn.clicked.connect(self.batch_scan)
        self.open_url_btn.clicked.connect(self.open_qr_url)
        self.copy_btn.clicked.connect(self.copy_qr_data)
        self.clear_btn.clicked.connect(self.clear_qr_data)
        self.contrast_cb.stateChanged.connect(self.update_detector_settings)
        self.partial_cb.stateChanged.connect(self.update_detector_settings)
        self.timer.timeout.connect(self.update_frame)
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        self.refresh_stats_btn.clicked.connect(self.update_statistics)
        self.export_history_btn.clicked.connect(self.export_history)
        self.clear_history_btn.clicked.connect(self.clear_history)
        self.filter_combo.currentTextChanged.connect(self.refresh_history)
    
    def update_detector_settings(self):
        self.qr_detector.enhance_contrast = self.contrast_cb.isChecked()
        self.qr_detector.detect_partial = self.partial_cb.isChecked()
    
    def start_camera(self):
        self.statusBar().showMessage("Initializing camera...")
        if self.camera.initialize_camera():
            self.timer.start(30)
            self.is_camera_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.capture_btn.setEnabled(True)
            self.status_label.setText("Status: Camera Running - Scanning...")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.statusBar().showMessage("Camera started successfully")
        else:
            self.status_label.setText("Status: Camera Error")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.statusBar().showMessage("Could not initialize camera")
            QMessageBox.warning(self, "Camera Error",
                              "Could not access camera.\n\n"
                              "Please:\n"
                              "1. Check if camera is connected\n"
                              "2. Close other apps using camera\n"
                              "3. Use 'Upload Image' button instead")
    
    def stop_camera(self):
        self.timer.stop()
        self.camera.release_camera()
        self.is_camera_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.video_label.setText("Camera Feed\nClick 'Start Camera' to begin")
        self.status_label.setText("Status: Camera Stopped")
        self.status_label.setStyleSheet("color: #2A82DA; font-weight: bold;")
        self.statusBar().showMessage("Camera stopped")
    
    def capture_frame(self):
        if self.current_frame is not None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"qr_scan_{timestamp}.jpg"
            cv2.imwrite(filename, self.current_frame)
            if self.qr_detector.detected_data:
                self.history_db.add_scan(
                    self.qr_detector.detected_data,
                    self.qr_detector.detection_confidence
                )
                self.refresh_history()
            self.statusBar().showMessage(f"Frame saved as {filename}")
    
    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open QR Code Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )
        
        if file_path:
            frame = cv2.imread(file_path)
            if frame is not None:
                self.current_frame = frame
                self.update_detector_settings()
                if self.qr_detector.detect_and_decode(frame):
                    frame = self.qr_detector.draw_bounding_box(frame)
                    self.process_qr_data(self.qr_detector.detected_data)
                    self.detection_count += 1
                    self.detection_count_label.setText(f"Detections: {self.detection_count}")
                    self.confidence_label.setText(f"Confidence: {self.qr_detector.detection_confidence*100:.0f}%")
                    self.status_label.setText("Status: QR Code Detected!")
                    self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    self.statusBar().showMessage("QR code detected in uploaded image")
                    self.open_url_btn.setEnabled(True)
                    self.copy_btn.setEnabled(True)
                    self.history_db.add_scan(
                        self.qr_detector.detected_data,
                        self.qr_detector.detection_confidence
                    )
                    self.refresh_history()
                else:
                    self.data_text.setPlainText("No QR code detected in the image.")
                    self.status_label.setText("Status: No QR Code Found")
                    self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
                    self.statusBar().showMessage("No QR code found in image")
                self.display_frame(frame)
            else:
                QMessageBox.warning(self, "Error", "Could not load image file")
    
    def batch_scan(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select QR Code Images", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_paths:
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(file_paths))
            results = []
            
            for i, file_path in enumerate(file_paths):
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()
                
                frame = cv2.imread(file_path)
                if frame is not None and self.qr_detector.detect_and_decode(frame):
                    results.append({
                        'file': file_path,
                        'data': self.qr_detector.detected_data,
                        'confidence': self.qr_detector.detection_confidence
                    })
                    self.history_db.add_scan(
                        self.qr_detector.detected_data,
                        self.qr_detector.detection_confidence
                    )
            
            self.progress_bar.setVisible(False)
            self.refresh_history()
            
            result_text = f"Batch Scan Results:\n"
            result_text += f"Processed: {len(file_paths)} files\n"
            result_text += f"Successful: {len(results)} QR codes\n\n"
            
            for result in results:
                result_text += f"File: {result['file']}\n"
                result_text += f"Data: {result['data'][:50]}...\n"
                result_text += f"Confidence: {result['confidence']*100:.0f}%\n"
                result_text += "-" * 40 + "\n"
            
            self.data_text.setPlainText(result_text)
            QMessageBox.information(self, "Batch Scan Complete",
                                  f"Processed {len(file_paths)} files\n"
                                  f"Found {len(results)} QR codes")
    
    def update_frame(self):
        frame = self.camera.read_frame()
        if frame is not None:
            self.frame_count += 1
            self.current_frame = frame
            
            current_time = time.time()
            self.fps_history.append(current_time)
            self.fps_history = [t for t in self.fps_history if current_time - t < 1.0]
            fps = len(self.fps_history)
            self.fps_label.setText(f"FPS: {fps}")
            
            self.update_detector_settings()
            if self.qr_detector.detect_and_decode(frame):
                frame = self.qr_detector.draw_bounding_box(frame)
                self.process_qr_data(self.qr_detector.detected_data)
                self.detection_count += 1
                self.detection_count_label.setText(f"Detections: {self.detection_count}")
                self.confidence_label.setText(f"Confidence: {self.qr_detector.detection_confidence*100:.0f}%")
                self.status_label.setText("Status: QR Code Detected!")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                self.statusBar().showMessage(f"QR detected: {self.qr_detector.detected_data[:50]}...")
                if self.qr_detector.detected_data != "Partial QR Code Detected":
                    self.open_url_btn.setEnabled(True)
                    self.copy_btn.setEnabled(True)
                current_time = time.time()
                if current_time - self.qr_detector.last_detection_time > 2:
                    self.history_db.add_scan(
                        self.qr_detector.detected_data,
                        self.qr_detector.detection_confidence
                    )
                    if current_time - self.qr_detector.last_detection_time > 5:
                        self.refresh_history()
            else:
                if self.frame_count % 20 == 0:
                    self.status_label.setText("Status: Scanning...")
                    self.status_label.setStyleSheet("color: #2A82DA; font-weight: bold;")
                    self.statusBar().showMessage("Scanning for QR codes...")
            
            self.display_frame(frame)
    
    def display_frame(self, frame):
        if frame is not None:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.width(), self.video_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.video_label.setPixmap(pixmap)
    
    def process_qr_data(self, data):
        if data == "Partial QR Code Detected":
            display_text = "Partial QR Code Detected\n\n"
            display_text += "A QR code pattern was detected, but could not be fully decoded.\n"
            display_text += "Try:\n"
            display_text += "• Moving closer to the QR code\n"
            display_text += "• Ensuring the entire code is visible\n"
            display_text += "• Improving lighting conditions"
        elif data.startswith(('http://', 'https://', 'www.')):
            display_text = f"URL Detected:\n\n{data}\n\n"
            display_text += "Click 'Open URL' to open in your browser."
        elif data.startswith('WIFI:'):
            display_text = "WiFi QR Code Detected\n\n"
            parts = data[5:].split(';')
            for part in parts:
                if part.startswith('S:'):
                    display_text += f"Network: {part[2:]}\n"
                elif part.startswith('P:'):
                    display_text += f"Password: {'*' * len(part[2:])}\n"
                elif part.startswith('T:'):
                    display_text += f"Security: {part[2:]}\n"
        elif data.startswith('mailto:'):
            display_text = f"Email Address:\n\n{data[7:]}\n\n"
            display_text += "Click to compose email."
        elif data.startswith('tel:'):
            display_text = f"Phone Number:\n\n{data[4:]}\n\n"
            display_text += "Click to call."
        else:
            display_text = f"Text Content:\n\n{data}"
        
        self.data_text.setPlainText(display_text)
    
    def refresh_history(self):
        filter_type = self.filter_combo.currentText()
        filter_map = {
            "All Scans": None,
            "URLs": "url",
            "WiFi": "wifi",
            "Contacts": "contact",
            "Text": "text",
            "Partial": "partial"
        }
        filter_value = filter_map.get(filter_type)
        scans = self.history_db.get_recent_scans(100)
        if filter_value:
            scans = [scan for scan in scans if scan[2] == filter_value]
        
        self.history_table.setRowCount(len(scans))
        for row, scan in enumerate(scans):
            timestamp, qr_data, data_type, confidence, scan_count = scan
            time_str = timestamp[:19].replace('T', ' ')
            self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.history_table.setItem(row, 1, QTableWidgetItem(qr_data[:100] + "..." if len(qr_data) > 100 else qr_data))
            self.history_table.setItem(row, 2, QTableWidgetItem(data_type.upper()))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{confidence*100:.0f}%"))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(scan_count)))
        
        self.update_statistics()
    
    def export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History", "qr_scan_history.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import csv
                scans = self.history_db.get_recent_scans(1000)
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'QR Data', 'Type', 'Confidence', 'Scan Count'])
                    for scan in scans:
                        timestamp, qr_data, data_type, confidence, scan_count = scan
                        writer.writerow([timestamp, qr_data, data_type, f"{confidence*100:.0f}%", scan_count])
                QMessageBox.information(self, "Export Successful", 
                                       f"Successfully exported {len(scans)} records to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export history: {str(e)}")
    
    def clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all scan history?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.history_db.clear_history()
            self.refresh_history()
            QMessageBox.information(self, "Success", "Scan history has been cleared.")
    
    def update_statistics(self):
        stats = self.history_db.get_scan_statistics()
        
        stats_text = "SCAN STATISTICS\n"
        stats_text += "=" * 40 + "\n\n"
        stats_text += f"Total Scans: {stats[0]}\n"
        stats_text += f"Unique QR Codes: {stats[1]}\n"
        stats_text += f"Successful Decodes: {stats[2]}\n\n"
        stats_text += "Scan Types:\n"
        stats_text += f"  URLs: {stats[3]}\n"
        stats_text += f"  WiFi: {stats[4]}\n"
        stats_text += f"  Contacts: {stats[5]}\n"
        stats_text += f"  Text: {stats[6]}\n"
        partial_scans = int(stats[0]) - int(stats[2])
        stats_text += f"  Partial: {partial_scans}\n\n"
        if int(stats[0]) > 0:
            success_rate = (int(stats[2]) / int(stats[0])) * 100
            stats_text += f"Success Rate: {success_rate:.1f}%\n"
        
        recent_scans = self.history_db.get_recent_scans(20)
        activity_text = "RECENT SCANS\n"
        activity_text += "=" * 40 + "\n\n"
        if recent_scans:
            for scan in recent_scans:
                timestamp, qr_data, data_type, confidence, scan_count = scan
                time_str = timestamp[11:19]
                activity_text += f"{time_str}: {data_type.upper()} - {qr_data[:30]}...\n"
        else:
            activity_text += "No scan activity recorded yet.\n"
        
        self.stats_text.setPlainText(stats_text)
        self.recent_activity_text.setPlainText(activity_text)
    
    def open_qr_url(self):
        if self.qr_detector.detected_data and self.qr_detector.detected_data.startswith(('http://', 'https://', 'www.')):
            url = self.qr_detector.detected_data
            if not url.startswith('http'):
                url = 'https://' + url
            webbrowser.open(url)
            self.statusBar().showMessage(f"Opening URL: {url}")
    
    def copy_qr_data(self):
        if self.qr_detector.detected_data:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.qr_detector.detected_data)
            self.statusBar().showMessage("QR data copied to clipboard")
    
    def clear_qr_data(self):
        self.data_text.clear()
        self.open_url_btn.setEnabled(False)
        self.copy_btn.setEnabled(False)
        self.statusBar().showMessage("QR data cleared")
    
    def show_about(self):
        about_text = """
        <h2>QR Code Scanner</h2>
        <p><b>Version:</b> 1.0</p>
        <p><b>Developed for:</b> Digital Image Processing Mini Project</p>
        
        <h3>Features:</h3>
        <ul>
        <li>Real-time camera QR code scanning</li>
        <li>Image upload and batch processing</li>
        <li>Contrast enhancement for better detection</li>
        <li>Partial QR code detection</li>
        <li>Scan history with database storage</li>
        <li>Statistics and analytics</li>
        <li>Export functionality to CSV</li>
        <li>Dark theme interface</li>
        </ul>
        
        <p><b>Core Technologies:</b> OpenCV, PyQt5, NumPy, SQLite</p>
        """
        QMessageBox.about(self, "About QR Code Scanner", about_text)
    
    def closeEvent(self, event):
        self.stop_camera()
        self.history_db.close()
        
        self.parent.set_dialog_open(False)
        self.parent.update_button_menu()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = QRScannerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()