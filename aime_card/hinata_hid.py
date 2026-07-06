from __future__ import annotations

from types import TracebackType

import hid

from .constants import (
	HINATA_VID,
	REPORT_ID,
	REPORT_LEN,
	USAGE_PAGE_READ,
	USAGE_PAGE_WRITE,
)


def _display_path(path: bytes | str) -> str:
	return (
		path.decode("utf-8", errors="ignore") if isinstance(path, bytes) else str(path)
	)


def find_devices() -> tuple[bytes, bytes]:
	"""枚舉 HINATA 讀取器，回傳 (read_path, write_path)。

	Windows 上 hidapi 會將同一 HID 介面的兩個 top-level collection 分別列為
	usage_page=0x01（讀）與 0x06（寫）兩條 path。
	Linux 上 hidapi 只依 interface 列舉，僅有單一 HID 介面（同時帶有 IN/OUT
	endpoint），usage_page 通常回報為 0x00，因此需退回使用同一條 path 同時讀寫。
	"""
	read_path: bytes | None = None
	write_path: bytes | None = None
	fallback_path: bytes | None = None

	for info in hid.enumerate(HINATA_VID, 0):
		usage_page = info.get("usage_page", 0)
		path = info["path"]
		display_path = _display_path(path)
		product = info.get("product_string") or ""

		if fallback_path is None:
			fallback_path = path

		if usage_page == USAGE_PAGE_READ and read_path is None:
			read_path = path
			print(
				f"[Device] Found READ interface (usage_page=0x01): {display_path} {product}"
			)
		elif usage_page == USAGE_PAGE_WRITE and write_path is None:
			write_path = path
			print(
				f"[Device] Found WRITE interface (usage_page=0x06): {display_path} {product}"
			)

	if read_path is not None and write_path is not None:
		return read_path, write_path

	# 退回：單一 HID 介面同時負責讀寫（Linux hidapi 行為）。
	if fallback_path is not None:
		print(
			"[Device] Using single HID interface for read/write: "
			f"{_display_path(fallback_path)}"
		)
		return fallback_path, fallback_path

	raise RuntimeError(
		"Could not find the HINATA reader (VID=0xF822). "
		"Please confirm the device is connected."
	)


class HinataDevice:
	"""封裝 HINATA HID 讀寫。"""

	def __init__(self, read_path: bytes, write_path: bytes) -> None:
		self._read_dev = hid.device()
		self._read_dev.open_path(read_path)
		if write_path == read_path:
			# Linux：讀寫共用同一 HID 介面，避免重複開啟同一節點造成衝突。
			self._write_dev = self._read_dev
			self._shared_dev = True
		else:
			self._write_dev = hid.device()
			self._write_dev.open_path(write_path)
			self._shared_dev = False
		self._read_dev.set_nonblocking(False)

	def __enter__(self) -> HinataDevice:
		return self

	def __exit__(
		self,
		exc_type: type[BaseException] | None,
		exc_value: BaseException | None,
		traceback: TracebackType | None,
	) -> None:
		self.close()

	def close(self) -> None:
		self._read_dev.close()
		if not self._shared_dev:
			self._write_dev.close()

	def send(self, cmd: int, payload: bytes = b"") -> None:
		"""送出 HINATA 主帧 [ReportID][CMD][PAYLOAD]，補零至定長。"""
		buf = bytearray([REPORT_ID, cmd]) + payload
		if len(buf) > REPORT_LEN + 1:
			raise ValueError("HID report length exceeds the 64-byte payload limit")
		buf.extend(b"\x00" * (REPORT_LEN + 1 - len(buf)))
		self._write_dev.write(bytes(buf))

	def read_frame(self, timeout_ms: int = 500) -> bytes | None:
		"""讀取一個 HID input report。"""
		data = self._read_dev.read(REPORT_LEN + 1, timeout_ms)
		return bytes(data) if data else None
