#!/bin/bash
# One-Click Render Deployment Script
# This script opens Render.com and shows deployment steps

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    GOVERNMENT SCHOOLS DISTANCE SYSTEM                ║"
echo "║                     ONE-CLICK DEPLOYMENT TO RENDER                   ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check git status
echo "Checking git status..."
REMOTE=$(git remote get-url origin 2>/dev/null)
if [ -z "$REMOTE" ]; then
    echo "Error: Not a git repository"
    exit 1
fi

echo "✅ Repository: $REMOTE"
echo ""

# Check if on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (current: $BRANCH)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "DEPLOYMENT INSTRUCTIONS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

echo "Your app is ready to deploy! Here's what to do:"
echo ""
echo "1. Open: https://render.com"
echo ""
echo "2. Sign up or login with GitHub"
echo ""
echo "3. Click 'New +' → 'Web Service'"
echo ""
echo "4. Select your repository: GovToBeacNhdcBefDistanceSystem"
echo ""
echo "5. Fill in these settings:"
echo ""
echo "   ┌─ RENDER CONFIGURATION ─────────────────────────────────────┐"
echo "   │                                                            │"
echo "   │  Name:          gov-schools-distance                      │"
echo "   │  Environment:   Python 3                                  │"
echo "   │                                                            │"
echo "   │  Build Cmd:     pip install -r requirements.txt           │"
echo "   │  Start Cmd:     gunicorn app:app                          │"
echo "   │                                                            │"
echo "   │  Plan:          Free (750 hrs/month)                      │"
echo "   │                                                            │"
echo "   └────────────────────────────────────────────────────────────┘"
echo ""
echo "6. Click 'Create Web Service' button"
echo ""
echo "7. Wait 2-5 minutes for deployment"
echo ""
echo "8. Get your live URL from the Render dashboard!"
echo ""

echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Ask if user wants to open Render.com
read -p "Open https://render.com now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Opening Render.com..."
    
    # Try to open in default browser
    if command -v open &> /dev/null; then
        open "https://render.com"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "https://render.com"
    elif command -v start &> /dev/null; then
        start "https://render.com"
    else
        echo "Please visit: https://render.com"
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "KEY POINTS:"
echo ""
echo "  • Repository is public and ready to deploy"
echo "  • GitHub integration is automatic"
echo "  • Future pushes to main branch will auto-redeploy"
echo "  • Logs visible in Render dashboard"
echo "  • Free tier includes 750 hours/month"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "After deployment completes:"
echo ""
echo "  Push updates with:"
echo "  $ git commit -m 'your changes'"
echo "  $ git push origin main"
echo ""
echo "  (Automatic redeploy in 2-5 minutes!)"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Need help? Run:"
echo "  python3 deploy_interactive.py"
echo ""
