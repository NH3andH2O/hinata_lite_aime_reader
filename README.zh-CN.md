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

- Windows 10/11。
- Python 3.10 或更新版本。
- 建议使用 uv 安装依赖与运行程序。
- HINATA Lite NFC 读卡器，程序会查找 `VID=0xF822` 的 HID 设备。
- 可读写的 MIFARE Classic 1K 兼容卡。
- Python 依赖：`hidapi`（提供程序中使用的 `hid` 模块）。

## 环境配置

使用 uv，在项目根目录同步依赖：

```bash
uv sync
```

如果安装 `hidapi` 失败，请先安装系统的 HIDAPI / libusb 相关软件包。Linux 如无法访问设备，需为 `VID=0xF822` 添加 udev 规则或以具备设备权限的用户运行。

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
