# Raspberry-Pi-Remote-Printer

A Raspberry Pi-based system that receives Telegram messages and prints them
on a Rongta USB thermal receipt printer.

## Features

- Remote printing through a Telegram bot
- USB thermal-printer communication
- Automatic startup through systemd
- Adjustable text size and spacing
- Basic sender authorization
- Headless Raspberry Pi operation

## Hardware

- Raspberry Pi Zero W
- Rongta USB thermal receipt printer
- USB connection between the Pi and printer

## System Architecture

Telegram User → Telegram Bot API → Raspberry Pi → USB Printer

## Installation

1. Clone the repository.
2. Create a Python virtual environment.
3. Install the requirements.
4. Configure the Telegram bot token.
5. Install and enable the systemd service.

## Demo

<img width="1205" height="813" alt="image" src="https://github.com/user-attachments/assets/976d67f2-4dd0-4825-ae3d-811c17ff86dd" />

<img width="2160" height="2880" alt="image" src="https://github.com/user-attachments/assets/e040aefc-5378-46e2-916e-0f07be465847" />

