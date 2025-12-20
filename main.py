#!/usr/bin/env python3
"""
Tyech Secure Eraser - Main CLI Entry Point

A secure device erasure system with support for multiple device types
and digital certificate generation.
"""

import argparse
import sys
import os
import json
import time

# Add engine directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine'))

from engine import EraseEngine, CertificateGenerator, ProgressTracker
from engine.device_utils import list_devices, get_device_details
from engine.utils import run_cmd


def demo_progress(device_type, method):
    """Demo progress display for different device types."""
    progress_tracker = ProgressTracker()
    
    if device_type == "hdd" and method == "secure":
        # Demo 3-pass HDD erase
        progress_tracker.start_progress(3, "Multi-pass HDD Erase")
        
        passes = ["Writing zeros", "Writing ones", "Writing random data"]
        for i, pass_name in enumerate(passes):
            progress_tracker.update_stage(i, pass_name, 0)
            for progress in range(0, 101, 5):
                progress_tracker.update_progress(progress)
                time.sleep(0.05)
    
    elif device_type == "ssd" and method == "secure":
        # Demo SSD secure erase
        progress_tracker.start_progress(3, "SSD Secure Erase")
        
        stages = ["Setting security password", "Getting erase estimate", "Running secure erase"]
        for i, stage_name in enumerate(stages):
            progress_tracker.update_stage(i, stage_name, 0)
            for progress in range(0, 101, 10):
                progress_tracker.update_progress(progress)
                time.sleep(0.1)
    
    elif device_type == "usb" and method == "fast":
        # Demo fast USB erase with 3 stages
        progress_tracker.start_progress(3, "Fast USB Erase")
        
        stages = ["Erasing first 1GB", "Erasing partition tables", "Random sampling overwrite"]
        stage_times = [3.0, 0.5, 1.0]  # Different times for each stage
        
        for i, (stage_name, stage_time) in enumerate(zip(stages, stage_times)):
            progress_tracker.update_stage(i, stage_name, 0)
            steps = int(stage_time * 20)  # 20 updates per second
            for step in range(steps + 1):
                progress = min(100, (step / steps) * 100)
                progress_tracker.update_progress(progress)
                time.sleep(0.05)
    
    elif device_type == "usb" and method == "format":
        # Demo secure format with 4 stages
        progress_tracker.start_progress(4, "Secure Format")
        
        stages = ["Erasing boot area", "Creating partition table", "Creating partition", "Formatting filesystem"]
        stage_times = [1.5, 0.3, 0.3, 0.4]  # Different times for each stage
        
        for i, (stage_name, stage_time) in enumerate(zip(stages, stage_times)):
            progress_tracker.update_stage(i, stage_name, 0)
            steps = max(1, int(stage_time * 20))
            for step in range(steps + 1):
                progress = min(100, (step / steps) * 100)
                progress_tracker.update_progress(progress)
                time.sleep(0.05)
    
    elif device_type == "usb" and method == "quick":
        # Demo quick USB wipe with 2 stages
        progress_tracker.start_progress(2, "Quick Wipe")
        
        stages = ["Erasing first 10MB", "Erasing backup partition tables"]
        for i, stage_name in enumerate(stages):
            progress_tracker.update_stage(i, stage_name, 0)
            for progress in range(0, 101, 15):
                progress_tracker.update_progress(progress)
                time.sleep(0.1)
    
    else:
        # Generic demo
        progress_tracker.start_progress(1, f"{device_type.upper()} {method} erase")
        for progress in range(0, 101, 2):
            progress_tracker.update_progress(progress)
            time.sleep(0.05)
    
    progress_tracker.stop_progress()
    print("\nDemo completed!")


def fix_partition_table(device_name):
    """Fix corrupted partition table on a device."""
    print(f"Attempting to fix partition table on {device_name}")
    print("WARNING: This will create a new partition table, erasing any existing partitions!")
    
    confirm = input("Type 'FIX' to confirm: ")
    if confirm != "FIX":
        print("Operation cancelled.")
        return
    
    device_path = f"/dev/{device_name}"
    
    try:
        print("Creating new partition table...")
        cmd1 = f"parted -s {device_path} mklabel msdos"
        run_cmd(cmd1)
        
        print("Creating primary partition...")
        cmd2 = f"parted -s {device_path} mkpart primary fat32 1MiB 100%"
        run_cmd(cmd2)
        
        print("Formatting as FAT32...")
        cmd3 = f"mkfs.fat -F32 {device_path}1"
        run_cmd(cmd3)
        
        print("Updating system...")
        run_cmd(f"partprobe {device_path}")
        run_cmd("udevadm settle")
        
        print(f"✅ Partition table fixed for {device_name}")
        
    except Exception as e:
        print(f"❌ Failed to fix partition table: {e}")


