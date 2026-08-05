# 🚀 Queen Koba - Quick Start Guide

## ✅ System Status

**Backend**: ✅ Complete with Admin API
**Frontend**: ✅ Customer site ready
**Admin**: ✅ Dashboard ready

---

## 🎯 How to Run Everything

### 1. Start MongoDB (if not running)
```bash
docker ps | grep mongo
# If not running:
docker start queenkoba-mongo
# Or:
docker run -d -p 27017:27017 --name queenkoba-mongo mongo:latest
```

### 2. Start Backend API
```bash
cd /home/user/Public/koba/backend/queen-koba-backend
source venv/bin/activate
python queenkoba_mongodb.py
```

**Backend will run on**: http://localhost:5000

### 3. Start Customer Frontend
```bash
cd /home/user/Public/koba/frontend
npm run dev
```

**Frontend will run on**: http://localhost:5173

### 4. Start Admin Dashboard
```bash
cd /home/user/Public/koba/admin
npm run dev
```

**Admin will run on**: http://localhost:5174

---

## 🔑 Login Credentials

### Admin Dashboard
- **URL**: http://localhost:5174
- **Email**: `info@queenkoba.com`
- **Password**: `admin123`

### Customer Site
- Register a new account or use any test account

---

## 📊 What's Available

### Customer Site (Port 5173)
✅ Product catalog
✅ Shopping cart
✅ Checkout flow
✅ Multi-currency support
✅ Payment methods by country

### Admin Dashboard (Port 5174)
✅ Login system
✅ Dashboard with KPIs
✅ Navigation (15 sections)
✅ Products page (placeholder)
✅ Orders page (placeholder)
✅ Customers page (placeholder)

### Backend API (Port 5000)
✅ Customer authentication
✅ Product management
✅ Cart & checkout
✅ Order processing
✅ **Admin authentication** ✅ NEW!
✅ **Admin dashboard KPIs** ✅ NEW!
✅ **Admin product list** ✅ NEW!
✅ **Admin order list** ✅ NEW!
✅ **Admin customer list** ✅ NEW!

---

## 🐛 Troubleshooting

### "500 Internal Server Error" on Admin Login
**Solution**: Backend needs to be restarted to load new admin endpoints.

```bash
# Stop backend (Ctrl+C)
# Then restart:
cd /home/user/Public/koba/backend/queen-koba-backend
source venv/bin/activate
python queenkoba_mongodb.py
```

### Port Already in Use
```bash
# Kill process on specific port
lsof -ti:5000 | xargs kill -9  # Backend
lsof -ti:5173 | xargs kill -9  # Frontend
lsof -ti:5174 | xargs kill -9  # Admin
```

### MongoDB Not Running
```bash
docker ps | grep mongo
# If not running:
docker start queenkoba-mongo
```

### Admin Login Fails
1. Ensure backend is running
2. Check browser console for errors
3. Verify MongoDB has admin user:
```bash
mongosh queenkoba
db.users.findOne({email: "info@queenkoba.com"})
```

---

## 📁 Project Structure

```
koba/
├── backend/
│   └── queen-koba-backend/
│       ├── queenkoba_mongodb.py  ← Backend API (with admin endpoints)
│       └── venv/
├── frontend/
│   └── src/                      ← Customer website
├── admin/
│   └── src/                      ← Admin dashboard
└── README.md
```

---

## 🎉 Success!

If all three are running, you have:
1. **Customer Site** - Beautiful e-commerce site
2. **Admin Dashboard** - Luxury admin panel
3. **Backend API** - Powering both

---

## 📝 Next Steps

1. **Test Admin Login** - Go to http://localhost:5174
2. **View Dashboard** - See KPIs and metrics
3. **Explore Navigation** - 15 sections available
4. **Build Out Pages** - Products, Orders, Customers need full implementation

---

**Need Help?**
- Check `admin/README.md` for detailed admin docs
- Check `admin/IMPLEMENTATION_SUMMARY.md` for what's built
- Check backend logs for API errors
