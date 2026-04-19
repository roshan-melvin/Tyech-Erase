#!/usr/bin/env python3
"""
Utility functions for the Tyech Secure Eraser Engine.
"""

import subprocess
import re
import time


def run_cmd(cmd, capture_stderr=False):
    """Run a shell command and return output as string."""
    try:
        if capture_stderr:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout, result.stderr, result.returncode
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout
    except Exception as e:
        if capture_stderr:
            return "", str(e), -1
        return ""


def run_cmd_with_progress(cmd, progress_tracker=None, timeout=None):
    """Run command and track progress from dd-style output."""
    try:
        process = subprocess.Popen(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        stdout_lines = []
        stderr_lines = []
        
        # Read output in real-time
        while True:
            # Check if process finished
            if process.poll() is not None:
                break
            
            # Read stderr for dd progress
            if process.stderr:
                line = process.stderr.readline()
                if line:
                    stderr_lines.append(line)
                    if progress_tracker:
                        progress = parse_dd_progress(line)
                        if progress is not None:
                            progress_tracker.update_progress(progress)
            
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


def parse_dd_progress(line, total_size_bytes=None):
    """Parse progress from dd output."""
    try:
        # Look for patterns like "2283798528 bytes (2.3 GB, 2.1 GiB) copied"
        if "bytes" in line and "copied" in line:
            # Extract bytes copied
            match = re.search(r'(\d+)\s+bytes', line)
            if match and total_size_bytes:
                bytes_copied = int(match.group(1))
                progress = min(100, (bytes_copied / total_size_bytes) * 100)
                return progress
    except Exception as e:
        pass
    return None
