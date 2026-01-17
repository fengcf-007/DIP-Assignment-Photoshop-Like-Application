import sys
import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QSlider, QFileDialog, QAction, QHBoxLayout,
    QDialog, QComboBox, QLineEdit, QFormLayout, QDialogButtonBox, 
    QInputDialog, QCheckBox, QRadioButton, QGridLayout, QColorDialog, 
    QListWidget, QMessageBox, QSizePolicy, QSpinBox, QGroupBox, 
    QFrame, QSplitter, QButtonGroup, 
)
from PyQt5.QtGui import (
    QImage, QPixmap, QDoubleValidator, QPainter, QPen, QColor, QIcon,
    QIntValidator, QPolygonF, QCloseEvent, QFont, 
)
from PyQt5.QtCore import (
    Qt, QRect, QPoint, QPointF, QMimeData
)
import keyboard
import copy
from functools import partial

import dip_barcode as barcode
import QRCODE as qrcode
import dip_assignment2 as a2


class myImage:
    def __init__(self) -> None:
        self.image = None
        self.gray_image = None
        self.imageLocation = None
        self.colorID = None
        self.height = None
        self.width = None
        self.blankCanvas = np.zeros((512,512,3), np.uint8)
        
    def loadImage(self, imageLocation, colorID):
        self.imageLocation = imageLocation
        self.colorID = colorID
        self.image = cv2.imread(self.imageLocation, self.colorID)
        if self.image is not None:
            self.gray_image = cv2.imread(self.imageLocation, 0)
            self.height = self.image.shape[0]
            self.width = self.image.shape[1]
            return True
        return False

    def showImage(self, imageDescription):
        self.imageDescription = imageDescription
        if self.image is not None:
            plt.imshow(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)) 
            plt.title(self.imageDescription)
            plt.show()

    def imageDetail(self):
        if self.image is not None:
            print("image dimension = {}".format(self.image.shape))
            print("image width = {}".format(self.image.shape[1]))
            print("image height = {}".format(self.image.shape[0]))
            if len(self.image.shape) > 2:
                print("image no. of channels = {}".format(self.image.shape[2]))
            else:
                print("image is grayscale")


### Path of assets folder loaded 
current_path = os.path.dirname(os.path.abspath(__file__))
assets_path = current_path + "\\Assets\\"







