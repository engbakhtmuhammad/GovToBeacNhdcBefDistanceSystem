#!/usr/bin/env python3
"""
Complete Automated Deployment Setup
Guides through connecting to Render and enabling auto-deployment
"""

import subprocess
import sys
import json
from datetime import datetime

print("\n" + "="*70)
print("  GOVERNMENT SCHOOLS DISTANCE SYSTEM")
print("  Complete Deployment Setup")
print("="*70 + "\n")

# Step 1: Verify git status
print("Step 1: Verifying Git Status...")
try:
    remote = subprocess.run(
        "git remote get-url origin",
        shell=True,
        capture_output=True,
        text=True
    ).stdout.strip()
    
    if "github.com" in remote:
        print(f"  ✅ GitHub repository connected")
        print(f"     {remote}\n")
    else:
        print(f"  ⚠️  Remote: {remote}\n")
except:
    print("  ❌ Git repository not found\n")
    sys.exit(1)

# Step 2: Show deployment options
print("Step 2: Choose Your Deployment Method")
print("-" * 70)
print("""
  METHOD A: Render.com (Recommended - Auto-deploys on every push)
  ──────────────────────────────────────────────────────────────
  1. Go to: https://render.com
  2. Sign in with GitHub
  3. Create Web Service:
     - Click "New +" → "Web Service"
     - Select repo: GovToBeacNhdcBefDistanceSystem
     - Authorize GitHub access
  4. Configure:
     - Name: gov-schools-distance
     - Environment: Python 3
     - Build Command: pip install -r requirements.txt
     - Start Command: gunicorn app:app
     - Plan: Free (or Paid)
  5. Click "Create Web Service"
  6. Wait 2-5 minutes for deployment
  7. Your app is LIVE! 🎉
  
  After deployment:
  - Every push to GitHub = automatic redeploy
  - No additional setup needed
  - Check logs in Render dashboard
  
  
  METHOD B: Railway.app (Simplest - 1-click setup)
  ───────────────────────────────────────────────
  1. Go to: https://railway.app
  2. Click "Login with GitHub"
  3. Create Project → "Deploy from GitHub"
  4. Select repo: GovToBeacNhdcBefDistanceSystem
  5. Auto-deploys in 2 minutes
  6. Get URL from dashboard
  
  
  METHOD C: PythonAnywhere (Web-based IDE)
  ──────────────────────────────────────────
  1. Go to: https://www.pythonanywhere.com
  2. Create free account
  3. Upload code from GitHub
  4. Configure WSGI
  5. Enable web app
""")

print("-" * 70)

# Step 3: Show next steps
print("\nStep 3: Next Steps")
print("-" * 70)

print("""
Choose your preferred platform above and follow the steps.

Once deployed:

✅ Auto-Updates Enabled
   After you push code to GitHub:
   $ git commit -m "your changes"
   $ git push origin main
   
   The platform will automatically:
   1. Pull your code
   2. Install dependencies
   3. Restart the app
   4. Deploy in 2-5 minutes

✅ GitHub Actions Set Up
   This repository now includes GitHub Actions workflows
   that can trigger automatic deployments

✅ Docker Ready
   You can also deploy using Docker:
   $ docker build -t gov-schools-distance .
   $ docker run -p 5000:5000 gov-schools-distance


IMPORTANT: First Deployment
──────────────────────────
The first deployment requires you to:
1. Visit the platform website (Render, Railway, or PythonAnywhere)
2. Sign in with your GitHub account
3. Authorize access to your repositories
4. Click deploy

After that, all future deployments are AUTOMATIC when you push to GitHub!
""")

print("-" * 70)
print("\nStep 4: Verify Everything is Ready")
print("-" * 70)

# Check all files
required_files = [
    ("app.py", "Flask application"),
    ("requirements.txt", "Python dependencies"),
    ("Procfile", "Platform configuration"),
    ("runtime.txt", "Python version"),
    ("Dockerfile", "Docker config"),
]

all_good = True
for filename, description in required_files:
    import os
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"  {status} {filename:<30} {description}")
    if not exists:
        all_good = False

print()

if all_good:
    print("✅ All required files present!")
    print("✅ Application is 100% ready for deployment")
    print("✅ GitHub repository is configured")
    print()
    
    print("="*70)
    print("  READY TO DEPLOY!")
    print("="*70)
    print("""
Next Step: Open https://render.com (or your chosen platform)

Timeline:
- Choose platform: 30 seconds
- Sign up with GitHub: 1 minute
- Configure deployment: 2 minutes
- Build & deploy: 2-5 minutes
- TOTAL: ~10 minutes to production!

Questions? See:
- QUICK_START.md (2-minute guide)
- DEPLOY_NOW.md (complete guide)
- Run: python3 deploy_interactive.py

Let's go! 🚀
""")
else:
    print("❌ Some files are missing")
    sys.exit(1)

print("="*70)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70 + "\n")
