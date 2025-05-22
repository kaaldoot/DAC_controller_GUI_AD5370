import sys
import serial
import serial.tools.list_ports
import csv
import struct
import os
import time  

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QProgressBar, QComboBox, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor

MIN_VOLTAGE = -4.0
MAX_VOLTAGE = 8.0

def voltage_to_dac(voltage):
    voltage = max(MIN_VOLTAGE, min(MAX_VOLTAGE, voltage))
    scaled = (voltage + 4.0) / 12.0
    return int(scaled * 65535)

class DACController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAC Controller")
        self.serial = None

        self.initUI()
        self.setDefaults()
        self.timer = QTimer()
        self.timer.timeout.connect(self.readSerial)
        self.timer.start(100)

    def initUI(self):
        font = QFont("Arial", 12)

        layout = QVBoxLayout()

        # Serial Port Selector
        port_layout = QHBoxLayout()
        port_label = QLabel("Serial Port:")
        port_label.setFont(font)
        self.port_selector = QComboBox()
        self.port_selector.setFont(font)
        self.refreshPorts()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setFont(font)
        self.connect_btn.clicked.connect(self.connectSerial)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_selector)
        port_layout.addWidget(self.connect_btn)
        layout.addLayout(port_layout)

        # Sample Rate
        sr_layout = QHBoxLayout()
        self.sample_rate_input = QLineEdit()
        self.sample_rate_input.setPlaceholderText("1000")
        self.sample_rate_input.setFont(font)
        sr_button = QPushButton("Set Sample Rate (Hz)")
        sr_button.setFont(font)
        sr_button.clicked.connect(self.setSampleRate)
        sr_layout.addWidget(self.sample_rate_input)
        sr_layout.addWidget(sr_button)
        layout.addLayout(sr_layout)

        # Channel Count
        ch_layout = QHBoxLayout()
        self.channel_count_input = QLineEdit()
        self.channel_count_input.setPlaceholderText("40")
        self.channel_count_input.setFont(font)
        ch_button = QPushButton("Set Channels")
        ch_button.setFont(font)
        ch_button.clicked.connect(self.setChannels)
        ch_layout.addWidget(self.channel_count_input)
        ch_layout.addWidget(ch_button)
        layout.addLayout(ch_layout)

        # Single channel index
        self.single_channel_layout = QHBoxLayout()
        self.single_channel_input = QLineEdit()
        self.single_channel_input.setPlaceholderText("Channel Index (0-39)")
        self.single_channel_input.setFont(font)
        self.single_channel_btn = QPushButton("Set Single Channel")
        self.single_channel_btn.setFont(font)
        self.single_channel_btn.clicked.connect(self.setSingleChannel)
        self.single_channel_layout.addWidget(self.single_channel_input)
        self.single_channel_layout.addWidget(self.single_channel_btn)
        layout.addLayout(self.single_channel_layout)
        self.single_channel_layout.setEnabled(False)

        # Start / Stop Buttons
        ctrl_layout = QHBoxLayout()
        start_btn = QPushButton("Start Streaming")
        stop_btn = QPushButton("Stop Streaming")
        status_btn = QPushButton("Get Status")
        for btn in (start_btn, stop_btn, status_btn):
            btn.setFont(font)
        start_btn.clicked.connect(self.startStreaming)
        stop_btn.clicked.connect(self.stopStreaming)
        status_btn.clicked.connect(self.getStatus)
        ctrl_layout.addWidget(start_btn)
        ctrl_layout.addWidget(stop_btn)
        ctrl_layout.addWidget(status_btn)
        layout.addLayout(ctrl_layout)

        # Separate buttons for Convert and Upload BIN
        bin_layout = QHBoxLayout()
        convert_btn = QPushButton("Convert CSV to BIN")
        convert_btn.setFont(font)
        convert_btn.clicked.connect(self.convertCSV)

        upload_btn = QPushButton("Upload BIN")
        upload_btn.setFont(font)
        upload_btn.clicked.connect(self.uploadBIN)

        self.progress = QProgressBar()
        bin_layout.addWidget(convert_btn)
        bin_layout.addWidget(upload_btn)
        bin_layout.addWidget(self.progress)
        layout.addLayout(bin_layout)

        # Serial log display
        self.serial_output = QTextEdit()
        self.serial_output.setReadOnly(True)
        self.serial_output.setStyleSheet("background-color: black; color: lime;")
        self.serial_output.setFont(QFont("Courier", 11))
        layout.addWidget(self.serial_output)

        self.setLayout(layout)

    def refreshPorts(self):
        self.port_selector.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_selector.addItems(ports)

    def connectSerial(self):
        port = self.port_selector.currentText()
        if port:
            try:
                self.serial = serial.Serial(port, 921600, timeout=1)
                QMessageBox.information(self, "Connection", f"Connected to {port}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection failed: {e}")

    def sendCommand(self, cmd):
        if self.serial and self.serial.is_open:
            self.serial.write(cmd.encode())

    def setSampleRate(self):
        val = self.sample_rate_input.text()
        if val.isdigit():
            self.sendCommand('1')
            self.serial.write((val + '\n').encode())
            QMessageBox.information(self, "Sample Rate", f"Sample rate set to {val} Hz")

    def setChannels(self):
        val = self.channel_count_input.text()
        if val.isdigit():
            count = int(val)
            self.sendCommand('2')
            self.serial.write((val + '\n').encode())
            self.single_channel_layout.setEnabled(count == 1)
            QMessageBox.information(self, "Channels", f"Channel count set to {val}")

    def setSingleChannel(self):
        val = self.single_channel_input.text()
        if val.isdigit():
            ch = int(val)
            if 0 <= ch <= 39:
                self.sendCommand('6')
                self.serial.write((val + '\n').encode())
                QMessageBox.information(self, "Single Channel", f"Set to channel {ch}")

    def startStreaming(self):
        self.sendCommand('3')
        QMessageBox.information(self, "Streaming", "Streaming started")

    def stopStreaming(self):
        self.sendCommand('4')
        QMessageBox.information(self, "Streaming", "Streaming stopped")

    def getStatus(self):
        self.sendCommand('5')

    def readSerial(self):
        if self.serial and self.serial.in_waiting:
            try:
                data = self.serial.read(self.serial.in_waiting).decode(errors='ignore')
                self.serial_output.moveCursor(QTextCursor.End)
                self.serial_output.insertPlainText(data)
                self.serial_output.moveCursor(QTextCursor.End)
            except Exception as e:
                print(f"Serial read error: {e}")

    def convertCSV(self):
        csv_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File")
        if not csv_path:
            return

        bin_path = os.path.join(os.getcwd(), "all_channels.bin")
        try:
            with open(csv_path, 'r') as csvfile, open(bin_path, 'wb') as binfile:
                reader = csv.reader(csvfile)
                header = next(reader)  # skip header

                previous_voltages = [0.0 for _ in range(40)]

                for row_num, row in enumerate(reader):
                    num_voltage_cols = len(row) - 1  # exclude index column at [0]

                    if num_voltage_cols <= 0:
                        # No voltage data, skip row
                        print(f"Skipping row {row_num} — no voltage columns")
                        continue

                    output_row = []
                    for ch in range(num_voltage_cols):
                        try:
                            voltage = float(row[ch + 1])  # Skip index at [0]
                            previous_voltages[ch] = voltage
                        except (ValueError, IndexError):
                            voltage = previous_voltages[ch]
                        dac_val = voltage_to_dac(voltage)
                        output_row.append(dac_val)

                    # Write all available converted channels for this row
                    for val in output_row:
                        binfile.write(struct.pack('>H', val))  # Big-endian 16-bit

            QMessageBox.information(self, "Conversion", f"BIN file saved as:\n{bin_path}")
        except Exception as e:
            QMessageBox.critical(self, "Conversion Failed", f"Error: {e}")


    def uploadBIN(self):
        bin_path = os.path.join(os.getcwd(), "all_channels.bin")
        if not os.path.exists(bin_path):
            QMessageBox.warning(self, "Upload Failed", "BIN file not found. Please convert CSV first.")
            return

        if self.serial and self.serial.is_open:
            try:
                self.sendCommand('U')  # Command to ESP32 to prepare for file reception
                with open(bin_path, 'rb') as f:
                    data = f.read()
                    total = len(data)
                    chunk_size = 256
                    sent = 0
                    while sent < total:
                        chunk = data[sent:sent+chunk_size]
                        self.serial.write(chunk)
                        sent += len(chunk)
                        self.progress.setValue(int((sent / total) * 100))
                        time.sleep(0.002)  #  Add 2 ms delay between chunks
                self.progress.setValue(100)
                QMessageBox.information(self, "Upload", "Upload complete.")
            except Exception as e:
                QMessageBox.critical(self, "Upload Failed", f"Upload error: {e}")
        else:
            QMessageBox.warning(self, "Upload Failed", "Serial port not connected.")

    def setDefaults(self):
        self.sample_rate_input.setText("1000")
        self.channel_count_input.setText("40")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DACController()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
