# Queen Koba Backend - Render Deployment Guide

## Prerequisites
- GitHub account
- Render account (free tier available)

## Deployment Steps

### 1. Push Code to GitHub
```bash
cd /home/user/Public/koba/backend/queen-koba-backend
git init
git add .
git commit -m "Initial commit - Queen Koba Backend"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `queenkoba-db`
   - **Database**: `queenkoba`
   - **User**: `queenkoba`
   - **Region**: Choose closest to your users
   - **Plan**: Free (1GB storage, expires after 90 days) or Starter ($7/month)
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://`)

### 3. Deploy Web Service on Render

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `queenkoba-backend`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or set to `backend/queen-koba-backend` if deploying from monorepo)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r app/requirements.txt`
   - **Start Command**: `gunicorn queenkoba_postgresql:app`
   - **Plan**: Free (or Starter $7/month for better performance)

4. **Environment Variables** - Add these:
   ```
   DATABASE_URL = [Paste Internal Database URL from step 2]
   JWT_SECRET_KEY = [Generate random string, e.g., use: openssl rand -hex 32]
   FRONTEND_URL = https://your-frontend.vercel.app
   ADMIN_URL = https://your-admin.vercel.app
   PYTHON_VERSION = 3.11.0
   ```

5. Click **Create Web Service**

### 4. Wait for Deployment
- Render will build and deploy your app (takes 2-5 minutes)
- Once deployed, you'll get a URL like: `https://queenkoba-backend.onrender.com`

### 5. Test Your API
```bash
curl https://queenkoba-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "counts": {
    "products": 6,
    "users": 1,
    "orders": 0
  }
}
```

### 6. Update Frontend & Admin

Update API URLs in your frontend and admin apps:

**Frontend** (`frontend/src/config.ts` or similar):
```typescript
export const API_URL = 'https://queenkoba-backend.onrender.com';
```

**Admin** (`admin/src/config.ts` or similar):
```typescript
export const API_URL = 'https://queenkoba-backend.onrender.com';
```

## Important Notes

### Free Tier Limitations
- **Spins down after 15 minutes of inactivity**
- First request after spin-down takes 30-60 seconds
- 750 hours/month free (enough for 1 service)
- Database expires after 90 days (backup your data!)

### Upgrading to Paid
- **Web Service**: $7/month (no spin-down, better performance)
- **Database**: $7/month (persistent, 10GB storage)

### Database Backups
```bash
# Backup database (run locally)
pg_dump YOUR_DATABASE_URL > backup.sql

# Restore database
psql YOUR_DATABASE_URL < backup.sql
```

### Monitoring
- View logs in Render Dashboard → Your Service → Logs
- Set up health check endpoint: `/health`

### Custom Domain (Optional)
1. Go to your service → Settings → Custom Domain
2. Add your domain (e.g., `api.queenkoba.com`)
3. Update DNS records as instructed

## Troubleshooting

### Build Fails
- Check `requirements.txt` path is correct
- Verify Python version compatibility

### Database Connection Error
- Ensure `DATABASE_URL` environment variable is set correctly
- Check database is in same region as web service

### CORS Errors
- Add your frontend/admin URLs to `FRONTEND_URL` and `ADMIN_URL` environment variables
- Restart the service after updating environment variables

### Slow First Request
- This is normal on free tier (cold start)
- Consider upgrading to paid tier or use a cron job to ping your API every 10 minutes

## Support
- Render Docs: https://render.com/docs
- Render Community: https://community.render.com/
