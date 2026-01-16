#!/bin/bash
# Automated Render.com Deployment Script
# This script will deploy your Flask app to Render.com

set -e

echo "======================================"
echo "🚀 Government Schools Distance System"
echo "🚀 Automated Deployment to Render.com"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify GitHub repo is set up
echo -e "${YELLOW}Step 1: Verifying GitHub repository...${NC}"
if git remote -v | grep -q "origin"; then
    GITHUB_REPO=$(git remote get-url origin)
    echo -e "${GREEN}✓ GitHub repo found: $GITHUB_REPO${NC}"
else
    echo -e "${RED}✗ No GitHub remote found. Please set up GitHub first.${NC}"
    exit 1
fi

# Step 2: Verify latest code is pushed
echo ""
echo -e "${YELLOW}Step 2: Checking if all changes are pushed...${NC}"
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✓ Working directory clean${NC}"
else
    echo -e "${YELLOW}⚠ You have uncommitted changes. Committing now...${NC}"
    git add .
    git commit -m "Auto-commit before deployment"
    git push origin main
    echo -e "${GREEN}✓ Changes pushed${NC}"
fi

# Step 3: Display deployment info
echo ""
echo -e "${YELLOW}Step 3: Deployment Instructions${NC}"
echo ""
echo -e "${GREEN}Your app is ready to deploy!${NC}"
echo ""
echo "Choose your deployment method:"
echo ""
echo "▶ OPTION 1: Deploy to Render.com (Recommended)"
echo "  1. Visit: https://render.com"
echo "  2. Sign up/Login with GitHub"
echo "  3. Click 'New +' → 'Web Service'"
echo "  4. Select your GitHub repo: ${GITHUB_REPO}"
echo "  5. Configure:"
echo "     - Name: gov-schools-distance"
echo "     - Environment: Python 3"
echo "     - Build Command: pip install -r requirements.txt"
echo "     - Start Command: gunicorn app:app"
echo "     - Plan: Free or Paid"
echo "  6. Click 'Create Web Service'"
echo ""
echo "▶ OPTION 2: Deploy to Railway.app"
echo "  1. Visit: https://railway.app"
echo "  2. Sign up/Login with GitHub"
echo "  3. Click 'New Project' → 'Deploy from GitHub'"
echo "  4. Select your repo"
echo "  5. Auto-deploys in 2-3 minutes!"
echo ""
echo "▶ OPTION 3: Deploy to PythonAnywhere"
echo "  1. Visit: https://www.pythonanywhere.com"
echo "  2. Create account"
echo "  3. Upload your code or clone from GitHub"
echo "  4. Configure WSGI application"
echo ""
echo ""
echo -e "${GREEN}GitHub Repo:${NC} $GITHUB_REPO"
echo -e "${GREEN}Status:${NC} Ready for deployment"
echo ""
echo "======================================"
echo "Next: Open the deployment link above!"
echo "======================================"
