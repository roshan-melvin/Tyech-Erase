#!/usr/bin/env python3
"""
Main Flask application for Tyech Secure Eraser website.
Serves all main pages and connects templates.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import json
from engine.device_utils import list_devices, get_device_details
from engine.erase_engine import EraseEngine

app = Flask(__name__)
app.secret_key = 'tyech-secure-key'  # For flash messages

# Home page
@app.route('/')
def index():
	return render_template('index.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
	# For demo, show last 10 erase logs from certificates (if available)
	cert_dir = '/home/rocroshan/Desktop/SIH(RF)/certificates'
	erase_jobs = []
	if os.path.exists(cert_dir):
		for fname in sorted(os.listdir(cert_dir), reverse=True):
			if fname.endswith('.json'):
				try:
					with open(os.path.join(cert_dir, fname), 'r') as f:
						cert_data = json.load(f)
					erase_jobs.append({
						'certificate_id': cert_data.get('certificate_id'),
						'device': cert_data.get('device_info', {}).get('name'),
						'timestamp': cert_data.get('erase_timestamp'),
						'method': cert_data.get('erase_method'),
						'status': 'Completed',
						'file': fname
					})
				except:
					continue
			if len(erase_jobs) >= 10:
				break
	return render_template('dashboard.html', erase_jobs=erase_jobs)

# Devices page
@app.route('/devices')
def devices():
	# Get device data from backend
	devices_json = list_devices()
	devices_data = json.loads(devices_json)
	return render_template('devices.html', devices=devices_data)

# Erase page
import subprocess

@app.route('/erase', methods=['GET', 'POST'])
def erase():
	devices_json = list_devices()
	devices_data = json.loads(devices_json)
	erase_result = None
	if request.method == 'POST':
		device_name = request.form.get('device_name')
		device_type = request.form.get('device_type')
		method = request.form.get('method', 'secure')
		if device_name and device_type:
			# Build the CLI command
			cmd = ["sudo", "./tyech-erase", "--erase", device_name, "--type", device_type, "--method", method, "--yes"]
			try:
				# Set a reasonable timeout to avoid hanging web requests (seconds)
				proc = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/rocroshan/Desktop/SIH(RF)", timeout=300)
				success = proc.returncode == 0
				# Combine stdout and stderr, show last 50 lines for clarity
				combined = (proc.stdout or '') + '\n' + (proc.stderr or '')
				output_lines = combined.splitlines()
				if not output_lines:
					output_lines = ["No output received. Possible error or permission issue."]
				# Detect common sudo password prompt patterns and return a clear error
				error_msg = None
				lower_combined = combined.lower()
				if 'sudo:' in lower_combined and 'password' in lower_combined:
					error_msg = ('Sudo is asking for a password. Configure passwordless sudo for the web user ' 
							'or run the web server with sufficient privileges. See /etc/sudoers (visudo).')
				erase_result = {
					'success': success,
					'log': output_lines[-50:],
					'error': None if success else (error_msg or "Erase failed. Check output for details.")
				}
			except subprocess.TimeoutExpired as te:
				erase_result = {
					'success': False,
					'log': ["Timeout: erase process exceeded 300s and was killed."],
					'error': 'Timeout'
				}
			except Exception as e:
				erase_result = {
					'success': False,
					'log': ["Exception: " + str(e)],
					'error': str(e)
				}
	return render_template('erase.html', devices=devices_data, erase_result=erase_result)

# Certificates page
import os

@app.route('/certificates')
def certificates():
	cert_dir = '/home/rocroshan/Desktop/SIH(RF)/certificates'
	cert_files = []
	if os.path.exists(cert_dir):
		for fname in os.listdir(cert_dir):
			if fname.endswith('.json') or fname.endswith('.pdf'):
				cert_files.append(fname)
	return render_template('certificates.html', cert_files=cert_files)

# Verify certificate page
from engine.certificate_generator import CertificateGenerator

@app.route('/verify', methods=['GET', 'POST'])
def verify():
	cert_dir = '/home/rocroshan/Desktop/SIH(RF)/certificates'
	cert_files = [f for f in os.listdir(cert_dir) if f.endswith('.json')] if os.path.exists(cert_dir) else []
	verify_result = None
	if request.method == 'POST':
		cert_file = request.form.get('cert_file')
		if cert_file:
			cert_path = os.path.join(cert_dir, cert_file)
			try:
				with open(cert_path, 'r') as f:
					cert_data = json.load(f)
				# Prepare signature data: exclude only digital_signature
				signature_data = dict(cert_data)
				signature = signature_data.pop('digital_signature', None)
				signature_data.pop('signature_algorithm', None)
				# Ensure field order and separators match CLI
				signature_data_json = json.dumps(signature_data, sort_keys=True, separators=(',', ':'))
				valid = False
				if signature:
					import base64
					from cryptography.hazmat.primitives import hashes
					from cryptography.hazmat.primitives.asymmetric import ec
					from cryptography.hazmat.primitives import serialization
					from cryptography.exceptions import InvalidSignature
					pubkey_path = '/home/rocroshan/Desktop/SIH(RF)/keys/public_key.pem'
					with open(pubkey_path, 'rb') as pkf:
						pubkey = serialization.load_pem_public_key(pkf.read())
					try:
						pubkey.verify(base64.b64decode(signature), signature_data_json.encode('utf-8'), ec.ECDSA(hashes.SHA256()))
						valid = True
					except InvalidSignature:
						valid = False
				verify_result = {
					'valid': valid,
					'cert_file': cert_file,
					'cert_data': cert_data
				}
			except Exception as e:
				verify_result = {'error': str(e)}
	return render_template('verify.html', cert_files=cert_files, verify_result=verify_result)

# Documentation page
@app.route('/documentation')
def documentation():
	return render_template('documentation.html')

# About page
@app.route('/about')
def about():
	return render_template('about.html')

# Admin dashboard
@app.route('/admin')
def admin():
	return render_template('admin.html')

# Enterprise solutions
@app.route('/enterprise')
def enterprise():
	return render_template('enterprise.html')

# API documentation
@app.route('/api-docs')
def api_docs():
	return render_template('api.html')

# Status page
@app.route('/status')
def status():
	return render_template('status.html')

if __name__ == '__main__':
	app.run(debug=True)
