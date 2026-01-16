#!/bin/bash
# Automated Render Deployment
# This script deploys your Flask app to Render and gets you a live URL

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                   AUTOMATIC RENDER DEPLOYMENT                        ║"
echo "║        Government Schools Distance Analysis System - Flask App        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "❌ curl is required but not found"
    exit 1
fi

echo "To deploy your app automatically, you need a Render API token."
echo ""
echo "Step 1: Get your API Token"
echo "───────────────────────────"
echo "1. Go to: https://dashboard.render.com/account/api-tokens"
echo "2. Create a new API token"
echo "3. Copy the token"
echo ""

read -p "Paste your Render API token (or press Enter to use manual deployment): " RENDER_TOKEN

if [ -z "$RENDER_TOKEN" ]; then
    echo ""
    echo "No token provided. Using manual deployment instructions instead..."
    echo ""
    echo "MANUAL DEPLOYMENT:"
    echo "─────────────────"
    echo ""
    echo "1. Go to: https://render.com"
    echo "2. Click 'New +' → 'Web Service'"
    echo "3. Authorize GitHub access"
    echo "4. Select repo: GovToBeacNhdcBefDistanceSystem"
    echo "5. Configure:"
    echo ""
    echo "   Name:       gov-schools-distance"
    echo "   Env:        Python 3"
    echo "   Build Cmd:  pip install -r requirements.txt"
    echo "   Start Cmd:  gunicorn app:app"
    echo "   Plan:       Free"
    echo ""
    echo "6. Click 'Create Web Service'"
    echo "7. Wait 2-5 minutes"
    echo "8. Your app will be live!"
    echo ""
    
    # Try to open browser
    if command -v open &> /dev/null; then
        echo "Opening https://render.com ..."
        open "https://render.com"
    fi
else
    echo ""
    echo "Token received. Attempting automated deployment..."
    echo ""
    
    # Deploy using Render API
    echo "Creating web service on Render..."
    
    RESPONSE=$(curl -s -X POST "https://api.render.com/v1/services" \
      -H "Authorization: Bearer $RENDER_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "type": "web_service",
        "name": "gov-schools-distance",
        "ownerId": "te_",
        "repo": "https://github.com/engbakhtmuhammad/GovToBeacNhdcBefDistanceSystem",
        "branch": "main",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "gunicorn app:app",
        "envVars": [
          {"key": "PYTHON_VERSION", "value": "3.11.7"}
        ],
        "plan": "free"
      }')
    
    SERVICE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -n "$SERVICE_ID" ]; then
        echo "✅ Service created! ID: $SERVICE_ID"
        echo ""
        echo "Your app is being deployed..."
        echo "This usually takes 3-5 minutes"
        echo ""
        echo "Check status at:"
        echo "https://dashboard.render.com/services/$SERVICE_ID"
    else
        echo "❌ Failed to create service"
        echo "Response: $RESPONSE"
        echo ""
        echo "Please use manual deployment instead:"
        echo "1. Visit https://render.com"
        echo "2. Sign in with GitHub"
        echo "3. Create Web Service"
        echo "4. See instructions above"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
