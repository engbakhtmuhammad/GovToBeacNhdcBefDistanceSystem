#!/usr/bin/env python3
"""
Interactive Deployment Assistant
Guides you through deploying to Render.com, Railway.app, or PythonAnywhere
"""

import webbrowser
import subprocess
import sys
from typing import Optional

class DeploymentAssistant:
    def __init__(self):
        self.github_url = "https://github.com/engbakhtmuhammad/GovToBeacNhdcBefDistanceSystem.git"
        self.repo_name = "GovToBeacNhdcBefDistanceSystem"
        self.repo_owner = "engbakhtmuhammad"
        
    def print_header(self):
        print("\n" + "="*60)
        print("🚀 GOVERNMENT SCHOOLS DISTANCE SYSTEM")
        print("📦 Interactive Deployment Assistant")
        print("="*60 + "\n")
    
    def print_options(self):
        print("Choose your deployment platform:\n")
        print("1. 🎯 Render.com (Recommended - Simple & Free)")
        print("   - Fastest setup")
        print("   - Free tier: 750 hours/month")
        print("   - Auto-deploys from GitHub")
        print("")
        print("2. 🚂 Railway.app (Simplest)")
        print("   - 1-click GitHub integration")
        print("   - Free tier: $5 credit/month")
        print("   - Auto-scaling available")
        print("")
        print("3. 🐍 PythonAnywhere (Python-focused)")
        print("   - Beginner-friendly")
        print("   - Web-based development")
        print("   - Free plan available")
        print("")
        print("4. 📖 View Full Guide")
        print("   - Read DEPLOY_NOW.md for details")
        print("")
        print("5. 🔗 Copy GitHub URL")
        print("   - Copy repo URL to clipboard")
        print("")
        print("0. ❌ Exit")
        print("")
    
    def deploy_render(self):
        print("\n" + "="*60)
        print("📦 DEPLOYING TO RENDER.COM")
        print("="*60 + "\n")
        
        print("Opening Render.com dashboard...\n")
        
        steps = [
            ("1. Visit https://render.com", "https://render.com"),
            ("2. Sign in with GitHub", "https://dashboard.render.com"),
            ("3. Click 'New +' → 'Web Service'", "https://dashboard.render.com/"),
            ("4. Select your GitHub repo", None),
        ]
        
        for step, url in steps:
            print(f"  {step}")
            if url and input("  Open this link? (y/n): ").lower() == 'y':
                webbrowser.open(url)
        
        print("\n5. Configure the service with these settings:")
        print("   ┌─────────────────────────────────────┐")
        print("   │ Name: gov-schools-distance          │")
        print("   │ Environment: Python 3               │")
        print("   │ Build: pip install -r requirements. │")
        print("   │ Start: gunicorn app:app             │")
        print("   │ Plan: Free                          │")
        print("   └─────────────────────────────────────┘")
        
        print("\n6. Click 'Create Web Service'")
        print("7. Wait 2-5 minutes for deployment")
        print("\n✅ Your app will be live at: https://gov-schools-distance.onrender.com")
        
        input("\nPress Enter when deployment is complete...")
        self.success_message("Render.com")
    
    def deploy_railway(self):
        print("\n" + "="*60)
        print("📦 DEPLOYING TO RAILWAY.APP")
        print("="*60 + "\n")
        
        print("Opening Railway.app dashboard...\n")
        
        steps = [
            ("1. Visit https://railway.app", "https://railway.app"),
            ("2. Sign in with GitHub", "https://railway.app"),
            ("3. Create New Project", None),
            ("4. Select 'Deploy from GitHub'", None),
        ]
        
        for step, url in steps:
            print(f"  {step}")
            if url and input("  Open this link? (y/n): ").lower() == 'y':
                webbrowser.open(url)
        
        print("\n5. Select your repository: GovToBeacNhdcBefDistanceSystem")
        print("6. Railway auto-detects Python and Flask")
        print("7. Wait for auto-deployment (2-3 minutes)")
        
        print("\n✅ Your deployment URL will appear in the Railway dashboard")
        
        input("\nPress Enter when deployment is complete...")
        self.success_message("Railway.app")
    
    def deploy_pythonanywhere(self):
        print("\n" + "="*60)
        print("📦 DEPLOYING TO PYTHONANYWHERE")
        print("="*60 + "\n")
        
        print("Opening PythonAnywhere...\n")
        
        steps = [
            ("1. Visit https://www.pythonanywhere.com", "https://www.pythonanywhere.com"),
            ("2. Create free account", None),
            ("3. Go to Web tab", None),
        ]
        
        for step, url in steps:
            print(f"  {step}")
            if url and input("  Open this link? (y/n): ").lower() == 'y':
                webbrowser.open(url)
        
        print("\n4. Click 'Add new web app'")
        print("5. Choose Python 3.11")
        print("6. Choose Flask framework")
        print("7. Pull code from GitHub or upload manually")
        print("8. Configure WSGI file to point to app:app")
        print("9. Reload the app")
        
        print("\n✅ Your app will be live at: https://yourusername.pythonanywhere.com")
        
        input("\nPress Enter when deployment is complete...")
        self.success_message("PythonAnywhere")
    
    def success_message(self, platform: str):
        print("\n" + "="*60)
        print(f"🎉 DEPLOYMENT TO {platform.upper()} COMPLETE!")
        print("="*60 + "\n")
        
        print("Your application is now live!\n")
        print("Next steps:")
        print("  1. Test your application in the browser")
        print("  2. Share the URL with others")
        print("  3. Monitor logs in the platform dashboard")
        print("")
        print("To update your app in the future:")
        print("  git commit -m 'Your changes'")
        print("  git push origin main")
        print("  → Automatic redeploy in 2-5 minutes!")
        print("")
    
    def show_github_url(self):
        print(f"\n📌 GitHub Repository URL:")
        print(f"   {self.github_url}\n")
        
        # Copy to clipboard
        try:
            subprocess.run(
                f"echo {self.github_url} | pbcopy",
                shell=True
            )
            print("✅ Copied to clipboard!\n")
        except:
            print("(You can copy it manually)\n")
    
    def run(self):
        self.print_header()
        
        while True:
            self.print_options()
            choice = input("Enter your choice (0-5): ").strip()
            
            if choice == '1':
                self.deploy_render()
                break
            elif choice == '2':
                self.deploy_railway()
                break
            elif choice == '3':
                self.deploy_pythonanywhere()
                break
            elif choice == '4':
                print("\nOpening DEPLOY_NOW.md...\n")
                try:
                    subprocess.run(["open", "DEPLOY_NOW.md"])
                except:
                    print("Please open DEPLOY_NOW.md manually")
            elif choice == '5':
                self.show_github_url()
            elif choice == '0':
                print("\n👋 Goodbye!\n")
                break
            else:
                print("\n❌ Invalid choice. Please try again.\n")


def main():
    try:
        assistant = DeploymentAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n\n👋 Deployment assistant closed.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
