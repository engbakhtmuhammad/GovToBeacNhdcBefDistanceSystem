#!/usr/bin/env python3
"""
Instant Flask Deployment with Public URL
Starts the app locally and exposes it publicly using ngrok
"""

import subprocess
import sys
import time
import os
from threading import Thread

def start_flask_server():
    """Start Flask app with Gunicorn"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("🚀 Starting Flask server with Gunicorn...")
    subprocess.run([
        'gunicorn',
        'app:app',
        '--bind', '127.0.0.1:5000',
        '--workers', '4',
        '--timeout', '120'
    ])

def start_ngrok_tunnel():
    """Start ngrok tunnel after a delay"""
    time.sleep(3)  # Give Flask time to start
    
    print("\n📡 Starting ngrok tunnel...")
    print("Creating public URL...\n")
    
    try:
        from pyngrok import ngrok
        
        # Start ngrok tunnel
        public_url = ngrok.connect(5000)
        
        print("\n" + "="*70)
        print("✅ APP IS NOW LIVE!")
        print("="*70)
        print(f"\n🌐 PUBLIC URL: {public_url}\n")
        print("Your Flask app is accessible at the URL above!")
        print("\nYou can share this URL to anyone")
        print("(Keep this terminal running for the app to stay online)\n")
        print("="*70)
        
        # Keep tunnel alive
        ngrok_process = ngrok.get_ngrok_process()
        ngrok_process.proc.wait()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have ngrok installed: pip install pyngrok")
        sys.exit(1)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("Government Schools Distance System")
    print("Instant Deployment with Public URL")
    print("="*70 + "\n")
    
    print("Starting Flask application...")
    print("This will create a public URL for your app\n")
    
    # Start Flask in main thread
    try:
        start_flask_server()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)
