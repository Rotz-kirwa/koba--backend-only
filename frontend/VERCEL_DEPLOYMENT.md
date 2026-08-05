# Queen Koba - Vercel Deployment Guide

## ✅ GitHub Repository
Your code is now live at: https://github.com/Rotz-kirwa/queen-koba

## 🚀 Deploy to Vercel

### Option 1: One-Click Deploy (Recommended)
1. Go to [Vercel](https://vercel.com)
2. Click "Add New Project"
3. Import from GitHub: `Rotz-kirwa/queen-koba`
4. Configure:
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

### Option 2: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
cd /home/user/Public/royal-melanin-glow
vercel

# Deploy to production
vercel --prod
```

## 🔧 Environment Variables (Optional)
If you want to connect to the backend, add these in Vercel:

```
VITE_API_URL=https://your-backend-url.com
```

## 📋 Build Settings for Vercel

**Framework:** Vite
**Build Command:** `npm run build`
**Output Directory:** `dist`
**Install Command:** `npm install`
**Node Version:** 18.x

## 🌐 Custom Domain (Optional)
1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain (e.g., queenkoba.com)
4. Follow DNS configuration instructions

## ✨ Features Deployed
- ✅ Multi-page e-commerce site
- ✅ Shopping cart with localStorage
- ✅ Checkout flow with payment options
- ✅ Contact page with form
- ✅ Testimonials with images
- ✅ Product catalog with images
- ✅ Responsive design (mobile + desktop)
- ✅ WhatsApp floating button
- ✅ Optimized hero images
- ✅ SEO meta tags

## 🔗 Expected URLs After Deployment
- Homepage: `https://your-project.vercel.app/`
- Shop: `https://your-project.vercel.app/shop`
- Checkout: `https://your-project.vercel.app/checkout`
- Contact: `https://your-project.vercel.app/contact`
- Story: `https://your-project.vercel.app/story`

## 📱 Backend Integration
To connect the backend:
1. Deploy backend to a hosting service (Heroku, Railway, Render)
2. Update `.env` file with backend URL
3. Redeploy to Vercel

## 🎉 Post-Deployment Checklist
- [ ] Test all pages load correctly
- [ ] Verify shopping cart works
- [ ] Test checkout flow
- [ ] Check mobile responsiveness
- [ ] Test WhatsApp button
- [ ] Verify contact form
- [ ] Check all images load
- [ ] Test navigation menu

## 🐛 Troubleshooting

### Build Fails
- Check Node version (use 18.x)
- Verify all dependencies in package.json
- Check for TypeScript errors

### Images Not Loading
- Ensure images are in `/public` folder
- Check image paths are correct
- Verify Dropbox links have `raw=1` parameter

### Routes Not Working
- Vercel automatically handles React Router
- If issues persist, add `vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

## 📞 Support
- GitHub Issues: https://github.com/Rotz-kirwa/queen-koba/issues
- Vercel Docs: https://vercel.com/docs

---

**Repository:** https://github.com/Rotz-kirwa/queen-koba
**Status:** ✅ Ready for deployment
