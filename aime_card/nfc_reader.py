from __future__ import annotations

import secrets
import sys
import time

from .constants import (
	DEFAULT_BLANK_KEY,
	KEY_A,
	KEY_B,
	MANUFACTURER_NAMES,
	MIFARE_1K_SECTOR_COUNT,
	MIFARE_BLOCKS_PER_SECTOR,
	MIFARE_DEFAULT_ACCESS_BITS,
)
from .hinata_hid import HinataDevice, find_devices
from .pn532 import Pn532Transport


def describe_manufacturer(code: int) -> str:
	return MANUFACTURER_NAMES.get(code, "Unknown manufacturer")


def run_read_mode() -> int:
	print("=== HINATA NFC UID Read Test (--read/-r) ===")
	try:
		read_path, write_path = find_devices()
	except RuntimeError as exc:
		print(f"[Error] {exc}", file=sys.stderr)
		return 1

	try:
		with HinataDevice(read_path, write_path) as device:
			pn532 = Pn532Transport(device)
			pn532.sam_configuration()
			print(
				"[Ready] PN532 initialized. Starting continuous card scan (Ctrl+C to stop)...\n"
			)
			_read_loop(pn532)
	except KeyboardInterrupt:
		print("\n[Stopped] Reading stopped.")
		return 0
	return 0


def run_write_mode(aime_id: str | None, loop: bool = False) -> int:
	mode_label = "Random Loop Write" if loop else "Write"
	print(f"=== HINATA NFC Aime {mode_label} Test (--write/-w) ===")
	try:
		read_path, write_path = find_devices()
	except RuntimeError as exc:
		print(f"[Error] {exc}", file=sys.stderr)
		return 1

	try:
		with HinataDevice(read_path, write_path) as device:
			pn532 = Pn532Transport(device)
			pn532.sam_configuration()
			print(
				"[Ready] PN532 initialized. Place the card to write (Ctrl+C to stop)...\n"
			)
			while True:
				current_id = (
					aime_id if aime_id is not None else generate_random_aime_id()
				)
				print(f"[Data] Aime ID for this write: {_format_aime_id(current_id)}")
				_wait_and_write_card(pn532, current_id)
				if not loop:
					break
				_wait_card_removed(pn532)
	except KeyboardInterrupt:
		print("\n[Stopped] Writing stopped.")
		return 0
	return 0


def generate_random_aime_id() -> str:
	first_digit = secrets.choice("012456789")
	remaining_digits = "".join(secrets.choice("0123456789") for _ in range(19))
	return first_digit + remaining_digits


def _format_aime_id(value: bytes | str) -> str:
	digits: str
	if isinstance(value, str):
		digits = value
	else:
		digits = bytes(value).hex().upper()
	return " ".join(digits[index : index + 4] for index in range(0, len(digits), 4))


def _read_loop(pn532: Pn532Transport) -> None:
	last_uid: bytes | None = None
	while True:
		uid = pn532.poll_iso14443a()
		if uid is None:
			# 卡片已移除，重置狀態以便讀取下一張
			last_uid = None
			time.sleep(0.3)
			continue
		if uid == last_uid:
			# 同一張卡仍在感應區，避免重複讀取
			time.sleep(0.1)
			continue

		last_uid = uid
		time.sleep(0.5)
		_print_card(uid, pn532)


def _print_card(uid: bytes, pn532: Pn532Transport) -> None:
	manufacturer_code = uid[0]
	uid_hex = uid.hex(" ").upper()
	print("[NFC card detected]")
	print(f"  UID        : {uid_hex}")
	print(
		f"  Manufacturer code: 0x{manufacturer_code:02X} "
		f"({describe_manufacturer(manufacturer_code)})"
	)

	status, data = _read_card_payload(uid, pn532)
	if status == "standard":
		print("  Verification result: Aime card")
		if data is not None:
			_print_block_3_data(data)
	elif status == "blank":
		print("  Verification result: blank card")
	elif status == "non_standard":
		print("  Verification result: non-standard card")
	else:
		print("  Verification result: unknown")

	print("  Read complete. Waiting for the next card...\n")


def _read_card_payload(uid: bytes, pn532: Pn532Transport) -> tuple[str, bytes | None]:
	data = pn532.read_aimeID(uid)
	if data is not None:
		return "standard", data

	# 驗證失敗後重新選卡，避免前一次錯 key 讓卡片停在不可讀狀態。
	pn532.poll_iso14443a()
	blank_data = pn532.read_aimeID(uid, DEFAULT_BLANK_KEY)
	if blank_data is not None and _looks_like_blank(blank_data):
		return "blank", None

	return "non_standard", None


