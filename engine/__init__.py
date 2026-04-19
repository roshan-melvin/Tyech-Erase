"""
Tyech Secure Eraser Engine

A modular secure device erasure system with support for multiple device types
and erasure methods, including digital certificate generation.
"""

__version__ = "2.1.0"
__author__ = "Tyech Solutions"

from .erase_engine import EraseEngine
from .certificate_generator import CertificateGenerator
from .progress_tracker import ProgressTracker
from .device_utils import list_devices, get_device_details, get_device_size_bytes
from .utils import run_cmd, run_cmd_with_progress

__all__ = [
    'EraseEngine',
    'CertificateGenerator', 
    'ProgressTracker',
    'list_devices',
    'get_device_details',
    'get_device_size_bytes',
    'run_cmd',
    'run_cmd_with_progress'
]
