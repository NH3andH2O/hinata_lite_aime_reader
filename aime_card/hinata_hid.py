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


def find_devices() -> tuple[bytes, bytes]:
	"""枚舉 HINATA 讀取器，回傳 (read_path, write_path)。"""
	read_path: bytes | None = None
	write_path: bytes | None = None
	for info in hid.enumerate(HINATA_VID, 0):
		usage_page = info.get("usage_page", 0)
		path = info["path"]
		display_path = (
			path.decode("utf-8", errors="ignore")
			if isinstance(path, bytes)
			else str(path)
		)
		product = info.get("product_string") or ""
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

	if read_path is None or write_path is None:
		raise RuntimeError(
			"Could not find a complete read/write interface for the HINATA reader "
			"(VID=0xF822). Please confirm the device is connected."
		)
	return read_path, write_path


class HinataDevice:
	"""封裝 HINATA HID 讀寫。"""

	def __init__(self, read_path: bytes, write_path: bytes) -> None:
		self._read_dev = hid.device()
		self._read_dev.open_path(read_path)
		self._write_dev = hid.device()
		self._write_dev.open_path(write_path)
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
