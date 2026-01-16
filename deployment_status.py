#!/usr/bin/env python3
"""
Deployment Status Report Generator
Shows complete deployment readiness status
"""

import subprocess
import os
from datetime import datetime

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "N/A"

def check_git_status():
    """Check git repository status"""
    try:
        remote = subprocess.run(
            "git remote get-url origin",
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        status = subprocess.run(
            "git status --porcelain",
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        branch = subprocess.run(
            "git rev-parse --abbrev-ref HEAD",
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        commits = subprocess.run(
            "git log --oneline | wc -l",
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        return {
            "remote": remote,
            "branch": branch,
            "commits": commits,
            "clean": len(status) == 0
        }
    except:
        return None

def check_files():
    """Check required deployment files"""
    files = {
        "app.py": "Flask application",
        "requirements.txt": "Python dependencies",
        "Procfile": "Platform configuration",
        "runtime.txt": "Python version",
        ".gitignore": "Git ignore rules",
        "Dockerfile": "Docker configuration",
        "docker-compose.yml": "Docker compose",
        "DEPLOY_NOW.md": "Deployment guide",
        "QUICK_START.md": "Quick start guide",
        "deploy.sh": "Bash deployment helper",
        "deploy_interactive.py": "Interactive deployer",
    }
    
    status = {}
    for filename, description in files.items():
        exists = os.path.exists(filename)
        status[filename] = {"exists": exists, "description": description}
    
    return status

def generate_report():
    """Generate deployment status report"""
    
    print("\n" + "="*70)
    print(" " * 10 + "DEPLOYMENT STATUS REPORT")
    print(" " * 5 + "Government Schools Distance System")
    print("="*70 + "\n")
    
    # Timestamp
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Git Status
    print("📦 GIT REPOSITORY STATUS")
    print("-" * 70)
    git_status = check_git_status()
    
    if git_status:
        print(f"  Repository:    ✅ Initialized")
        print(f"  Remote:        {git_status['remote']}")
        print(f"  Branch:        {git_status['branch']}")
        print(f"  Total Commits: {git_status['commits']}")
        print(f"  Status:        {'✅ Clean (all committed)' if git_status['clean'] else '⚠️  Changes pending'}")
    else:
        print("  ❌ Git not available")
    
    print()
    
    # 2. File Status
    print("📁 REQUIRED FILES")
    print("-" * 70)
    files_status = check_files()
    
    all_exist = True
    for filename, info in files_status.items():
        status_icon = "✅" if info["exists"] else "❌"
        print(f"  {status_icon} {filename:<30} {info['description']}")
        if not info["exists"]:
            all_exist = False
    
    print()
    
    # 3. Deployment Readiness
    print("🚀 DEPLOYMENT READINESS")
    print("-" * 70)
    
    checks = [
        ("Git repository configured", git_status is not None),
        ("All files present", all_exist),
        ("Code committed", git_status and not git_status['clean']),
        ("Remote repository linked", git_status and bool(git_status['remote'])),
        ("Python dependencies defined", files_status.get('requirements.txt', {}).get('exists', False)),
        ("Platform configuration ready", files_status.get('Procfile', {}).get('exists', False)),
        ("Docker support ready", files_status.get('Dockerfile', {}).get('exists', False)),
        ("Deployment guides available", files_status.get('QUICK_START.md', {}).get('exists', False)),
    ]
    
    for check_name, passed in checks:
        status = "✅" if passed else "⚠️ "
        print(f"  {status} {check_name}")
    
    all_passed = all(passed for _, passed in checks)
    
    print()
    
    # 4. Next Steps
    print("📋 RECOMMENDED NEXT STEPS")
    print("-" * 70)
    
    if all_passed:
        print("  ✅ Your application is READY FOR DEPLOYMENT!")
        print()
        print("  Choose one of these platforms:")
        print()
        print("  1️⃣  Render.com (Recommended)")
        print("      Visit: https://render.com")
        print("      • Simple & Free (750 hrs/month)")
        print("      • Auto-deploys from GitHub")
        print("      • Time to live: 2-5 minutes")
        print()
        print("  2️⃣  Railway.app")
        print("      Visit: https://railway.app")
        print("      • 1-click GitHub deployment")
        print("      • $5 free credit/month")
        print("      • Time to live: 2-3 minutes")
        print()
        print("  3️⃣  PythonAnywhere")
        print("      Visit: https://www.pythonanywhere.com")
        print("      • Python-focused hosting")
        print("      • Web-based IDE available")
        print("      • Time to live: 5-10 minutes")
        print()
        print("  Or run:")
        print("  $ python3 deploy_interactive.py")
        print()
    else:
        print("  ⚠️  Some requirements are missing. Please check above.")
    
    print()
    
    # 5. GitHub Repository
    if git_status:
        print("🔗 GITHUB REPOSITORY")
        print("-" * 70)
        print(f"  {git_status['remote']}")
        print()
    
    # 6. Deployment Scripts
    print("🛠️  AVAILABLE DEPLOYMENT TOOLS")
    print("-" * 70)
    print("  • deploy.sh")
    print("    Bash script that shows deployment options")
    print("    $ bash deploy.sh")
    print()
    print("  • deploy_interactive.py")
    print("    Interactive Python deployment assistant")
    print("    $ python3 deploy_interactive.py")
    print()
    print("  • deploy_render.py")
    print("    Direct Render.com API deployment")
    print("    $ python3 deploy_render.py --token YOUR_API_TOKEN")
    print()
    
    # 7. Local Testing
    print("🧪 LOCAL TESTING (Before Deployment)")
    print("-" * 70)
    print("  Install dependencies:")
    print("  $ pip install -r requirements.txt")
    print()
    print("  Run locally:")
    print("  $ python app.py")
    print()
    print("  Or with Gunicorn (production server):")
    print("  $ gunicorn app:app --bind 0.0.0.0:5000")
    print()
    
    # 8. Documentation
    print("📚 DOCUMENTATION")
    print("-" * 70)
    print("  • QUICK_START.md      - 2-minute deployment guide")
    print("  • DEPLOY_NOW.md       - Comprehensive deployment guide")
    print("  • DEPLOYMENT.md       - Detailed deployment options")
    print("  • README.md           - Application documentation")
    print()
    
    print("="*70)
    if all_passed:
        print("  ✨ APPLICATION IS READY TO DEPLOY! ✨")
    print("="*70 + "\n")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    generate_report()
