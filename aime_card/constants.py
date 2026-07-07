from __future__ import annotations

# HINATA 設備常數
HINATA_VID = 0xF822
HINATA_MANUFACTURER = "NERI"
USAGE_PAGE_READ = 0x01
USAGE_PAGE_WRITE = 0x06

REPORT_ID = 0x01
REPORT_LEN = 64  # 不含 ReportID 的資料長度

# HINATA 主協議命令
CMD_PN532_TRANSPORT = 0xE2

# PN532 命令
PN532_SAM_CONFIGURATION = 0x14
PN532_IN_LIST_PASSIVE_TARGET = 0x4A
PN532_IN_DATA_EXCHANGE = 0x40
PN532_TFI_HOST = 0xD4  # Host -> PN532
PN532_TFI_RESPONSE = 0xD5  # PN532 -> Host

# 常見 NFC 晶片製造商代碼 (UID 首字節, ISO/IEC 7816-6)
MANUFACTURER_NAMES = {
	0x04: "NXP Semiconductors",
	0x05: "Infineon Technologies",
	0x07: "Texas Instruments",
	0x16: "EM Microelectronic-Marin",
	0x28: "STMicroelectronics",
	0x44: "GenStar / FM (Fudan Microelectronics, etc.)",
}

# key
KEY_A = b"\x57\x43\x43\x46\x76\x32"
KEY_B = b"\x57\x43\x43\x46\x76\x32"
DEFAULT_BLANK_KEY = b"\xff\xff\xff\xff\xff\xff"
MIFARE_1K_SECTOR_COUNT = 16
MIFARE_BLOCKS_PER_SECTOR = 4
MIFARE_DEFAULT_ACCESS_BITS = b"\xff\x07\x80\x69"
