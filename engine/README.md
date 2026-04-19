# Tyech Secure Eraser Engine - Modular Architecture

This directory contains the modular components of the Tyech Secure Eraser Engine v2.1.

## 📁 Module Structure

### Core Modules

- **`__init__.py`** - Package initialization and exports
- **`erase_engine.py`** - Main erasure engine with device-specific logic
- **`certificate_generator.py`** - Digital certificate generation and verification
- **`progress_tracker.py`** - Progress tracking and time estimation
- **`device_utils.py`** - Device detection and information utilities
- **`utils.py`** - Common utility functions and command execution

## 🔧 Module Responsibilities

### EraseEngine (`erase_engine.py`)
- Main erasure logic for different device types (USB, SSD, HDD, NVMe, Android)
- Device-specific erasure methods (secure, quick, fast, format)
- Signal handling for graceful interruption
- Logging and error handling

### CertificateGenerator (`certificate_generator.py`)
- ECDSA key pair generation and management
- Digital signature creation and verification
- JSON and PDF certificate generation
- Compliance with NIST 800-88 standards

### ProgressTracker (`progress_tracker.py`)
- Real-time progress display with progress bars
- Time estimation and ETA calculations
- Multi-stage operation tracking
- Thread-safe progress updates

### DeviceUtils (`device_utils.py`)
- Device detection (USB, SSD, HDD, NVMe, Android ADB/Fastboot)
- Device information extraction (size, model, serial)
- Cross-platform device categorization

### Utils (`utils.py`)
- Command execution with error handling
- Progress parsing from dd-style output
- Common utility functions

## 🎯 Key Features

### Modular Design
- **Separation of Concerns**: Each module has a specific responsibility
- **Maintainability**: Easy to update individual components
- **Testability**: Modules can be tested independently
- **Extensibility**: Easy to add new device types or erasure methods

### Enhanced Functionality
- **Progress Tracking**: Real-time progress with accurate time estimation
- **Multi-Stage Operations**: Support for complex multi-pass erasure
- **Error Recovery**: Graceful handling of interruptions and errors
- **Certificate Generation**: Cryptographically signed erasure certificates

## 🔄 Import Usage

```python
# Import the main classes
from engine import EraseEngine, CertificateGenerator, ProgressTracker

# Import utilities
from engine.device_utils import list_devices, get_device_details
from engine.utils import run_cmd

# Create instances
engine = EraseEngine()
cert_gen = CertificateGenerator()
tracker = ProgressTracker()
```

## 🚀 Advantages Over Monolithic Design

1. **Code Organization**: Logical separation of functionality
2. **Easier Debugging**: Issues isolated to specific modules
3. **Team Development**: Multiple developers can work on different modules
4. **Selective Loading**: Only load required components
5. **Better Testing**: Unit tests for individual components
6. **Documentation**: Each module is self-documented

## 🔐 Security Features

- **Digital Signatures**: All certificates cryptographically signed
- **Key Management**: Secure ECDSA key generation and storage
- **Audit Trail**: Comprehensive logging of all operations
- **Verification**: Certificate integrity verification

## 📈 Performance Improvements

- **Optimized Commands**: Better block sizes and options
- **Progress Feedback**: Real-time status updates
- **Resource Management**: Efficient memory and CPU usage
- **Background Processing**: Non-blocking progress display

---

*Part of Tyech Secure Eraser v2.1 - Professional Secure Erasure Solution*