### Main Window
class myWindowsOpencV(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Assignment Paint Application: BS23110051")
        self.setGeometry(200, 200, 1200, 700)

        # Initialize myImage class
        self.my_image = myImage()

        self.data_initiate()
        # Initialize image storage
        self.image_list = []
        self.original_image_list = []
        self.main_index = -1
        self.current_index = -1
        
        self.original_image = None
        self.display_image = None
        self.display_scale_x = 1.0
        self.display_scale_y = 1.0
        self.display_offset = (0.0, 0.0)
        
        self.recent_file_limit = 6
        self.recently_used_list = []
        self.recently_saved_list = []
        
        self.recently_saved_path = None
        self.new_canvas_counter = 0
        
        self.zoom_factor = 1.0
        self.move_diff_pos = None
        self.canva_offset = (0, 0)
        self.release_cancel_move_mode = False

        self.undo_stack = []
        self.redo_stack = []
        
        self.selected_rect = (0, 0, 0, 0)
        
        self.view_windows = []
        self.free_transform_tool = None
        
        self.histogram_display = None
        self.dialog_open = False
        
# --------------------------------------------------------------------------------
        
        
### Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # The main horizontal layout that holds the 3 frames
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        
        ## Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(8) # Width of the drag area
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
            }
            QSplitter::handle:hover {
                background-color: #d0d0d0;
            }
            QSplitter::handle:pressed {
                background-color: #b0b0b0;
                background-color: blue;
            }
        """)
        
        

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
### Left Sidebar
        def left_side_bar(self):
            self.left_frame = QFrame()
            self.left_frame.setMinimumWidth(260)
            self.left_frame.setFrameShape(QFrame.StyledPanel)
            
            # Layout inside the frame
            self.sidebar_layout = QVBoxLayout(self.left_frame)
            self.sidebar_layout.setAlignment(Qt.AlignTop)
            
            
            
    # -------------------------------------------------
        ## Color Palette
            self.sidebar_layout.addWidget(QLabel("<b>Color Palette</b>"))
            self.color_palette = ColorPalette(self, color_callback=self.set_active_color)
            self.sidebar_layout.addWidget(self.color_palette)

        # Active color preview
            sub_layout_color = QHBoxLayout()
            sub_layout_color.addWidget(QLabel("Active:"))
            self.active_color_display = QLabel()
            self.active_color_display.setFixedSize(50, 25)
            self.active_color_display.setStyleSheet("background-color: black;")
            sub_layout_color.addWidget(self.active_color_display)
            sub_layout_color.addStretch()
            self.sidebar_layout.addLayout(sub_layout_color)
            
            self.sidebar_layout.addSpacing(10)

    # -------------------------------------------------
        ## Paint tool
            self.sidebar_layout.addWidget(QLabel("<b>Paint Tools</b>"))
            
            paint_tool_area = QHBoxLayout()
            paint_tool_second_area = QHBoxLayout()
            shape_tool_area = QHBoxLayout()
            
            
            self.sidebar_layout.addLayout(paint_tool_area)
            self.sidebar_layout.addLayout(paint_tool_second_area)
            self.sidebar_layout.addLayout(shape_tool_area)
            
   
    # -------------------------------------------------
        ## Thickness
            self.thickness_layout = QFormLayout()
            
            self.pen_preview = a2.PenPreviewWidget()
            self.pen_preview_layout = QVBoxLayout()
            self.pen_preview_layout.addWidget(self.pen_preview)
            self.pen_preview_layout.setAlignment(Qt.AlignCenter)
            
            self.thickness = QLabel("30.0")
            self.thickness_slider = QSlider(Qt.Horizontal)
            self.thickness_slider.setRange(10, 10000)
            self.thickness_slider.setValue(3000)
            self.thickness_slider.valueChanged.connect(lambda val: self.thickness_change(val))
            self.thickness_slider.setStyleSheet("""
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
            
            self.thickness_layout.addRow("Thickness:", self.thickness)
            self.thickness_layout.addRow(self.thickness_slider)
            self.sidebar_layout.addLayout(self.pen_preview_layout)
            self.sidebar_layout.addLayout(self.thickness_layout)
            
            self.pen_preview.update_preview(self.pen_thickness, self.pen_color)

            self.sidebar_layout.addStretch() # Push Undo/Exit to bottom


    # -------------------------------------------------
        ## Histogram
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            self.sidebar_layout.addWidget(line)

            self.histogram_panel = a2.HistogramPanel(self)
            self.sidebar_layout.addWidget(self.histogram_panel)
            
        
        left_side_bar(self)
        

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
### Central Area
        self.center_frame = QFrame()
        self.center_frame.setFrameShape(QFrame.StyledPanel)
        
        self.center_layout = QVBoxLayout(self.center_frame)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Image Display
        self.image_label = SelectLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(700, 420)
        self.image_label.setStyleSheet("background-color: #808080; border: 2px solid #555;")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.center_layout.addWidget(self.image_label, stretch=1)


        # Canvas Buttons Area 
        self.buttons_container = QWidget()
        self.buttons_container.setMaximumHeight(100)
        self.canvas_button_layout = QGridLayout(self.buttons_container) 
        self.canvas_button_layout.setSpacing(2)
        self.canvas_button_layout.setContentsMargins(2, 2, 2, 2)
        # self.canvas_button_layout.setAlignment(Qt.AlignLeft)
        
        self.center_layout.addWidget(self.buttons_container)
        

        
        
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
### Right SideBar Area
        def right_side_bar(self):
            self.right_frame = QFrame()
            self.right_frame.setMinimumWidth(220)
            self.right_frame.setFrameShape(QFrame.Shape.StyledPanel)
            
            self.right_frame_layout = QVBoxLayout(self.right_frame)
            self.right_frame_layout.setContentsMargins(0, 0, 0, 0)
            self.right_frame_layout.setSpacing(0)

            # Vertical Splitter
            self.right_splitter = QSplitter(Qt.Orientation.Vertical)
            self.right_splitter.setHandleWidth(8)
            self.right_splitter.setStyleSheet("""
                QSplitter::handle {
                    background-color: #e0e0e0;
                    border: 1px solid #ccc;
                }
                QSplitter::handle:hover {
                    background-color: #d0d0d0;
                }
                QSplitter::handle:pressed {
                    background-color: #b0b0b0;
                    background-color: blue;
                }
            """)


        # -------------------------------------------------
        ## Thumbnail Layout
            self.right_top_widget = QWidget()
            self.right_top_layout = QVBoxLayout(self.right_top_widget)
            self.right_top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.right_top_layout.setContentsMargins(10, 10, 10, 10)
        
        ## Thumbnail image
            self.right_top_layout.addWidget(QLabel("<b>Thumbnail</b>"))
            self.thumbnail_label = a2.ResizableLabel()
            self.thumbnail_label.setMinimumSize(100, 100)
            self.thumbnail_label.setAlignment(Qt.AlignCenter)
            self.thumbnail_label.setStyleSheet("background-color: #808080; border: 3px solid white;")
            self.right_top_layout.addWidget(self.thumbnail_label, alignment=Qt.AlignCenter)
            
            self.right_top_layout.addSpacing(10)

            
        # Zoom
            self.zoom_label = QLabel("Zoom: 100%")
            self.zoom_slider = QSlider(Qt.Horizontal)
            self.zoom_slider.setRange(1, 2000)
            self.zoom_slider.setValue(100)
            self.zoom_slider.setMaximumHeight(15)
            self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)
            self.zoom_slider.setStyleSheet("""
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
            
            self.right_top_layout.addWidget(self.zoom_label)
            self.right_top_layout.addWidget(self.zoom_slider)
            
            
        # -------------------------------------------------
        ## Layer Layout
            self.right_bottom_widget = QWidget()
            self.right_bottom_layout = QVBoxLayout(self.right_bottom_widget)
            self.right_bottom_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.right_bottom_layout.setContentsMargins(20, 10, 20, 10)
            
            self.layer_panel = a2.LayersPanel(self)
            self.right_bottom_layout.addWidget(self.layer_panel)
        
            
            
            
            self.right_splitter.addWidget(self.right_top_widget)
            self.right_splitter.addWidget(self.right_bottom_widget)
            
            self.right_splitter.setStretchFactor(0, 0)
            self.right_splitter.setStretchFactor(1, 1)

            self.right_frame_layout.addWidget(self.right_splitter)
        right_side_bar(self)

###
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
    ## Combine sidebar + image area
        self.splitter.addWidget(self.left_frame)
        self.splitter.addWidget(self.center_frame)
        self.splitter.addWidget(self.right_frame)
        
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        
        # Add the splitter to the main window layout
        self.main_layout.addWidget(self.splitter)
        

# --------------------------------------------------------------------------------
        # Setup menu bar
        self.setup_menu()
        self.setup_top_toolbar()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
    
# --------------------------------------------------------------------------------
    
    def setup_menu(self):
        """Setup the menu bar """
        menubar = self.menuBar()
        
# --------------------------------------------------------------------------------
    ### File menu
        file_menu = menubar.addMenu("&File(F) ")
        def file_menu_initiate(self):
            # Create New Canvas
            self.new_action = QAction("New(&N) ...", self)
            self.new_action.setShortcut("Ctrl+N")
            self.new_action.triggered.connect(self.create_new_canvas)
            file_menu.addAction(self.new_action)
            
            # Load Image action
            self.load_action = QAction("Open(&O) ...", self)
            self.load_action.setShortcut("Ctrl+O")
            self.load_action.triggered.connect(self.load_image_dialog)
            file_menu.addAction(self.load_action)
            
            # Load Image from Clipboard
            self.load_clipboard_action = QAction("Create canvas from Clipboard(&B) ", self)
            self.load_clipboard_action.setShortcut("ctrl+b")
            self.load_clipboard_action.setEnabled(False)
            self.load_clipboard_action.triggered.connect(self.load_clipboard_image)
            file_menu.addAction(self.load_clipboard_action)

            # Recenlty Used document
            self.recently_used_menu = file_menu.addMenu("Recently Used Document(&T) ")
            # Recenlty Saved document
            self.recently_saved_menu = file_menu.addMenu("Recently saved Document(&R)  ")
            
            file_menu.addSeparator()
            
            # Save Image action
            self.save_action = QAction("Save(&S) ", self)
            self.save_action.setShortcut("Ctrl+S")
            self.save_action.triggered.connect(self.save_image)
            file_menu.addAction(self.save_action)
            
            self.save_as_action = QAction("Save As(&A) ...", self)
            self.save_as_action.setShortcut("Ctrl+Shift+S")
            self.save_as_action.triggered.connect(self.save_image_as)
            file_menu.addAction(self.save_as_action)
            
            file_menu.addSeparator()
            
            self.close_action = QAction("Close(&C) ", self)
            self.close_action.setShortcut("Ctrl+W")
            self.close_action.triggered.connect(self.close_current_image)
            file_menu.addAction(self.close_action)
            
            # Exit action
            exit_action = QAction("Exit(&X) ", self)
            exit_action.triggered.connect(self.close_application)
            file_menu.addAction(exit_action)
        file_menu_initiate(self)
    
# --------------------------------------------------------------------------------
    ### Edit menu
        edit_menu = menubar.addMenu("&Edit(E) ")
        def edit_menu_initiate(self):
        
            self.undo_action = QAction("Undo(&U) ", self)
            self.undo_action.triggered.connect(self.undo)
            self.undo_action.setShortcut("ctrl+z")
            edit_menu.addAction(self.undo_action)
            
            self.redo_action = QAction("Redo(&R) ", self)
            self.redo_action.triggered.connect(self.redo)
            self.redo_action.setShortcut("ctrl+y")
            edit_menu.addAction(self.redo_action)
            
            edit_menu.addSeparator()
            
            self.copy_action = QAction("Copy(&C) ", self)
            self.copy_action.triggered.connect(self.copy)
            self.copy_action.setEnabled(False)
            self.copy_action.setShortcut("ctrl+c")
            edit_menu.addAction(self.copy_action)
            
            self.cut_action = QAction("Cut(&T) ", self)
            self.cut_action.triggered.connect(self.cut)
            self.cut_action.setEnabled(False)
            self.cut_action.setShortcut("ctrl+x")
            edit_menu.addAction(self.cut_action)
            
            self.paste_action = QAction("Paste(&P) ", self)
            self.paste_action.triggered.connect(self.paste)
            self.paste_action.setEnabled(False)
            self.paste_action.setShortcut("ctrl+v")
            edit_menu.addAction(self.paste_action)
            
            edit_menu.addSeparator()
            
            self.free_transform_action = QAction("Free Transform tool(&T) ", self)
            self.free_transform_action.setShortcut("ctrl+t")
            self.free_transform_action.triggered.connect(self.free_transform)
            edit_menu.addAction(self.free_transform_action)
        edit_menu_initiate(self)
    
# --------------------------------------------------------------------------------
    ### Image menu
        image_menu = menubar.addMenu("&Image(I) ")
        def image_menu_initiate(self):
        # --------------------------------------------------------------------------------
        ## Adjustment menu
            adjust_submenu = image_menu.addMenu("Adjustment ")
            
            self.color_convert_action =QAction("Color Format Change(&F) ...", self)
            self.color_convert_action.triggered.connect(self.color_convert)
            adjust_submenu.addAction(self.color_convert_action)
            
            adjust_submenu.addSeparator()
            
            self.color_adjust_action = QAction("Hue/Saturation(&H) ...", self)
            self.color_adjust_action.setShortcut("Ctrl+U")
            self.color_adjust_action.triggered.connect(self.color_adjust)
            adjust_submenu.addAction(self.color_adjust_action)
            
            self.color_intensity_adjust_action = QAction("Contrast/Intensity(&I) ...", self)
            self.color_intensity_adjust_action.triggered.connect(self.color_intensity_adjust)
            adjust_submenu.addAction(self.color_intensity_adjust_action)

            adjust_submenu.addSeparator()
            
            self.color_negative_action = QAction("Color Negative(&N) ", self)
            self.color_negative_action.triggered.connect(self.color_negative)
            adjust_submenu.addAction(self.color_negative_action)
            
            self.color_inverse_action = QAction("Color Inverse(&I) ", self)
            self.color_inverse_action.triggered.connect(self.color_inverse)
            adjust_submenu.addAction(self.color_inverse_action)


            
        # --------------------------------------------------------------------------------
            image_menu.addSeparator()
            
            self.image_size_action = QAction("Img &Size(S) ...", self)
            self.image_size_action.triggered.connect(self.image_size)
            image_menu.addAction(self.image_size_action)
            
            self.image_expand_action = QAction("Img &Expand(E) ...", self)
            self.image_expand_action.triggered.connect(self.image_expand)
            image_menu.addAction(self.image_expand_action)

            self.image_position_action = QAction("Img Translate(&L) ...", self)
            self.image_position_action.triggered.connect(self.image_position)
            image_menu.addAction(self.image_position_action)
            
            self.image_rotate_action = QAction("Img &Rotate(R) ...", self)
            self.image_rotate_action.triggered.connect(self.image_rotation)
            image_menu.addAction(self.image_rotate_action)
            
            image_menu.addSeparator()
            
            self.cropping_action = QAction("Crop(&X) ", self)
            self.cropping_action.triggered.connect(self.crop_selected_area)
            image_menu.addAction(self.cropping_action)
            
            self.crop_image_action = QAction("Crop Image(&C) ...", self)
            self.crop_image_action.triggered.connect(self.crop_image)
            image_menu.addAction(self.crop_image_action)
            
            image_menu.addSeparator()
        
        # -------------------------------------------------------------
        ## Rotate Submenu
            rotate_submenu = image_menu.addMenu("Rotate ")
            
            self.flip_h_action = QAction("Flip &Horizontally(H)", self)
            self.flip_h_action.triggered.connect(lambda: self.flip_image("h"))
            rotate_submenu.addAction(self.flip_h_action)
            
            self.flip_v_action = QAction("Flip &Vertically(V)", self)
            self.flip_v_action.triggered.connect(lambda: self.flip_image("v"))
            rotate_submenu.addAction(self.flip_v_action)
            
            rotate_submenu.addSeparator()
            
            self.rotate_180_action = QAction("Rotate 180°(&1) ", self)
            self.rotate_180_action.triggered.connect(lambda: self.rotate_image_90_degree(180))
            rotate_submenu.addAction(self.rotate_180_action)

            self.rotate_ccw_action = QAction("Rotate 90° Counter-Clockwise(&9)", self)
            self.rotate_ccw_action.triggered.connect(lambda: self.rotate_image_90_degree(-1))
            rotate_submenu.addAction(self.rotate_ccw_action)
            
            self.rotate_cw_action = QAction("Rotate 90° Clockwise(&G)", self)
            self.rotate_cw_action.triggered.connect(lambda: self.rotate_image_90_degree(1))
            rotate_submenu.addAction(self.rotate_cw_action)
        
        # -------------------------------------------------------------
            image_menu.addSeparator()
            
            self.image_detail_action = QAction("Image Details(&D) ... ", self)
            self.image_detail_action.setShortcut("alt+i")
            self.image_detail_action.triggered.connect(self.show_image_details)
            image_menu.addAction(self.image_detail_action)
        image_menu_initiate(self)
        
# --------------------------------------------------------------------------------
    ### Layer menu
        layer_menu = menubar.addMenu("&Layer(L)")
        def layer_menu_initiate(self):
            
            self.new_layer_action = QAction("New Layer(&N) ", self)
            self.new_layer_action.setShortcut("alt+a")
            self.new_layer_action.triggered.connect(self.create_new_layer)
            layer_menu.addAction(self.new_layer_action)
            
            self.copy_layer_action = QAction("Copy Layer(&C) ", self)
            self.copy_layer_action.triggered.connect(self.copy_layer)
            layer_menu.addAction(self.copy_layer_action)
            
            layer_menu.addSeparator()
            
            self.delete_layer_action = QAction("Delete Layer(&D) ", self)
            self.delete_layer_action.setShortcut("alt+d")
            self.delete_layer_action.triggered.connect(self.delete_layer)
            layer_menu.addAction(self.delete_layer_action)
            
            self.clear_layer_action = QAction("Clear Layer ", self)
            self.clear_layer_action.setShortcut("delete")
            self.clear_layer_action.triggered.connect(self.clear_layer)
            layer_menu.addAction(self.clear_layer_action)
            
            layer_menu.addSeparator()
            
            self.write_down_action = QAction("Write Down ", self)
            self.write_down_action.setShortcut("f")
            self.write_down_action.triggered.connect(self.write_down)
            layer_menu.addAction(self.write_down_action)
            
            self.merge_down_action = QAction("Merge Down ", self)
            self.merge_down_action.setShortcut("ctrl+e")
            self.merge_down_action.triggered.connect(self.merge_layer)
            layer_menu.addAction(self.merge_down_action)
            
            self.merge_all_action = QAction("Merge All Layer ", self)
            self.merge_all_action.triggered.connect(self.merge_all_layer)
            layer_menu.addAction(self.merge_all_action)
            
            self.merge_all_visible_action = QAction("Merge All Visible Layer ", self)
            self.merge_all_visible_action.triggered.connect(self.merge_all_visible_layer)
            layer_menu.addAction(self.merge_all_visible_action)
            
            
            layer_menu.addSeparator()
        ## Rotate Submenu
            rotate_submenu = layer_menu.addMenu("Rotate ")
            
            self.layer_flip_h_action = QAction("Flip &Horizontally(H)", self)
            self.layer_flip_h_action.triggered.connect(lambda: self.flip_image("h"))
            rotate_submenu.addAction(self.layer_flip_h_action)
            
            self.layer_flip_v_action = QAction("Flip &Vertically(V)", self)
            self.layer_flip_v_action.triggered.connect(lambda: self.flip_image("v"))
            rotate_submenu.addAction(self.layer_flip_v_action)
            
            rotate_submenu.addSeparator()
            
            self.layer_rotate_180_action = QAction("Rotate 180°(&1) ", self)
            self.layer_rotate_180_action.triggered.connect(lambda: self.layer_rotate(180))
            rotate_submenu.addAction(self.layer_rotate_180_action)

            self.layer_rotate_ccw_action = QAction("Rotate 90° Counter-Clockwise(&9)", self)
            self.layer_rotate_ccw_action.triggered.connect(lambda: self.layer_rotate(-1))
            rotate_submenu.addAction(self.layer_rotate_ccw_action)
            
            self.layer_rotate_cw_action = QAction("Rotate 90° Clockwise(&G)", self)
            self.layer_rotate_cw_action.triggered.connect(lambda: self.layer_rotate(1))
            rotate_submenu.addAction(self.layer_rotate_cw_action)
            
            layer_menu.addSeparator()
            
            self.layer_to_front_action = QAction("Move Layer to Up ", self)
            self.layer_to_front_action.triggered.connect(lambda: self.layer_move(1))
            layer_menu.addAction(self.layer_to_front_action)
            
            self.layer_to_down_action = QAction("Move Layer to Down ", self)
            self.layer_to_down_action.triggered.connect(lambda: self.layer_move(-1))
            layer_menu.addAction(self.layer_to_down_action)
            
            self.layer_to_top_action = QAction("Move Layer to Top ", self)
            self.layer_to_top_action.triggered.connect(lambda: self.layer_move_top(1))
            layer_menu.addAction(self.layer_to_top_action)
            
            self.layer_to_bottom_action = QAction("Move Layer to Bottom ", self)
            self.layer_to_bottom_action.triggered.connect(lambda: self.layer_move_top(-1))
            layer_menu.addAction(self.layer_to_bottom_action)
            
            layer_menu.addSeparator()
            
            self.layer_rename_action = QAction("Rename Laeyer(F2) ", self)
            self.layer_rename_action.triggered.connect(self.rename_layer)
            self.layer_rename_action.setShortcut("f2")
            layer_menu.addAction(self.layer_rename_action)
            
            
        layer_menu_initiate(self)
        
        
# --------------------------------------------------------------------------------
    ### Select Menu
        select_menu = menubar.addMenu("&Select(S) ")
        def select_menu_initiate(self):
        
            self.select_action = QAction("Select(&S)", self)
            self.select_action.setShortcut("s")
            self.select_action.setCheckable(True)
            self.select_action.triggered.connect(self.enable_selection_mode)
            select_menu.addAction(self.select_action)
            
            self.select_cancel_action = QAction("Select Cancel(&D) ", self)
            self.select_cancel_action.setShortcut("Ctrl+D")
            self.select_cancel_action.triggered.connect(self.disabled_selection_mode)
            select_menu.addAction(self.select_cancel_action)
            
            self.select_all_action = QAction("Select All(&A)", self)
            self.select_all_action.setShortcut("Ctrl+A")
            self.select_all_action.triggered.connect(self.select_all)
            select_menu.addAction(self.select_all_action)
        select_menu_initiate(self)

    
# --------------------------------------------------------------------------------
    ### View Menu
        view_menu = menubar.addMenu("&View(V) ")
        def view_menu_initiate(self):
        
            self.view_window_action = QAction("Create View Window(&V) ", self)
            self.view_window_action.setShortcut("alt+n")
            self.view_window_action.triggered.connect(self.open_new_view_window)
            view_menu.addAction(self.view_window_action)

            view_menu.addSeparator()
        ## Canvas Operations
            self.view_zoom_in_action = QAction("View Zoom in(10%) ", self)
            self.view_zoom_in_action.setShortcut("ctrl+[")
            self.view_zoom_in_action.triggered.connect(lambda: self.set_zoom_factor((self.zoom_factor+0.1) * 100.0, change=True))
            view_menu.addAction(self.view_zoom_in_action)
            
            self.view_zoom_out_action = QAction("View Zoom out(10%) ", self)
            self.view_zoom_out_action.setShortcut("ctrl+]")
            self.view_zoom_out_action.triggered.connect(lambda: self.set_zoom_factor((self.zoom_factor-0.1) * 100.0, change=True))
            view_menu.addAction(self.view_zoom_out_action)
        
            self.view_zoom_reset_action = QAction("View Zoom Reset(&R) ", self)
            self.view_zoom_reset_action.triggered.connect(lambda: self.update_image_display(reset_scale=True))
            view_menu.addAction(self.view_zoom_reset_action)
            
            
            self.view_position_reset_action = QAction("View Position Reset(&P) ", self)
            self.view_position_reset_action.triggered.connect(lambda: self.update_image_display(reset_position=True))
            view_menu.addAction(self.view_position_reset_action)

            view_menu.addSeparator()

            self.next_canvas_action = QAction("Next View Canvas ", self)
            self.next_canvas_action.triggered.connect(lambda: self.next_canvas(1))
            self.next_canvas_action.setShortcut("ctrl+tab")
            view_menu.addAction(self.next_canvas_action)
            self.previous_canvas_action = QAction("Previous View Canvas ", self)
            self.previous_canvas_action.setShortcut("ctrl+shift+tab")
            self.previous_canvas_action.triggered.connect(lambda: self.next_canvas(-1))
            view_menu.addAction(self.previous_canvas_action)
            
            view_menu.addSeparator()
        ## Ruler and Grid
            ruler_menu = view_menu.addMenu("Ruler and Grid")
            self.ruler_action = QAction("Ruler ", self)
            self.ruler_action.setCheckable(True)
            self.ruler_action.setChecked(True)
            self.ruler_action.triggered.connect(self.toggle_ruler)
            ruler_menu.addAction(self.ruler_action)
            
            self.grid_action = QAction("Grid ", self)
            self.grid_action.setCheckable(True)
            self.grid_action.triggered.connect(self.toggle_grid)
            ruler_menu.addAction(self.grid_action)
            
            self.ruler_settings_action = QAction("Ruler & Grid Settings ...", self)
            self.ruler_settings_action.triggered.connect(self.grid_ruler_settings)
            ruler_menu.addAction(self.ruler_settings_action)
        
        ## Display Histogram
            histogram_submenu = view_menu.addMenu("Histogram ")
            self.histogram_action = QAction("Open Histogram Window", self)
            self.histogram_action.triggered.connect(self.show_histogram)
            histogram_submenu.addAction(self.histogram_action)
            
            self.histogram_panel_action = QAction("Histogram Panel", self)
            self.histogram_panel_action.setCheckable(True)
            self.histogram_panel_action.setChecked(True)
            self.histogram_panel_action.triggered.connect(
                lambda: self.histogram_panel.setVisible(self.histogram_panel_action.isChecked())
            )
            histogram_submenu.addAction(self.histogram_panel_action)
            
        view_menu_initiate(self)

    # -----------------------------------------------
    ### Filter Menu
        filter_menu = menubar.addMenu("Filter(&I) ")
        def filter_menu_initiate(self):
            
        ## Edge detecte
            self.edge_detection_action = QAction("Edge Detection ...", self)
            self.edge_detection_action.triggered.connect(self.edge_detection)
            filter_menu.addAction(self.edge_detection_action)
            
        ## Thresholding 
            self.thresholding_action = QAction("Thresholding ...", self)
            self.thresholding_action.triggered.connect(self.thresholding)
            filter_menu.addAction(self.thresholding_action)
            
            self.power_law_action = QAction("Power Law Trans ...", self)
            self.power_law_action.triggered.connect(self.power_law_transformation)
            filter_menu.addAction(self.power_law_action)
            
            self.piecewise_action = QAction("Piecewise Linear Trans ...", self)
            self.piecewise_action.triggered.connect(self.piecewise_transformation)
            filter_menu.addAction(self.piecewise_action)
            
            self.morphology_action = QAction("Morphological filter ...", self)
            self.morphology_action.triggered.connect(self.morphology_filter)
            filter_menu.addAction(self.morphology_action)
            
            self.histogram_action = QAction("Histogram EQ ...", self)
            self.histogram_action.triggered.connect(self.histogram_equalization)
            filter_menu.addAction(self.histogram_action)
            
            
            
            filter_menu.addSeparator()
        ## Bit Plane Slicing
            self.bit_plane_action = QAction("Bit Plane Slicing ...", self)
            self.bit_plane_action.triggered.connect(self.bit_plane_panel)
            filter_menu.addAction(self.bit_plane_action)
            
            
            filter_menu.addSeparator()
        ## Blur Filters
            blur_submenu = filter_menu.addMenu("Blur ")
            self.blur_filter_action = QAction("Blur ...", self)
            self.blur_filter_action.triggered.connect(lambda: self.image_enhance_filter("Blur"))
            blur_submenu.addAction(self.blur_filter_action)
            
            self.blur_more_filter_action = QAction("Blur More ...", self)
            self.blur_more_filter_action.triggered.connect(lambda: self.image_enhance_filter("Blur More"))
            blur_submenu.addAction(self.blur_more_filter_action)
            
            self.blur_gaussian_filter_action = QAction("Gaussian Blur ...", self)
            self.blur_gaussian_filter_action.triggered.connect(lambda: self.image_enhance_filter("Gaussian Blur"))
            blur_submenu.addAction(self.blur_gaussian_filter_action)
            
            self.blur_motion_filter_action = QAction("Motion Blur ...", self)
            self.blur_motion_filter_action.triggered.connect(lambda: self.image_enhance_filter("Motion Blur", 140))
            blur_submenu.addAction(self.blur_motion_filter_action)
            
            self.blur_radial_filter_action = QAction("Radial Blur ...", self)
            self.blur_radial_filter_action.triggered.connect(lambda: self.image_enhance_filter("Radial Blur", 160))
            blur_submenu.addAction(self.blur_radial_filter_action)
            
            
        ## Sharpen Filters
            sharpen_submenu = filter_menu.addMenu("Sharpen ")
            self.sharpen_filter_action = QAction("Sharpen ...", self)
            self.sharpen_filter_action.triggered.connect(lambda: self.image_enhance_filter("Sharpen"))
            sharpen_submenu.addAction(self.sharpen_filter_action)
            
            self.sharpen_edge_filter_action = QAction("Sharpen Edge ", self)
            self.sharpen_edge_filter_action.triggered.connect(lambda: self.image_onetime_enhance_filter("Sharpen Edge"))
            sharpen_submenu.addAction(self.sharpen_edge_filter_action)
            
            self.sharpen_usm_filter_action = QAction("Unsharp Mask (USM) ...", self)
            self.sharpen_usm_filter_action.triggered.connect(lambda: self.image_enhance_filter("Unsharp Mask (USM)", 180))
            sharpen_submenu.addAction(self.sharpen_usm_filter_action)
        
        

        ## Noise Filters
            noise_submenu = filter_menu.addMenu("Noise ")
            
            self.noise_add_filter_action = QAction("Add Noise ...", self)
            self.noise_add_filter_action.triggered.connect(lambda: self.image_enhance_filter("Add Noise", 140))
            noise_submenu.addAction(self.noise_add_filter_action)

            self.noise_remove_filter_action = QAction("Noise Removal ...", self)
            self.noise_remove_filter_action.triggered.connect(lambda: self.image_enhance_filter("Noise Removal"))
            noise_submenu.addAction(self.noise_remove_filter_action)

            self.median_filter_action = QAction("Median ...", self)
            self.median_filter_action.triggered.connect(lambda: self.image_enhance_filter("Median"))
            noise_submenu.addAction(self.median_filter_action)

        
        ## Style Filters
            style_submenu = filter_menu.addMenu("Style ")
            
            self.diffuse_filter_action = QAction("Diffuse ...", self)
            self.diffuse_filter_action.triggered.connect(lambda: self.image_enhance_filter("Diffuse"))
            style_submenu.addAction(self.diffuse_filter_action)
            
            self.solarize_filter_action = QAction("Solarize ...", self)
            self.solarize_filter_action.triggered.connect(lambda: self.image_enhance_filter("Solarize"))
            style_submenu.addAction(self.solarize_filter_action)
            
            
        ## Other
            other_submenu = filter_menu.addMenu("Other ")
            
            self.edge_enhance_filter_action = QAction("Edge Enhancement ...", self)
            self.edge_enhance_filter_action.triggered.connect(lambda: self.image_enhance_filter("Edge Enhance"))
            other_submenu.addAction(self.edge_enhance_filter_action)
            
            self.beauty_filter_action = QAction("Beautify ...", self)
            self.beauty_filter_action.triggered.connect(lambda: self.image_enhance_filter("Beautify", 140))
            other_submenu.addAction(self.beauty_filter_action)
        filter_menu_initiate(self)


# --------------------------------------------------------------------------------
    ### Tool Menu
        tool_menu = menubar.addMenu("&Tool(T) ")
        def tool_menu_initiate(self):
            self.barcode_action = QAction("Barcode Reader(&B) ...", self)
            self.barcode_action.triggered.connect(self.open_barcode_tool)
            tool_menu.addAction(self.barcode_action)
            
            self.qrcode_action = QAction("QRcode Reader(&Q) ...", self)
            self.qrcode_action.triggered.connect(self.open_qrcode_tool)
            tool_menu.addAction(self.qrcode_action)
        
            tool_menu.addSeparator()
            
            self.text_action = QAction("Insert Text(&T) ...", self)
            self.text_action.setShortcut("alt+t")
            self.text_action.triggered.connect(lambda: self.insert_text_tool(None))
            tool_menu.addAction(self.text_action)
            
            self.insert_img_action = QAction("Insert Image(&I) ...", self)
            self.insert_img_action.triggered.connect(self.insert_image_tool)
            tool_menu.addAction(self.insert_img_action)
            
            self.combine_img_action = QAction("Combine Image(&C) ...", self)
            self.combine_img_action.triggered.connect(self.combine_images)
            tool_menu.addAction(self.combine_img_action)
            
            tool_menu.addSeparator()
            
            self.matplotlib_action = QAction("Show in Matplotlib(&M) ...", self)
            self.matplotlib_action.triggered.connect(self.show_in_matplotlib)
            tool_menu.addAction(self.matplotlib_action)
        tool_menu_initiate(self)


        self.update_button_menu()
        self.update_recent_used_menu()
        self.update_recent_saved_menu()
        
    
    def setup_top_toolbar(self):
        """ Setup toolbar menu """
        
        toolbar = self.addToolBar("Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)
        toolbar_paint = self.addToolBar("ToolPaint")
        toolbar_paint.setOrientation(Qt.Vertical)
        self.addToolBar(Qt.LeftToolBarArea, toolbar_paint)
        
        
    # ---------------------------------------------------------
    ## Main Toolbar Menu
        
        self.new_action.setIcon(QIcon(f"{assets_path}new-blank-page.png"))
        self.save_action.setIcon(QIcon(f"{assets_path}toolbar-diskette.png"))
        self.load_action.setIcon(QIcon(f"{assets_path}toolbar-folder.png"))
        
        self.undo_action.setIcon(QIcon(f"{assets_path}toolbar-turn-left.png"))
        self.redo_action.setIcon(QIcon(f"{assets_path}toolbar-turn-right.png"))
        
       
        toolbar.addAction(self.new_action)
        toolbar.addAction(self.load_action)
        toolbar.addAction(self.save_action)
        
        toolbar.addSeparator()
        toolbar.addSeparator()
        
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        
    # ---------------------------------------------------------
    ## Paint Toolbar Menu

        self.move_action = QAction(QIcon(f"{assets_path}hand.svg"), "Move(M)", self)
        self.move_action.triggered.connect(self.enable_moving_mode)
        self.move_action.setShortcut("m")
        self.move_action.setCheckable(True)

        self.pen_action = QAction(QIcon(f"{assets_path}pencil.svg"), "Pen(B)", self)
        self.pen_action.triggered.connect(lambda: self.toggle_draw_mode("pen")) 
        self.pen_action.setShortcut("b")
        self.line_action = QAction(QIcon(f"{assets_path}line-tool.svg"), "Line(D)", self)
        self.line_action.triggered.connect(lambda: self.toggle_draw_mode('line'))
        self.line_action.setShortcut("d")
        self.eraser_action = QAction(QIcon(f"{assets_path}ereaser.svg"), "Eraser(E)", self)
        self.eraser_action.triggered.connect(lambda: self.toggle_draw_mode('ereaser'))
        self.eraser_action.setShortcut("e")
        
        self.circle_action = QAction(QIcon(f"{assets_path}circle.svg"), "Circle(C)", self)
        self.circle_action.triggered.connect(lambda: self.toggle_draw_mode('circle'))
        self.circle_action.setShortcut("c")
        self.triangle_action = QAction(QIcon(f"{assets_path}triangle.svg"), "Triangle(T)", self)
        self.triangle_action.triggered.connect(lambda: self.toggle_draw_mode('triangle'))
        self.triangle_action.setShortcut("t")
        self.rectangle_action = QAction(QIcon(f"{assets_path}rectangle.svg"), "Rectangle(R)", self)
        self.rectangle_action.triggered.connect(lambda: self.toggle_draw_mode('rectangle'))
        self.rectangle_action.setShortcut("r")
        
        self.bucket_action = QAction(QIcon(f"{assets_path}paint.svg"), "Bucket(G)", self)
        self.bucket_action.triggered.connect(lambda: self.toggle_draw_mode("paint bucket"))
        self.bucket_action.setShortcut("g")

        toolbar_paint.addAction(self.move_action)

        toolbar_paint.addSeparator()
        toolbar_paint.addSeparator()
    
        toolbar_paint.addAction(self.pen_action)
        toolbar_paint.addAction(self.line_action)
        toolbar_paint.addAction(self.eraser_action)
        
        toolbar_paint.addSeparator()
        toolbar_paint.addSeparator()
        
        toolbar_paint.addAction(self.circle_action)
        toolbar_paint.addAction(self.rectangle_action)
        toolbar_paint.addAction(self.triangle_action)
        
        toolbar_paint.addSeparator()
        toolbar_paint.addSeparator()
        
        toolbar_paint.addAction(self.bucket_action)
        
        
    
    
# --------------------------------------------------------------------------------
    
    ### Global Settings Data
    def data_initiate(self):
        
        ### Redo Undo limit
        self.max_undo         = 40
        self.max_redo         = self.max_undo

        ## --- Pen Settings
        self.pen_thickness    = 30
        self.pen_color        = (0, 0, 0)
        ## --- Grid and Ruler Setting
        self.grid_size        = 64
        self.grid_thickness   = 1
        self.grid_color       = QColor(180, 180, 180, 160)

        self.ruler_thickness  = 20
        self.ruler_grid       = 50

# --------------------------------------------------------------------------------
### File Menu Functions
    def load_image_dialog(self):
        """Open a file dialog to select and load an image."""
        file_path, _ = QFileDialog.getOpenFileNames(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path is None: return
            
        for path in file_path:
            img = cv2.imread(path)
            if img is None: continue

            self.add_recently_used(path)
                
            base_layer = a2.Layer(self.layer_panel, "Background", img)
            self.image_list.append((path, [base_layer]))
            self.original_image_list.append(img)
            
            self.undo_stack.append([])
            self.redo_stack.append([])
                
        self.current_index = len(self.image_list)-1
        self.create_canvas_buttons()
        self.switch_canvas(self.current_index)
        
        self.update_button_menu()
    def load_image(self, file_path):
        """ Direct loading image by given path """
        
        if file_path:
            img = cv2.imread(file_path)
            if img is not None:
                
                ## Create a base image for load image
                base_layer = a2.Layer(self.layer_panel, "Background", img)
                
                self.image_list.append((file_path, [base_layer]))
                self.original_image_list.append(img)
                self.add_recently_used(file_path)
                
                self.undo_stack.append([])
                self.redo_stack.append([])
                
            self.current_index = len(self.image_list)-1
            self.main_index = self.current_index
            
            
            _, current_layers = self.image_list[self.current_index]
            self.layer_panel.set_layers(current_layers)
            self.display_image = current_layers[0].image
            
            self.create_canvas_buttons()
            self.switch_canvas(self.current_index)
        
        self.update_button_menu()
        
    def update_image_display(self, reset_scale=False, reset_position=False):
        """Display the current OpenCV image in the QLabel."""
        if self.display_image is None or len(self.layer_panel.layers)==0 :
            return

    ## Get Image from layer
        active_index = self.layer_panel.active_layer_index
        if active_index == -1 or active_index >= len(self.layer_panel.layers):
            return
        
        # Output image of all layers
        image = self.display_image
        if len(image.shape) == 2: 
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
        elif len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        height, width, _ = image.shape

            
        bytes_per_line = image.strides[0]
        qt_image = QImage(
            image.data, 
            width, height, bytes_per_line, 
            QImage.Format_RGBA8888
        ).rgbSwapped()
        pix = QPixmap.fromImage(qt_image)

        label_w = self.image_label.width()
        label_h = self.image_label.height()
        
        # Origin Zoom to 100% 
        ratio_w = label_w / width
        ratio_h = label_h / height
        self.origin_zoom = min(ratio_w, ratio_h)
        
    ## Reseting viewing control
        if reset_position: self.canva_offset = (0, 0)
        if reset_scale: self.set_zoom_factor(100.0, change=False)
        
        # Final scale to canvas
        total_scale = self.origin_zoom * self.zoom_factor
        
        # Scale image
        new_w = int(width * total_scale)
        new_h = int(height * total_scale)
        scaled_pix = pix.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        
    ## View Moving Control
        x_offset = (label_w - scaled_pix.width()) // 2
        y_offset = (label_h - scaled_pix.height()) // 2
        x_canva_offset, y_canva_offset = self.canva_offset
        
        if self.move_diff_pos != None:
            x_canva_offset    += self.move_diff_pos.x()
            y_canva_offset    += self.move_diff_pos.y()
            self.canva_offset = x_canva_offset, y_canva_offset
        
        self.display_scale_x    = scaled_pix.width() / width
        self.display_scale_y    = scaled_pix.height() / height
        self.display_offset     = (x_offset + x_canva_offset, y_offset + y_canva_offset)

    ## Apply view control
        canvas = QPixmap(label_w, label_h)
        canvas.fill(Qt.transparent)

        painter = QPainter(canvas)
        painter.drawPixmap(x_offset + x_canva_offset, y_offset + y_canva_offset, scaled_pix)
        painter.end()

        self.image_label.setPixmap(canvas)
        self.image_label.update_selected_rect()
        
        
    # Display thumbnail image   
        self.display_thumbnail_image()
        

    # Display view windows
        for w in self.view_windows:
            if not w.isVisible(): continue
            if w.current_index == self.main_index:
                w.set_image(image)
                continue
            _, layers = self.image_list[w.current_index]
            w.set_image(a2.LayerManager.compose_layers(layers))
    
        self.update_button_menu()
    
    def display_current_image(self, reset_scale=False):
        if 0 <= self.main_index < len(self.image_list):
            
            file_path, layers = self.image_list[self.main_index]
            self.display_image = a2.LayerManager.compose_layers(layers)
            self.layer_panel.refresh_list()
            
            # Update Histogram 
            if self.histogram_panel.isVisible():
                self.histogram_panel.update_histogram()
            if self.histogram_display is not None:
                self.histogram_display.update_histogram()
            
            self.update_image_display(reset_scale, reset_scale)
            self.setWindowTitle(file_path)
    def update_image_display_preview(self, preview):
        h, w = preview.shape[:2]
        bytes_per_line = preview.strides[0]
        qimg = QImage(preview.tobytes(), w, h, bytes_per_line, QImage.Format_BGR888)
        pix = QPixmap.fromImage(qimg)
        scaled_pix = pix.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pix)
    
    def display_thumbnail_image(self):
        current_focus = self.get_focus_window()
        image = current_focus.display_image.copy()
        if image is None: return
        
        if len(image.shape) == 2: 
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
        elif len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
        height, width, _ = image.shape
            
        bytes_per_line = image.strides[0]
        qt_image = QImage(
            image.data, 
            width, height, bytes_per_line, 
            QImage.Format_RGBA8888
        ).rgbSwapped()
        pix = QPixmap.fromImage(qt_image)
        
        thumb_pix = pix.scaled(
        self.thumbnail_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.thumbnail_label.setPixmap(thumb_pix)
    
    def set_current_index_focus(self):
        """ Update self as focus window """
        if self.dialog_open: return
        
        if self.current_index != self.main_index:
            _, layers = self.image_list[self.main_index]
            self.layer_panel.set_layers(layers)
        
        self.current_index = self.main_index
        self.grid_action.setChecked(self.image_label.show_grid)
        self.ruler_action.setChecked(self.image_label.show_ruler)
        
        for i in self.view_windows:
            i.on_focus = False
            i.disabled_selection_mode()
    def current_focus_layer_image(self, img=None):
        """ Get or set current layer image """
        
        layer_idx = self.layer_panel.active_layer_index
        if layer_idx < 0 or self.current_index < 0: return None
        if layer_idx >= len(self.layer_panel.layers): return None
        
        _, layers = self.image_list[self.current_index]
        if img is not None:
            self.layer_panel.layers[layer_idx].set_image(img)
            return None
        return layers[layer_idx].image
    def get_current_focus_layer(self): 
        """ Get current layer """
        
        layer_idx = self.layer_panel.active_layer_index
        if layer_idx < 0 or self.current_index < 0: return None
        
        _, layers = self.image_list[self.current_index]
        if layer_idx >= len(layers): return None
        
        return layers[layer_idx]
    
    def backup_all_layer(self):
        layers = []
        for layer in self.layer_panel.layers:
            state = a2.LayerState(
                name=layer.name,
                opacity=layer.opacity,
                is_visible=layer.visible,
                blend_mode=layer.blend_mode,
                clipping_mask=layer.clipping_mask, 
                image_data=layer.image 
            )
            layers.append(state)
        return layers
    def get_all_backup_layer(self, layers_data):
        layers = []
        for layer in layers_data:
            lyr = a2.Layer( 
                self.layer_panel, layer.name, layer.image_data, 
                layer.is_visible, layer.opacity, layer.blend_mode, 
                layer.clipping_mask
            )
            layers.append(lyr)
        return layers
        
    
    
## Save
    def save_image(self):
        """ Save and direct rewrite the original image """
        
        if self.display_image is None: return
        if 0 > self.current_index >= len(self.image_list): return
        
        
        orig_path, layers = self.image_list[self.current_index]
        img = a2.LayerManager.compose_layers(layers)
        
        if not os.path.exists(orig_path) or orig_path.startswith("NewCanvas_"):
            self.save_image_as(empty_canvas=True)
            return

        success = cv2.imwrite(orig_path, self.display_image)
        if not success: return
        
        print(f"Image saved successfully at: {orig_path}")
        self.add_recently_saved(orig_path)
        self.original_image_list[self.current_index] = img
        
        if self.histogram_display is not None:
            self.histogram_display.update_histogram()
                
    def save_image_as(self, empty_canvas=False):
        if self.display_image is None:
            QMessageBox.warning(self, "No Image", "No image to save.")
            return
        if 0 > self.current_index >= len(self.image_list): return
        
        
        default_name = "new_image.jpg"
        orig_path, layers = self.image_list[self.current_index]
        img = a2.LayerManager.compose_layers(layers)
        
        base = os.path.basename(orig_path)
        name, ext = os.path.splitext(base)
        default_name = f"{name}_edited{ext}"

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", default_name, "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if not save_path: return
        success = cv2.imwrite(save_path, img)
        
        if success:      
            self.add_recently_saved(save_path)
            self.image_list[self.current_index] = (save_path, img)
            self.display_current_image()
            
            if empty_canvas:
                self.original_image_list[self.current_index] = img
                if self.histogram_display is not None:
                    self.histogram_display.update_histogram()

## New Canvas
    def create_new_canvas(self):
        dialog = NewCanvasDialog()
        if dialog.exec_() == QDialog.Accepted:
            width, height = dialog.get_size()
            
            if not (width and height):
                print(" Invalid size entered.")
                return
            
        # Create new blank white layer 
            # blank = np.zeros((height, width, 4), np.uint8) 
            blank = np.ones((height, width, 4), np.uint8) * 255
            layer = a2.Layer(self.layer_panel, "Background", blank)
            
            self.new_canvas_counter   += 1
            canvas_name               = f"NewCanvas_{self.new_canvas_counter}"
            self.image_list.append((canvas_name, [layer]))
            self.original_image_list.append(blank)
            
            self.current_index        = len(self.image_list) - 1
            self.main_index           = self.current_index
            
            self.undo_stack.append([])
            self.redo_stack.append([])
            
            self.layer_panel.set_layers([layer])
            self.display_image = layer.image
            
            self.create_canvas_buttons()
            self.switch_canvas(self.current_index)
            
            self.update_button_menu()
    def create_empty_canvas(self):
        """ Create default empty canvas """
        width, height = 1024, 1024
        
    # Create new blank white layer 
        # blank = np.zeros((height, width, 4), np.uint8) 
        blank = np.ones((height, width, 4), np.uint8) * 255
        layer = a2.Layer(self.layer_panel, "Background", blank)
        
        
        self.new_canvas_counter += 1
        canvas_name = f"NewCanvas_{self.new_canvas_counter}"
        self.image_list.append((canvas_name, [layer]))
        self.original_image_list.append(blank)
        
        self.current_index = len(self.image_list) - 1
        self.main_index = self.current_index
        
        self.undo_stack.append([])
        self.redo_stack.append([])
        
        self.layer_panel.set_layers([layer])
        self.display_image = layer.image
        
        self.create_canvas_buttons()
        self.switch_canvas(self.current_index)
        
    
## Load form Clipboard
    def close_current_image(self):
        if self.current_index < 0 or not self.image_list:
            QMessageBox.warning(self, "No Image", "No displaying image.")
            return

        ## Only close view window if user focus on it
        for i in self.view_windows:
            if i.on_focus:
                i.close()
                self.current_index = self.main_index
                self.switch_canvas(self.current_index)
                return

        closed_index = self.current_index
        self.image_list.pop(closed_index)
        self.original_image_list.pop(closed_index)
        
        self.undo_stack.pop(closed_index)
        self.redo_stack.pop(closed_index)
        
        ## Close related view windows
        delete_list = []
        for i in self.view_windows:
            if i.current_index == closed_index:
                delete_list.append(i)
        for i in delete_list:
            i.close()
        
        ## Respown canvas buttons
        for i in reversed(range(self.canvas_button_layout.count())):
            widget = self.canvas_button_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.create_canvas_buttons()


        if len(self.image_list) > 0:
            # Move to the previous image
            self.current_index = min(closed_index, len(self.image_list)-1)
            self.main_index = self.current_index
            self.switch_canvas(self.current_index)            
            
            for i in self.view_windows:
                i.current_index -= 1 if i.current_index > closed_index else 0
        else:
            self.current_index = -1
            self.main_index = -1
            
            self.image_label.setText("No Image Loaded")
            self.image_label.setPixmap(QPixmap())
            self.layer_panel.set_layers([])
            self.thumbnail_label.setPixmap(QPixmap())
            self.setWindowTitle("Assignment Paint Application: BS23110051")
            
            self.display_image = None
        
        self.update_button_menu()
        
        
    def load_clipboard_image(self):
        if self.image_label.copied_image is None:
            return

        
        image = self.image_label.copied_image.copy()
        layer = a2.Layer(self.layer_panel, "Background", image)
        
        self.new_canvas_counter += 1
        canvas_name = f"NewCanvas_{self.new_canvas_counter}"
        self.image_list.append((canvas_name, [layer]))
        self.original_image_list.append(image)
        
        self.current_index = len(self.image_list) - 1
        self.main_index = self.current_index
        
        self.undo_stack.append([])
        self.redo_stack.append([])
        
        self.layer_panel.set_layers([layer])
        self.display_image = layer.image
        self.display_current_image(True)
        
        self.create_canvas_buttons()
        self.switch_canvas(self.current_index)
        

## Recently Used
    def add_recently_used(self, file_path):
        if not file_path: return

        # Remove if exists (to re-add at top)
        if file_path in self.recently_used_list:
            self.recently_used_list.remove(file_path)

        self.recently_used_list.insert(0, file_path)
        self.recently_used_list = self.recently_used_list[:self.recent_file_limit]

        self.update_recent_used_menu()
    def load_recently_used(self, file_path):
        if self.dialog_open: return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Missing",
                                f"The file does not exist:\n{file_path}")
            # Remove missing file
            if file_path in self.recently_used_list:
                self.recently_used_list.remove(file_path)
                self.update_recent_used_menu()
            return

        # Load file using your own open_image method
        self.load_image(file_path)
    def update_recent_used_menu(self):
        self.recently_used_menu.clear()

        if not self.recently_used_list:
            empty_action = QAction("No recently file opened ", self)
            empty_action.setEnabled(False)
            self.recently_used_menu.addAction(empty_action)
            return

        for i, path in enumerate(self.recently_used_list):
            action = QAction(f"&{i+1}. {path}", self)
            # action.triggered.connect(lambda: self.load_recently_used(path))
            action.triggered.connect(partial(self.load_recently_used, path))
            self.recently_used_menu.addAction(action)
## Recently Saved
    def add_recently_saved(self, file_path):
        if not file_path: return

        # Remove if exists (to re-add at top)
        if file_path in self.recently_saved_list:
            self.recently_saved_list.remove(file_path)

        self.recently_saved_list.insert(0, file_path)
        self.recently_saved_list = self.recently_saved_list[:self.recent_file_limit]

        self.update_recent_saved_menu()
    def load_recently_saved(self, file_path):
        if self.dialog_open: return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Missing",
                                f"The file does not exist:\n{file_path}")
            # Remove missing file
            if file_path in self.recently_saved_list:
                self.recently_saved_list.remove(file_path)
                self.update_recent_saved_menu()
            return

        # Load file using your own open_image method
        self.load_image(file_path)
    def update_recent_saved_menu(self):
        self.recently_saved_menu.clear()

        if not self.recently_saved_list:
            empty_action = QAction("No recently file saved ", self)
            empty_action.setEnabled(False)
            self.recently_saved_menu.addAction(empty_action)
            return

        for i, path in enumerate(self.recently_saved_list):
            action = QAction(f"&{i+1}. {path}", self)
            action.triggered.connect(partial(self.load_recently_saved, path))
            self.recently_saved_menu.addAction(action)
    
    
    
#/layer
# --------------------------------------------------------------------------------
### Edit Menu Functions
#/layer
    def crop_selected_area(self):
        if self.display_image is None: return

        current_focus = self.get_focus_window()
        if current_focus.selected_rect == (0, 0, 0, 0): return
        self.push_undo_state()

        x1, y1, x2, y2    = current_focus.selected_rect
        _, layers         = self.image_list[self.current_index]
        
        for layer in layers:
            cropped = layer.image[y1:y2, x1:x2].copy()
            layer.set_image(cropped)
        
        self.display_current_image()
        self.disabled_selection_mode()
        self.selected_rect = (0, 0, 0, 0)
        
#/layer
    def crop_image(self):
        if self.display_image is None: return
        
        dialog = CropDialog(self)

        self.push_undo_state()
        if dialog.exec_() == QDialog.Accepted:
            self.display_current_image()

    


#/layer
# --------------------------------------------------------------------------------
### Image Menu Functions
#/layer
    def image_size(self):
        if self.display_image is None: return
        
        dialog = ScaleImageDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            
            self.display_current_image()
#/layer    
    def image_position(self):
        if self.display_image is None: return 
        
        
        dialog = TranslateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            
            self.display_current_image()
#/layer    
    def flip_image(self, mode):
        if self.display_image is None:
            return

        self.push_undo_state()
        _, layers = self.image_list[self.current_index]
        
        for layer in layers:
            img = layer.image
        
            if mode == "h":
                flip_img = cv2.flip(img, 1)  # horizontal flip
            elif mode == "v":
                flip_img = cv2.flip(img, 0)  # vertical flip
        
            layer.set_image(flip_img)
        
        self.display_current_image()
#/layer
    def image_rotation(self):
        if self.display_image is None: return

        angle, ok = QInputDialog.getInt(self, "Rotate Image", "Rotation angle(degrees):", 0, -360, 360, 1)
        if ok:
            self.push_undo_state()
            self.rotate_image(angle)
#/layer
    def rotate_image(self, angle):
        if self.display_image is None: return

        _, layers = self.image_list[self.current_index]
        for layer in layers:
            img = layer.image
            center = (img.shape[1] // 2, img.shape[0] // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            rotated = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), 
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0) 
                                     )
            layer.set_image(rotated)
            
        self.display_current_image()
#/layer
    def rotate_image_90_degree(self, type=1):
        if self.display_image is None: return

        self.push_undo_state()
        
        _, layers = self.image_list[self.current_index]
        for layer in layers:
            img = layer.image
            if type == 1:
                rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif type == -1:
                rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif type == 180:
                rotated = cv2.rotate(img, cv2.ROTATE_180)
            layer.set_image(rotated)

        
        self.display_current_image()
#/layer
    def image_expand(self):
        if self.display_image is None: return

        dialog = ExpandCanvasDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.display_current_image()

#/layer
    def show_image_details(self):
        if self.display_image is None: return

        path, _ = self.image_list[self.current_index]
        dialog = ImageDetailsDialog(self, path)
        dialog.exec_()
#/layer
    def free_transform(self):
        ## Return if transform processing
        if self.image_label.transform_mode: return
        if self.dialog_open: return
        for i in self.view_windows:
            if i.image_label.transform_mode and i.isVisible():
                return
        
        ##
        for i in self.view_windows:
            if i.on_focus and i.isVisible():
                i.free_transform()
                return
        
        if self.image_label.selection_rect == QRect():
            self.select_all()

        self.image_label.enable_transform(True)
        self.image_label.update()
        self.update_button_menu()
        

    
    
    
#/layer
# --------------------------------------------------------------------------------
### Select Menu Functions
    def enable_selection_mode(self):
        if self.display_image is None:
            QMessageBox.warning(self, "No Image", "No displaying image.")
            return

        if self.image_label.select_mode:
            self.image_label.enable_selection(False)            
            self.select_action.setChecked(False)
            return

        self.image_label.enable_selection(True)
        self.select_action.setChecked(True)
        
        self.image_label.enable_moving(False)
        self.move_action.setChecked(False)
        
        for i in self.view_windows:
            if i.isVisible():
                i.enable_selection_mode()
    
    def disabled_selection_mode(self):
        self.image_label.selection_rect = QRect()
        self.selected_rect = (0, 0, 0, 0)
        self.image_label.update()
        self.update_button_menu()
        
        for i in self.view_windows:
            if i.isVisible():
                i.disabled_selection_mode()
            
    def on_selection_made(self, rect: QRect):
        if self.display_image is None:
            QMessageBox.warning(self, "No Image", "No displaying image.")
            return

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

        for i in self.view_windows:
            if i.on_focus and i.isVisible():
                return
        
        x1, y1, w, h = self.get_canvas_area_size()

        display_rect = QRect(
            x1, y1, w, h
        )

        self.image_label.selection_rect = display_rect
        # Emit true image-space rectangle
        self.on_selection_made(display_rect)
        self.image_label.update()

        self.update_button_menu()

    def get_canvas_area_size(self):
        h, w = self.display_image.shape[:2]

        # Map full image to label coordinates for visual rectangle
        scale = self.display_scale_x
        offset_x, offset_y = self.display_offset

        return (offset_x, offset_y, 
                int(w * scale), int(h * scale))
    
    def get_result_by_roi(self, img, result, roi):
        """
        Apply the result, if there are ROI existing
        """
        if roi != (0, 0, 0, 0):
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            elif len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                
            if len(result.shape) == 2:
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGRA)
            elif len(result.shape) == 3:
                result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
            
            x1, y1, x2, y2 = roi
            h, w = result.shape[:2]
            x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
            y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
            
            region = img.copy()
            region[y1:y2, x1:x2] = result[y1:y2, x1:x2]
        else:
            region = result
        return region
    
    
    def copy(self):
        if self.image_label.transform_mode: return
        for i in self.view_windows:
            if i.image_label.transform_mode: return
        
        for i in self.view_windows:
            if i.on_focus and i.image_label.selection_rect != QRect():
                self.image_label.copy_image(i.selected_rect)
                self.update_button_menu()
                return
            
        if self.image_label.selection_rect == QRect(): return
        self.image_label.copy_image(self.selected_rect)
        self.update_button_menu()

    def cut(self):
        if self.image_label.transform_mode: return
        for i in self.view_windows:
            if i.image_label.transform_mode: return
        
        
        for i in self.view_windows:
            if i.on_focus and i.image_label.selection_rect != QRect():
                i.push_undo_state()
                self.image_label.cut_image(i.selected_rect)
                self.update_button_menu()
                return
            
        if self.image_label.selection_rect == QRect(): return
        self.push_undo_state()
        self.image_label.cut_image(self.selected_rect)
        self.update_button_menu()
        
        if self.histogram_display is not None:
            self.histogram_display.update_histogram()
        
    def paste(self):
        if self.image_label.transform_mode: return
        for i in self.view_windows:
            if i.image_label.transform_mode: return
        
        ## Make paste to available to every window
        for i in self.view_windows:
            if i.on_focus:
                i.push_undo_state()
                i.image_label.paste_from_clipboard()
                self.update_button_menu()
                return
        
        self.push_undo_state()
        self.image_label.paste_from_clipboard()
        self.update_button_menu()
        
        if self.histogram_display is not None:
            self.histogram_display.update_histogram()

    
    
    
#/layer
# --------------------------------------------------------------------------------
### Color Menu Functions
#/layer
    def color_convert(self):
        if self.display_image is None: return

        img = self.current_focus_layer_image()
        dialog = ColorConvertDialog(self, img)

        self.push_undo_state(reset_redo=False)
        if dialog.exec_() == QDialog.Rejected:
            self.undo_stack[self.current_index].pop()

        self.display_current_image()
#/layer
    def color_negative(self):
        if self.display_image is None: return

        current_layer = self.get_current_focus_layer()
        if current_layer is None: return

        self.push_undo_state()
        img = current_layer.image.copy()
        
        b, g, r, a = cv2.split(img)
        bgr_image = cv2.merge([b, g, r])

        if self.selected_rect != (0, 0, 0, 0):
            x1, y1, x2, y2 = self.selected_rect
            h, w = img.shape[:2]
            x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
            y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

            if x1 < x2 and y1 < y2:
                roi = bgr_image[y1:y2, x1:x2]
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                inv_roi = 255 - gray_roi
                bgr_image[y1:y2, x1:x2] = cv2.cvtColor(inv_roi, cv2.COLOR_GRAY2BGR)
        else:
            gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
            inverted_gray = 255 - gray
            bgr_image = cv2.cvtColor(inverted_gray, cv2.COLOR_GRAY2BGR)

        current_layer.image = cv2.merge([*cv2.split(bgr_image), a])
        self.display_current_image()
        
#/layer
    def color_inverse(self):
        if self.display_image is None: return

        current_layer = self.get_current_focus_layer()
        if current_layer is None: return

        self.push_undo_state()

        img = current_layer.image.copy()

        b, g, r, a = cv2.split(img)
        bgr_image = cv2.merge([b, g, r])

        if self.selected_rect != (0, 0, 0, 0):
            x1, y1, x2, y2 = self.selected_rect
            h, w = img.shape[:2]
            x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
            y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))

            if x1 < x2 and y1 < y2:
                bgr_image[y1:y2, x1:x2] = 255 - bgr_image[y1:y2, x1:x2]
        else:
            bgr_image = 255 - bgr_image

        current_layer.set_image(cv2.merge([*cv2.split(bgr_image), a]))
        self.display_current_image()

#/layer
    def color_adjust(self):
        if self.display_image is None: return
    
        self.push_undo_state(False)
        dialog = ColorAdjustDialog(self)
        
        if dialog.exec_() != QDialog.Accepted:
            self.undo_stack[self.current_index].pop()
            
        self.display_current_image()
#/layer
    def color_intensity_adjust(self):
        if self.display_image is None: return
    
        self.push_undo_state(False)
        dialog = ColorIntensityAdjustDialog(self)
        
        if dialog.exec_() != QDialog.Accepted:
            self.undo_stack[self.current_index].pop()
            
        self.display_current_image()
    
    
    
    
# --------------------------------------------------------------------------------
    
### View Menu Functions
    def next_canvas(self, next):
        if len(self.image_list) > 1:
                self.switch_canvas((self.current_index + next) % len(self.image_list))
    
    def get_focus_window(self):
        for i in self.view_windows:
            if i.on_focus:
                return i
        
        return self
    
#/layer
    def open_new_view_window(self):
        if self.display_image is None:
            QMessageBox.warning(self, "No Image", "No image to display.")
            return

        image_name = self.image_list[self.current_index][0]
        view = a2.ImageViewWindow(self, self.current_index, image_name, self.image_list)
        view.show()
        view.set_image(self.display_image)

        self.view_windows.append(view)

    def toggle_ruler(self, checked):
        for i in self.view_windows:
            if i.on_focus:
                i.image_label.show_ruler = checked
                i.image_label.update()
                return

        self.image_label.show_ruler = checked
        self.image_label.update()
    def toggle_grid(self, checked):
        for i in self.view_windows:
            if i.on_focus:
                i.image_label.show_grid = checked
                i.image_label.update()
                return

        self.image_label.show_grid = checked
        self.image_label.update()
    def grid_ruler_settings(self):
        dialog = a2.GridSettingsDialog(self)
        dialog.exec_()
        
    def show_histogram(self):
        if self.histogram_display is not None:
            self.histogram_display.close()
            
        self.histogram_display = a2.HistogramWindow(self)
        self.histogram_display.show()
        
        for i in self.view_windows:
            i.histogram_display = self.histogram_display





# --------------------------------------------------------------------------------

### Filter Menu Functions
    def set_dialog_open(self, bool):
        self.dialog_open = bool
        for i in self.view_windows:
            i.dialog_open = bool
        self.update_button_menu()
    def image_enhance_filter(self, method="", hsize=130):
        if self.display_image is None:
            return

        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.enhance = a2.EnhancePanel(self, method, hsize)
        self.enhance.show()
    
    def image_onetime_enhance_filter(self, method=""):
        if self.display_image is None: return

        result = None
        self.push_undo_state()
        layer = self.get_current_focus_layer()
        img = layer.image.copy()
        
        if method == "Sharpen Edge":
            result = a2.ImageEnhancer.apply_sharpen_edge(img)
        if result is None: return
    
        
        current_focus = self.get_focus_window()
        ori_image = layer.image.copy()
        region = self.get_result_by_roi(ori_image, result, current_focus.selected_rect)
        
        layer.set_image(region)
        self.display_current_image()
    
    def bit_plane_panel(self):
        if self.display_image is None:
            return

        self.bit_plane = a2.BitPlaneSlicer(self)
        self.bit_plane.show()

    def edge_detection(self):
        if self.display_image is None:
            return

        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.edge_det = a2.EdgeDetectionPanel(self)
        self.edge_det.show()

    def thresholding(self):
        if self.display_image is None:
            return

        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.threshold_dialog = a2.ThresholdPanel(self)
        self.threshold_dialog.show()

    def power_law_transformation(self):
        if self.display_image is None:
            return
        
        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.power_law_dialog = a2.PowerLawPanel(self)
        self.power_law_dialog.show()

    def piecewise_transformation(self):
        if self.display_image is None:
            return
        
        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.piecewise_dialog = a2.PiecewisePanel(self)
        self.piecewise_dialog.show()

    def morphology_filter(self):
        if self.display_image is None:
            return
        
        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.morphology_dialog = a2.MorphologyPanel(self)
        self.morphology_dialog.show()
    
    def histogram_equalization(self):
        if self.display_image is None:
            return
        
        self.push_undo_state(False)
        self.set_dialog_open(True)
        self.histogram_eq_dialog = a2.HistogramEqualizationPanel(self)
        self.histogram_eq_dialog.show()



# --------------------------------------------------------------------------------
    
### Canvas Layer Buttons
    def create_canvas_buttons(self):
        while self.canvas_button_layout.count():
            item = self.canvas_button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        max_per_row = 6
        for i, (path, _) in enumerate(self.image_list):
            file_name = os.path.basename(path)
            
            btn = QPushButton(file_name[:18])
            btn.setMinimumHeight(30)
            btn.clicked.connect(lambda _, x=i: self.switch_canvas(x))
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored)
            
            row = i // max_per_row 
            col = i % max_per_row
            
            self.canvas_button_layout.addWidget(btn, row, col)
    
    def switch_canvas(self, index):
        if self.image_label.transform_mode: return
        if self.dialog_open and self.current_index != index: return
        
        if 0 <= index < len(self.image_list):
            self.image_label.apply_free_transform(cancel=True)
            self.disabled_selection_mode()
            
            self.current_index = index
            self.main_index = index
            
            _, layers = self.image_list[index]
            self.layer_panel.set_layers(layers, reset=True)
            
            # Set active editing image
            if self.layer_panel.active_layer_index > -1:
                self.display_image = self.layer_panel.update_composite()
            else:
                self.display_image = layers[0].image
            self.display_current_image(True)
            
            
            # Highlight the selected canvas button
            for i in range(self.canvas_button_layout.count()):
                button = self.canvas_button_layout.itemAt(i).widget()
                if button:
                    if i == index: button.setStyleSheet("background-color: lightblue;")
                    else: button.setStyleSheet("")

    
     
     
# --------------------------------------------------------------------------------
### Layer Functions
    def create_new_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.add_new_layer()
        
    def copy_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.copy_layer()
    
    def delete_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.delete_layer()
        
    def clear_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.clear_layer()
        self.display_current_image()
    
    def write_down(self):
        if self.layer_panel is None: return
        self.layer_panel.write_down()
        self.display_current_image()
    
    def merge_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.merge_down()
        
    def merge_all_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.merge_all_layer()
        self.display_current_image()
        
    def merge_all_visible_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.merge_all_visible_layer()
        self.display_current_image()
            
    def layer_rotate(self, type=1):
        if self.display_image is None: return

        self.push_undo_state()
        
        layer = self.get_current_focus_layer()
        img = layer.image.copy()
        if type == 1:
            rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif type == -1:
            rotated = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif type == 180:
            rotated = cv2.rotate(img, cv2.ROTATE_180)
        rotated = cv2.resize(rotated, (img.shape[1], img.shape[0]))
        layer.set_image(rotated)

        
        self.display_current_image()
    
    def layer_flip(self, mode):
        if self.display_image is None: return

        self.push_undo_state()
        layer = self.get_current_focus_layer()
        img = layer.image
    
        if mode == "h":
            flip_img = cv2.flip(img, 1)  # horizontal flip
        elif mode == "v":
            flip_img = cv2.flip(img, 0)  # vertical flip
    
        layer.set_image(flip_img)
        self.display_current_image()
    
    def layer_move(self, mode):
        if self.layer_panel is None: return
        self.layer_panel.layer_move(mode)
        self.display_current_image()
    
    def layer_move_top(self, mode):
        if self.layer_panel is None: return
        self.layer_panel.layer_move_top(mode)
        self.display_current_image()
    
    def rename_layer(self):
        if self.layer_panel is None: return
        self.layer_panel.rename_layer()
        self.display_current_image()
    
    
    
    
#/layer
# --------------------------------------------------------------------------------
### Paint Tool Functions
    def thickness_change(self, value):
        
        self.thickness.setText(str(value / 100))        
        self.pen_thickness = value / 100
        self.image_label.pen_thickness = self.pen_thickness
        
        current_color = self.pen_color
        self.pen_preview.update_preview(self.pen_thickness, current_color)
        
        for i in self.view_windows:
            if i.isVisible():
                i.image_label.pen_thickness = self.pen_thickness

    def toggle_draw_mode(self, mode):
        
        self.image_label.enable_drawing(True, mode)
                
        for i in self.view_windows:
            if i.isVisible():
                i.image_label.enable_drawing(True, mode)
                i.image_label.enable_moving(False)   
                         
        self.move_action.setChecked(False)
        self.image_label.enable_moving(False)
        
    def set_active_color(self, color):
        
        self.active_color = color
        self.pen_color = color
        self.image_label.pen_color = self.pen_color
        self.active_color_display.setStyleSheet(
            f"background-color: rgb({color[2]}, {color[1]}, {color[0]}); border: 1px solid gray;"
        )
        
        self.pen_preview.update_preview(self.pen_thickness, color)
        
        for i in self.view_windows:
            if i.isVisible():
                i.image_label.pen_color = self.pen_color
    
    def enable_moving_mode(self):
        if self.image_label.move_mode:
            self.image_label.enable_moving(False)
            self.move_action.setChecked(False)
            return
        
        self.image_label.enable_moving(True)
        self.move_action.setChecked(True)
    
    ## Listen mouse scroll
    def wheelEvent(self, event):
        if self.display_image is None: return
        delta = event.angleDelta().y()

        if delta > 0:
            self.set_zoom_factor(self.zoom_factor*106.0, change=True)
        else:
            self.set_zoom_factor(self.zoom_factor*95.0, change=True)
    def set_zoom_factor(self, value_percent, change=False):
        _value = np.clip(value_percent, 
                         1, 1000.0
                )
        
        slider_val = 0
        # Zoom in 1% to 100%
        if _value <= 100.0:
            slider_val = int((_value / 100.0) * 1000)
        # Zoom out 100% to 1000%
        else:
            ratio = (_value - 100.0) / 900.0
            slider_val = int(1000 + (ratio * 1000))
        
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(int(slider_val))
        self.zoom_slider.blockSignals(False)
        
        self.zoom_factor = _value / 100.0
        self.zoom_label.setText(f"Zoom: {_value:.1f} %")
        
        if change: 
            self.update_image_display()
    def zoom_slider_changed(self, value):
        percent = 0.0
        
        # Zoom in 1% to 100%
        if value <= 1000:
            percent = (value / 1000.0) * 100.0
            if percent < 1: percent = 1
        # Zoom out 100% to 1000%
        else:
            ratio = (value - 1000) / 1000.0
            percent = 100.0 + (ratio * 900.0)

        self.zoom_factor = percent / 100.0
        self.zoom_label.setText(f"Zoom: {percent:.1f} %")
        self.update_image_display()
    
    def push_undo_state(self, reset_redo=True):
        if self.display_image is None or self.current_index < 0:
            return
        
        layers = self.backup_all_layer()
        
        self.undo_stack[self.current_index].append(layers)
        if reset_redo: self.redo_stack[self.current_index] = []
        
        
        if len(self.undo_stack[self.current_index]) > self.max_undo:
            self.undo_stack[self.current_index].pop(0)
        
        self.update_button_menu()     
    def undo(self):
        if self.image_label.transform_mode: return
        if len(self.undo_stack) <= self.current_index or self.current_index < 0: return
        if not self.undo_stack[self.current_index]:
            return

        self.push_redo_state()
        layers_data = self.undo_stack[self.current_index].pop().copy()
        layers = self.get_all_backup_layer(layers_data)


        path, _ = self.image_list[self.current_index]
        self.image_list[self.current_index] = (path, layers)
        self.layer_panel.set_layers(layers)
        self.display_current_image()
        self.update_button_menu()
        

    def push_redo_state(self):
        if self.current_index < 0: return
        
        layers = self.backup_all_layer()
        
        self.redo_stack[self.current_index].append(layers.copy())
        
        if len(self.redo_stack[self.current_index]) > self.max_redo:
            self.redo_stack[self.current_index].pop(0)
            
        self.update_button_menu()
    def redo(self):
        if self.image_label.transform_mode: return
        if len(self.redo_stack) <= self.current_index: return
        if not self.redo_stack[self.current_index]:
            return
        
        self.push_undo_state(False)
        layers_data = self.redo_stack[self.current_index].pop().copy()
        layers = self.get_all_backup_layer(layers_data)
        
        
        path, _ = self.image_list[self.current_index]
        self.image_list[self.current_index] = (path, layers)
        self.layer_panel.set_layers(layers)
        self.display_current_image()
        self.update_button_menu()
        

    
    
    
    
# --------------------------------------------------------------------------------
### Tool Functions
    def show_in_matplotlib(self):
        """Show the current display image in matplotlib."""
        if self.display_image is None:
            QMessageBox.warning(self, "No Image", "No displaying image.")
            return
        
        # Update my_image with current display image for matplotlib display
        temp_image = myImage()
        _, layers = self.image_list[self.current_index]
        composite_img = a2.LayerManager.compose_layers(layers)
        temp_image.image = composite_img
        title = os.path.basename(self.image_list[self.current_index][0]) if self.current_index != -1 else "Image"
        temp_image.showImage(title)

#/layer
    def combine_images(self):
        dialog = ImageStitchDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            paths = settings["paths"]
            direction = settings["direction"]
            spacing = settings["spacing"]
            preview = settings["preview"]

            if len(paths) < 2:
                QMessageBox.warning(self, "Combine Images", "Please select at least two images.")
                return

            images = [cv2.imread(p) for p in paths if cv2.imread(p) is not None]
            if not images:
                QMessageBox.warning(self, "Error", "No valid images found.")
                return

            # Resize all to the same height/width depending on direction
            if direction == "Horizontal":
                min_height = min(img.shape[0] for img in images)
                resized = [cv2.resize(img, (int(img.shape[1] * min_height / img.shape[0]), min_height)) for img in images]
            else:
                min_width = min(img.shape[1] for img in images)
                resized = [cv2.resize(img, (min_width, int(img.shape[0] * min_width / img.shape[1]))) for img in images]

            # Apply spacing
            if spacing > 0:
                spacer = np.ones((min_height, spacing, 3), dtype=np.uint8) * 255 if direction == "Horizontal" else np.ones((spacing, min_width, 3), dtype=np.uint8) * 255
                stitched = resized[0]
                for img in resized[1:]:
                    if direction == "Horizontal":
                        stitched = np.hstack((stitched, spacer, img))
                    else:
                        stitched = np.vstack((stitched, spacer, img))
            else:
                stitched = np.hstack(resized) if direction == "Horizontal" else np.vstack(resized)

            if preview:
                self.preview_image = stitched.copy()
                self.update_image_display_preview(stitched)
                reply = QMessageBox.question(self, "Preview", "Apply this combined image?",
                                            QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    self.update_image_display()
                    return

            self.create_empty_canvas()
            layer = self.get_current_focus_layer()
            layer.set_image(stitched)
            self.display_current_image()


#/layer
    def insert_text_tool(self, _text=None):
        if self.display_image is None: return
        self.dialog_open = True

        dialog = TextInsertDialog(self, _text)
        if dialog.exec_() == QDialog.Accepted:
            vals = dialog.get_values()
            text = vals["text"]
            font_scale = vals["font_scale"]
            thickness = vals["thickness"]
            color = (*vals["color"], 255)
            
            img = self.current_focus_layer_image()
            self.push_undo_state()

            ## Disabled selection mode
            if self.image_label.select_mode:
                self.enable_selection_mode()
                
                
            current_focus = self.get_focus_window()
            def preview_handler(event):
                current_focus.image_label.set_text_preview(
                    True, text, event.pos(), color, font_scale, thickness
                )

            def apply_handler(event):
                if event.button() == Qt.RightButton:
                    self.text_cancel(img)
                    return
                if event.button() != Qt.LeftButton: return
                
                self.apply_text_on_click(event, img, text, font_scale, color, thickness)
        

            # Let user click a point to place text
            current_focus.image_label.setCursor(Qt.CrossCursor)
            current_focus.image_label.mouseMoveEvent = preview_handler
            current_focus.image_label.mousePressEvent = apply_handler
    def draw_text(self, image, text, x, y, scale, color, thickness):
        """
        Draws text using QPainter
        """
        if not image.flags['C_CONTIGUOUS']:
            image = np.ascontiguousarray(image)

        h, w, channels = image.shape
        if channels == 3:
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            fmt = QImage.Format_RGB888
        elif channels == 4:
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            fmt = QImage.Format_RGBA8888
        
        qimg = QImage(
            rgb_img.data, 
            w, h, image.strides[0], fmt
        )
        
        painter = QPainter(qimg)
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        pixel_size = int(scale * 22)
        if pixel_size < 1: pixel_size = 1
        
        font = QFont("Helvetica", pixel_size)
        if thickness > 1:
            font.setBold(True)
            if thickness > 2: font.setWeight(QFont.Black)
            
        painter.setFont(font)
        b,g,r,a = color
        painter.setPen(QPen(QColor(r,g,b,a,)))
        
        painter.drawText(x, y, text)
        painter.end()
        
        ptr = qimg.bits()
        ptr.setsize(h * w * channels)
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, channels))
        
        # 8. Convert back to BGR for OpenCV
        if channels == 4:
            return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        else:
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        
    def apply_text_on_click(self, event, image, text, font_scale, color, thickness):
        if self.display_image is None: return
        self.dialog_open = False

        
        x = event.pos().x()
        y = event.pos().y()

        # Convert from label coordinates to image coordinates
        current_focus = self.get_focus_window()
        x = int((x - current_focus.display_offset[0]) / current_focus.display_scale_x)
        y = int((y - current_focus.display_offset[1]) / current_focus.display_scale_y)

        # Draw text
        img = image.copy()
        
        current_focus = self.get_focus_window()
        if current_focus.selected_rect != (0,0,0,0):
                region = image.copy()
                x1, y1, x2, y2 = self.selected_rect
                
                region = self.draw_text(region, text, x, y, 
                            font_scale, color, thickness
                            )
                img[y1:y2, x1:x2] = region[y1:y2, x1:x2].copy()
        
        else:
            img = self.draw_text(img, text, x, y,
                        font_scale, color, thickness
                        )

        # Update display
        self.current_focus_layer_image(img)
        self.display_current_image()
        
        # Restore normal cursor
        current_il = current_focus.image_label
        current_il.set_text_preview(False)
        
        current_il.setCursor(Qt.ArrowCursor)
        current_il.mousePressEvent = current_il.default_mouse_press
        current_il.mouseMoveEvent = current_il.default_mouse_move
    def text_cancel(self, image):
        self.dialog_open = False
        
        current_focus = self.get_focus_window()
        current_il = current_focus.image_label
        current_il.set_text_preview(False)
        
        self.undo_stack[self.current_index].pop()
        self.current_focus_layer_image(image)
        self.display_current_image()
        
        
        current_il.setCursor(Qt.ArrowCursor)
        current_il.mousePressEvent = current_il.default_mouse_press
        current_il.mouseMoveEvent = current_il.default_mouse_move


#/layer
    def insert_image_tool(self):
        if self.display_image is None: 
            QMessageBox.warning(self, "No Image", "No image to display.")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if not file_path: return
        
        img = cv2.imread(file_path)
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        elif len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            
        self.push_undo_state()
        self.layer_panel.add_new_layer()
        
        for i in self.view_windows:
            if i.on_focus:
                i.image_label.insert_image(img)
                return
        self.image_label.insert_image(img)
            
    def open_barcode_tool(self):
        
        self.set_dialog_open(True)
        
        image = None
        if self.display_image is not None:
            _, layers = self.image_list[self.main_index]
            image = a2.LayerManager.compose_layers(layers)
        
        self.barcode = barcode.BarcodeReader(self, image)
        self.barcode.show()
    def open_qrcode_tool(self):
        
        self.set_dialog_open(True)
        
        window = qrcode.QRScannerApp(self)
        window.show()
    
    
    
    def update_button_menu(self):
    ## Check transform mode for all windows
        if self.image_label.transform_mode:
            on_transform = True
        else:
            on_transform = False
            for i in self.view_windows:
                if i.isVisible() and i.image_label.transform_mode:
                    on_transform = True
                    break
    
    ## Check select mode for all windows
        no_selection = True
        if self.get_focus_window().image_label.selection_rect != QRect():
            no_selection = False
        
        
    # -------------------------------------------------------#
    ## None Display image
        non_display_image = self.display_image is None or self.current_index < 0 \
            or on_transform or self.dialog_open
    # Undo Redo
        self.undo_action.setEnabled(not non_display_image)
        self.redo_action.setEnabled(not non_display_image)
        
    ## Save Saveas Close button
        self.save_action.setEnabled(not non_display_image)
        self.save_as_action.setEnabled(not non_display_image)
        self.close_action.setEnabled(not non_display_image)
        
    # Crop Image
        self.crop_image_action.setEnabled(not non_display_image)
        
    # Image Menu
        self.image_size_action.setEnabled(not non_display_image)
        self.image_position_action.setEnabled(not non_display_image)
        self.image_rotate_action.setEnabled(not non_display_image)
        self.image_expand_action.setEnabled(not non_display_image)
        self.free_transform_action.setEnabled(not non_display_image)
        self.flip_h_action.setEnabled(not non_display_image)
        self.flip_v_action.setEnabled(not non_display_image)
        self.rotate_ccw_action.setEnabled(not non_display_image)
        self.rotate_cw_action.setEnabled(not non_display_image)
        self.image_detail_action.setEnabled(not non_display_image)
        
    # Select button
        self.select_action.setEnabled(not non_display_image)
        self.select_all_action.setEnabled(not non_display_image)
        self.color_convert_action.setEnabled(not non_display_image)
        self.color_negative_action.setEnabled(not non_display_image)
        self.color_inverse_action.setEnabled(not non_display_image)
        self.color_adjust_action.setEnabled(not non_display_image)
        self.color_intensity_adjust_action.setEnabled(not non_display_image)
        
    # View button
        self.view_window_action.setEnabled(not non_display_image)
        self.view_zoom_in_action.setEnabled(not non_display_image)
        self.view_zoom_out_action.setEnabled(not non_display_image)
        self.view_zoom_reset_action.setEnabled(not non_display_image)
        self.view_position_reset_action.setEnabled(not non_display_image)
        
    # Tool button
        self.text_action.setEnabled(not non_display_image)
        self.insert_img_action.setEnabled(not non_display_image)
        self.matplotlib_action.setEnabled(not non_display_image)
        
    # Filter Conteol Panel button
        self.edge_detection_action.setEnabled(not non_display_image)
        self.thresholding_action.setEnabled(not non_display_image)
        self.power_law_action.setEnabled(not non_display_image)
        self.piecewise_action.setEnabled(not non_display_image)
        self.morphology_action.setEnabled(not non_display_image)
        self.histogram_action.setEnabled(not non_display_image)
        self.bit_plane_action.setEnabled(not non_display_image)
        
    # Filter button
        self.blur_filter_action.setEnabled(not non_display_image)
        self.blur_more_filter_action.setEnabled(not non_display_image)
        self.blur_gaussian_filter_action.setEnabled(not non_display_image)
        self.blur_motion_filter_action.setEnabled(not non_display_image)
        self.blur_radial_filter_action.setEnabled(not non_display_image)
        
        self.sharpen_filter_action.setEnabled(not non_display_image)
        self.sharpen_edge_filter_action.setEnabled(not non_display_image)
        self.sharpen_usm_filter_action.setEnabled(not non_display_image)
        
        self.noise_add_filter_action.setEnabled(not non_display_image)
        self.noise_remove_filter_action.setEnabled(not non_display_image)
        self.median_filter_action.setEnabled(not non_display_image)
        
        self.diffuse_filter_action.setEnabled(not non_display_image)
        self.solarize_filter_action.setEnabled(not non_display_image)
        
        self.edge_enhance_filter_action.setEnabled(not non_display_image)
        self.beauty_filter_action.setEnabled(not non_display_image)
        
    # Layer
        self.new_layer_action.setEnabled(not non_display_image)
        self.copy_layer_action.setEnabled(not non_display_image)
        self.delete_layer_action.setEnabled(not non_display_image)
        self.clear_layer_action.setEnabled(not non_display_image)
        self.write_down_action.setEnabled(not non_display_image)
        self.merge_down_action.setEnabled(not non_display_image)
        self.merge_all_action.setEnabled(not non_display_image)
        self.merge_all_visible_action.setEnabled(not non_display_image)
        
        self.layer_flip_h_action.setEnabled(not non_display_image)
        self.layer_flip_v_action.setEnabled(not non_display_image)
        self.layer_rotate_180_action.setEnabled(not non_display_image)
        self.layer_rotate_ccw_action.setEnabled(not non_display_image)
        self.layer_rotate_cw_action.setEnabled(not non_display_image)
        
        self.layer_to_front_action.setEnabled(not non_display_image)
        self.layer_to_down_action.setEnabled(not non_display_image)
        self.layer_to_top_action.setEnabled(not non_display_image)
        self.layer_to_bottom_action.setEnabled(not non_display_image)
        self.layer_rename_action.setEnabled(not non_display_image)
        
    # QR/ Barcode
        self.barcode_action.setEnabled(not non_display_image)
        self.qrcode_action.setEnabled(not non_display_image)
            
            
    # -------------------------------------------------------#
    ## None Selected Area
        non_selected_area = no_selection or on_transform or self.dialog_open
    ## Copy Paste button
        self.copy_action.setEnabled(not non_selected_area)
        self.cut_action.setEnabled(not non_selected_area)
        self.cropping_action.setEnabled(not non_selected_area)
        
    # Select button
        self.select_cancel_action.setEnabled(not non_selected_area)
        
        
        
    # -------------------------------------------------------#
    ## Paste button
        if self.display_image is None or self.current_index < 0 or\
            on_transform or self.dialog_open:
                
            self.paste_action.setEnabled(False)
            self.load_clipboard_action.setEnabled(False)
        else:
            if self.image_label.copied_image is None and not QApplication.clipboard().mimeData().hasImage():
                self.paste_action.setEnabled(False)
                self.load_clipboard_action.setEnabled(False)
            else: 
                self.paste_action.setEnabled(True)
                self.load_clipboard_action.setEnabled(True)
        
    ## Undo Redo button
        if self.display_image is None or self.current_index < 0 or\
            on_transform or self.dialog_open: 
                
            self.undo_action.setEnabled(False)
        elif len(self.undo_stack[self.current_index]) == 0:
            self.undo_action.setEnabled(False)
        else: 
            self.undo_action.setEnabled(True)

        if self.display_image is None or self.current_index < 0 or\
            on_transform or self.dialog_open: 
                
            self.redo_action.setEnabled(False)
        elif len(self.redo_stack[self.current_index]) == 0:
            self.redo_action.setEnabled(False)
        else: 
            self.redo_action.setEnabled(True)
        
    # -------------------------------------------------------#
    ## Next Previous view button
        if len(self.image_list) < 2 or on_transform or self.dialog_open:
            self.next_canvas_action.setEnabled(False)
            self.previous_canvas_action.setEnabled(False)
        else:
            self.next_canvas_action.setEnabled(True)
            self.previous_canvas_action.setEnabled(True)
            
            
    # -------------------------------------------------------#
    ## Open New button
        if on_transform or self.dialog_open:
            self.new_action.setEnabled(False)
            self.load_action.setEnabled(False)
            
            self.combine_img_action.setEnabled(False)
        else:
            self.new_action.setEnabled(True)
            self.load_action.setEnabled(True)
            
            self.combine_img_action.setEnabled(True)
            
    
    # -------------------------------------------------------#
    ## Layer
        if self.layer_panel is not None:
            has_multi_layer = len(self.layer_panel.layers) > 1 
            layer_len = len(self.layer_panel.layers) 
            layer_idx = self.layer_panel.active_layer_index 
        else:
            has_multi_layer = False
            layer_idx = 0
            layer_len = 1
        
        self.write_down_action.setEnabled(has_multi_layer)
        self.merge_down_action.setEnabled(has_multi_layer)
        self.merge_all_action.setEnabled(has_multi_layer)
        self.merge_all_visible_action.setEnabled(has_multi_layer)
        self.delete_layer_action.setEnabled(has_multi_layer)
        
        self.layer_to_front_action.setEnabled(layer_idx != (layer_len-1))
        self.layer_to_top_action.setEnabled(layer_idx != (layer_len-1))
        self.layer_to_down_action.setEnabled(layer_idx > 0)
        self.layer_to_bottom_action.setEnabled(layer_idx > 0)
        
            
        
        
        
        
# --------------------------------------------------------------------------------
    
    def keyPressEvent(self, event):
    ## Free Transform key
        # Accept
        if event.key() == Qt.Key_Return:
            if self.image_label.transform_mode:
                self.image_label.apply_free_transform(cancel=False)
            else:
                for i in self.view_windows:
                    if i.image_label.transform_mode:
                        i.image_label.apply_free_transform(cancel=False)
                        return
        # Reject
        if event.key() == Qt.Key_Escape:
            if self.image_label.transform_mode:
                self.image_label.apply_free_transform(cancel=True)
            else:
                for i in self.view_windows:
                    if i.image_label.transform_mode:
                        i.image_label.apply_free_transform(cancel=True)
                        return
    
    ## Move tool key
        if event.key() == Qt.Key_Space and not self.image_label.move_mode:
            if not self.image_label.mouse_pressing: 
                self.release_cancel_move_mode = True
                self.image_label.enable_moving(True)
        
    ## Update square aspect ratio 
        if event.key() == Qt.Key_Shift:
            self.image_label.update()
        
    def keyReleaseEvent(self, event):
    ## Move tool key
        if event.key() == Qt.Key_Space and self.release_cancel_move_mode and self.image_label.move_mode:
            if self.image_label.mouse_pressing: return
            
            self.release_cancel_move_mode = False
            self.image_label.enable_moving(False)
        
    ## Update square aspect ratio 
        if event.key() == Qt.Key_Shift:
            self.image_label.update()
    
    

# --------------------------------------------------------------------------------
    def close_application(self):
        """Closes the application."""
        QApplication.instance().quit()
        


# --------------------------------------------------------------------------------
#/layer
### Window for create new canvas
class NewCanvasDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create New Canvas")
        self.setFixedSize(320, 140)

        layout = QFormLayout()

        # Template size 
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Square (1024x1024)", "Square Small (512x512)", 
            "A4 (2480x3508)", "A5 (1748x2480)", "Custom"
        ])
        layout.addRow("Template:", self.template_combo)

        # Width and Height inputs
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()
        self.width_input.setPlaceholderText("Width (px)")
        self.height_input.setPlaceholderText("Height (px)")
        layout.addRow("Width:", self.width_input)
        layout.addRow("Height:", self.height_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

        self.setLayout(layout)

        self.template_combo.currentIndexChanged.connect(self.set_template_size)
        self.set_template_size(0)

    def set_template_size(self, index):
        if index == 0:  # Square
            self.width_input.setText("1024")
            self.height_input.setText("1024")
        elif index == 1:  # Square Small
            self.width_input.setText("512")
            self.height_input.setText("512")
        if index == 2:  # A4
            self.width_input.setText("2480")
            self.height_input.setText("3508")
        elif index == 3:  # A5
            self.width_input.setText("1748")
            self.height_input.setText("2480")
        elif index == 4:  # Custom
            pass
        
    def get_size(self):
        width = int(self.width_input.text())
        height = int(self.height_input.text())
        return width, height


# --------------------------------------------------------------------------------
#/layer
### Window for scale image
class ScaleImageDialog(QDialog):
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
### Window for expand image
class ExpandCanvasDialog(QDialog):
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
### Window for translate image
class TranslateDialog(QDialog):
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
### Window for image details
class ImageDetailsDialog(QDialog):
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
### Window for crop image
class CropDialog(QDialog):
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



# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
#/layer
### Label for Paint Tool, Select, Paint Bucket Tool
class SelectLabel(QLabel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mouse_pressing = False
        self.default_mouse_press = self.mousePressEvent
        self.default_mouse_move = self.mouseMoveEvent
    ## Select tool
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.selection_rect = QRect()
        self.select_mode = False
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #808080; border: 1px solid #404040;")
        
        self.display_scale = 1.0
        self.last_display_scale = 1.0
        self.display_offset = (0, 0)
        self.image_size = None
        
    ## Move tool
        self.move_mode = False
        self.last_mouse_pos = None
    ## Paint tool
        self.draw_mode = True
        self.draw_type = "pen"
        self.pen_path = []
        self.pen_color = parent.pen_color
        self.pen_thickness = parent.pen_thickness
    ## Line drawing
        self.line_start_point = None
        self.line_end_point = None
    ## Erase drawing
        self.erase_last_point = None
    ## Shape drawing
        self.shape_start_point = None
        self.shape_end_point = None
        self.temp_shape_preview = None
    ## Paint Bucket tool
        self.bucket_tolerance = 35
        
    ## Free Transform tool
        self.transform_mode = False
        self.original_image = None
        self.handle_size = 18
        self.transform_buffer = None
        
        self.drag_start = False
        self.drag_start_point = QPoint()
        self.handle_list = []
        self.handle_list_default = []
        self.dragging_corner = None
        self.dragging_corner_index = -1
        self.drag_offset = QPoint()
        
        self.bounding_box = QRect()
        self.aspect_ratio = 1.0
    
    ## Copy Cut Paste
        self.copied_image = None
        self.copied_rect = (0, 0, 0, 0)
        self.copied_aspect_ratio = 1.0
    
    ## Grid and rulers
        self.show_grid = False
        self.grid_size = parent.grid_size
        self.grid_thickness = parent.grid_thickness
        self.grid_color = parent.grid_color
        
        self.show_ruler = True
        self.ruler_thickness = parent.ruler_thickness
        self.ruler_grid = parent.ruler_grid
        self.ruler_background = QColor(45, 45, 45)
        self.ruler_text_color = QColor(220, 220, 220)
        
    # Text insert
        self.show_text_preview = False
        self.text_content = ""
        self.text_pos = None 
        self.text_color = (0, 0, 0, 0)
        self.text_font_scale = 1.0
        self.text_thickness = 1
        
    
    def enable_selection(self, enable=True):
        """Enable or disable mouse selection mode."""
        self.select_mode = enable
        
        if enable:
            self.setCursor(Qt.CrossCursor)
            self.move_mode = False
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()
    def enable_drawing(self, enable=True, draw_type="line"):
        """Enable or disable pen drawing mode."""
        self.draw_mode = enable
        self.draw_type = draw_type
        self.select_mode = False
        
        self.update()
        if enable:
            self.setCursor(Qt.CrossCursor)
            self.move_mode = False
        else:
            self.setCursor(Qt.ArrowCursor)
    def enable_moving(self, enable=True):
        self.move_mode = enable
        
        if enable:
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    def enable_transform(self, enable=True):
        
        self.parent.push_undo_state()
        x1, y1, x2, y2 = self.parent.selected_rect

        current_layer = self.parent.get_current_focus_layer()
        full_img = current_layer.image.copy()
        self.transform_buffer = full_img[y1:y2, x1:x2].copy()
        self.original_image = full_img.copy()
        
        # Left empty transparent
        full_img[y1:y2, x1:x2] = 0
        
        current_layer.set_image(full_img)
        self.parent.display_current_image()
        
        
        # Store bounding box with selected area
        self.bounding_box = QRect(QPoint(x1, y1), QPoint(x2, y2))
        self.handle_list = [
            QPoint(x1, y1),
            QPoint(x2, y1),
            QPoint(x1, y2),
            QPoint(x2, y2),
        ]
        self.aspect_ratio = (x2-x1) / (y2-y1)
        
        self.transform_mode = enable
        self.update()
    def set_text_preview(self, active, text="", pos=None, color=(0,0,0), scale=1.0, thickness=1):
        self.show_text_preview = active
        self.text_content = text
        self.text_pos = pos
        self.text_color = color
        self.text_font_scale = scale
        self.text_thickness = thickness
        self.update() 
    
    
    def mousePressEvent(self, event):
        if not event.button() == Qt.LeftButton: return
        if self.parent.current_index == -1: return
        self.mouse_pressing = True
        
    ## Set current focus image
        self.parent.set_current_index_focus()
        
    ## Moving Mode
        if self.move_mode or self.parent.dialog_open:
            self.setCursor(Qt.ClosedHandCursor)
            self.last_mouse_pos = event.pos()
    
    ## Free Transform Mode
        elif self.transform_mode:
            self.drag_start = True
            pos = event.pos()
            
            # Check which corner handle clicked
            for i, pt in enumerate(self.handle_list):
                scale = self.parent.display_scale_x
                ox, oy = self.parent.display_offset
                screen_x = int(pt.x() * scale + ox)
                screen_y = int(pt.y() * scale + oy)

                if abs(pos.x() - screen_x) < self.handle_size and abs(pos.y() - screen_y) < self.handle_size:
                    self.dragging_corner_index = i
                    
                    width = self.handle_list[3].x() - self.handle_list[0].x()
                    height = self.handle_list[3].y() - self.handle_list[0].y()
                    self.aspect_ratio = abs(width / height)
                    return

            # else begin moving entire box
            self.dragging_corner_index = -1
            self.drag_offset = event.pos()
            self.drag_start_point = event.pos()
            self.handle_list_default = copy.deepcopy(self.handle_list)
    
    
    ## Select Area Mode
        elif self.select_mode:
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.selecting = True
    
    ## Drawing Mode
        elif self.draw_mode:
            self.parent.push_undo_state()
            
            match self.draw_type:
                case "pen": 
                    self.pen_last_point = event.pos()
                    self.pen_path = [event.pos()]
                case "line":
                    self.line_start_point = event.pos()
                    self.line_end_point = event.pos()
                case "ereaser":
                    self.pen_last_point = event.pos()
                    self.pen_path = [event.pos()]
                case "circle"| "triangle"| "rectangle":
                    self.temp_preview = self.parent.current_focus_layer_image()
                    self.parent.original_image = self.temp_preview
                    self.shape_start_point = event.pos()
                    self.shape_end_point = event.pos()
                case "paint bucket":
                    x = event.pos().x()
                    y = event.pos().y()
                    self.on_paint_bucket_click(x, y)
                
        self.update()
        super().mousePressEvent(event)   
        

    def mouseMoveEvent(self, event):
        if self.parent.current_index == -1: return
    ## Moving Mode
        if self.move_mode or self.parent.dialog_open:
            if self.parent.display_image is None: return
            if self.last_mouse_pos is None: return
            
            dx = event.x() - self.last_mouse_pos.x()
            dy = event.y() - self.last_mouse_pos.y()
            self.last_mouse_pos = event.pos()
            self.display_offset = (dx, dy)
            
            self.parent.move_diff_pos = QPoint(dx, dy)
            self.parent.update_image_display()

    ## Free Transform Mode
        elif self.transform_mode:
            if not self.drag_start: return
            
            x = event.pos().x()
            y = event.pos().y()
            
            # Convert back to image coords
            ox, oy = self.parent.display_offset
            sx, sy = self.parent.display_scale_x, self.parent.display_scale_y
            ix = int((x - ox) / sx)
            iy = int((y - oy) / sy)
            
            
            # Resize (dragging corners)
            if self.dragging_corner_index >= 0:
                ## Keep aspect ration if pressed shift
                new_x, new_y = ix, iy
                if keyboard.is_pressed("shift"):
                    opposite_index = self.dragging_corner_index ^ 3
                    opposite_point = self.handle_list[opposite_index]
                    
                    dx = ix - opposite_point.x()
                    dy = iy - opposite_point.y()
                    ## Follow mouse horizontally if aspect ration landscape
                    if self.aspect_ratio > 1: 
                        new_h = int(abs(dx) / self.aspect_ratio)
                        new_y = opposite_point.y() + np.sign(dy if dy != 0 else dx) * new_h
                        
                    ## Follow mouse vertically if aspect ration portrait
                    else: 
                        new_w = int(abs(dy) * self.aspect_ratio)
                        new_x = opposite_point.x() + np.sign(dx if dx != 0 else dy) * new_w
                    
                
                ## Update moving corner point
                x1, x2 = self.bounding_box.left(), self.bounding_box.right()
                y1, y2 = self.bounding_box.top(), self.bounding_box.bottom()
                match self.dragging_corner_index:
                    case 0:
                        x1, y1 = new_x, new_y
                    case 1:
                        x2, y1 = new_x, new_y
                    case 2:
                        x1, y2 = new_x, new_y
                    case 3:
                        x2, y2 = new_x, new_y
                    
                self.bounding_box = QRect(QPoint(x1, y1),
                                    QPoint(x2, y2))
                self.handle_list = [
                    QPoint(x1, y1),
                    QPoint(x2, y1),
                    QPoint(x1, y2),
                    QPoint(x2, y2),
                ]

                self.update()
                return

            # ------------------------------------------------
            # Move whole area
            new_x, new_y = x, y
            self.drag_offset = event.pos()
            
            if keyboard.is_pressed("shift"):
                if abs(x - self.drag_start_point.x()) > abs(y - self.drag_start_point.y()):
                    new_y = self.drag_start_point.y()
                else:
                    new_x = self.drag_start_point.x()
                
            dx = new_x - self.drag_start_point.x()
            dy = new_y - self.drag_start_point.y()
            scale = self.parent.display_scale_x
            for i, pt in enumerate(self.handle_list):
                ori_pt = self.handle_list_default[i]
                pt.setX(ori_pt.x() + int(dx / scale))
                pt.setY(ori_pt.y() + int(dy / scale))
                
            self.bounding_box = QRect(QPoint(self.handle_list[0]),
                                    QPoint(self.handle_list[3]))

            self.update()
        
    ## Selecting Area Mode
        elif self.select_mode and self.selecting:
            self.end_point = event.pos()
            x1, y1 = self.start_point.x(), self.start_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            
            if keyboard.is_pressed('shift'):
                side_length = min(abs(x2 - x1), abs(y2 - y1))
                if x2 > x1: x2 = x1 + side_length
                else: x2 = x1 - side_length
                
                if y2 > y1: y2 = y1 + side_length
                else: y2 = y1 - side_length
                self.end_point = QPoint(x2, y2)
            
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
        
    ## Drawing Mode    
        elif self.draw_mode:
            
            match self.draw_type:
                case "pen":
                    if len(self.pen_path) > 0:
                        self.pen_path.append(event.pos())
                        self.update()
                    
                case "line":
                    if self.line_start_point:
                        self.line_end_point = event.pos()
                        self.update()
                
                case "ereaser":
                    if len(self.pen_path) > 0:
                        self.pen_path.append(event.pos())
                        self.update()
                
                case "circle"| "triangle"| "rectangle":
                    if self.shape_start_point:
                        self.shape_end_point = event.pos()
                        self.update()
                     
        super().mouseMoveEvent(event)   


    def mouseReleaseEvent(self, event):
        if not event.button() == Qt.LeftButton: return
        if self.parent.current_index == -1: return
        self.mouse_pressing = False
        
    ## Moving complete
        if self.move_mode or self.parent.dialog_open:
            self.setCursor(Qt.OpenHandCursor)
            self.last_mouse_pos = None
            self.parent.move_diff_pos = None
        
    ## Transform
        elif self.transform_mode:
            self.drag_start = False
        
        
    ## Selection complete
        elif self.select_mode and self.start_point:
            self.selecting = False
            # self.end_point = event.pos()
            if self.end_point == self.start_point:
                self.selection_rect = QRect()
                return
            
            # self.display_scale = self.parent.zoom_factor
            self.selection_rect = QRect(self.start_point, self.end_point)

            self.parent.on_selection_made(self.selection_rect)
            self.update()
        
    ## Drawing complete
        elif self.draw_mode:
            
            match self.draw_type:
                case "pen":
                    self.pen_last_point = None
                    self.draw_pen_on_image(self.get_draw_color(self.pen_color))
                    self.pen_path = []
                    
                case "line":
                    self.draw_line_on_image(self.line_start_point, event.pos(), self.pen_color)
                    self.line_start_point = None
                    self.line_end_point = None
                
                case "ereaser":
                    self.pen_last_point = None
                    self.draw_pen_on_image((0, 0, 0, 0))
                    self.pen_path = []
                
                case "circle"| "triangle"| "rectangle":
                    self.shape_end_point = event.pos()
                    self.apply_shape(self.draw_type)
                    self.shape_start_point = None
                    self.shape_end_point = None
                    self.temp_preview = None
        
        
        self.parent.update_button_menu()
        if self.parent.histogram_display is not None:
            self.parent.histogram_display.update_histogram()
        super().mouseReleaseEvent(event)   


    def paintEvent(self, event):
        super().paintEvent(event)
    
    # ------------------------------------------------
    # Select Area Functions
        if self.selection_rect != QRect() and not self.transform_mode:
            painter = QPainter(self)
            pen = QPen(Qt.gray, 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.transparent)
            painter.drawRect(self.selection_rect)
            painter.end()
            
    # ------------------------------------------------  
            
    ## Free Transform Functions
        if self.transform_mode:
            
            x1 = self.handle_list[0].x()
            y1 = self.handle_list[0].y()
            x2 = self.handle_list[3].x()
            y2 = self.handle_list[3].y()
            
            image = self.transform_buffer.copy()
            dest_w = x2 - x1
            dest_h = y2 - y1
            
            # Horizontal Flip check
            if dest_w < 0:
                image = cv2.flip(image, 1) # Flip Horizontal
                dest_w = abs(dest_w)
                draw_x = x2
            else: draw_x = x1
            # Vertical Flip check
            if dest_h < 0:
                image = cv2.flip(image, 0)
                dest_h = abs(dest_h)
                draw_y = y2
            else: draw_y = y1
            
            
            resized_preview = cv2.resize(image, (dest_w, dest_h), interpolation=cv2.INTER_LINEAR)

            # Convert to QImage for Qt Drawing
            h, w, ch = resized_preview.shape
            bytes_per_line = ch * w
            rgb_data = cv2.cvtColor(resized_preview, cv2.COLOR_BGRA2RGBA)
            q_img = QImage(
                rgb_data.data, 
                w, h, bytes_per_line, 
                QImage.Format_RGBA8888
            )
            
            ## Calculate Screen coordinat
            sx = self.parent.display_scale_x
            sy = self.parent.display_scale_y
            ox, oy = self.parent.display_offset
            
            screen_x = int(draw_x * sx + ox)
            screen_y = int(draw_y * sy + oy)
            screen_w = int(dest_w * sx)
            screen_h = int(dest_h * sy)
            
            painter = QPainter(self)
            # painter.setOpacity(0.7) 
            painter.drawImage(
                QRect(screen_x, screen_y, screen_w, screen_h), 
                q_img
            )
            
            # Draw the bordering box
            painter.setPen(QPen(Qt.blue, 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(screen_x, screen_y, screen_w, screen_h)
            
            painter.setBrush(Qt.transparent)
            painter.setPen(Qt.black)
            for pt in self.handle_list:
                px = int(pt.x() * sx + ox)
                py = int(pt.y() * sy + oy)
                painter.drawRect(px - 6, py - 6, 12, 12)
                
            painter.end()
            

        
        elif self.show_text_preview:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            zoom = self.parent.display_scale_x
            pixel_size = int(self.text_font_scale * 22 * zoom)
            if pixel_size < 1: pixel_size = 1
            
            font = QFont("Helvetica", pixel_size)
            if self.text_thickness > 1:
                font.setBold(True)
                if self.text_thickness > 2: font.setWeight(QFont.Black)
                
            painter.setFont(font)
            
            # Convert BGR to RGB
            b, g, r, a = self.text_color
            layer   = self.parent.get_current_focus_layer()
            if layer is None: a = 255
            else: a = int(layer.opacity * 255)
            
            pen = QPen(QColor(r, g, b, a))
            painter.setPen(pen)
            painter.setBrush(Qt.transparent)
            
            if self.text_pos is not None:
                painter.drawText(self.text_pos, self.text_content)
            painter.end()
    
    # ------------------------------------------------
    ## Drawing 
        elif self.draw_mode:
            match self.draw_type:
                
                case "pen":
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    
                    # Use the same color/thickness as the tool
                    b,g,r   = self.pen_color
                    layer   = self.parent.get_current_focus_layer()
                    if layer is None: return
                    if layer is None: a = 255
                    else: a = int(layer.opacity * 255)
                    
                    pen = QPen(QColor(r,g,b,a), 
                                max(1,round(self.pen_thickness)) * self.parent.display_scale_x, 
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    painter.setPen(pen)
                    painter.setBrush(Qt.transparent)
                        
                    # Draw the list of points
                    if len(self.pen_path) > 0:
                        poly_path = QPolygonF(self.pen_path)
                        painter.drawPolyline(poly_path)
                    painter.end()
                
                case "line":
                    painter = QPainter(self)
                    
                    b,g,r   = self.pen_color
                    layer   = self.parent.get_current_focus_layer()
                    if layer is None: a = 255
                    else: a = int(layer.opacity * 255)
                    
                    pen = QPen(QColor(r,g,b, a), 
                            max(1,round(self.pen_thickness)) * self.parent.display_scale_x, 
                            Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                            )
                    painter.setPen(pen)
                    if not (self.line_start_point is None or self.line_end_point is None):
                        p1 = self.line_start_point
                        p2 = self.line_end_point
                        
                        # Draw vertical or horizontal
                        if keyboard.is_pressed('shift'):
                            dx = abs(p2.x() - p1.x())
                            dy = abs(p2.y() - p1.y())
                            if dx > dy:
                                p2 = QPoint(p2.x(), p1.y()) 
                            else:
                                p2 = QPoint(p1.x(), p2.y()) 
                        
                        painter.setBrush(Qt.transparent)
                        painter.drawLine(p1, p2)
                    painter.end()
    
                case "ereaser":
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    
                    # Use the same color/thickness as the tool
                    b,g,r,a   = 200, 200, 200, 155
                    
                    pen = QPen(QColor(r,g,b,a), 
                                max(1,round(self.pen_thickness)) * self.parent.display_scale_x, 
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                    painter.setPen(pen)
                    painter.setBrush(Qt.transparent)
                        
                    # Draw the list of points
                    if len(self.pen_path) > 0:
                        poly_path = QPolygonF(self.pen_path)
                        painter.drawPolyline(poly_path)
                    painter.end()
    
                case "circle"| "triangle"| "rectangle":
                    
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing, True)

                    if not (self.shape_start_point is None or self.shape_end_point is None):
                        p1 = self.shape_start_point
                        p2 = self.shape_end_point
                        
                        x, y = p1.x(), p1.y()
                        w = p2.x() - p1.x()
                        h = p2.y() - p1.y()
                        
                        # Keep Square aspect ratio
                        if keyboard.is_pressed('shift'):
                            side = min(abs(w), abs(h))
                            w = side if w > 0 else -side
                            h = side if h > 0 else -side
                        
                        # Get pen color
                        b, g, r = self.pen_color
                        layer   = self.parent.get_current_focus_layer()
                        if layer is None: a = 255
                        else: a = int(layer.opacity * 255)
                        
                        
                        pen = QPen(QColor(r, g, b, a), 
                                self.pen_thickness * self.parent.display_scale_x, 
                                Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                        painter.setPen(pen)
                        painter.setBrush(Qt.NoBrush)
                    
                        match self.draw_type:
                            case "rectangle":
                                painter.drawRect(x, y, w, h)
                                
                            case "circle":
                                painter.drawEllipse(x, y, w, h)
                                
                            case "triangle":
                                p_top = QPointF(x + w/2, y)
                                p_bottom_left = QPointF(x, y + h)
                                p_bottom_right = QPointF(x + w, y + h)
                                
                                points = [p_bottom_left, p_top, p_bottom_right]
                                painter.drawPolygon(QPolygonF(points))

                    painter.end()
                    
        
    
    ## On Top Area
    # ------------------------------------------------
    ## Rule and Grid Lines
        # Grid Lines
        if self.show_grid:
            grid_painter = QPainter(self)
            grid_painter.setRenderHint(QPainter.Antialiasing, False)
            grid_painter.setPen(QPen(self.grid_color, self.grid_thickness, Qt.SolidLine))

            sx = self.parent.display_scale_x
            ox, oy = self.parent.display_offset
            if self.parent.current_index >= 0:
                img = self.parent.display_image
                h, w = img.shape[:2]

                # vertical grid lines
                x = 0
                while x <= w:
                    px = int(x * sx + ox)
                    grid_painter.drawLine(px, 0, px, self.height())
                    x += self.grid_size

                # horizontal grid lines
                y = 0
                while y <= h:
                    py = int(y * sx + oy)
                    grid_painter.drawLine(0, py, self.width(), py)
                    y += self.grid_size
            
            grid_painter.end()
        
        # Rule Lines
        if self.show_ruler:
            ruler_painter = QPainter(self)
            ruler_painter.setRenderHint(QPainter.Antialiasing, False)
            scale = self.parent.display_scale_x
            ox, oy = self.parent.display_offset
            
            if self.parent.current_index >= 0 and self.parent.display_image is not None:
                img = self.parent.display_image
                h, w = img.shape[:2]

                ruler_painter.fillRect(0, 0, self.width(), self.ruler_thickness, self.ruler_background)
                ruler_painter.fillRect(0, 0, self.ruler_thickness, self.height(), self.ruler_background)

                # Draw ticks & numbers
                ruler_painter.setPen(self.ruler_text_color)

                xstep = max(2, int((w/self.ruler_grid) * scale))
                ystep = max(2, int((h/self.ruler_grid) * scale))
                # Horizontal ticks (top ruler)
                x = 0
                while x <= w:
                    px = int(x * scale + ox)
                    if self.ruler_thickness <= px <= self.width():
                        ruler_painter.drawLine(px, 0, px, self.ruler_thickness)
                        ruler_painter.drawText(px + 2, self.ruler_thickness - 4, str(int(x)))
                    x += w / xstep

                # Vertical ticks (left ruler)
                y = 0
                while y <= h:
                    py = int(y * scale + oy)
                    if self.ruler_thickness <= py <= self.height():
                        ruler_painter.drawLine(0, py, self.ruler_thickness, py)
                        ruler_painter.drawText(2, py - 2, str(int(y)))
                    y += h / ystep
                ruler_painter.end()

        
     
    

## Select Area Functions
    def update_selected_rect(self):
        if self.selection_rect == QRect(): return
        
        x1, y1, x2, y2 = self.parent.selected_rect 
        scale_x = self.parent.display_scale_x
        scale_y = self.parent.display_scale_y
        offset_x, offset_y = self.parent.display_offset

        display_x1 = int(x1 * scale_x + offset_x)
        display_y1 = int(y1 * scale_y + offset_y)
        display_x2 = int(x2 * scale_x + offset_x)
        display_y2 = int(y2 * scale_y + offset_y)

        self.selection_rect = QRect(QPoint(display_x1, display_y1), QPoint(display_x2, display_y2))
        self.update()
    
## Pen and Line drawing functions
    def get_draw_color(self, base_color):
        if len(base_color) == 3:
            return (*base_color, 255) 
        return base_color
    
    def draw_pen_on_image(self, color):
        scale = self.parent.display_scale_x
        offset_x, offset_y = self.parent.display_offset
        thickness = max(1, round(self.pen_thickness))
        
        pts = []
        for p in self.pen_path:
            ix = int((p.x() - offset_x) / scale)
            iy = int((p.y() - offset_y) / scale)
            pts.append([ix, iy])
        
        points_array = np.array(pts, np.int32)
        points_array = points_array.reshape((-1, 1, 2))
        
        
        image = self.parent.current_focus_layer_image()
        if image is None: return

        # 3. Apply to Image (Handle Selection Masking)
        if self.selection_rect != QRect():
            # Draw on a temp copy if selection exists
            region_x1, region_y1, region_x2, region_y2 = self.parent.selected_rect
            region = image.copy()
            
            # Draw polyline
            cv2.polylines(region, [points_array], False, color, thickness)
            
            # Paste only the selected area back
            image[region_y1:region_y2, region_x1:region_x2] = \
                region[region_y1:region_y2, region_x1:region_x2].copy()
        else:
            # Draw directly
            cv2.polylines(image, [points_array], False, color, thickness)

        # 4. Finalize update
        self.parent.current_focus_layer_image(image)
        self.parent.display_current_image()
    
    def draw_line_on_image(self, start_pos, end_pos, color):
        if self.parent.display_image is not None:
            scale = self.parent.display_scale_x
            offset_x, offset_y = self.parent.display_offset
            
        # Draw vertical or horizontal
            if keyboard.is_pressed('shift'):
                dx = abs(end_pos.x() - start_pos.x())
                dy = abs(end_pos.y() - start_pos.y())
                
                if dx > dy:
                    end_pos.setY(start_pos.y()) # Horizontal
                else:
                    end_pos.setX(start_pos.x()) # Vertical
            
        # Calculate coordinat point in canvas
            x1 = int((start_pos.x() - offset_x) / scale)
            y1 = int((start_pos.y() - offset_y) / scale)
            x2 = int((end_pos.x() - offset_x) / scale)
            y2 = int((end_pos.y() - offset_y) / scale)

            thickness = max(1, round(self.pen_thickness))
            color_bgra = self.get_draw_color(color)
            image = self.parent.current_focus_layer_image().copy()
            if image is None: return

            # Draw the line directly on selected area
            if self.selection_rect != QRect():
                region_x1, region_y1, region_x2, region_y2 = self.parent.selected_rect
                region = image.copy()
                
                cv2.line(region, (x1, y1), (x2, y2), color_bgra, thickness)
                image[region_y1:region_y2, region_x1:region_x2] = \
                    region[region_y1:region_y2, region_x1:region_x2].copy()
                
            else:
                # Draw the line directly on the image
                cv2.line(image, (x1, y1), (x2, y2), color_bgra, thickness)

            self.parent.current_focus_layer_image(image)
            self.parent.display_current_image()
            self.update()
    
## Shape drawing functions
    def apply_shape(self, shape_type):
        if self.parent.display_image is None: return

        current_layer = self.parent.get_current_focus_layer()
        if current_layer is None: return
        img = current_layer.image.copy()
        
        # Calculate point on layer  
        sx, sy    = self.parent.display_scale_x, self.parent.display_scale_y
        ox, oy    = self.parent.display_offset
        x1, y1    = int((self.shape_start_point.x() - ox) / sx), int((self.shape_start_point.y() - oy) / sy)
        x2, y2    = int((self.shape_end_point.x() - ox) / sx), int((self.shape_end_point.y() - oy) / sy)

        color     = self.get_draw_color(self.pen_color)
        thickness = max(1, round(self.pen_thickness))
        
        
        ## Fit the length of width and height of the shape
        if keyboard.is_pressed('shift'): 
            side_length = min(abs(x2 - x1), abs(y2 - y1))
            if x2 > x1: x2 = x1 + side_length
            else: x2 = x1 - side_length
            
            if y2 > y1: y2 = y1 + side_length
            else: y2 = y1 - side_length

        region = img.copy()
        match shape_type:
            case "rectangle":
                cv2.rectangle(region, (x1, y1), (x2, y2), color, thickness)

            case "circle":
                # Calculate center
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                
                axis_x = abs(x2 - x1) // 2
                axis_y = abs(y2 - y1) // 2
                
                cv2.ellipse(region, (cx, cy), (axis_x, axis_y), 0, 0, 360, color, thickness)
            
            case "triangle":
                pts = np.array([[x1, y2], [int((x1 + x2) / 2), y1], [x2, y2]], np.int32)
                cv2.polylines(region, [pts], isClosed=True, color=color, thickness=thickness)
    
        if self.parent.selected_rect != (0,0,0,0):
            region_x1, region_y1, region_x2, region_y2 = self.parent.selected_rect
            img[region_y1:region_y2, region_x1:region_x2] = region[region_y1:region_y2, region_x1:region_x2]
        else:
            img = region
    
    
        self.parent.current_focus_layer_image(img)
        self.parent.display_current_image()

## Paint Bucket Functions
    def on_paint_bucket_click(self, x, y):
        if self.parent.display_image is None: return

        current_layer = self.parent.get_current_focus_layer()
        if current_layer is None: return
        # Convert click coords to image coords
        img_h, img_w = current_layer.image.shape[:2]
        
        scale_x, scale_y = self.parent.display_scale_x, self.parent.display_scale_y
        offset_x, offset_y = self.parent.display_offset
        
        img_x = int((x - offset_x) / scale_x)
        img_y = int((y - offset_y) / scale_y)

        if not (0 <= img_x < img_w and 0 <= img_y < img_h):
            return

        color = self.pen_color
        mask = np.zeros((img_h + 2, img_w + 2), np.uint8)
        img = current_layer.image.copy()
        b, g, r, a = cv2.split(img)
        bgr_image = cv2.merge([b, g, r])
        
        # For transparent BG issue
        seed_alpha = a[img_y, img_x]
        mask_view = mask[1:-1, 1:-1]
        if seed_alpha == 0:
            mask_view[a > 0] = 1
        else:
            mask_view[a == 0] = 2
        
        
        cv2.floodFill(
            bgr_image, mask, (img_x, img_y), color, (self.bucket_tolerance,) * 3,
            (self.bucket_tolerance,) * 3, flags=cv2.FLOODFILL_FIXED_RANGE
        )
        
        
        fill_mask = mask[1:-1, 1:-1]
        a[fill_mask == 1] = 255
        result = cv2.merge([*cv2.split(bgr_image), a])
        
        if self.selection_rect != QRect():
            region_x1, region_y1, region_x2, region_y2 = self.parent.selected_rect
            region = result.copy()
            img[region_y1:region_y2, region_x1:region_x2] = region[region_y1:region_y2, region_x1:region_x2].copy()
            result = img
            
        
        current_layer.set_image(result)
        self.parent.display_current_image()

## Free Transform Functions
    def apply_free_transform(self, cancel=False):
        if not self.transform_mode: return
        self.transform_mode = False
        current_layer = self.parent.get_current_focus_layer()
        if not current_layer: return
        
            
        if cancel and self.original_image is not None:
            img = self.original_image.copy()
            current_layer.set_image(img)
            
        elif self.transform_buffer is not None:
            self.selection_rect = QRect()
            result = current_layer.image
            
            x1 = self.handle_list[0].x()
            y1 = self.handle_list[0].y()
            x2 = self.handle_list[3].x()
            y2 = self.handle_list[3].y()
            
            w = max(1, abs(x2 - x1))
            h = max(1, abs(y2 - y1))
            

            img = self.transform_buffer
            if x2 < x1: img = cv2.flip(img, 1)
            if y2 < y1: img = cv2.flip(img, 0)
            
            overlay = cv2.resize(img, (w, h), interpolation=cv2.INTER_LANCZOS4)
            tl_x = min(x1, x2)
            tl_y = min(y1, y2)
            
            result = self.paste(result, overlay, tl_x, tl_y)
            current_layer.set_image(result)
            
        self.parent.display_current_image()
        self.original_image = None

## Copy Cut Paste tool
    def copy_image(self, rect: QRect):
        
        x1, y1, x2, y2 = rect
        current_layer = self.parent.get_current_focus_layer()
        
        if current_layer is None: return
        self.copied_image = current_layer.image[y1:y2, x1:x2].copy()
        
        self.aspect_ratio = (x2-x1) / (y2-y1)
        self.copied_rect = (x1, y1, x2, y2)
        
        # Save in system clipboard
        self.copy_to_clipboard(self.copied_image)
        
    def cut_image(self, rect: QRect):
        
        x1, y1, x2, y2 = rect
        current_layer = self.parent.get_current_focus_layer()
        if current_layer is None: return
        
        # Copy and left empty transparent area
        img = current_layer.image.copy()
        self.copied_image = img[y1:y2, x1:x2].copy()
        img[y1:y2, x1:x2] = 0
        current_layer.set_image(img)
        
        self.aspect_ratio = (x2-x1) / (y2-y1)
        self.copied_rect = (x1, y1, x2, y2)
        
        self.parent.display_current_image()
        
        # Save in system clipboard
        self.copy_to_clipboard(self.copied_image)
    
    def copy_to_clipboard(self, image):
        img_h, img_w = image.shape[:2]
        channels = 1 if len(image.shape) == 2 else image.shape[2]

        if channels == 3:
            temp_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
        elif channels == 4:
            temp_img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)

        # Contiguous memory
        if not temp_img.flags['C_CONTIGUOUS']:
            temp_img = np.ascontiguousarray(temp_img)
        q_image = QImage(
            temp_img.data, 
            img_w, 
            img_h, 
            img_w * 4, 
            QImage.Format_RGBA8888
        )

        # Using qmimedata so won't lost data
        q_pixmap = QPixmap.fromImage(q_image)
        mime_data = QMimeData()
        mime_data.setImageData(q_pixmap.toImage())
        
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        

    
    
    def paste(self, bg, img, x, y):
        """
        Apply pasting image
        """
        h, w = img.shape[:2]
        H, W = bg.shape[:2]
        
        # Clipping
        x1 = max(x, 0)
        y1 = max(y, 0)
        x2 = min(x+w, W)
        y2 = min(y+h, H)
        
         # Out of bounds
        if x2 <= x1 or y2 <= y1: return bg
        
        # Overlay offsets
        ox1 = x1 - x
        oy1 = y1 - y
        ox2 = ox1 + (x2 - x1)
        oy2 = oy1 + (y2 - y1)
        
        fg_crop = img[oy1:oy2, ox1:ox2]
        bg_crop = bg[y1:y2, x1:x2]
        
        # Simple Alpha Blending
        if img.shape[2] == 4:
            alpha = fg_crop[:, :, 3] / 255.0
            alpha = cv2.merge([alpha, alpha, alpha])
            
            # Ensure BG has alpha if needed, or stick to 3 channels
            if bg.shape[2] == 3:
                fg_color = fg_crop[:, :, :3]
                blended = (fg_color * alpha + bg_crop * (1 - alpha))
                bg[y1:y2, x1:x2] = blended.astype(np.uint8)
            else:
                # Alpha to Alpha blending is harder, strictly simplified here:
                # Standard Porter-Duff 'Source Over'
                fg_alpha = fg_crop[:, :, 3] / 255.0
                bg_alpha = bg_crop[:, :, 3] / 255.0
                out_alpha = fg_alpha + bg_alpha * (1 - fg_alpha)
                
                out_color = (fg_crop[:,:,:3] * fg_alpha[:,:,None] + bg_crop[:,:,:3] * bg_alpha[:,:,None] * (1 - fg_alpha[:,:,None])) / (out_alpha[:,:,None] + 1e-6)
                
                bg[y1:y2, x1:x2, :3] = out_color.astype(np.uint8)
                bg[y1:y2, x1:x2, 3] = (out_alpha * 255).astype(np.uint8)
        else:
            # No alpha in overlay, just overwrite
            if bg.shape[2] == 4:
                # Add opaque alpha to fg
                fg_crop = cv2.cvtColor(fg_crop, cv2.COLOR_BGR2BGRA)
            bg[y1:y2, x1:x2] = fg_crop
            
        return bg
    def paste_image(self, copied_rect=None, copied_image=None, copied_aspect_ratio=None):
        """
        Paste the "copied_image" by transform mode, able to adjust the image before paste
        """
        if copied_image is None and self.copied_image is None: return
        
        x1, y1, x2, y2 = self.copied_rect if copied_rect is None else copied_rect
        self.region = self.copied_image if copied_image is None else copied_image
        if self.region is None: return
        
        self.transform_buffer = self.region.copy()
        current_img = self.parent.current_focus_layer_image()        
        if current_img is None: return
        
        self.original_image = current_img.copy()
        
        # Store bounding box with selected area
        self.bounding_box = QRect(QPoint(x1, y1), QPoint(x2, y2))
        self.handle_list = [
            QPoint(x1, y1),
            QPoint(x2, y1),
            QPoint(x1, y2),
            QPoint(x2, y2),
        ]
        self.handle_list_default = copy.deepcopy(self.handle_list)
        self.aspect_ratio = self.copied_aspect_ratio if copied_aspect_ratio is None else copied_aspect_ratio
        
        self.transform_mode = True
        self.drag_start_point = QPoint(x1, y1)
        self.update()

    def paste_from_clipboard(self):
        """
        Get image from system clipboard and paste
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # If no image in clipboard, take image from copied image
        if not mime_data.hasImage():
            self.paste_image()
            return


        q_image = clipboard.image()
        if q_image.isNull(): return
        q_image = q_image.convertToFormat(QImage.Format_RGBA8888)
        width = q_image.width()
        height = q_image.height()

        ptr = q_image.bits()
        ptr.setsize(q_image.byteCount())
        
        
        clipboard_view = np.array(ptr).reshape(height, width, 4)
        clipboard_img = cv2.cvtColor(clipboard_view, cv2.COLOR_RGBA2BGRA)

        paste_x, paste_y = 0, 0
        if self.copied_image is not None:
            if self.copied_image.shape == clipboard_img.shape and \
            np.array_equal(self.copied_image, clipboard_img):
                paste_x = self.copied_rect[0]
                paste_y = self.copied_rect[1]

        self.paste_image(
            copied_rect=(paste_x, paste_y, paste_x + clipboard_img.shape[1], paste_y + clipboard_img.shape[0]),
            copied_image=clipboard_img
        )
    

#/layer
    def insert_image(self, img):
        if self.transform_mode: return
        
        # Scale the image to current canvas size
        x, y, canvas_w, canvas_h = self.parent.get_canvas_area_size()
        height, width = img.shape[:2]
        
        scale_w, scale_h = (canvas_w / width), (canvas_h / height)
        scale = min(scale_w, scale_h)
        display_w = width * scale
        display_h = height * scale
        
        center_offset_x = ((x+canvas_w) - display_w) // 2
        center_offset_y = ((y+canvas_h) - display_h) // 2
        
        display_rect = QRect(
            int(center_offset_x), int(center_offset_y),
            int(display_w), int(display_h)
        )
        
        self.selection_rect = display_rect
        self.parent.on_selection_made(display_rect)
        x1, y1, x2, y2 = self.parent.selected_rect
        aspect_ratio = (x2-x1) / (y2-y1)
        
        self.paste_image(self.parent.selected_rect, img, aspect_ratio)
        
        
        
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
#/ #/layer
### Window for color conversion
class ColorConvertDialog(QDialog):
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

#/ #/layer
### Window for color edit
class ColorAdjustDialog(QDialog):
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

#/ #/layer
class ColorIntensityAdjustDialog(QDialog):
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


# --------------------------------------------------------------------------------
#/
### Color Palette Widget
class ColorPalette(QWidget):

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
#/
## Windows for combine image
class ImageStitchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Combine / Stitch Images")
        self.setFixedSize(400, 300)

        self.image_paths = []
        self.direction = "Horizontal"
        self.spacing = 0

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Images to Combine:"))
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Images")
        remove_btn = QPushButton("Remove Selected")
        add_btn.clicked.connect(self.add_images)
        remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        # Direction
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Direction:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Horizontal", "Vertical"])
        dir_layout.addWidget(self.direction_combo)
        layout.addLayout(dir_layout)

        # Spacing
        layout.addWidget(QLabel("Spacing (pixels):"))
        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(0, 100)
        self.spacing_slider.setValue(0)
        layout.addWidget(self.spacing_slider)

        # Preview
        self.preview_checkbox = QCheckBox("Show Preview")
        layout.addWidget(self.preview_checkbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.bmp)")
        if files:
            self.image_paths.extend(files)
            self.refresh_list()

    def remove_selected(self):
        for item in self.list_widget.selectedItems():
            self.image_paths.remove(item.text())
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        self.list_widget.addItems(self.image_paths)

    def get_settings(self):
        return {
            "paths": self.image_paths,
            "direction": self.direction_combo.currentText(),
            "spacing": self.spacing_slider.value(),
            "preview": self.preview_checkbox.isChecked(),
        }
#/ #/layer
## Create a view window
class ImageViewWindow(QMainWindow):
    def __init__(self, parent=None, image_index=-1, image_name=""):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.parent = parent
        
        title = os.path.basename(image_name)
        self.setWindowTitle(title)
        self.resize(600, 400)

        self.image_index = image_index

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        # self.image_label = QLabel()
        self.image_label = SelectLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)

        self.current_image = None

    def set_image(self, image):
        if image is None:
            self.image_label.clear()
            return

        self.current_image = image.copy()
        self.update_scaled_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scaled_image()

    def update_scaled_image(self):
        if self.current_image is None:
            return

        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_image)

        # Scale to fit window
        scaled_pix = pix.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pix)

    def event(self, e):
        if e.type() == 24:  # QEvent.WindowActivate
            
            self.parent.current_index = self.image_index
            
            return True
        return super().event(e)
