import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Qt
from home import Home
from video_feed_thread import VideoFeedThread
from triggering_object import TriggeringObject

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Camera setup
    # Using MacBook's built-in camera for now
    # rtsp_url = 0  # 0 for default camera (MacBook's built-in camera)
    # For later: Switch to USB webcam or IP camera by uncommenting one of the following:
    # rtsp_url = 1  # For USB webcam (if Mac camera is 0, next device is 1)
    rtsp_url = "rtsp://binod:admin!123@192.168.1.10:554/stream?stream=1"  # For IP camera

    video_thread = VideoFeedThread(rtsp_url)
    video_thread.start()

    window = Home()
    window.show()

    triggering_object = TriggeringObject()
    triggering_thread = QThread()
    triggering_object.moveToThread(triggering_thread)
    triggering_thread.start()

    video_thread.change_pixmap_signal.connect(window.update_image)
    window.start_triggering_signal.connect(triggering_object.start_triggering)
    window.stop_triggering_signal.connect(triggering_object.stop_triggering)
    video_thread.color_detected_signal.connect(triggering_object.handle_color_detection)
    triggering_object.function_triggered_signal.connect(window.update_last_function)
    window.start_calibration_signal.connect(triggering_object.start_calibration)
    window.calibration_finished_signal.connect(triggering_object.finish_calibration)
    triggering_object.calibration_finished_signal.connect(window.handle_calibration_result)

    app.aboutToQuit.connect(video_thread.stop)
    app.aboutToQuit.connect(triggering_thread.quit)
    app.aboutToQuit.connect(triggering_thread.wait)

    sys.exit(app.exec())