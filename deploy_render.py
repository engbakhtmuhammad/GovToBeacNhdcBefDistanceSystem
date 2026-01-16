#!/usr/bin/env python3
"""
Automated Render.com Deployment Script
Usage: python3 deploy_render.py --token YOUR_RENDER_API_TOKEN
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime

class RenderDeployer:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
    def get_github_repo(self):
        """Get GitHub repo URL from git config"""
        try:
            repo = subprocess.check_output(
                ["git", "remote", "get-url", "origin"],
                cwd=os.getcwd(),
                text=True
            ).strip()
            # Extract owner/repo from GitHub URL
            if "github.com" in repo:
                parts = repo.split("/")
                return f"{parts[-2]}/{parts[-1].replace('.git', '')}"
            return repo
        except:
            return None
    
    def create_web_service(self, repo_path):
        """Create a new web service on Render"""
        print("🚀 Creating web service on Render.com...")
        
        payload = {
            "name": "gov-schools-distance",
            "serviceDetails": {
                "repo": f"https://github.com/{repo_path}",
                "branch": "main",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn app:app",
                "envVars": [
                    {"key": "PORT", "value": "5000"},
                    {"key": "FLASK_ENV", "value": "production"}
                ]
            },
            "type": "web_service"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/services",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                service_id = data.get("service", {}).get("id")
                service_url = data.get("service", {}).get("serviceDetails", {}).get("url")
                
                print(f"✅ Service created successfully!")
                print(f"   Service ID: {service_id}")
                print(f"   URL: {service_url}")
                return service_id, service_url
            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)
                return None, None
                
        except Exception as e:
            print(f"❌ Failed to create service: {str(e)}")
            return None, None
    
    def deploy(self):
        """Main deployment flow"""
        print("="*50)
        print("Government Schools Distance System")
        print("Deploying to Render.com...")
        print("="*50)
        print()
        
        repo = self.get_github_repo()
        if not repo:
            print("❌ Could not determine GitHub repository")
            print("Make sure you're in a git repository with a GitHub remote")
            return False
        
        print(f"✓ GitHub Repo: {repo}")
        
        service_id, url = self.create_web_service(repo)
        
        if service_id and url:
            print()
            print("🎉 Deployment Initiated!")
            print(f"   Your app will be live at: {url}")
            print("   (May take 2-5 minutes to build and deploy)")
            return True
        else:
            print("❌ Deployment failed")
            return False


def main():
    if len(sys.argv) < 2 or "--token" not in " ".join(sys.argv):
        print("Usage: python3 deploy_render.py --token YOUR_RENDER_API_TOKEN")
        print()
        print("To get your Render API token:")
        print("  1. Go to: https://dashboard.render.com/account/api-tokens")
        print("  2. Create a new API token")
        print("  3. Run: python3 deploy_render.py --token <YOUR_TOKEN>")
        sys.exit(1)
    
    token_idx = sys.argv.index("--token")
    if token_idx + 1 >= len(sys.argv):
        print("Error: Please provide your Render API token after --token")
        sys.exit(1)
    
    token = sys.argv[token_idx + 1]
    
    deployer = RenderDeployer(token)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
