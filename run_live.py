#!/usr/bin/env python3
"""
Deploy Flask App with Public URL via ngrok
Creates an instant public link to your app
"""

import subprocess
import time
import sys
import os
from pyngrok import ngrok

def main():
    print("\n" + "="*70)
    print("🚀 GOVERNMENT SCHOOLS DISTANCE SYSTEM")
    print("   INSTANT DEPLOYMENT WITH PUBLIC URL")
    print("="*70 + "\n")
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    print("Step 1: Starting Flask Server...")
    print("-" * 70)
    
    # Start Gunicorn server
    server_process = subprocess.Popen([
        sys.executable, '-m', 'gunicorn',
        'app:app',
        '--bind', '127.0.0.1:5000',
        '--workers', '2',
        '--timeout', '120',
        '--access-logfile', '-',
        '--error-logfile', '-'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    print("✅ Flask server started on http://127.0.0.1:5000")
    print()
    print("Step 2: Creating Public URL with ngrok...")
    print("-" * 70)
    
    try:
        # Create ngrok tunnel
        public_url = ngrok.connect(5000, "http")
        
        print(f"✅ Public tunnel created!\n")
        print("="*70)
        print("🎉 YOUR APP IS NOW LIVE!")
        print("="*70)
        print()
        print(f"📍 PUBLIC URL: {public_url}")
        print()
        print("You can share this URL with anyone!")
        print("(Keep this terminal open for the app to stay online)")
        print()
        print("Features:")
        print("  ✓ File upload & analysis")
        print("  ✓ Distance calculations")
        print("  ✓ Excel export")
        print("  ✓ Interactive maps")
        print("  ✓ Real-time processing")
        print()
        print("="*70)
        print()
        print("To stop: Press Ctrl+C")
        print()
        
        # Keep running
        server_process.wait()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        server_process.terminate()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        ngrok.kill()
        server_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
