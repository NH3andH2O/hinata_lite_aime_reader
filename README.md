# HINATA Lite Aime Reader

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![uv](https://img.shields.io/badge/uv-package%20manager-654ff0?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

English | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

An Aime card read/write tool for the HINATA Lite NFC reader.

## Features

- Continuously scan NFC cards and read UIDs.
- Detect Aime cards, blank cards, and non-standard cards.
- Write a specified or randomly generated 20-digit Aime ID.
- Support loop mode for writing random Aime IDs.

## Requirements

- Windows 10/11.
- Python 3.10 or later.
- uv is recommended for installing dependencies and running the tool.
- HINATA Lite NFC reader; the program searches for a HID device with `VID=0xF822`.
- Read/write-capable MIFARE Classic 1K compatible card.
- Python dependency: `hidapi` (provides the `hid` module used by the program).

## Setup

Using uv, sync dependencies from the project root:

```bash
uv sync
```

If `hidapi` installation fails, install the system HIDAPI / libusb packages first. On Linux, if the device cannot be accessed, add a udev rule for `VID=0xF822` or run as a user with device permissions.

## Usage

Read a card:

```powershell
uv run hinata-aime --read
uv run hinata-aime -r
```

Write a random Aime ID:

```powershell
uv run hinata-aime --write
uv run hinata-aime -w
```

Write a specified Aime ID (must be 20 digits):

```powershell
uv run hinata-aime --write 12345678901234567890
uv run hinata-aime -w 12345678901234567890
```

Loop writing random Aime IDs:

```powershell
uv run hinata-aime --write --loop
uv run hinata-aime -w -l
```

## Development

This project provides `ruff.toml`. To run formatting and checks:

```powershell
uv run ruff check .
uv run ruff format .
```

