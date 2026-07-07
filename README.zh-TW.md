# HINATA Lite Aime Reader

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![uv](https://img.shields.io/badge/uv-package%20manager-654ff0?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

[English](README.md) | [简体中文](README.zh-CN.md) | 繁體中文

HINATA Lite NFC 讀卡器的 Aime 卡讀寫工具

## 功能

- 連續掃描 NFC 卡片並讀取 UID。
- 判斷 Aime 卡、空白卡與非標準卡。
- 寫入指定或隨機產生的 20 位 Aime ID。
- 支援隨機 Aime ID 循環寫入模式。

## 環境需求

- Windows 10/11 或 Linux。
- Python 3.10 或更新版本。
- 建議使用 uv 安裝依賴與執行程式。
- HINATA Lite NFC 讀卡器，程式會尋找 `VID=0xF822` 的 HID 裝置。
- 可讀寫的 MIFARE Classic 1K 相容卡。
- Python 依賴：`hidapi`（提供程式中使用的 `hid` 模組）。

## 安装

使用 uv，在專案根目錄同步依賴：

```bash
git clone https://github.com/NH3andH2O/hinata_lite_aime_reader.git
cd hinata_lite_aime_reader
uv sync
```

如果安裝 `hidapi` 失敗，請先安裝系統的 HIDAPI / libusb 相關套件。

在 Linux 上，讀卡器作為 HID 裝置預設歸 `root` 所有，一般使用者沒有額外權限無法開啟。只需執行一次以下指令（需要 sudo）安裝內建的 udev 規則，之後即可免 `sudo` 使用：

```bash
uv run hinata-aime --install-udev
```

此指令會將 `VID=0xF822` 且 manufacturer 為 `NERI` 的 HINATA udev 規則寫入 `/etc/udev/rules.d/99-hinata.rules`，重新載入規則，並授予 `plugdev` 群組與目前本機登入席位（`uaccess`）存取權限。規則會涵蓋 `hidraw`，以及部分 Linux `hidapi` 建置會開啟的 USB device 節點。請確認目前使用者在 `plugdev` 群組中，然後重新插拔裝置。之後即可無需 `sudo` 執行本工具。

## 執行方式

讀取卡片：

```powershell
uv run hinata-aime --read
uv run hinata-aime -r
```

寫入隨機 Aime ID：

```powershell
uv run hinata-aime --write
uv run hinata-aime -w
```

寫入指定 Aime ID（必須是 20 位數字）：

```powershell
uv run hinata-aime --write 12345678901234567890
uv run hinata-aime -w 12345678901234567890
```

循環寫入隨機 Aime ID：

```powershell
uv run hinata-aime --write --loop
uv run hinata-aime -w -l
```

## 開發工具

本專案提供 `ruff.toml`。如需執行格式化與檢查：

```powershell
uv run ruff check .
uv run ruff format .
```
