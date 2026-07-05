from __future__ import annotations

import argparse

from . import __version__
from .nfc_reader import run_read_mode, run_write_mode


def _is_20_digit_value(value: str) -> bool:
	return len(value) == 20 and value.isdigit()


def main(argv: list[str] | None = None) -> int:
	parser = argparse.ArgumentParser(description="HINATA NFC Aime read/write tool")
	mode = parser.add_mutually_exclusive_group(required=True)
	mode.add_argument(
		"-r",
		"--read",
		action="store_true",
		help="Read mode (continuously scan for cards and read card data)",
	)
	mode.add_argument(
		"-w",
		"--write",
		nargs="?",
		const="",
		metavar="AIME_ID",
		help="Write mode; optionally specify an Aime ID, otherwise one is generated randomly",
	)
	parser.add_argument(
		"-l",
		"--loop",
		action="store_true",
		help="Loop write mode; only available when no Aime ID is specified",
	)
	args = parser.parse_args(argv)
	print(f"HINATA Lite Aime Reader v{__version__}")

	if args.read:
		if args.loop:
			parser.error("--loop can only be used with --write")
		return run_read_mode()

	write_value = args.write or None
	if write_value is not None and not _is_20_digit_value(write_value):
		parser.error("--write Aime ID is invalid")
	if args.loop and write_value is not None:
		parser.error(
			"--loop is only available with --write when no Aime ID is specified"
		)
	return run_write_mode(write_value, loop=args.loop)
