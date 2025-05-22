# DAC_controller_GUI_AD5370
ESP32 AD5370 DAC Streaming Controller
This project implements a firmware for ESP32 to control the Analog Devices AD5370 DAC, supporting high-speed waveform streaming from an SD card or RAM buffer. The ESP32 communicates over UART with a PC or host device, accepting commands to configure sampling rate, active channels, start/stop streaming, status queries, and binary waveform uploads using the XMODEM protocol.

Features
Initialize and control AD5370 DAC via SPI

Configure sample rate (Hz) and number of output channels (1–40)

Start and stop DAC streaming on command

Upload waveform binary files (all_channels.bin) to ESP32 SD card via UART using XMODEM protocol

Select single channel output mode for high-speed streaming

Status reporting over UART

Robust command menu over serial console

Compatible with UART terminal tools and custom PC software

Hardware Requirements
ESP32 development board (tested on ESP32-S3)

Analog Devices AD5370 DAC module (SPI interface)

MicroSD card module (for storing waveform files)

UART serial connection to PC (default 115200 baud)

Power supply appropriate for DAC and ESP32

Software Requirements
Arduino framework or ESP-IDF (code here targets Arduino environment)

Terminal software supporting XMODEM file transfer (e.g., Tera Term, CoolTerm, minicom)

Optional: Python scripts for control and file upload

UART Command Set
Command	Description
1	Set sample rate (Hz)
2	Set number of channels (1–40)
3	Start DAC streaming
4	Stop DAC streaming
5	Query current configuration status
6	Select single output channel (if 1 channel active)
U	Upload binary waveform file via XMODEM

Usage
Connect ESP32 UART to PC (e.g., via USB-to-serial) at 115200 baud, 8N1.

Open terminal software and connect to the ESP32 serial port.

After power-up, the ESP32 prints the command menu and waits for input.

Enter commands 1–6 to configure and control DAC streaming.

To upload a waveform binary file:

Send U command.

Use terminal software’s Send File → XMODEM option to transfer all_channels.bin.

Wait for upload confirmation (UPLOAD_DONE).

Use commands to start streaming the uploaded waveform.

File Upload Details
The binary file must be named all_channels.bin.

Files are stored on the SD card root directory.

XMODEM transfer is required; raw uploads are not supported by default.

Transfer failure will be indicated with XMODEM receive failed.

Troubleshooting
Ensure UART baud rate and settings match on both ESP32 and PC.

Use terminal software supporting XMODEM protocol for uploads.

If upload repeatedly fails, verify wiring and SD card operation.

Check serial logs for error messages.

Development
The main firmware is in main.cpp.

SPI communication with AD5370 is abstracted in ad5370.cpp / ad5370.h.

SD card read/write is handled in sdcard.cpp / sdcard.h.

XMODEM receiver implementation in xmodem.cpp.

License
This project is open source under the MIT License.

Acknowledgments
AD5370 DAC datasheet and application notes by Analog Devices

ESP32 Arduino core and libraries

XMODEM protocol implementations from open source references
