# Government Schools Distance Analysis System - Deployment Guide

## Quick Deploy to Render.com (Recommended - FREE)

### Step 1: Create GitHub Repository
```bash
cd /path/to/GovToSchoolsDistanceSystem
git init
git add .
git commit -m "Initial commit"
git branch -M main
```

Then create a new repository on GitHub and push:
```bash
git remote add origin https://github.com/YOUR_USERNAME/GovToSchoolsDistanceSystem.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name:** GovToSchoolsDistance
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free (or Paid if you need better performance)
6. Click "Create Web Service"

Your app will be live at: `https://govtoschemoolsdistance.onrender.com`

---

## Alternative: Deploy to Railway.app

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway auto-detects Python and Flask
5. Your app will be live in 2-3 minutes

---

## Alternative: Deploy to PythonAnywhere

1. Go to https://www.pythonanywhere.com
2. Create free account
3. Upload your code
4. Configure WSGI to point to `app:app`
5. Enable web app

---

## Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment to development
export FLASK_ENV=development

# Run locally
python app.py

# Visit http://localhost:5000
```

---

## Important Notes

- **File Uploads:** Free tier services may have temporary storage. Implement database storage for production.
- **Max File Size:** Currently set to 50MB. Adjust in `app.py` if needed.
- **Environment Variables:** Use `.env` file for sensitive data (never commit secrets)
- **Persistent Storage:** Consider adding cloud storage (AWS S3, Google Cloud Storage) for production