#/
## Window for insert text
class TextInsertDialog(QDialog):
    def __init__(self, parent=None, text=None):
        super().__init__(parent)
        self.setWindowTitle("Insert Text")
        self.setMinimumWidth(300)
        self.color = (0, 0, 0)
        self.font_scale = 1
        self.thickness = 2
        self.position = (50, 50)

        layout = QVBoxLayout()

    # --- Text input
        layout.addWidget(QLabel("Text:"))
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Enter text...")
        if text is not None:
            self.text_input.setText(text)
        layout.addWidget(self.text_input)

    # --- Font size
        layout.addWidget(QLabel("Font size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 10)
        self.size_spin.setValue(2)
        layout.addWidget(self.size_spin)

    # --- Thickness
        layout.addWidget(QLabel("Thickness:"))
        self.thick_spin = QSpinBox()
        self.thick_spin.setRange(1, 10)
        self.thick_spin.setValue(2)
        layout.addWidget(self.thick_spin)

    # --- Color picker
        color_layout = QHBoxLayout()
        self.color_label = QLabel("Color: ")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 20)
        self.color_preview.setStyleSheet(f"background-color: rgb{self.color}; border:1px solid gray;")

        self.color_btn = QPushButton("Select Color")
        self.color_btn.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_btn)
        layout.addLayout(color_layout)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)

    def select_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = (color.red(), color.green(), color.blue())
            self.color_preview.setStyleSheet(
                f"background-color: rgb{self.color}; border:1px solid gray;"
            )

    def get_values(self):
        return {
            "text": self.text_input.text(),
            "font_scale": self.size_spin.value(),
            "thickness": self.thick_spin.value(),
            "color": self.color,
            "position": self.position
        }


# --------------------------------------------------------------------------------

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    window = myWindowsOpencV()
    window.show()
    
    window.create_empty_canvas()
    window.display_current_image()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main() 



