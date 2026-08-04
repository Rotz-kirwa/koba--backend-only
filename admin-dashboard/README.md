# Queen Koba Admin Dashboard

Admin panel for managing Queen Koba e-commerce platform.

## Features

- **Dashboard**: Overview with key metrics (orders, revenue, users, products)
- **Orders Management**: View and update order statuses
- **Products Management**: Add, edit, delete products
- **Users Management**: View registered users
- **Payments Tracking**: Monitor all payment transactions

## Setup

```bash
cd /home/user/Public/queen-koba-admin
npm install
npm run dev
```

Admin panel runs on: `http://localhost:3001`

## Backend Connection

Connects to the same backend as the main store:
- API URL: `http://localhost:5000`
- Configured in `.env` file

## Default Admin Credentials

- Email: `admin@queenkoba.com`
- Password: `admin123`

⚠️ **Change these in production!**

## Project Structure

```
queen-koba-admin/
├── src/
│   ├── components/
│   │   └── Sidebar.tsx          # Navigation sidebar
│   ├── pages/
│   │   ├── Dashboard.tsx        # Main dashboard
│   │   ├── Orders.tsx           # Orders management
│   │   ├── Products.tsx         # Products management
│   │   ├── Users.tsx            # Users management
│   │   ├── Payments.tsx         # Payments tracking
│   │   └── Login.tsx            # Admin login
│   ├── lib/
│   │   └── api.ts               # API service layer
│   ├── App.tsx                  # Main app with routing
│   └── main.tsx                 # Entry point
├── .env                         # Environment config
└── package.json
```

## API Endpoints Used

- `POST /auth/login` - Admin login
- `GET /admin/stats` - Dashboard statistics
- `GET /admin/orders` - List all orders
- `PATCH /admin/orders/:id/status` - Update order status
- `GET /products` - List products
- `POST /admin/products` - Create product
- `PUT /admin/products/:id` - Update product
- `DELETE /admin/products/:id` - Delete product
- `GET /admin/users` - List users
- `GET /admin/payments` - List payments

## Tech Stack

- React 18 + TypeScript
- Vite
- React Router DOM
- Tailwind CSS
- Lucide React (icons)
- Recharts (charts)

## Development

The admin dashboard is completely separate from the main store but shares the same backend API.

**Main Store**: `http://localhost:8080` (port 8080)
**Admin Panel**: `http://localhost:3001` (port 3001)
**Backend API**: `http://localhost:5000` (port 5000)
