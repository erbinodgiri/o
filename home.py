from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QMessageBox
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap, QFont

class Home(QWidget):
    """Main window for the application."""

    # Signals for communicating with the triggering thread
    start_triggering_signal = Signal()
    stop_triggering_signal = Signal()
    function_triggered_signal = Signal(str)  # Signal to receive triggered function name
    start_calibration_signal = Signal()
    calibration_finished_signal = Signal() # Add the calibration finished signal

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bottle Cap Sorter")
        self.setGeometry(0, 0, 800, 480)
        self.setFixedSize(800, 480) # Make the window fixed size

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Left section: Video feed
        self.video_feed_label = QLabel()
        self.video_feed_label.setAlignment(Qt.AlignCenter)
        self.video_feed_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.video_feed_label, 70)  # 70% width

        # Right section: Control panel
        control_layout = QVBoxLayout()
        control_layout.setAlignment(Qt.AlignTop)
        control_layout.setSpacing(20)
        main_layout.addLayout(control_layout, 25)  # 25% width

        # "Bottle Cap Sorter" label
        heading_label = QLabel("Bottle Cap Sorter")
        heading_label.setFont(QFont("Arial", 16, QFont.Bold))
        heading_label.setAlignment(Qt.AlignCenter)
        control_layout.addWidget(heading_label)

        # Label for last triggered function
        self.last_function_label = QLabel("Triggered: None")  # Initialize the label
        self.last_function_label.setAlignment(Qt.AlignCenter)
        self.last_function_label.setVisible(False)  # Initially hidden
        control_layout.addWidget(self.last_function_label)

        # Start/Stop button
        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setFont(QFont("Arial", 12))
        self.start_stop_button.clicked.connect(self.toggle_triggering)
        control_layout.addWidget(self.start_stop_button)

        # Calibrate button
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setFont(QFont("Arial", 12))
        self.calibrate_button.clicked.connect(self.start_calibration)  # Connect to new method
        control_layout.addWidget(self.calibrate_button)

        self.setLayout(main_layout)
        self.triggering_enabled = False
        self.calibration_timer = QTimer(self) # Add a QTimer
        self.calibration_timer.timeout.connect(self.finish_calibration) # Connect timeout

    @Slot(QPixmap)
    def update_image(self, pixmap):
        """Updates the displayed camera image."""
        scaled_pixmap = pixmap.scaled(self.video_feed_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_feed_label.setPixmap(scaled_pixmap)

    @Slot(str)
    def update_last_function(self, function_name):
        """Updates the label with the name of the last triggered function."""
        self.last_function_label.setText(f"Triggered: {function_name}")
        self.last_function_label.setVisible(True)  # Make sure it's visible

    @Slot()
    def toggle_triggering(self):
        """Toggles the triggering state (start/stop)."""
        if self.triggering_enabled:
            self.start_stop_button.setText("Start")
            self.stop_triggering_signal.emit()
            self.triggering_enabled = False
            self.last_function_label.setVisible(False)
            self.calibrate_button.setVisible(True)

        else:
            self.start_stop_button.setText("Stop")
            self.start_triggering_signal.emit()
            self.triggering_enabled = True
            self.last_function_label.setVisible(True)
            self.calibrate_button.setVisible(False)

    def get_trigger_signals(self): #getter for start stop signals
        return self.start_triggering_signal, self.stop_triggering_signal
    
    def get_function_triggered_signal(self):
        return self.function_triggered_signal
    
    def get_calibration_signals(self):
        return self.start_calibration_signal, self.calibration_finished_signal # return the signals

    @Slot()
    def start_calibration(self):
        """Handles the calibration button click."""
        self.start_calibration_signal.emit() # Emit start signal to TriggeringObject
        self.calibration_timer.start(5000)  # Start the timer for 5 seconds (5000 ms)
        self.calibration_dialog = QMessageBox(self)
        self.calibration_dialog.setWindowTitle("Calibrating")
        self.calibration_dialog.setText("Calibrating... Please wait.")
        self.calibration_dialog.setStandardButtons(QMessageBox.NoButton)
        self.calibration_dialog.show()

    @Slot()
    def finish_calibration(self):
        """Handles the end of the calibration timer."""
        self.calibration_timer.stop()
        if self.calibration_dialog is not None:
            self.calibration_dialog.close()
            self.calibration_dialog.hide()

        self.calibration_finished_signal.emit() #telling it has finished.

    @Slot(str, str)
    def handle_calibration_result(self, result, background_color):
        """Handles the calibration result signal from TriggeringObject."""
        if result == "PASSED":
            QMessageBox.information(self, "Calibration Passed", f"Calibration was successful. Background color: {background_color}")
        else:
            QMessageBox.critical(self, "Calibration Failed", f"Calibration failed: {background_color}") #bacground color carries the error message
        self.calibration_dialog = None