def refresh_device_manual(device_name):
    """Manually refresh device information."""
    print(f"Refreshing device information for {device_name}...")
    device_path = f"/dev/{device_name}"
    
    try:
        run_cmd(f"partprobe {device_path}")
        run_cmd("udevadm settle")
        run_cmd("udevadm trigger --subsystem-match=block")
        print(f"✅ Device {device_name} refreshed successfully")
    except Exception as e:
        print(f"❌ Failed to refresh device: {e}")


def speed_test_device(device_name):
    """Test write speed of a device with both filesystem and raw device tests."""
    
    print(f"🚀 Testing write speed for device {device_name}")
    
    # Get device size for proportional testing
    from engine.device_utils import get_device_size_bytes
    device_size = get_device_size_bytes(device_name)
    if device_size:
        print(f"📏 Device size: {device_size / (1024**3):.2f} GB")
        # Test with up to 1GB or 5% of device size, whichever is smaller
        raw_test_mb = min(1024, max(100, int((device_size * 0.05) / (1024**2))))
    else:
        print("⚠️  Could not determine device size, using 100MB test")
        raw_test_mb = 100
    
    # Test 1: Filesystem speed
    print(f"\n📁 Test 1: Filesystem Write Speed")
    print("⚠️  This is a non-destructive test - writes to a temporary file")
    
    # Mount the device temporarily if it's not mounted
    mount_point = f"/mnt/test_{device_name}"
    device_path = f"/dev/{device_name}1"  # Try first partition
    
    filesystem_speed = 0
    try:
        # Try to mount
        run_cmd(f"mkdir -p {mount_point}")
        mount_result = run_cmd(f"mount {device_path} {mount_point}")
        
        if "already mounted" in mount_result or os.path.ismount(mount_point):
            # Run filesystem speed test
            test_file = f"{mount_point}/speed_test.tmp"
            start_time = time.time()
            cmd = f"dd if=/dev/zero of={test_file} bs=1M count=100 conv=fdatasync"
            result = run_cmd(cmd)
            end_time = time.time()
            
            # Calculate speed
            test_duration = end_time - start_time
            if test_duration > 0:
                filesystem_speed = 100 / test_duration  # MB/s
                print(f"✅ Filesystem write speed: {filesystem_speed:.2f} MB/s")
            
            # Cleanup
            run_cmd(f"rm -f {test_file}")
            run_cmd(f"umount {mount_point}")
        else:
            print("❌ Could not mount device for filesystem test")
            
    except Exception as e:
        print(f"❌ Filesystem test failed: {e}")
    
    # Test 2: Raw device speed (more accurate for erase prediction)
    print(f"\n💾 Test 2: Raw Device Write Speed")
    print(f"⚠️  Writing {raw_test_mb}MB directly to /dev/{device_name} (will overwrite data!)")
    
    response = input("Continue with raw device test? (y/N): ")
    if response.lower() != 'y':
        print("Raw device test skipped.")
        return
    
    try:
        start_time = time.time()
        cmd = f"dd if=/dev/zero of=/dev/{device_name} bs=1M count={raw_test_mb} conv=fdatasync"
        result = run_cmd(cmd)
        end_time = time.time()
        
        test_duration = end_time - start_time
        if test_duration > 0:
            raw_speed = raw_test_mb / test_duration
            print(f"✅ Raw device write speed: {raw_speed:.2f} MB/s")
            
            # Estimate full erase time
            if device_size:
                device_gb = device_size / (1024**3)
                estimated_time = (device_gb * 1024) / raw_speed
                hours = int(estimated_time // 3600)
                minutes = int((estimated_time % 3600) // 60)
                print(f"⏱️  Estimated full erase time: {hours}h {minutes}m")
        else:
            print("❌ Could not calculate speed - test too fast")
            
    except Exception as e:
        print(f"❌ Raw device test failed: {e}")
        
    # Cleanup on error
    try:
        run_cmd(f"umount {mount_point} 2>/dev/null")
        run_cmd(f"rmdir {mount_point} 2>/dev/null")
    except:
        pass


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Tyech Secure Eraser v2.1 - Secure Device Erasure Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                           # List all devices
  %(prog)s --erase sda --type usb --dry-run # Dry run USB erase
  %(prog)s --erase sda --type usb --method secure # Secure USB erase
  %(prog)s --speed-test sda                 # Test device write speed
  %(prog)s --verify cert.json               # Verify certificate signature

Device Types: usb, nvme, ssd, hdd, adb, fastboot
Erase Methods: secure, quick, fast, format
        """
    )
    
    parser.add_argument("--list", action="store_true", help="List all detected devices")
    parser.add_argument("--erase", help="Erase specified device (e.g., sda, nvme0n1)")
    parser.add_argument("--type", help="Device type (usb, nvme, ssd, hdd, adb, fastboot)")
    parser.add_argument("--method", default="secure", choices=["secure", "quick", "fast", "format", "intelligent"], 
                       help="Erase method (secure, quick, fast, format, or intelligent auto-selection)")
    parser.add_argument("--details", help="Get detailed info for specific device")
    parser.add_argument("--cert-dir", default="/home/rocroshan/Desktop/SIH(RF)/certificates", 
                       help="Directory to save certificates")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without actually erasing")
    parser.add_argument("--demo-progress", action="store_true",
                       help="Demo progress display without actual erase (for testing)")
    parser.add_argument("--yes", "--force", dest='yes', action="store_true",
                       help="Bypass interactive confirmation prompts (use with care)")
    parser.add_argument("--speed-test", help="Test write speed for specified device")
    parser.add_argument("--fix-partition", help="Fix/recreate partition table for specified device")
    parser.add_argument("--refresh", help="Refresh device information (force system to re-detect)")
    parser.add_argument("--no-refresh", action="store_true", help="Skip device refresh after erase")
    parser.add_argument("--benchmark", action="store_true",
                       help="Run performance benchmarks on detected devices")
    parser.add_argument("--compliance-report", action="store_true",
                       help="Generate detailed compliance report")
    parser.add_argument("--verify", help="Verify digital signature of a JSON certificate")
    parser.add_argument("--public-key", help="Public key file for verification (default: ./keys/public_key.pem)")
    
    args = parser.parse_args()
    
    if args.list:
        print("🔍 Scanning for devices...")
        devices = list_devices()
        print("\n📱 Detected Devices:")
        print("=" * 50)
        print(devices)
        return
    
    if args.details:
        print(f"🔍 Getting details for device: {args.details}")
        details = get_device_details(args.details)
        print(json.dumps(details, indent=2))
        return
    
    if args.speed_test:
        speed_test_device(args.speed_test)
        return
    
    if args.erase:
        if not args.type:
            print("❌ Error: --type is required when using --erase")
            parser.print_help()
            return
        
        if args.dry_run:
            print("🔍 DRY RUN MODE - No actual erase will be performed")
            print(f"Would erase device: {args.erase}")
            print(f"Device type: {args.type}")
            print(f"Erase method: {args.method}")
            print(f"Certificate directory: {args.cert_dir}")
            if args.demo_progress:
                demo_progress(args.type, args.method)
            return
        
        if args.demo_progress:
            demo_progress(args.type, args.method)
            return
        
        # Perform actual erase
        print(f"🚨 WARNING: About to erase device {args.erase} ({args.type})")
        print("This operation is IRREVERSIBLE and will DESTROY ALL DATA!")
        # If --yes/--force is provided, skip the interactive confirmation
        if not getattr(args, 'yes', False):
            confirm = input("Type 'ERASE' to confirm: ")
            if confirm != "ERASE":
                print("Operation cancelled.")
                return
        
        # Initialize erase engine
        engine = EraseEngine()
        cert_generator = CertificateGenerator()
        
        # Get device details before erase
        device_details = get_device_details(args.erase)
        
        # Perform erase
        success = engine.erase_device(args.erase, args.type, args.method, args.no_refresh)
        
        if success:
            print("\n✅ Erase completed successfully!")
            
            # Generate certificate
            print("📜 Generating erase certificate...")
            log_hash = engine.get_log_hash()
            cert_result = cert_generator.generate_certificate(
                device_details, engine.erase_log, log_hash, args.cert_dir, args.method, args.type
            )
            
            print(f"📄 JSON Certificate: {cert_result['json_certificate']}")
            print(f"📋 PDF Certificate: {cert_result['pdf_certificate']}")
            print(f"🔑 Public Key ID: {cert_result['public_key_fingerprint']}")
        else:
            print("\n❌ Erase failed!")
            sys.exit(1)
        
        return
    
    if args.fix_partition:
        fix_partition_table(args.fix_partition)
        return
    
    if args.refresh:
        refresh_device_manual(args.refresh)
        return
    
    if args.verify:
        public_key_path = args.public_key or "./keys/public_key.pem"
        print(f"🔐 Verifying certificate: {args.verify}")
        print(f"Using public key: {public_key_path}")
        
        success, message = CertificateGenerator.verify_certificate(args.verify, public_key_path)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            sys.exit(1)
        return
    
    # No arguments provided, show help
    parser.print_help()


if __name__ == "__main__":
    main()
