from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .constants import HINATA_VID

UDEV_RULE_PATH = Path("/etc/udev/rules.d/99-hinata.rules")

_VID_HEX = f"{HINATA_VID:04x}"

UDEV_RULE_CONTENT = f"""# HINATA Lite Aime reader (VID=0x{_VID_HEX.upper()})
# 讓一般使用者可存取 hidraw 及 usb 節點，無須 root。
SUBSYSTEM=="hidraw", ATTRS{{idVendor}}=="{_VID_HEX}", MODE="0660", GROUP="plugdev", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{{idVendor}}=="{_VID_HEX}", MODE="0660", GROUP="plugdev", TAG+="uaccess"
"""


def install_udev_rules() -> int:
	"""安裝 udev 規則，讓一般使用者免 sudo 存取 HINATA 讀卡器（僅 Linux）。"""
	if sys.platform != "linux":
		print("[udev] Skipped: udev rules are only needed on Linux.")
		return 0

	if shutil.which("sudo") is None:
		print(
			"[udev] 'sudo' not found. Please run this command as root, or manually "
			f"create {UDEV_RULE_PATH} with the following content:\n\n{UDEV_RULE_CONTENT}"
		)
		return 1

	print(f"[udev] Installing rule to {UDEV_RULE_PATH} (requires sudo)...")
	try:
		# 透過 sudo tee 寫入需要 root 權限的檔案。
		subprocess.run(
			["sudo", "tee", str(UDEV_RULE_PATH)],
			input=UDEV_RULE_CONTENT.encode("utf-8"),
			stdout=subprocess.DEVNULL,
			check=True,
		)
		subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)
		subprocess.run(["sudo", "udevadm", "trigger"], check=True)
	except subprocess.CalledProcessError as exc:
		print(f"[udev] Failed to install rules: {exc}")
		return 1

	print(
		"[udev] Done. If the device is already plugged in, please re-plug it "
		"(or it should now be accessible). No sudo needed to run the reader afterwards."
	)
	return 0
