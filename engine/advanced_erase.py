#!/usr/bin/env python3
"""
Advanced erase methods for cutting-edge security based on latest research.
Implements NIST SP 800-88 Rev. 1 with modern hardware-specific optimizations.
"""

import os
import sys
import time
import datetime
import subprocess
import re
from .utils import run_cmd


class AdvancedEraseEngine:
    """Advanced erase methods based on latest research findings."""
    
    def __init__(self):
        self.erase_log = []
    
    def log_message(self, message, level="INFO"):
        """Log message with timestamp."""
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f]")
        log_entry = f"{timestamp} {level}: {message}"
        self.erase_log.append(log_entry)
        print(log_entry)
    
    def detect_nvme_device(self, device):
        """Detect if device is NVMe for optimized erasure."""
        try:
            # Check if device is NVMe
            result = run_cmd(f"lsblk -o NAME,TRAN | grep {device}")
            if result and "nvme" in result.lower():
                return True
            
            # Alternative check using nvme-cli
            result = run_cmd("nvme list")
            if result and device in result:
                return True
            
            return False
        except:
            return False
    
    def nvme_sanitize_erase(self, device):
        """
        Perform NVMe Sanitize command - fastest and most secure for NVMe SSDs.
        Based on research: more effective than overwrite due to wear-leveling.
        """
        self.log_message(f"Starting NVMe Sanitize for {device}")
        
        try:
            # Check if nvme-cli is available
            result = run_cmd("which nvme")
            if not result:
                self.log_message("nvme-cli not found, falling back to standard erase", "WARNING")
                return False
            
            # Get NVMe device path
            nvme_device = f"/dev/{device}"
            if not device.startswith("nvme"):
                # Convert block device to nvme device
                result = run_cmd(f"ls -la /dev/{device}")
                if not result:
                    return False
            
            # Perform NVMe sanitize (crypto erase if supported, block erase otherwise)
            self.log_message("Attempting NVMe Crypto Erase (instant secure erase)")
            result = run_cmd(f"nvme sanitize {nvme_device} --sanact=0x02")  # Crypto Erase
            
            if result and "success" in result.lower():
                self.log_message("NVMe Crypto Erase completed successfully")
                return True
            
            # Fallback to block erase
            self.log_message("Crypto erase not supported, attempting Block Erase")
            result = run_cmd(f"nvme sanitize {nvme_device} --sanact=0x01")  # Block Erase
            
            if result and "success" in result.lower():
                self.log_message("NVMe Block Erase completed successfully")
                return True
            
            return False
            
        except Exception as e:
            self.log_message(f"NVMe sanitize failed: {e}", "ERROR")
            return False
    
    def ata_secure_erase(self, device):
        """
        Perform ATA Secure Erase - hardware-level erasure for SATA SSDs.
        Research shows this is more effective than software overwrite.
        """
        self.log_message(f"Starting ATA Secure Erase for {device}")
        
        try:
            device_path = f"/dev/{device}"
            
            # Check if device supports secure erase
            result = run_cmd(f"hdparm -I {device_path} | grep -i 'erase'")
            if not result or "not supported" in result.lower():
                self.log_message("ATA Secure Erase not supported by device", "WARNING")
                return False
            
            # Check if device is frozen
            if "frozen" in result.lower():
                self.log_message("Device is frozen, attempting to unfreeze")
                # Try to unfreeze by suspend/resume cycle
                run_cmd("echo mem > /sys/power/state")
                time.sleep(2)
            
            # Set user password (required for secure erase)
            self.log_message("Setting temporary user password")
            result = run_cmd(f"hdparm --user-master u --security-set-pass password {device_path}")
            
            if "failed" in result.lower():
                self.log_message("Failed to set security password", "ERROR")
                return False
            
            # Perform secure erase
            self.log_message("Executing ATA Secure Erase command")
            result = run_cmd(f"hdparm --user-master u --security-erase password {device_path}")
            
            if "failed" in result.lower():
                self.log_message("ATA Secure Erase failed", "ERROR")
                return False
            
            self.log_message("ATA Secure Erase completed successfully")
            return True
            
        except Exception as e:
            self.log_message(f"ATA Secure Erase failed: {e}", "ERROR")
            return False
    
    def enhanced_hpa_dco_erase(self, device):
        """
        Enhanced HPA/DCO detection and erasure based on forensic research.
        Addresses 'invisible data' problem in hidden areas.
        """
        self.log_message(f"Starting enhanced HPA/DCO erasure for {device}")
        
        try:
            device_path = f"/dev/{device}"
            
            # Detect HPA (Host Protected Area)
            self.log_message("Scanning for Host Protected Areas (HPA)")
            result = run_cmd(f"hdparm -N {device_path}")
            
            if result and "/" in result:
                # HPA detected - format: sectors = 123456/789012
                sectors_info = re.search(r'(\d+)/(\d+)', result)
                if sectors_info:
                    current_sectors = int(sectors_info.group(1))
                    max_sectors = int(sectors_info.group(2))
                    
                    if current_sectors < max_sectors:
                        hidden_sectors = max_sectors - current_sectors
                        self.log_message(f"HPA detected: {hidden_sectors} hidden sectors")
                        
                        # Disable HPA to access hidden area
                        self.log_message("Disabling HPA to access hidden sectors")
                        run_cmd(f"hdparm -N p{max_sectors} {device_path}")
                        
                        # Erase the hidden area
                        self.log_message("Erasing HPA hidden area")
                        hidden_start = current_sectors * 512
                        hidden_size = hidden_sectors * 512
                        
                        # Use dd to zero out hidden area
                        run_cmd(f"dd if=/dev/zero of={device_path} bs=512 seek={current_sectors} count={hidden_sectors} conv=notrunc")
            
            # Detect DCO (Device Configuration Overlay)
            self.log_message("Scanning for Device Configuration Overlay (DCO)")
            result = run_cmd(f"hdparm --dco-identify {device_path}")
            
            if result and "DCO" in result:
                self.log_message("DCO detected, attempting to restore full capacity")
                run_cmd(f"hdparm --dco-restore {device_path}")
            
            self.log_message("HPA/DCO erasure completed")
            return True
            
        except Exception as e:
            self.log_message(f"HPA/DCO erasure failed: {e}", "ERROR")
            return False
    
    def opal_self_encrypting_erase(self, device):
        """
        OPAL Self-Encrypting Drive cryptographic erase.
        Instant secure erase by changing encryption keys.
        """
        self.log_message(f"Checking for OPAL SED support on {device}")
        
        try:
            device_path = f"/dev/{device}"
            
            # Check if sedutil is available
            result = run_cmd("which sedutil-cli")
            if not result:
                self.log_message("sedutil-cli not found, skipping OPAL erase", "WARNING")
                return False
            
            # Scan for OPAL support
            result = run_cmd(f"sedutil-cli --scan {device_path}")
            
            if result and ("OPAL" in result or "Enterprise" in result):
                self.log_message("OPAL SED detected, performing cryptographic erase")
                
                # Perform PSID revert (cryptographic erase)
                result = run_cmd(f"sedutil-cli --yesIreallywanttoERASEALLmydatausingthePSID {device_path}")
                
                if result and "success" in result.lower():
                    self.log_message("OPAL cryptographic erase completed successfully")
                    return True
            
            return False
            
        except Exception as e:
            self.log_message(f"OPAL erase failed: {e}", "ERROR")
            return False
    
    def intelligent_erase_selection(self, device, device_type):
        """
        Intelligently select the fastest and most secure erase method
        based on device type and capabilities.
        """
        self.log_message(f"Performing intelligent erase method selection for {device}")
        
        # Priority order based on research:
        # 1. OPAL SED (instant cryptographic erase)
        # 2. NVMe Sanitize (hardware-level, very fast)
        # 3. ATA Secure Erase (hardware-level, fast)
        # 4. Enhanced HPA/DCO + standard erase (comprehensive)
        
        success = False
        method_used = "none"
        
        # Try OPAL SED first (fastest if available)
        if self.opal_self_encrypting_erase(device):
            success = True
            method_used = "OPAL SED Cryptographic Erase"
        
        # Try NVMe Sanitize for NVMe devices
        elif self.detect_nvme_device(device) and self.nvme_sanitize_erase(device):
            success = True
            method_used = "NVMe Sanitize"
        
        # Try ATA Secure Erase for SATA SSDs
        elif device_type in ["ssd", "hdd"] and self.ata_secure_erase(device):
            success = True
            method_used = "ATA Secure Erase"
        
        # Always perform HPA/DCO erase for comprehensive coverage
        if device_type in ["ssd", "hdd"]:
            self.enhanced_hpa_dco_erase(device)
        
        self.log_message(f"Intelligent erase completed using: {method_used}")
        return success, method_used
    
    def get_erase_log(self):
        """Return the complete erase log."""
        return self.erase_log
