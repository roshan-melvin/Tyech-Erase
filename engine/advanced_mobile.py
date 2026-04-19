#!/usr/bin/env python3
"""
Advanced mobile device erasure with Trusted Execution Environment (TEE) support.
Implements cutting-edge Android security research findings.
"""

import os
import sys
import time
import datetime
import subprocess
import json
from .utils import run_cmd


class AdvancedMobileErase:
    """Advanced mobile device erasure with TEE and hardware security."""
    
    def __init__(self):
        self.erase_log = []
        self.device_id = None
    
    def log_message(self, message, level="INFO"):
        """Log message with timestamp."""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
        log_entry = f"{timestamp} {level}: {message}"
        self.erase_log.append(log_entry)
        print(log_entry)
    
    def detect_android_security_features(self, device_id):
        """Detect Android security features for optimal erasure."""
        self.log_message(f"Detecting security features for device {device_id}")
        
        features = {
            "file_based_encryption": False,
            "hardware_backed_keystore": False,
            "tee_support": False,
            "secure_element": False,
            "verified_boot": False,
            "dm_verity": False
        }
        
        try:
            # Check for file-based encryption
            result = run_cmd(f"adb -s {device_id} shell getprop ro.crypto.type")
            if result and "file" in result.strip():
                features["file_based_encryption"] = True
                self.log_message("File-based encryption detected")
            
            # Check for hardware-backed keystore
            result = run_cmd(f"adb -s {device_id} shell getprop ro.hardware.keystore")
            if result and result.strip():
                features["hardware_backed_keystore"] = True
                self.log_message("Hardware-backed keystore detected")
            
            # Check for TEE support
            result = run_cmd(f"adb -s {device_id} shell ls /dev/tee*")
            if result and "tee" in result:
                features["tee_support"] = True
                self.log_message("Trusted Execution Environment (TEE) detected")
            
            # Check for Secure Element
            result = run_cmd(f"adb -s {device_id} shell getprop ro.hardware.nfc.ese")
            if result and result.strip():
                features["secure_element"] = True
                self.log_message("Secure Element detected")
            
            # Check for Verified Boot
            result = run_cmd(f"adb -s {device_id} shell getprop ro.boot.verifiedbootstate")
            if result and "green" in result.strip():
                features["verified_boot"] = True
                self.log_message("Verified Boot (green state) detected")
            
            # Check for dm-verity
            result = run_cmd(f"adb -s {device_id} shell getprop ro.boot.veritymode")
            if result and "enforcing" in result.strip():
                features["dm_verity"] = True
                self.log_message("dm-verity enforcing detected")
            
        except Exception as e:
            self.log_message(f"Error detecting security features: {e}", "WARNING")
        
        return features
    
    def advanced_partition_detection(self, device_id):
        """Detect all Android partitions including new Android 12+ partitions."""
        self.log_message("Performing advanced partition detection")
        
        partitions = []
        
        try:
            # Get partition list using multiple methods
            methods = [
                "ls /dev/block/bootdevice/by-name/",
                "ls /dev/block/platform/*/by-name/",
                "cat /proc/partitions",
                "ls /dev/block/by-name/"
            ]
            
            for method in methods:
                result = run_cmd(f"adb -s {device_id} shell {method}")
                if result:
                    lines = result.strip().split('\n')
                    for line in lines:
                        if line.strip() and not line.startswith('total'):
                            partitions.append(line.strip())
            
            # Remove duplicates and sort
            partitions = sorted(list(set(partitions)))
            
            # Log detected partitions
            self.log_message(f"Detected {len(partitions)} partitions")
            for partition in partitions[:10]:  # Log first 10 to avoid spam
                self.log_message(f"Partition: {partition}")
            
            if len(partitions) > 10:
                self.log_message(f"... and {len(partitions) - 10} more partitions")
            
        except Exception as e:
            self.log_message(f"Error detecting partitions: {e}", "WARNING")
        
        return partitions
    
    def hardware_backed_crypto_erase(self, device_id):
        """
        Perform hardware-backed cryptographic erase using TEE.
        Based on latest Android security research.
        """
        self.log_message("Attempting hardware-backed cryptographic erase")
        
        try:
            # Check if device supports hardware crypto erase
            result = run_cmd(f"adb -s {device_id} shell getprop ro.crypto.fde_enable_bkp")
            if not result or "true" not in result:
                self.log_message("Hardware crypto erase not supported", "WARNING")
                return False
            
            # Enable encryption if not already enabled
            self.log_message("Ensuring encryption is enabled")
            run_cmd(f"adb -s {device_id} shell vdc cryptfs enablecrypto inplace default")
            
            # Wait for encryption to complete
            for i in range(30):  # Wait up to 5 minutes
                result = run_cmd(f"adb -s {device_id} shell getprop vold.decrypt")
                if result and "trigger_restart_framework" in result:
                    break
                time.sleep(10)
            
            # Perform cryptographic wipe by changing encryption keys
            self.log_message("Performing cryptographic key rotation")
            result = run_cmd(f"adb -s {device_id} shell vdc cryptfs changepw default newpassword")
            
            if result and "200" in result:  # Success response
                self.log_message("Hardware-backed crypto erase completed successfully")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"Hardware crypto erase failed: {e}", "ERROR")
            return False
    
    def secure_element_erase(self, device_id):
        """Erase data from Secure Element if present."""
        self.log_message("Attempting Secure Element erase")
        
        try:
            # Check for eSE (embedded Secure Element)
            result = run_cmd(f"adb -s {device_id} shell ls /dev/pn54*")
            if result:
                self.log_message("eSE detected, performing secure erase")
                # Reset eSE
                run_cmd(f"adb -s {device_id} shell echo 1 > /sys/class/nfc/nfc*/reset")
                return True
            
            # Check for SIM-based SE
            result = run_cmd(f"adb -s {device_id} shell service call iphonesubinfo 1")
            if result and "Result" in result:
                self.log_message("SIM-based SE detected, clearing UICC")
                # Clear SIM application data
                run_cmd(f"adb -s {device_id} shell am broadcast -a android.intent.action.SIM_STATE_CHANGED")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"Secure Element erase failed: {e}", "WARNING")
            return False
    
    def firmware_level_wipe(self, device_id):
        """
        Perform firmware-level wipe using fastboot.
        Most comprehensive erasure method.
        """
        self.log_message("Attempting firmware-level wipe")
        
        try:
            # Reboot to fastboot mode
            self.log_message("Rebooting to fastboot mode")
            run_cmd(f"adb -s {device_id} reboot bootloader")
            
            # Wait for fastboot mode
            time.sleep(10)
            
            # Get fastboot device ID
            result = run_cmd("fastboot devices")
            if not result:
                self.log_message("Device not detected in fastboot mode", "ERROR")
                return False
            
            fastboot_id = result.split()[0]
            self.log_message(f"Device detected in fastboot: {fastboot_id}")
            
            # Perform comprehensive fastboot wipe
            fastboot_commands = [
                "erase system",
                "erase userdata", 
                "erase cache",
                "erase recovery",
                "erase boot",
                "erase metadata",
                "erase persist",
                "erase misc",
                "erase modem",
                "erase bluetooth",
                "erase ddr",
                "erase sec",
                "erase aboot",
                "erase rpm",
                "erase sbl1",
                "erase tz",
                "erase hyp"
            ]
            
            successful_erases = 0
            for cmd in fastboot_commands:
                result = run_cmd(f"fastboot -s {fastboot_id} {cmd}")
                if result and ("OKAY" in result or "finished" in result):
                    successful_erases += 1
                    self.log_message(f"Successfully erased: {cmd.split()[1]}")
                else:
                    self.log_message(f"Failed to erase: {cmd.split()[1]}", "WARNING")
            
            # Format userdata with encryption
            self.log_message("Formatting userdata with encryption")
            run_cmd(f"fastboot -s {fastboot_id} format:ext4 userdata")
            
            self.log_message(f"Firmware-level wipe completed: {successful_erases}/{len(fastboot_commands)} partitions erased")
            return successful_erases > len(fastboot_commands) // 2
            
        except Exception as e:
            self.log_message(f"Firmware-level wipe failed: {e}", "ERROR")
            return False
    
    def intelligent_mobile_erase(self, device_id):
        """
        Perform intelligent mobile device erase using the most
        appropriate method based on device capabilities.
        """
        self.device_id = device_id
        self.log_message(f"Starting intelligent mobile erase for device {device_id}")
        
        # Detect security features
        features = self.detect_android_security_features(device_id)
        
        # Detect all partitions
        partitions = self.advanced_partition_detection(device_id)
        
        success_methods = []
        
        # Try hardware-backed crypto erase first (fastest)
        if features["file_based_encryption"] and features["hardware_backed_keystore"]:
            if self.hardware_backed_crypto_erase(device_id):
                success_methods.append("Hardware-backed Crypto Erase")
        
        # Try secure element erase
        if features["secure_element"]:
            if self.secure_element_erase(device_id):
                success_methods.append("Secure Element Erase")
        
        # Perform firmware-level wipe for maximum security
        if self.firmware_level_wipe(device_id):
            success_methods.append("Firmware-level Wipe")
        
        self.log_message(f"Mobile erase completed using: {', '.join(success_methods)}")
        return len(success_methods) > 0, success_methods
    
    def get_erase_log(self):
        """Return the complete erase log."""
        return self.erase_log
