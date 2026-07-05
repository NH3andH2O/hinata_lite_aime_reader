from __future__ import annotations

import time

from .constants import (
	CMD_PN532_TRANSPORT,
	KEY_A,
	KEY_B,
	PN532_IN_DATA_EXCHANGE,
	PN532_IN_LIST_PASSIVE_TARGET,
	PN532_SAM_CONFIGURATION,
	PN532_TFI_HOST,
	PN532_TFI_RESPONSE,
)
from .hinata_hid import HinataDevice

PN532_ERROR_NAMES = {
	0x01: "Timeout",
	0x02: "CRC",
	0x03: "Parity",
	0x04: "CollisionBitCount",
	0x05: "MifareFraming",
	0x06: "CollisionBitColl",
	0x07: "NoBufs",
	0x09: "RfNoBufs",
	0x0A: "ActiveTooSlow",
	0x0B: "RfProto",
	0x0D: "TooHot",
	0x0E: "InternalNoBufs",
	0x10: "Inval",
	0x12: "DepInvalidCmd",
	0x13: "DepBadData",
	0x14: "MifareAuth",
	0x18: "NoSecure",
	0x19: "I2cBusy",
	0x23: "UidChecksum",
	0x25: "DepState",
	0x26: "HciInval",
	0x27: "Context",
	0x29: "Released",
	0x2A: "CardSwapped",
	0x2B: "NoCard",
	0x2C: "Mismatch",
	0x2D: "Overcurrent",
	0x2E: "NoNad",
}


def describe_pn532_error(status: int) -> str:
	return PN532_ERROR_NAMES.get(status, "Unknown")


def build_frame(cmd: int, data: bytes = b"") -> bytes:
	"""組裝標準 PN532 信息帧 (含前後 preamble)。"""
	length = len(data) + 2  # TFI + CMD + DATA
	lcs = (-length) & 0xFF  # 使 LEN + LCS == 0
	body = bytes([PN532_TFI_HOST, cmd]) + data
	dcs = (-sum(body)) & 0xFF  # 使 Σ(TFI..DATA) + DCS == 0
	return bytes([0x00, 0x00, 0xFF, length, lcs]) + body + bytes([dcs, 0x00])


