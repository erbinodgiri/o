import serial
from PySide6.QtCore import QObject, Signal, QThread, QSettings
from collections import deque

class TriggeringObject(QObject):
    function_triggered_signal = Signal(str)
    calibration_finished_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        # Initialize serial communication with Arduino
        # Adjust the port based on your system (e.g., /dev/tty.usbserial-XXXX on macOS, COM3 on Windows)
        self.serial_port = serial.Serial('/dev/cu.usbserial-A5069RR4', 9600, timeout=1)
        # Wait briefly for the serial connection to establish
        import time
        time.sleep(2)  # Give Arduino time to reset after serial connection
        # Map colors to Arduino commands
        self.servo_mapping = {
            "RED2": "RED2",
            "GREEN": "GREEN",
            "BLUE": "BLUE",
        }
        self.last_triggered_color = None
        self.color_history = deque()
        self.max_history_size = 3
        self.is_triggering_enabled = False
        self.settings = QSettings()
        self.background_color = self.settings.value("background_color", defaultValue=None)
        self.is_calibrating = False
        self.calibration_colors = deque()
        self.calibration_colors_max_size = 50

    def start_triggering(self):
        print("Triggering started.")
        self.is_triggering_enabled = True

    def stop_triggering(self):
        print("Triggering stopped.")
        self.is_triggering_enabled = False

    def handle_color_detection(self, color):
        if self.is_calibrating:
            self.calibration_colors.append(color)
            if len(self.calibration_colors) > self.calibration_colors_max_size:
                self.calibration_colors.popleft()
        elif self.is_triggering_enabled:
            self.color_history.append(color)
            if len(self.color_history) > self.max_history_size:
                self.color_history.popleft()
            if len(self.color_history) == self.max_history_size and all(c == self.color_history[0] for c in self.color_history):
                if self.last_triggered_color != color:
                    if self.last_triggered_color and self.last_triggered_color in self.servo_mapping:
                        self._move_servo(self.last_triggered_color, 0)
                    if color != self.background_color:
                        self.trigger_action(color)
                    else:
                        self.handle_background_color()

    def trigger_action(self, color):
        if color == "RED2":
            self.handle_red2_color()
        elif color == "GREEN":
            self.handle_green_color()
        elif color == "BLUE":
            self.handle_blue_color()
        elif color == "YELLOW":
            self.handle_yellow_color()
        elif color == "ORANGE":
            self.handle_orange_color()
        elif color == "PINK":
            self.handle_pink_color()
        elif color == "WHITE":
            self.handle_white_color()
        elif color == "BLACK":
            self.handle_black_color()
        else:
            self.handle_unknown_color()

    def _move_servo(self, color, angle):
        if color in self.servo_mapping:
            try:
                command = f"{self.servo_mapping[color]}:{angle}\n"
                self.serial_port.write(command.encode())
                print(f"Sent to Arduino: {command.strip()}")
            except serial.SerialException as e:
                print(f"Serial error: {e}")

    def handle_red2_color(self):
        print("Red2 color detected! Triggering Red2 action")
        self.function_triggered_signal.emit("RED2")
        self.last_triggered_color = "RED2"
        self._move_servo("RED2", 90)

    def handle_green_color(self):
        print("Green color detected! Triggering Green action")
        self.function_triggered_signal.emit("GREEN")
        self.last_triggered_color = "GREEN"
        self._move_servo("GREEN", 90)

    def handle_blue_color(self):
        print("Blue color detected! Triggering Blue action")
        self.function_triggered_signal.emit("BLUE")
        self.last_triggered_color = "BLUE"
        self._move_servo("BLUE", 90)

    def handle_yellow_color(self):
        print("Yellow color detected! Triggering Yellow action")
        self.function_triggered_signal.emit("YELLOW")
        self.last_triggered_color = "YELLOW"

    def handle_orange_color(self):
        print("Orange color detected! Triggering Orange action")
        self.function_triggered_signal.emit("ORANGE")
        self.last_triggered_color = "ORANGE"

    def handle_pink_color(self):
        print("Pink color detected! Triggering Pink action")
        self.function_triggered_signal.emit("PINK")
        self.last_triggered_color = "PINK"

    def handle_white_color(self):
        print("White color detected! Triggering White action")
        self.function_triggered_signal.emit("WHITE")
        self.last_triggered_color = "WHITE"

    def handle_black_color(self):
        print("Black color detected! Triggering Black action")
        self.function_triggered_signal.emit("BLACK")
        self.last_triggered_color = "BLACK"

    def handle_unknown_color(self):
        print("Unknown color detected! Triggering Unknown action")
        self.function_triggered_signal.emit("UNKNOWN")
        self.last_triggered_color = "UNKNOWN"

    def handle_background_color(self):
        print("Background color detected! No action triggered")
        self.function_triggered_signal.emit("BACKGROUND")

    def start_calibration(self):
        print("Calibration started.")
        self.is_calibrating = True
        self.calibration_colors.clear()

    def finish_calibration(self):
        self.is_calibrating = False
        print("Calibration finished.")
        if len(self.calibration_colors) == self.calibration_colors_max_size:
            if all(color == self.calibration_colors[0] for color in self.calibration_colors):
                self.background_color = self.calibration_colors[0]
                self.settings.setValue("background_color", self.background_color)
                self.calibration_finished_signal.emit("PASSED", self.background_color)
            else:
                self.calibration_finished_signal.emit("FAILED", "Inconsistent colors during calibration")
        else:
            self.calibration_finished_signal.emit("FAILED", "Not enough samples collected")