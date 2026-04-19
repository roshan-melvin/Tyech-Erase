#!/usr/bin/env python3
"""
Main erase engine for secure device erasure operations.
"""

import os
import sys
import time
import signal
import hashlib
import datetime
import subprocess
from .utils import run_cmd
from .progress_tracker import ProgressTracker
from .certificate_generator import CertificateGenerator
from .device_utils import get_device_size_bytes
from .advanced_erase import AdvancedEraseEngine
from .advanced_mobile import AdvancedMobileErase


class EraseEngine:
    """Main erase engine for different device types."""
    
    def __init__(self):
        self.erase_log = []
        self.start_time = None
        self.end_time = None
        self.progress_tracker = ProgressTracker()
        self.current_process = None
        self.interrupted = False
        self.advanced_erase = AdvancedEraseEngine()
        self.advanced_mobile = AdvancedMobileErase()
        
        # Set up signal handlers for graceful interruption only in main thread
        import threading
        if threading.current_thread() == threading.main_thread():
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interruption signals gracefully."""
        self.interrupted = True
        self.log_message("Erase operation interrupted by user", "WARNING")
        
        if self.current_process:
            try:
                self.current_process.terminate()
                time.sleep(2)
                if self.current_process.poll() is None:
                    self.current_process.kill()
            except:
                pass
        
        self.progress_tracker.stop_progress()
        print("\n\nErase operation was interrupted!")
        print("WARNING: Device may be in an inconsistent state.")
        print("You may need to repartition the device to use it again.")
        sys.exit(1)
    
    def log_message(self, message, level="INFO"):
        """Add a message to the erase log."""
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.erase_log.append(log_entry)
        # Don't print during progress display to avoid interfering
        if not self.progress_tracker.is_running:
            print(log_entry)
    
    def erase_device(self, device_name, device_type, method="secure", no_refresh=False):
        """Erase a device based on its type using advanced methods."""
        self.start_time = datetime.datetime.now()
        self.log_message(f"Starting advanced erase of {device_name} (type: {device_type})")
        
        try:
            # Try advanced methods first for better speed and security
            if device_type in ["nvme", "ssd", "hdd"]:
                # Use intelligent erase selection for storage devices
                success, method_used = self.advanced_erase.intelligent_erase_selection(device_name, device_type)
                
                # Merge logs from advanced erase engine
                self.erase_log.extend(self.advanced_erase.get_erase_log())
                
                if success:
                    self.log_message(f"Advanced erase successful using: {method_used}")
                else:
                    self.log_message("Advanced erase failed, falling back to standard methods", "WARNING")
                    # Fallback to standard methods
                    if device_type == "nvme":
                        success = self._erase_nvme(device_name, method, no_refresh)
                    elif device_type == "ssd":
                        success = self._erase_ssd(device_name, method, no_refresh)
                    elif device_type == "hdd":
                        success = self._erase_hdd(device_name, method, no_refresh)
            
            elif device_type == "usb":
                success = self._erase_usb(device_name, method, no_refresh)
            
            elif device_type in ["adb", "fastboot"]:
                # Use advanced mobile erasure
                success, methods_used = self.advanced_mobile.intelligent_mobile_erase(device_name)
                
                # Merge logs from advanced mobile engine
                self.erase_log.extend(self.advanced_mobile.get_erase_log())
                
                if success:
                    self.log_message(f"Advanced mobile erase successful using: {', '.join(methods_used)}")
                else:
                    self.log_message("Advanced mobile erase failed, falling back to standard methods", "WARNING")
                    # Fallback to standard methods
                    if device_type == "adb":
                        success = self._erase_android_adb(device_name)
                    else:
                        success = self._erase_android_fastboot(device_name)
            
            else:
                self.log_message(f"Unsupported device type: {device_type}", "ERROR")
                return False
            
            self.end_time = datetime.datetime.now()
            duration = self.end_time - self.start_time
            
            if success:
                self.log_message(f"Erase completed successfully in {duration}")
                if not no_refresh:
                    self._refresh_device(device_name)
            else:
                self.log_message("Erase failed", "ERROR")
            
            return success
        
        except Exception as e:
            self.log_message(f"Erase failed with exception: {str(e)}", "ERROR")
            return False
        finally:
            self.progress_tracker.stop_progress()
    
    def _erase_nvme(self, device_name, method, no_refresh=False):
        """Erase NVMe device using nvme format command."""
        self.progress_tracker.start_progress(1, "NVMe Format")
        
        if method == "secure":
            cmd = f"nvme format /dev/{device_name} --ses=1"
        else:
            cmd = f"nvme format /dev/{device_name}"
        
        self.log_message(f"Running NVMe format: {cmd}")
        
        # NVMe format doesn't provide progress, so we simulate it
        self.progress_tracker.update_progress(10)
        stdout, stderr, returncode = run_cmd(cmd, capture_stderr=True)
        self.progress_tracker.update_progress(100)
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        
        self.log_message(f"Command output: {stdout}")
        if stderr:
            self.log_message(f"Command stderr: {stderr}")
        
        return returncode == 0
    
    def _erase_ssd(self, device_name, method, no_refresh=False):
        """Erase SATA SSD using hdparm secure erase."""
        # Check if secure erase is supported
        check_cmd = f"hdparm -I /dev/{device_name} | grep -i 'erase'"
        self.log_message(f"Checking secure erase support: {check_cmd}")
        
        if method == "secure":
            self.progress_tracker.start_progress(3, "SSD Secure Erase")
            
            # Set security password
            self.progress_tracker.update_stage(0, "Setting security password", 0)
            cmd1 = f"hdparm --user-master u --security-set-pass p /dev/{device_name}"
            stdout1, stderr1, ret1 = run_cmd(cmd1, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            # Get erase estimate
            self.progress_tracker.update_stage(1, "Getting erase estimate", 0)
            cmd2 = f"hdparm -I /dev/{device_name} | grep -i 'erase'"
            stdout2, stderr2, ret2 = run_cmd(cmd2, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            # Run secure erase
            self.progress_tracker.update_stage(2, "Running secure erase", 0)
            cmd3 = f"hdparm --user-master u --security-erase p /dev/{device_name}"
            stdout3, stderr3, ret3 = run_cmd(cmd3, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            stdout = f"{stdout1}\n{stdout2}\n{stdout3}"
            stderr = f"{stderr1}\n{stderr2}\n{stderr3}"
            returncode = ret3
        else:
            self.progress_tracker.start_progress(1, "Basic SSD Erase")
            cmd = f"dd if=/dev/zero of=/dev/{device_name} bs=64M status=progress"
            stdout, stderr, returncode = self._run_dd_with_progress(cmd)
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        
        self.log_message(f"Command output: {stdout}")
        if stderr:
            self.log_message(f"Command stderr: {stderr}")
        
        return returncode == 0
    
    def _erase_hdd(self, device_name, method, no_refresh=False):
        """Erase HDD using multiple pass overwrite."""
        if method == "secure":
            passes = [
                ("zero", "Writing zeros (Pass 1/3)"),
                ("one", "Writing ones (Pass 2/3)"), 
                ("random", "Writing random data (Pass 3/3)")
            ]
        else:
            passes = [("zero", "Single pass zero write")]
        
        self.progress_tracker.start_progress(len(passes), "Multi-pass HDD Erase")
        
        for i, (pattern, description) in enumerate(passes):
            self.progress_tracker.update_stage(i, description, 0)
            
            if pattern == "zero":
                cmd = f"dd if=/dev/zero of=/dev/{device_name} bs=64M status=progress"
            elif pattern == "one":
                cmd = f"tr '\\0' '\\377' < /dev/zero | dd of=/dev/{device_name} bs=64M status=progress"
            else:  # random
                cmd = f"dd if=/dev/urandom of=/dev/{device_name} bs=64M status=progress"
            
            self.log_message(f"Running pass {i+1}: {cmd}")
            stdout, stderr, returncode = self._run_dd_with_progress(cmd)
            
            if returncode not in [0, 1]:  # 1 is OK for "No space left on device"
                self.log_message(f"Pass {i+1} failed with return code {returncode}", "WARNING")
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        return True
    
    def _erase_usb(self, device_name, method, no_refresh=False):
        """Erase USB device."""
        if method == "format":
            return self._format_usb_quick(device_name, no_refresh)
        elif method == "fast":
            return self._erase_usb_fast(device_name, no_refresh)
        elif method == "quick":
            return self._erase_usb_quick_wipe(device_name, no_refresh)
        
        self.progress_tracker.start_progress(1, "USB Erase")
        
        # Get device size for accurate progress
        device_size = get_device_size_bytes(device_name)
        if device_size:
            self.log_message(f"Device size: {device_size / (1024**3):.2f} GB")
        
        # Optimize block size for speed and compatibility
        # Use larger blocks for better performance, but not too large to avoid memory issues
        cmd = f"dd if=/dev/zero of=/dev/{device_name} bs=64M status=progress conv=fdatasync"
        self.log_message(f"Running optimized USB erase: {cmd}")
        
        # Use enhanced progress tracking
        stdout, stderr, returncode = self._run_dd_with_progress(cmd, device_size)
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        
        self.log_message(f"Command output: {stdout}")
        if stderr:
            self.log_message(f"Command stderr: {stderr}")
        
        # Check if erase was successful
        # For USB devices, several conditions indicate SUCCESS:
        # - Return code 0: Normal completion
        # - Return code 1 + "No space left": Complete device overwritten  
        # - Return code -15 (SIGTERM) + "No space left": Process terminated but succeeded
        success = False
        if returncode == 0:
            success = True
            self.log_message("USB erase completed successfully")
        elif returncode == 1 and stderr and "No space left on device" in stderr:
            success = True
            self.log_message("USB erase completed - entire device overwritten")
        elif returncode == -15 and stderr and "No space left on device" in stderr:
            success = True
            self.log_message("USB erase completed - process terminated after full overwrite")
        elif returncode in [1, -15] and stdout and "copied" in stdout:
            success = True
            self.log_message("USB erase completed - data successfully written")
        else:
            self.log_message(f"USB erase may have failed - return code: {returncode}", "WARNING")
        
        if success:
            self.log_message("USB device successfully erased")
        
        return success
    
    def _erase_usb_fast(self, device_name, no_refresh=False):
        """Fast USB erase - writes zeros to first 1GB + random sampling for speed."""
        self.progress_tracker.start_progress(3, "Fast USB Erase")
        
        # Get device size
        device_size = get_device_size_bytes(device_name)
        if device_size:
            self.log_message(f"Device size: {device_size / (1024**3):.2f} GB")
        
        device_path = f"/dev/{device_name}"
        
        try:
            # Stage 1: Erase first 1GB
            self.progress_tracker.update_stage(0, "Erasing first 1GB", 0)
            cmd1 = f"dd if=/dev/zero of={device_path} bs=64M count=16 status=progress"
            stdout1, stderr1, ret1 = run_cmd(cmd1, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            # Stage 2: Erase partition tables
            self.progress_tracker.update_stage(1, "Erasing partition tables", 0)
            cmd2 = f"dd if=/dev/zero of={device_path} bs=512 count=2048 status=progress"
            stdout2, stderr2, ret2 = run_cmd(cmd2, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            # Stage 3: Random sampling overwrite
            self.progress_tracker.update_stage(2, "Random sampling overwrite", 0)
            if device_size and device_size > 2 * 1024**3:  # > 2GB
                # Write random 64MB blocks at various positions
                for i in range(5):
                    offset = (device_size // 6) * (i + 1)
                    cmd3 = f"dd if=/dev/zero of={device_path} bs=64M count=1 seek={offset // (64*1024*1024)} status=none"
                    run_cmd(cmd3)
                    self.progress_tracker.update_progress((i + 1) * 20)
            else:
                self.progress_tracker.update_progress(100)
            
            self.progress_tracker.stop_progress()
            return True
            
        except Exception as e:
            self.log_message(f"Fast USB erase failed: {e}", "ERROR")
            return False
    
    def _erase_usb_quick_wipe(self, device_name, no_refresh=False):
        """Quick USB wipe - just overwrites first 10MB + partition table (very fast)."""
        self.progress_tracker.start_progress(2, "Quick Wipe")
        
        # Get device size
        device_size = get_device_size_bytes(device_name)
        if device_size:
            self.log_message(f"Device size: {device_size / (1024**3):.2f} GB")
        
        device_path = f"/dev/{device_name}"
        
        try:
            # Stage 1: Erase first 10MB
            self.progress_tracker.update_stage(0, "Erasing first 10MB", 0)
            cmd1 = f"dd if=/dev/zero of={device_path} bs=1M count=10 status=progress"
            stdout1, stderr1, ret1 = run_cmd(cmd1, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            # Stage 2: Erase last 1MB (backup partition tables)
            self.progress_tracker.update_stage(1, "Erasing backup partition tables", 0)
            if device_size:
                last_mb_offset = max(0, (device_size // 1048576) - 1)
                cmd2 = f"dd if=/dev/zero of={device_path} bs=1M count=1 seek={last_mb_offset} status=progress"
            else:
                cmd2 = f"dd if=/dev/zero of={device_path} bs=512 count=2048 status=progress"
            stdout2, stderr2, ret2 = run_cmd(cmd2, capture_stderr=True)
            self.progress_tracker.update_progress(100)
            
            self.progress_tracker.stop_progress()
            return True
            
        except Exception as e:
            self.log_message(f"Quick USB wipe failed: {e}", "ERROR")
            return False
    
    def _format_usb_quick(self, device_name, no_refresh=False):
        """Secure format USB device - overwrites key areas then formats."""
        self.progress_tracker.start_progress(4, "Secure Format")
        device_path = f"/dev/{device_name}"
        
        try:
            # Stage 1: Erase boot area
            self.progress_tracker.update_stage(0, "Erasing boot area", 0)
            cmd1 = f"dd if=/dev/zero of={device_path} bs=1M count=100 status=progress"
            run_cmd(cmd1)
            self.progress_tracker.update_progress(100)
            
            # Stage 2: Create new partition table
            self.progress_tracker.update_stage(1, "Creating partition table", 0)
            cmd2 = f"parted -s {device_path} mklabel msdos"
            run_cmd(cmd2)
            self.progress_tracker.update_progress(100)
            
            # Stage 3: Create partition
            self.progress_tracker.update_stage(2, "Creating partition", 0)
            cmd3 = f"parted -s {device_path} mkpart primary fat32 1MiB 100%"
            run_cmd(cmd3)
            self.progress_tracker.update_progress(100)
            
            # Stage 4: Format filesystem
            self.progress_tracker.update_stage(3, "Formatting filesystem", 0)
            cmd4 = f"mkfs.fat -F32 {device_path}1"
            run_cmd(cmd4)
            self.progress_tracker.update_progress(100)
            
            self.progress_tracker.stop_progress()
            return True
            
        except Exception as e:
            self.log_message(f"USB format failed: {e}", "ERROR")
            return False
    
    def _refresh_device(self, device_name):
        """Refresh device information and notify system of changes."""
        device_path = f"/dev/{device_name}"
        
        try:
            self.log_message("Refreshing device information...")
            run_cmd(f"partprobe {device_path}")
            run_cmd(f"udevadm settle")
            run_cmd(f"udevadm trigger --subsystem-match=block")
            self._update_desktop_files()
            self.log_message("Device refresh completed")
        except Exception as e:
            self.log_message(f"Device refresh failed: {e}", "WARNING")
    
    def _update_desktop_files(self):
        """Update desktop environment to show new drives."""
        try:
            # Update file manager
            run_cmd("pkill -HUP nautilus")  # GNOME
            run_cmd("pkill -HUP thunar")    # XFCE
            run_cmd("pkill -HUP dolphin")   # KDE
            
            # Update desktop
            run_cmd("xdg-desktop-menu forceupdate")
        except Exception as e:
            self.log_message(f"Desktop update failed: {e}", "WARNING")
    
    def _run_dd_with_progress(self, cmd, device_size=None):
        """Run dd command with enhanced progress tracking."""
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.current_process = process
            stdout_lines = []
            stderr_lines = []
            
            while True:
                if process.poll() is not None:
                    break
                
                # Read stderr for dd progress
                if process.stderr:
                    line = process.stderr.readline()
                    if line:
                        stderr_lines.append(line)
                        if device_size:
                            progress = self._parse_dd_progress(line, device_size)
                            if progress is not None:
                                self.progress_tracker.update_progress(progress)
                
                time.sleep(0.1)
            
            # Get remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_lines.extend(remaining_stdout.splitlines())
            if remaining_stderr:
                stderr_lines.extend(remaining_stderr.splitlines())
            
            return '\n'.join(stdout_lines), '\n'.join(stderr_lines), process.returncode
            
        except Exception as e:
            return "", str(e), -1
        finally:
            self.current_process = None
    
    def _parse_dd_progress(self, line, total_size_bytes):
        """Parse progress from dd output."""
        try:
            import re
            # Look for patterns like "2283798528 bytes (2.3 GB, 2.1 GiB) copied"
            if "bytes" in line and "copied" in line:
                match = re.search(r'(\d+)\s+bytes', line)
                if match:
                    bytes_copied = int(match.group(1))
                    progress = min(100, (bytes_copied / total_size_bytes) * 100)
                    return progress
        except Exception as e:
            pass
        return None
    
    def _erase_android_adb(self, device_id):
        """Erase Android device via ADB."""
        self.progress_tracker.start_progress(1, "Android ADB Erase")
        self.log_message(f"Erasing Android device {device_id} via ADB")
        
        # Factory reset command
        cmd = f"adb -s {device_id} shell am broadcast -a android.intent.action.MASTER_CLEAR"
        
        # Simulate progress for ADB command
        for i in range(0, 101, 10):
            self.progress_tracker.update_progress(i)
            time.sleep(0.5)
        
        stdout, stderr, returncode = run_cmd(cmd, capture_stderr=True)
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        
        self.log_message(f"ADB command output: {stdout}")
        if stderr:
            self.log_message(f"ADB command stderr: {stderr}")
        
        return returncode == 0
    
    def _erase_android_fastboot(self, device_id):
        """Erase Android device via Fastboot."""
        self.progress_tracker.start_progress(1, "Android Fastboot Erase")
        self.log_message(f"Erasing Android device {device_id} via Fastboot")
        
        # Erase userdata partition
        cmd = f"fastboot -s {device_id} erase userdata"
        
        # Simulate progress for fastboot command
        for i in range(0, 101, 15):
            self.progress_tracker.update_progress(i)
            time.sleep(0.3)
        
        stdout, stderr, returncode = run_cmd(cmd, capture_stderr=True)
        
        self.progress_tracker.stop_progress()
        print()  # New line after progress
        
        self.log_message(f"Fastboot command output: {stdout}")
        if stderr:
            self.log_message(f"Fastboot command stderr: {stderr}")
        
        return returncode == 0
    
    def get_log_hash(self):
        """Generate SHA256 hash of the complete log."""
        log_content = "\n".join(self.erase_log)
        return hashlib.sha256(log_content.encode()).hexdigest()
