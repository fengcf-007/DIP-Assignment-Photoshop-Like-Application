import copy
import cv2
import numpy as np
import keyboard
from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint, QPointF, QMimeData
from PyQt5.QtGui import (
    QPainter, QPen, QPolygonF, QImage, QColor, QFont, 
    QPixmap, 
)


"""
A QLabel subclass to handle 
Image display, mouse events for selection, drawing, moving, and transforming.
"""
class SelectLabel(QLabel):
    """
    A QLabel subclass to handle \n
    Image display, mouse events for selection, drawing, moving, and transforming.
    """

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

  