import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class VideoFeedThread(QThread):
    change_pixmap_signal = Signal(QPixmap)
    color_detected_signal = Signal(str)  # Add a new signal for color detection

    def __init__(self, rtsp_url,
                 top_bottom_crop_percent=0.2, left_right_crop_percent=0.3,
                 roi_x1_percent=0.4, roi_y1_percent=0.4,
                 roi_x2_percent=0.6, roi_y2_percent=0.6):
        super().__init__()
        self.rtsp_url = rtsp_url
        self._run_flag = True
        self.top_bottom_crop_percent = top_bottom_crop_percent
        self.left_right_crop_percent = left_right_crop_percent
        self.roi_x1_percent = roi_x1_percent
        self.roi_y1_percent = roi_y1_percent
        self.roi_x2_percent = roi_x2_percent
        self.roi_y2_percent = roi_y2_percent
        # Define color ranges (HSV) - these will need tuning
        self.color_ranges = {
            "RED": [(0, 100, 100), (10, 255, 255)],
            "RED2": [(160, 100, 100), (180, 255, 255)],
            "ORANGE": [(11, 100, 100), (25, 255, 255)],
            "YELLOW": [(26, 100, 100), (35, 255, 255)],
            "GREEN": [(36, 50, 50), (85, 255, 255)],
            "BLUE": [(86, 50, 50), (130, 255, 255)],
            "PINK": [(140, 50, 50), (160, 255, 255)],
            "WHITE": [(0, 0, 200), (180, 30, 255)],
            "BLACK": [(0, 0, 0), (180, 255, 50)],
        }
        self.color_names = list(self.color_ranges.keys())

    def crop_frame(self, frame):
        """Crops a frame using percentages."""
        height, width, _ = frame.shape
        left_crop = int(width * self.left_right_crop_percent)
        right_crop = int(width * self.left_right_crop_percent)
        top_crop = int(height * self.top_bottom_crop_percent)
        bottom_crop = int(height * self.top_bottom_crop_percent)
        cropped_frame = frame[top_crop:height - bottom_crop, left_crop:width - right_crop]
        return cropped_frame

    def define_roi(self, width, height):
        """Calculates ROI coordinates based on percentages."""
        x1 = int(width * self.roi_x1_percent)
        y1 = int(height * self.roi_y1_percent)
        x2 = int(width * self.roi_x2_percent)
        y2 = int(height * self.roi_y2_percent)
        return x1, y1, x2, y2

    def get_roi_color(self, frame, x1, y1, x2, y2):
        """Extracts ROI, calculates average color, and returns the color name."""
        roi = frame[y1:y2, x1:x2]  # Extract ROI
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        average_hsv = cv2.mean(hsv_roi)[:3]  # Get average HSV, ignore alpha
        dominant_color = self.match_color(average_hsv)
        return dominant_color

    def match_color(self, hsv_value):
        """Matches an HSV value to a color name."""
        h, s, v = hsv_value
        for color_name, (lower, upper) in self.color_ranges.items():
            h_lower, s_lower, v_lower = lower
            h_upper, s_upper, v_upper = upper
            if (h_lower <= h <= h_upper and
                    s_lower <= s <= s_upper and
                    v_lower <= v <= v_upper):
                return color_name
        return "UNKNOWN"  # Default color is unknown

    def draw_roi_rectangle(self, frame, x1, y1, x2, y2, color_name):
        """Draws a rectangle on the frame to show the ROI."""
        color = (255, 255, 255)  # Default: White
        if color_name == "RED" or color_name == "RED2":
            color = (0, 0, 255)
        elif color_name == "ORANGE":
            color = (0, 165, 255)  # Orange
        elif color_name == "YELLOW":
            color = (0, 255, 255)
        elif color_name == "GREEN":
            color = (0, 255, 0)
        elif color_name == "BLUE":
            color = (255, 0, 0)
        elif color_name == "PINK":
            color = (255, 192, 203)
        elif color_name == "WHITE":
            color = (255, 255, 255)
        elif color_name == "BLACK":
            color = (0, 0, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)  # Draw rectangle
        cv2.putText(frame, color_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            print("Error: Could not open RTSP stream.")
            return

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                cropped_frame = self.crop_frame(frame)
                h, w, _ = cropped_frame.shape
                x1, y1, x2, y2 = self.define_roi(w, h)
                color_name = self.get_roi_color(cropped_frame, x1, y1, x2, y2)
                self.draw_roi_rectangle(cropped_frame, x1, y1, x2, y2, color_name)

                rgb_image = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                self.change_pixmap_signal.emit(pixmap)
                self.color_detected_signal.emit(color_name) # Emit the color
            else:
                print("Error: Could not read frame.")
                break
        cap.release()

    def stop(self):
        self._run_flag = False
    
    def get_color_detected_signal(self):
        return self.color_detected_signal
        