class Pn532Transport:
	"""透過 HINATA CMD=0xE2 存取 PN532。"""

	def __init__(self, device: HinataDevice) -> None:
		self._device = device

	def sam_configuration(self) -> None:
		"""初始化 PN532 (SAMConfiguration normal mode)。"""
		frame = build_frame(PN532_SAM_CONFIGURATION, bytes([0x01, 0x14, 0x01]))
		self._device.send(CMD_PN532_TRANSPORT, frame)
		# 等待應答 (跳過 ACK)，失敗也不致命
		self.wait_response(PN532_SAM_CONFIGURATION, timeout_ms=500)

	def wait_response(self, expect_cmd: int, timeout_ms: int = 800) -> bytes | None:
		"""等待 PN532 真正應答帧，跳過 ACK (00 00 FF 00 FF 00)。

		回傳 PN532 應答的 DATA 部分 (TFI/CMD 之後)，無則 None。
		"""
		deadline = time.monotonic() + timeout_ms / 1000.0
		resp_cmd = expect_cmd + 1  # PN532 上行 CMD = host_cmd + 1
		while time.monotonic() < deadline:
			frame = self._device.read_frame(timeout_ms=200)
			if not frame:
				continue
			data = _parse_response_frame(frame, resp_cmd)
			if data is not None:
				return data
		return None

	def poll_iso14443a(self) -> bytes | None:
		"""執行一次寻卡，回傳 UID；無卡回傳 None。"""
		# InListPassiveTarget: [max_tg=1, brty=0x00 (ISO14443A)]
		frame = build_frame(PN532_IN_LIST_PASSIVE_TARGET, bytes([0x01, 0x00]))
		self._device.send(CMD_PN532_TRANSPORT, frame)
		data = self.wait_response(PN532_IN_LIST_PASSIVE_TARGET, timeout_ms=400)
		if not data:
			return None
		return parse_iso14443a_uid(data)

	def in_data_exchange_status(
		self, data: bytes, timeout_ms: int = 500
	) -> tuple[int, bytes] | None:
		"""執行 InDataExchange，回傳 (PN532 status, data)。"""
		frame = build_frame(PN532_IN_DATA_EXCHANGE, bytes([0x01]) + data)
		self._device.send(CMD_PN532_TRANSPORT, frame)
		resp = self.wait_response(PN532_IN_DATA_EXCHANGE, timeout_ms=timeout_ms)
		if resp is None:
			return None
		return resp[0], bytes(resp[1:])

	def in_data_exchange(self, data: bytes, timeout_ms: int = 500) -> bytes | None:
		"""執行 InDataExchange，回傳去除 status 後的資料。"""
		result = self.in_data_exchange_status(data, timeout_ms=timeout_ms)
		if result is None:
			return None
		status, payload = result
		if status != 0x00:
			return None
		return payload

	def mifare_authenticate(self, uid: bytes, block: int, key: bytes) -> bool:
		"""使用 MIFARE key 驗證指定 block，先嘗試 KeyA 再嘗試 KeyB。"""
		if len(uid) < 4 or len(key) != 6:
			return False
		uid4 = uid[:4]
		payload_a = bytes([0x60, block]) + key + uid4
		if self.in_data_exchange(payload_a, timeout_ms=500) is not None:
			return True
		payload_b = bytes([0x61, block]) + key + uid4
		return self.in_data_exchange(payload_b, timeout_ms=500) is not None

	def mifare_read_block(self, uid: bytes, block: int, key: bytes) -> bytes | None:
		"""先驗證後讀取 MIFARE block，成功回傳 16 bytes。"""
		if not self.mifare_authenticate(uid, block, key):
			return None
		resp = self.in_data_exchange(bytes([0x30, block]), timeout_ms=500)
		if not resp or len(resp) < 16:
			return None
		return bytes(resp[:16])

	def mifare_write_block(
		self, uid: bytes, block: int, key: bytes, data: bytes
	) -> str | None:
		"""先驗證後寫入 MIFARE block；成功回傳 None，失敗回傳原因。"""
		if len(data) != 16:
			return f"block {block} write data length is not 16 bytes"
		if not self.mifare_authenticate(uid, block, key):
			return f"block {block} authentication failed"

		result = self.in_data_exchange_status(
			bytes([0xA0, block]) + data, timeout_ms=800
		)
		if result is None:
			return f"block {block} write timed out or no response"
		status, _payload = result
		if status != 0x00:
			return (
				f"block {block} write failed: PN532 0x{status:02X} "
				f"({describe_pn532_error(status)})"
			)
		return None

	def read_aime_block_2(
		self, uid: bytes, key: bytes | None = None
	) -> tuple[bytes, bytes] | None:
		"""讀取 block 2，並回傳成功使用的 key。"""
		keys = (key,) if key is not None else (KEY_A, KEY_B)
		for current_key in keys:
			data = self.mifare_read_block(uid, 2, current_key)
			if data is not None:
				return data, current_key
		return None

	def read_aimeID(self, uid: bytes, key: bytes | None = None) -> bytes | None:
		"""讀取 block 2 的第 7-16 位資料；未指定 key 時使用 constants.py 定義的 key。"""
		result = self.read_aime_block_2(uid, key)
		if result is None:
			return None
		data, _key = result
		return data[6:16]


def parse_iso14443a_uid(data: bytes) -> bytes | None:
	"""解析 InListPassiveTarget 的 ISO14443A UID。"""
	# data: [NbTg, Tg, ATQA(2), SAK(1), UID_LEN(1), UID(N), ...]
	if len(data) < 6 or data[0] < 1:
		return None
	uid_len = data[5]
	uid = data[6 : 6 + uid_len]
	if len(uid) != uid_len or uid_len == 0:
		return None
	return bytes(uid)


def _parse_response_frame(frame: bytes, resp_cmd: int) -> bytes | None:
	idx = _find_preamble(frame)
	if idx is None:
		return None
	length = frame[idx + 3]
	lcs = frame[idx + 4]
	if (length + lcs) & 0xFF != 0:
		return None
	if length == 0:
		return None  # ACK 帧，跳過
	data_end = idx + 5 + length
	if data_end + 2 > len(frame):
		return None
	body = frame[idx + 5 : data_end]
	dcs = frame[data_end]
	if (sum(body) + dcs) & 0xFF != 0:
		return None
	if body[0] != PN532_TFI_RESPONSE or body[1] != resp_cmd:
		return None
	return body[2:]


def _find_preamble(frame: bytes) -> int | None:
	"""在 HID report 中尋找 PN532 preamble 00 00 FF 的起始索引。"""
	for i in range(len(frame) - 6):
		if frame[i] == 0x00 and frame[i + 1] == 0x00 and frame[i + 2] == 0xFF:
			return i
	return None
