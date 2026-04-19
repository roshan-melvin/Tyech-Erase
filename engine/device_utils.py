#!/usr/bin/env python3
"""
Device detection and management utilities for Tyech Secure Eraser.
"""

import json
import subprocess
from .utils import run_cmd


def get_device_details(device_name):
    """Get detailed device information using hdparm."""
    details = {
        "name": device_name,
        "hdparm_info": {},
        "smart_info": {}
    }
    
    # Get hdparm information
    hdparm_cmd = f"hdparm -I /dev/{device_name} 2>/dev/null"
    hdparm_output = run_cmd(hdparm_cmd)
    if hdparm_output:
        details["hdparm_info"]["raw"] = hdparm_output
        # Parse serial number and model
        for line in hdparm_output.splitlines():
            line = line.strip()
            if "Serial Number:" in line:
                details["hdparm_info"]["serial"] = line.split(":", 1)[1].strip()
            elif "Model Number:" in line:
                details["hdparm_info"]["model"] = line.split(":", 1)[1].strip()
    
    # Get SMART info for SSDs/HDDs
    smart_cmd = f"smartctl -i /dev/{device_name} 2>/dev/null"
    smart_output = run_cmd(smart_cmd)
    if smart_output:
        details["smart_info"]["raw"] = smart_output
    
    return details


def get_device_size_bytes(device_name):
    """Get device size in bytes."""
    try:
        cmd = f"blockdev --getsize64 /dev/{device_name}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except:
        pass
    return None


def list_devices():
    """List all available storage devices categorized by type."""
    output = {
        "usb": [],
        "nvme": [],
        "hdd": [],
        "ssd": [],
        "adb": [],
        "fastboot": []
    }

    # --- Parse lsblk JSON ---
    lsblk_raw = run_cmd("lsblk -o NAME,SIZE,MODEL,ROTA,RM,TYPE -J")
    try:
        lsblk_json = json.loads(lsblk_raw)
    except:
        lsblk_json = {"blockdevices": []}

    for dev in lsblk_json.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue

        name = dev.get("name")
        size = dev.get("size")
        model = (dev.get("model") or "").upper()
        rota = dev.get("rota")
        rm = str(dev.get("rm"))

        if rm == "1":
            output["usb"].append({"name": name, "size": size, "model": model})
        elif name.startswith("nvme"):
            output["nvme"].append({"name": name, "size": size, "model": model})
        elif rota is True and ("FLASH" in model or "USB" in model):
            output["usb"].append({"name": name, "size": size, "model": model})
        elif rota is True:
            output["hdd"].append({"name": name, "size": size, "model": model})
        elif rota is False:
            output["ssd"].append({"name": name, "size": size, "model": model})

    # --- Detect NVMe devices via nvme-cli as fallback ---
    nvme_raw = run_cmd("nvme list 2>/dev/null | tail -n +3")
    for line in nvme_raw.splitlines():
        parts = line.split()
        if len(parts) >= 1:
            nvme_device = parts[0].split('/')[-1]
            if not any(dev["name"] == nvme_device for dev in output["nvme"]):
                output["nvme"].append({"name": nvme_device, "size": "Unknown", "model": "NVMe Device"})

    # --- Android devices via adb ---
    adb_raw = run_cmd("adb devices")
    adb_devices = []
    for line in adb_raw.splitlines()[1:]:
        if line.strip() and "device" in line:
            device_id = line.split()[0]
            adb_devices.append({"id": device_id, "status": "connected"})
    output["adb"] = adb_devices if adb_devices else "adb not installed or no devices"

    # --- Android devices via fastboot ---
    fastboot_raw = run_cmd("fastboot devices")
    fastboot_devices = []
    for line in fastboot_raw.splitlines():
        if line.strip():
            device_id = line.split()[0]
            fastboot_devices.append({"id": device_id, "status": "fastboot"})
    output["fastboot"] = fastboot_devices if fastboot_devices else "fastboot not installed or no devices"

    return json.dumps(output, indent=2)