def _looks_like_blank(data: bytes) -> bool:
	return all(value == 0x00 for value in data) or all(value == 0xFF for value in data)


def _print_block_3_data(data: bytes) -> None:
	print(f"  Aime ID    : {_format_aime_id(data)}")


def _wait_and_write_card(pn532: Pn532Transport, aime_id: str) -> str:
	while True:
		uid = pn532.poll_iso14443a()
		if uid is None:
			time.sleep(0.3)
			continue

		time.sleep(0.5)
		uid_hex = uid.hex(" ").upper()
		print("[NFC card detected]")
		print(f"  UID        : {uid_hex}")
		return _write_card(uid, pn532, aime_id)


def _write_card(uid: bytes, pn532: Pn532Transport, aime_id: str) -> str:
	payload = bytes.fromhex(aime_id)
	existing_data = pn532.read_aimeID(uid)
	if existing_data is not None:
		return _write_readable_aime_card(uid, pn532, payload, existing_data)

	# 驗證失敗後重新選卡，避免前一次錯 key 讓卡片停在不可讀狀態。
	pn532.poll_iso14443a()
	blank_block = pn532.mifare_read_block(uid, 2, DEFAULT_BLANK_KEY)
	if blank_block is None:
		print("  Write result: failed")
		print("  Reason      : non-standard card")
		return "failed"
	if not _looks_like_blank(blank_block[6:16]):
		print("  Write result: failed")
		print(
			"  Reason      : the card is readable with the blank-card key, but block 2 bytes 7-16 are not blank"
		)
		return "failed"

	print("  Verification result: blank card")
	error = _write_blank_card(uid, pn532, payload, blank_block)
	if error is not None:
		print("  Write result: failed")
		print(f"  Reason      : {error}")
		return "failed"
	print("  Write result: success")
	print(f"  Aime ID    : {_format_aime_id(payload)}")
	return "written"


def _write_readable_aime_card(
	uid: bytes, pn532: Pn532Transport, payload: bytes, existing_data: bytes
) -> str:
	print("  Verification result: Aime card")
	print(f"  Original Aime ID: {_format_aime_id(existing_data)}")
	if not _looks_like_blank(existing_data) and not _confirm_overwrite():
		print("  Write result: canceled; original data was not overwritten")
		return "skipped"

	block_result = pn532.read_aime_block_2(uid)
	if block_result is None:
		print("  Write result: failed")
		print("  Reason      : could not reread block 2 to preserve the other bytes")
		return "failed"

	block_data, key = block_result
	new_block = bytearray(block_data)
	new_block[6:16] = payload
	error = pn532.mifare_write_block(uid, 2, key, bytes(new_block))
	if error is not None:
		print("  Write result: failed")
		print(f"  Reason      : {error}")
		return "failed"

	print("  Write result: success")
	print(f"  Aime ID    : {_format_aime_id(payload)}")
	return "written"


def _write_blank_card(
	uid: bytes, pn532: Pn532Transport, payload: bytes, block_2: bytes
) -> str | None:
	for sector in range(MIFARE_1K_SECTOR_COUNT):
		trailer_block = sector * MIFARE_BLOCKS_PER_SECTOR + (
			MIFARE_BLOCKS_PER_SECTOR - 1
		)
		trailer_data = pn532.mifare_read_block(uid, trailer_block, DEFAULT_BLANK_KEY)
		if trailer_data is None:
			return f"Failed to read sector {sector} trailer block {trailer_block}"

		new_trailer = _build_sector_trailer(trailer_data)
		error = pn532.mifare_write_block(
			uid, trailer_block, DEFAULT_BLANK_KEY, new_trailer
		)
		if error is not None:
			return f"Failed to update sector {sector} keys: {error}"

	new_block = bytearray(block_2)
	new_block[6:16] = payload
	error = pn532.mifare_write_block(uid, 2, KEY_A, bytes(new_block))
	if error is not None:
		return f"Failed to write block 2 Aime ID: {error}"
	return None


def _build_sector_trailer(trailer_data: bytes) -> bytes:
	access_bits = trailer_data[6:10]
	if _looks_like_blank(access_bits):
		access_bits = MIFARE_DEFAULT_ACCESS_BITS
	return KEY_A + access_bits + KEY_B


def _confirm_overwrite() -> bool:
	try:
		answer = input("  The card already contains data. Overwrite? (y/[N]): ")
	except EOFError:
		return False
	return answer.strip().lower() == "y"


def _wait_card_removed(pn532: Pn532Transport) -> None:
	print("  Please remove the card...\n")
	while pn532.poll_iso14443a() is not None:
		time.sleep(0.2)
	time.sleep(0.3)
