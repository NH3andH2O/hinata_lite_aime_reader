# HINATA Lite Aime Reader

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![uv](https://img.shields.io/badge/uv-package%20manager-654ff0?logo=uv&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-261230?logo=ruff&logoColor=white)](https://docs.astral.sh/ruff/)

[English](README.md) | 简体中文 | [繁體中文](README.zh-TW.md)

HINATA Lite NFC 读卡器的 Aime 卡读写工具

## 功能

- 连续扫描 NFC 卡片并读取 UID。
- 识别 Aime 卡、空白卡与非标准卡。
- 写入指定或随机生成的 20 位 Aime ID。
- 支持随机 Aime ID 循环写入模式。

## 环境需求

- Windows 10/11 或 Linux。
- Python 3.10 或更新版本。
- 建议使用 uv 安装依赖与运行程序。
- HINATA Lite NFC 读卡器，程序会查找 `VID=0xF822` 的 HID 设备。
- 可读写的 MIFARE Classic 1K 兼容卡。
- Python 依赖：`hidapi`（提供程序中使用的 `hid` 模块）。

## 安裝

使用 uv，在项目根目录同步依赖：

```bash
git clone https://github.com/NH3andH2O/hinata_lite_aime_reader.git
cd hinata_lite_aime_reader
uv sync
```

如果安装 `hidapi` 失败，请先安装系统的 HIDAPI / libusb 相关软件包。

在 Linux 上，读卡器作为 HID 设备默认归 `root` 所有，普通用户没有额外权限无法打开。只需执行一次以下命令（需要 sudo）安装内置的 udev 规则，之后即可免 `sudo` 使用：

```bash
uv run hinata-aime --install-udev
```

该命令会将 `VID=0xF822` 且 manufacturer 为 `NERI` 的 HINATA udev 规则写入 `/etc/udev/rules.d/99-hinata.rules`，重新加载规则，并授予 `plugdev` 组及当前本地登录席位（`uaccess`）访问权限。规则会覆盖 `hidraw` 以及部分 Linux `hidapi` 构建会打开的 USB device 节点。请确保当前用户在 `plugdev` 组中，然后重新插拔设备。之后即可无需 `sudo` 运行本工具。

## 运行方式

读取卡片：

```powershell
uv run hinata-aime --read
uv run hinata-aime -r
```

写入随机 Aime ID：

```powershell
uv run hinata-aime --write
uv run hinata-aime -w
```

写入指定 Aime ID（必须是 20 位数字）：

```powershell
uv run hinata-aime --write 12345678901234567890
uv run hinata-aime -w 12345678901234567890
```

循环写入随机 Aime ID：

```powershell
uv run hinata-aime --write --loop
uv run hinata-aime -w -l
```

## 开发工具

本项目提供 `ruff.toml`。如需执行格式化与检查：

```powershell
uv run ruff check .
uv run ruff format .
```
