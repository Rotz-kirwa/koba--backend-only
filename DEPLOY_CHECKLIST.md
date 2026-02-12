# Render Deployment Checklist

## ✅ Pre-Deployment
- [x] CORS configuration updated with environment variables
- [x] requirements.txt includes all dependencies
- [x] gunicorn added for production server
- [x] .env.example created
- [x] .gitignore created
- [x] build.sh script created
- [x] render.yaml configuration created

## 📋 Deployment Steps

### 1. Push to GitHub
```bash
cd /home/user/Public/koba/backend/queen-koba-backend
git init
git add .
git commit -m "Ready for Render deployment"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Create Database on Render
- Go to https://dashboard.render.com/
- New + → PostgreSQL
- Name: `queenkoba-db`
- Database: `queenkoba`
- User: `queenkoba`
- Plan: Free or Starter ($7/mo)
- Copy **Internal Database URL**

### 3. Create Web Service on Render
- New + → Web Service
- Connect GitHub repo
- Name: `queenkoba-backend`
- Runtime: Python 3
- Build Command: `pip install -r app/requirements.txt`
- Start Command: `gunicorn queenkoba_postgresql:app`
- Plan: Free or Starter ($7/mo)

### 4. Add Environment Variables
```
DATABASE_URL = [Paste from step 2]
JWT_SECRET_KEY = [Generate: openssl rand -hex 32]
FRONTEND_URL = https://your-frontend.vercel.app
ADMIN_URL = https://your-admin.vercel.app
PYTHON_VERSION = 3.11.0
```

### 5. Deploy & Test
- Wait for build to complete (2-5 minutes)
- Test: `curl https://YOUR-APP.onrender.com/health`
- Check logs if errors occur

### 6. Update Frontend/Admin
Update API_URL in both apps to point to your Render URL:
```
https://queenkoba-backend.onrender.com
```

## 🎯 Your Render URL
After deployment, your API will be at:
```
https://queenkoba-backend.onrender.com
```

## 🔧 Post-Deployment
- [ ] Test all endpoints
- [ ] Update frontend API URL
- [ ] Update admin API URL
- [ ] Test login/signup
- [ ] Test product fetching
- [ ] Test cart operations
- [ ] Test checkout
- [ ] Monitor logs for errors

## 💡 Tips
- Free tier spins down after 15 min inactivity
- First request after spin-down takes 30-60 seconds
- Upgrade to paid ($7/mo) for always-on service
- Set up health check monitoring
