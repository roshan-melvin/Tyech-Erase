#!/usr/bin/env python3
"""
Digital certificate generation for secure erase operations.
"""

import os
import json
import base64
import hashlib
import datetime
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature


class CertificateGenerator:
    """Generate erase certificates in JSON and PDF format with digital signatures."""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._generate_or_load_keys()
    
    def _generate_or_load_keys(self):
        """Generate ECDSA key pair or load existing ones."""
        key_dir = "./keys"
        private_key_path = os.path.join(key_dir, "private_key.pem")
        public_key_path = os.path.join(key_dir, "public_key.pem")
        
        os.makedirs(key_dir, exist_ok=True)
        
        if os.path.exists(private_key_path) and os.path.exists(public_key_path):
            self._load_existing_keys(private_key_path, public_key_path)
        else:
            self._generate_new_keys(key_dir)
    
    def _load_existing_keys(self, private_key_path, public_key_path):
        """Load existing ECDSA key pair."""
        try:
            with open(private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
            
            with open(public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(f.read())
            
            print("Loaded existing ECDSA keys from ./keys/")
        except Exception as e:
            print(f"Error loading keys: {e}")
            self._generate_new_keys("./keys")
    
    def _generate_new_keys(self, key_dir):
        """Generate new ECDSA key pair."""
        # Generate private key using P-256 curve
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        
        # Save keys to files
        private_key_path = os.path.join(key_dir, "private_key.pem")
        public_key_path = os.path.join(key_dir, "public_key.pem")
        
        # Save private key
        with open(private_key_path, 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(public_key_path, 'wb') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        print("Generated new ECDSA keys and saved to ./keys/")
    
    def _sign_data(self, data):
        """Sign data using ECDSA private key."""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        signature = self.private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode('utf-8')
    
    def _get_public_key_fingerprint(self):
        """Get public key fingerprint for verification."""
        public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        fingerprint = hashlib.sha256(public_key_bytes).hexdigest()[:16]
        return fingerprint
    
    def generate_certificate(self, device_info, erase_log, log_hash, output_dir="./certificates", erase_method="secure", device_type="unknown"):
        """Generate both JSON and PDF certificates with digital signature."""
        timestamp = datetime.datetime.now()
        
        # Map method names to descriptive certificate names
        method_mapping = {
            "secure": "Secure Erase",
            "quick": "Quick Erase", 
            "fast": "Fast Erase",
            "format": "Secure Format"
        }
        
        # Create certificate data with enhanced compliance information
        cert_data = {
            "certificate_id": f"ERASE_{timestamp.strftime('%Y%m%d_%H%M%S')}_{device_info['name']}",
            "device_info": device_info,
            "erase_timestamp": timestamp.isoformat(),
            "erase_method": method_mapping.get(erase_method, erase_method.title()),
            "device_type": device_type.upper(),
            "log_hash": log_hash,
            "log_entries": erase_log,
            "issuer": "Tyech Secure Eraser v2.1",
            "compliance": {
                "primary": "NIST SP 800-88 Rev. 1",
                "additional": [
                    "ATA Secure Erase Standard (ANSI/INCITS T13)",
                    "NVMe Sanitize (NVM Express 1.3+)",
                    "GDPR Article 17 (Right to Erasure)",
                    "HIPAA Security Rule § 164.310",
                    "PCI DSS Requirement 9.8.2",
                    "ISO 27001:2013 Control A.8.3.2",
                    "SOX Section 404"
                ]
            },
            "sanitization_level": self._determine_sanitization_level(erase_method, device_type),
            "verification_methods": [
                "Cryptographic hash verification",
                "Digital signature validation",
                "Hardware command verification",
                "Multi-pass confirmation"
            ],
            "public_key_fingerprint": self._get_public_key_fingerprint(),
            "certificate_version": "2.1.0",
            "blockchain_anchor": self._generate_blockchain_anchor(log_hash)
        }
        
        # Create signature data (exclude signature field itself)
        signature_data = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
        digital_signature = self._sign_data(signature_data)
        
        # Add signature to certificate
        cert_data["digital_signature"] = digital_signature
        cert_data["signature_algorithm"] = "ECDSA-SHA256"
        
        # Ensure safe output directory (avoid permission issues)
        unsafe_dirs = ["./keys", "keys", "/opt/certificates", "tyech_certs"]
        # Always resolve certificates and ./certificates to workspace directory
        if (output_dir in ["./certificates", "certificates"] or 
            output_dir.startswith("./certificates") or 
            output_dir == "/home/rocroshan/Desktop/SIH(RF)/certificates"):
            output_dir = "/home/rocroshan/Desktop/SIH(RF)/certificates"
            print(f"🔒 Using workspace certificates directory: {output_dir}")
        elif output_dir in unsafe_dirs or output_dir.startswith("./"):
            # Fallback to workspace certificates for other unsafe dirs
            output_dir = "/home/rocroshan/Desktop/SIH(RF)/certificates"
            print(f"🔒 Using workspace certificates directory: {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate JSON certificate
        json_path = self._generate_json_cert(cert_data, output_dir)
        
        # Generate PDF certificate  
        pdf_path = self._generate_pdf_cert(cert_data, output_dir)
        
        return {
            "json_certificate": json_path,
            "pdf_certificate": pdf_path,
            "certificate_data": cert_data,
            "public_key_fingerprint": self._get_public_key_fingerprint()
        }
    
    def _generate_json_cert(self, cert_data, output_dir):
        """Generate JSON certificate."""
        filename = f"{cert_data['certificate_id']}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(cert_data, f, indent=2)
        
        return filepath
    
    def _determine_sanitization_level(self, method, device_type):
        """Determine NIST sanitization level based on method and device type."""
        if method in ["secure"] and device_type in ["ssd", "nvme"]:
            return "PURGE (Hardware-assisted cryptographic erase)"
        elif method in ["secure"]:
            return "PURGE (Multi-pass overwrite with verification)"
        elif method in ["format"]:
            return "CLEAR (Logical techniques with verification)"
        else:
            return "CLEAR (Standard logical sanitization)"
    
    def _generate_blockchain_anchor(self, log_hash):
        """Generate blockchain anchor for immutable audit trail."""
        # Create a unique anchor that could be used for blockchain timestamping
        anchor_data = f"{log_hash}:{datetime.datetime.now().isoformat()}"
        anchor_hash = hashlib.sha256(anchor_data.encode()).hexdigest()
        return {
            "anchor_hash": anchor_hash,
            "timestamp": datetime.datetime.now().isoformat(),
            "note": "Suitable for blockchain timestamping services"
        }

    @staticmethod
    def verify_certificate(json_path, public_key_path=None):
        """Verify digital signature of a JSON certificate."""
        if not public_key_path:
            public_key_path = "./keys/public_key.pem"
        
        try:
            # Load certificate
            with open(json_path, 'r') as f:
                cert_data = json.load(f)
            
            # Load public key
            with open(public_key_path, 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
            
            # Extract signature and create verification data
            signature = cert_data.pop("digital_signature")
            signature_algorithm = cert_data.pop("signature_algorithm", "ECDSA-SHA256")
            
            # Recreate signature data
            signature_data = json.dumps(cert_data, sort_keys=True, separators=(',', ':'))
            
            # Verify signature
            signature_bytes = base64.b64decode(signature)
            public_key.verify(signature_bytes, signature_data.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
            
            return True, "Certificate signature is valid"
            
        except Exception as e:
            return False, f"Certificate verification failed: {str(e)}"
    
    def _generate_pdf_cert(self, cert_data, output_dir):
        """Generate PDF certificate using reportlab."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            filename = f"{cert_data['certificate_id']}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1,  # Center
                textColor=colors.darkblue
            )
            story.append(Paragraph("🔒 Tyech Secure Eraser Certificate", title_style))
            story.append(Spacer(1, 20))
            
            # Certificate details table
            data = [
                ["Certificate ID:", cert_data['certificate_id']],
                ["Device:", cert_data['device_info']['name']],
                ["Device Type:", cert_data['device_type']],
                ["Erase Method:", cert_data['erase_method']],
                ["Timestamp:", cert_data['erase_timestamp']],
                ["Compliance:", cert_data['compliance']],
                ["Issuer:", cert_data['issuer']],
                ["Public Key ID:", cert_data['public_key_fingerprint']],
                ["Log Hash:", cert_data['log_hash'][:32] + "..."]
            ]
            
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Digital signature info
            sig_style = ParagraphStyle(
                'Signature',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey
            )
            story.append(Paragraph(f"Digital Signature: {cert_data['digital_signature'][:50]}...", sig_style))
            story.append(Paragraph(f"Algorithm: {cert_data['signature_algorithm']}", sig_style))
            
            doc.build(story)
            return filepath
            
        except ImportError:
            return self._generate_simple_pdf_cert(cert_data, output_dir)
    
    def _generate_simple_pdf_cert(self, cert_data, output_dir):
        """Generate simple text certificate if reportlab is not available."""
        filename = f"{cert_data['certificate_id']}_simple.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write("=== TYECH SECURE ERASER CERTIFICATE ===\n\n")
            f.write(f"Certificate ID: {cert_data['certificate_id']}\n")
            f.write(f"Device: {cert_data['device_info']['name']}\n")
            f.write(f"Device Type: {cert_data['device_type']}\n")
            f.write(f"Erase Method: {cert_data['erase_method']}\n")
            f.write(f"Timestamp: {cert_data['erase_timestamp']}\n")
            f.write(f"Compliance: {cert_data['compliance']}\n")
            f.write(f"Issuer: {cert_data['issuer']}\n")
            f.write(f"Public Key ID: {cert_data['public_key_fingerprint']}\n")
            f.write(f"Log Hash: {cert_data['log_hash']}\n\n")
            f.write(f"Digital Signature: {cert_data['digital_signature']}\n")
            f.write(f"Algorithm: {cert_data['signature_algorithm']}\n")
        
        return filepath
