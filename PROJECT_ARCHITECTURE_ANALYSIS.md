# Queen Koba E-Commerce Platform - Complete Architecture Analysis

## 📋 Executive Summary

Queen Koba is a full-stack e-commerce platform for premium Kenyan skincare products targeting melanin-rich skin across East Africa. The platform features multi-currency support, mobile money payments, and a complete shopping experience.

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Frontend)                   │
│  React + TypeScript + Vite + TailwindCSS + shadcn/ui       │
│                  Port: 5173 (Development)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       │ (JSON)
┌──────────────────────▼──────────────────────────────────────┐
│                   API LAYER (Backend)                        │
│     Flask + Flask-CORS + Flask-JWT-Extended + bcrypt        │
│                  Port: 5000 (Development)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ PyMongo
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  DATABASE LAYER                              │
│              MongoDB (NoSQL Document Store)                  │
│                  Port: 27017 (Default)                       │
│   Collections: products, users, orders                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Backend Architecture

### Technology Stack
- **Framework**: Flask 2.3.3 (Python web framework)
- **Database**: MongoDB 4.5.0 (NoSQL document database)
- **Authentication**: Flask-JWT-Extended 4.5.3 (JWT tokens)
- **Security**: bcrypt 4.1.2 (password hashing)
- **CORS**: Flask-CORS 4.0.0 (cross-origin requests)
- **Environment**: python-dotenv 1.0.0

### Core Components

#### 1. Main Application (`queenkoba_mongodb.py`)
**Purpose**: Central API server handling all business logic

**Key Features**:
- RESTful API endpoints
- JWT-based authentication
- Multi-currency pricing engine
- Shopping cart management
- Order processing
- Payment method routing

**Configuration**:
```python
MONGO_URI: mongodb://localhost:27017/queenkoba
JWT_SECRET_KEY: queenkoba-jwt-secret-2024
JWT_ACCESS_TOKEN_EXPIRES: 24 hours
HOST: 0.0.0.0
PORT: 5000
```

#### 2. Database Schema

**Products Collection**:
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  base_price_usd: Number,
  category: String,  // "Cream", "Serum", "Mask", etc.
  in_stock: Boolean,
  image_url: String,
  prices: {
    KES: { amount: Number, symbol: "KSh", country: "Kenya" },
    UGX: { amount: Number, symbol: "USh", country: "Uganda" },
    BIF: { amount: Number, symbol: "FBu", country: "Burundi" },
    CDF: { amount: Number, symbol: "FC", country: "DRC Congo" }
  },
  created_at: ISODate
}
```

**Users Collection**:
```javascript
{
  _id: ObjectId,
  username: String,
  email: String (unique),
  password_hash: String (bcrypt),
  country: String,
  preferred_currency: String,  // "KES", "UGX", "BIF", "CDF"
  role: String,  // "admin" or "customer"
  cart: [
    {
      product_id: String,
      quantity: Number,
      added_at: ISODate
    }
  ],
  orders: [ObjectId],  // References to orders
  created_at: ISODate,
  updated_at: ISODate
}
```

**Orders Collection**:
```javascript
{
  _id: ObjectId,
  order_id: String,  // Human-readable ID (e.g., "QK123456")
  user_id: String,
  items: [
    {
      product_id: String,
      product_name: String,
      quantity: Number,
      price_per_item: Number,
      item_total: Number
    }
  ],
  total_usd: Number,
  shipping_address: Object,
  payment_method: String,
  payment_status: String,  // "pending", "completed", "failed"
  order_status: String,  // "processing", "shipped", "delivered"
  created_at: ISODate,
  updated_at: ISODate
}
```

#### 3. API Endpoints

**Public Endpoints** (No Authentication):
```
GET  /                              - API information
GET  /health                        - Health check & database status
GET  /products                      - List all products with multi-currency prices
GET  /products/<id>                 - Get single product details
POST /auth/register                 - Register new user
POST /auth/login                    - Login user (returns JWT token)
GET  /payment-methods/<country>     - Get payment methods by country
```

**Protected Endpoints** (Require JWT Token):
```
GET    /auth/profile                - Get user profile
GET    /cart                        - View user's cart
POST   /cart/add                    - Add item to cart
DELETE /cart/remove/<product_id>   - Remove item from cart
POST   /checkout                    - Create order from cart
GET    /orders                      - Get user's order history
GET    /orders/<id>                 - Get specific order details
```

#### 4. Multi-Currency System

**Exchange Rates** (Base: USD):
```python
KES: 128.5      # Kenyan Shilling
UGX: 3582.34    # Ugandan Shilling
BIF: 2850.0     # Burundi Franc
CDF: 2700.0     # Congolese Franc
```

**Price Calculation Logic**:
```python
def calculate_prices(base_price_usd):
    for currency, rate in exchange_rates.items():
        local_price = base_price_usd * rate
        # Returns prices object with all currencies
```

#### 5. Payment Methods by Country

**Kenya**:
- M-Pesa (Mobile Money) - Primary
- Airtel Money (Mobile Money)
- Visa/Mastercard
- Bank Transfer

**Uganda**:
- MTN Mobile Money - Primary
- Airtel Money
- Visa/Mastercard

**Burundi**:
- Lumicash (Mobile Money)
- EcoCash (Mobile Money)
- Bank Transfer

**DRC Congo**:
- Orange Money (Mobile Money)
- Vodacom M-Pesa (Mobile Money)
- Bank Transfer

#### 6. Authentication Flow

```
1. User Registration:
   POST /auth/register
   → Hash password with bcrypt
   → Store user in MongoDB
   → Generate JWT token
   → Return token + user data

2. User Login:
   POST /auth/login
   → Verify email exists
   → Compare password hash
   → Generate JWT token
   → Return token + user data

3. Protected Requests:
   Authorization: Bearer <JWT_TOKEN>
   → Verify token signature
   → Extract user_id from token
   → Process request
```

---

## 🎨 Frontend Architecture

### Technology Stack
- **Framework**: React 18.3.1 with TypeScript
- **Build Tool**: Vite 5.4.19
- **Styling**: TailwindCSS 3.4.17
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Routing**: React Router DOM 6.30.1
- **State Management**: React Context API
- **Animations**: Framer Motion 12.33.0
- **HTTP Client**: Fetch API
- **Form Handling**: React Hook Form 7.61.1

### Project Structure

```
frontend/
├── public/
│   ├── images/          # Product images
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── ui/         # shadcn/ui components
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── Hero.tsx
│   │   ├── ProductStore.tsx
│   │   ├── CartDrawer.tsx
│   │   └── ...
│   ├── context/
│   │   └── CartContext.tsx    # Global cart state
│   ├── data/
│   │   └── products.ts        # Static product data
│   ├── hooks/
│   │   ├── use-mobile.tsx
│   │   └── use-toast.ts
│   ├── lib/
│   │   ├── api.ts            # API client & endpoints
│   │   └── utils.ts          # Utility functions
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Shop.tsx
│   │   ├── Checkout.tsx
│   │   ├── Story.tsx
│   │   └── ...
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── .env                     # Environment variables
├── package.json
├── vite.config.ts
└── tailwind.config.ts
```

### Core Components

#### 1. API Client (`src/lib/api.ts`)

**Purpose**: Centralized API communication layer

**Features**:
- Automatic JWT token injection
- Error handling
- Type-safe endpoints
- Base URL configuration

**Structure**:
```typescript
const API_BASE_URL = 'http://localhost:5000'

// API modules:
- authAPI: register, login, getProfile
- productsAPI: getAll, getById
- cartAPI: get, add, remove
- ordersAPI: create, getAll, getById
- paymentAPI: getByCountry
```

**Token Management**:
```typescript
// Store token after login
localStorage.setItem('queenkoba_token', token)

// Inject in all requests
headers['Authorization'] = `Bearer ${token}`
```

#### 2. Cart Context (`src/context/CartContext.tsx`)

**Purpose**: Global shopping cart state management

**State**:
```typescript
interface CartItem {
  product: Product
  quantity: number
}

interface CartContextType {
  items: CartItem[]
  addToCart: (product, qty) => void
  removeFromCart: (productId) => void
  updateQuantity: (productId, qty) => void
  clearCart: () => void
  total: number
  itemCount: number
  isOpen: boolean
  setIsOpen: (open) => void
}
```

**Persistence**:
```typescript
// Save to localStorage on every change
localStorage.setItem('queenkoba-cart', JSON.stringify(items))

// Load on app initialization
const saved = localStorage.getItem('queenkoba-cart')
```

#### 3. Product Data (`src/data/products.ts`)

**Purpose**: Static product catalog (frontend fallback)

**Products**:
1. Eternal Radiance - Complexion Clarifying Cleanser (KES 1,500)
2. Eternal Radiance - Complexion Clarifying Toner (KES 1,800)
3. Eternal Radiance - Complexion Clarifying Serum (KES 2,500)
4. Eternal Radiance - Complexion Clarifying Cream (KES 2,200)
5. Eternal Radiance - Complexion Clarifying Mask (KES 1,200)
6. Full Royal Routine Bundle (KES 8,000 - 15% OFF)

**Key Ingredients**: Qasil, Liwa, Moringa, Snail Mucin Extract

#### 4. Checkout Flow (`src/pages/Checkout.tsx`)

**4-Step Process**:

**Step 1: Shipping Information**
- Full name, email, phone
- Country selection (Kenya, Uganda, Burundi, DR Congo)
- Address, city, postal code

**Step 2: Payment Method Selection**
- Fetches country-specific payment methods from API
- Fallback to hardcoded methods if API fails
- Visual selection with logos

**Step 3: Payment Details**
- Mobile Money: Phone number input
- Card: Card number, expiry, CVV
- Bank Transfer: Bank name, account number

**Step 4: Review & Confirm**
- Display shipping details
- Display payment method
- Show order summary
- Place order button

**Currency Conversion**:
```typescript
const currencyConfig = {
  Kenya: { code: "KES", symbol: "KSh", rate: 1 },
  Uganda: { code: "UGX", symbol: "UGX", rate: 28.5 },
  Burundi: { code: "BIF", symbol: "FBu", rate: 285 },
  Congo: { code: "CDF", symbol: "FC", rate: 280 }
}
```

#### 5. Routing (`src/App.tsx`)

**Routes**:
```typescript
/           → Home page (Hero + Products + Testimonials)
/all        → Index page (All sections)
/story      → Brand story
/ingredients → Ingredient details
/shop       → Product catalog
/reviews    → Customer reviews
/checkout   → Checkout flow
/contact    → Contact form
*           → 404 Not Found
```

**Global Components** (Present on all pages):
- Navbar (sticky header)
- CartDrawer (slide-out cart)
- WhatsAppFloat (floating WhatsApp button)
- Footer
- Toast notifications

---

## 🔄 Data Flow

### 1. Product Browsing Flow

```
User visits /shop
    ↓
Frontend loads products from local data (products.ts)
    ↓
(Optional) Frontend fetches products from API
    GET /products
    ↓
Backend queries MongoDB products collection
    ↓
Backend calculates multi-currency prices
    ↓
Backend returns products with all currency options
    ↓
Frontend displays products with user's preferred currency
```

### 2. Add to Cart Flow

```
User clicks "Add to Cart"
    ↓
CartContext.addToCart(product, quantity)
    ↓
Update local state (items array)
    ↓
Save to localStorage
    ↓
Open CartDrawer (setIsOpen(true))
    ↓
Display success toast notification
```

### 3. Checkout Flow

```
User clicks "Checkout"
    ↓
Navigate to /checkout
    ↓
Step 1: Collect shipping information
    ↓
Step 2: Fetch payment methods
    POST /payment-methods/{country}
    ↓
Backend returns country-specific payment options
    ↓
User selects payment method
    ↓
Step 3: Collect payment details
    ↓
Step 4: Review order
    ↓
User confirms order
    ↓
Frontend sends order to backend
    POST /checkout
    {
      shipping_address: {...},
      payment_method: "mpesa",
      items: [...]
    }
    ↓
Backend creates order in MongoDB
    ↓
Backend clears user's cart
    ↓
Backend returns order confirmation
    ↓
Frontend clears local cart
    ↓
Frontend shows success message
    ↓
Redirect to home page
```

### 4. Authentication Flow

```
User Registration:
    ↓
User fills registration form
    ↓
POST /auth/register
    {
      username, email, password,
      country, preferred_currency
    }
    ↓
Backend hashes password (bcrypt)
    ↓
Backend stores user in MongoDB
    ↓
Backend generates JWT token
    ↓
Frontend stores token in localStorage
    ↓
Frontend updates UI (logged in state)

User Login:
    ↓
User enters email & password
    ↓
POST /auth/login
    ↓
Backend verifies credentials
    ↓
Backend generates JWT token
    ↓
Frontend stores token
    ↓
Frontend redirects to dashboard/home
```

---

## 🔐 Security Features

### Backend Security
1. **Password Hashing**: bcrypt with salt rounds
2. **JWT Authentication**: Signed tokens with 24-hour expiry
3. **CORS Protection**: Configured allowed origins
4. **Input Validation**: Request data validation
5. **MongoDB Injection Prevention**: PyMongo parameterized queries

### Frontend Security
1. **Token Storage**: localStorage (consider httpOnly cookies for production)
2. **Protected Routes**: JWT required for cart/checkout
3. **XSS Prevention**: React's built-in escaping
4. **HTTPS**: Required for production deployment

---

## 🌍 Multi-Currency & Localization

### Currency Support
- **Base Currency**: USD (for internal calculations)
- **Display Currencies**: KES, UGX, BIF, CDF
- **Conversion**: Real-time calculation based on exchange rates
- **User Preference**: Stored in user profile

### Country-Specific Features
- **Payment Methods**: Different options per country
- **Currency Display**: Automatic based on country selection
- **Shipping Costs**: Country-specific rates
- **Mobile Money Integration**: Country-specific providers

---

## 📦 Deployment Architecture

### Development Environment
```
Frontend: http://localhost:5173 (Vite dev server)
Backend:  http://localhost:5000 (Flask dev server)
Database: mongodb://localhost:27017 (Local MongoDB)
```

### Production Recommendations

**Frontend**:
- Deploy to: Vercel, Netlify, or AWS S3 + CloudFront
- Build command: `npm run build`
- Output: `dist/` directory
- Environment: Set `VITE_API_URL` to production backend URL

**Backend**:
- Deploy to: AWS EC2, Heroku, or DigitalOcean
- WSGI Server: Gunicorn (4 workers)
- Process Manager: systemd or PM2
- Environment: Set production MongoDB URI and secrets

**Database**:
- MongoDB Atlas (cloud) or self-hosted MongoDB
- Enable authentication
- Configure backups
- Set up monitoring

---

## 🔧 Configuration Files

### Backend Configuration
**File**: `backend/queen-koba-backend/.env`
```env
MONGO_URI=mongodb://localhost:27017/queenkoba
JWT_SECRET_KEY=queenkoba-jwt-secret-2024
SECRET_KEY=queenkoba-secret-key-2024
FLASK_ENV=development
```

### Frontend Configuration
**File**: `frontend/.env`
```env
VITE_API_URL=http://localhost:5000
VITE_APP_NAME=Queen Koba
VITE_APP_VERSION=1.0.0
```

---

## 🚀 Running the Application

### Backend Setup
```bash
cd backend/queen-koba-backend

# Option 1: Automated setup
chmod +x run_queenkoba.sh
./run_queenkoba.sh

# Option 2: Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt
python queenkoba_mongodb.py
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Database Setup
```bash
# Option 1: Docker
docker run -d -p 27017:27017 --name queenkoba-mongo mongo:latest

# Option 2: System service
sudo systemctl start mongodb

# Option 3: MongoDB Atlas (cloud)
# Use connection string in .env
```

---

## 📊 Key Features Summary

### E-Commerce Features
✅ Product catalog with images and descriptions
✅ Shopping cart with add/remove/update
✅ Multi-step checkout process
✅ Order management and history
✅ User authentication and profiles

### Payment Features
✅ Multi-currency support (4 currencies)
✅ Country-specific payment methods
✅ Mobile money integration (M-Pesa, MTN, etc.)
✅ Card payments (Visa/Mastercard)
✅ Bank transfer option

### User Experience
✅ Responsive design (mobile, tablet, desktop)
✅ Smooth animations (Framer Motion)
✅ Toast notifications
✅ WhatsApp integration
✅ SEO optimized (meta tags, schema.org)

### Technical Features
✅ RESTful API architecture
✅ JWT authentication
✅ MongoDB document storage
✅ TypeScript type safety
✅ Component-based architecture

---

## 🎯 Business Logic

### Product Seeding
- 6 core products automatically seeded on first run
- Admin user created: `info@queenkoba.com`
- Multi-currency prices calculated automatically

### Cart Management
- Persistent cart (localStorage)
- Quantity updates
- Real-time total calculation
- Currency conversion

### Order Processing
1. Validate cart items
2. Calculate totals in user's currency
3. Create order record
4. Clear user's cart
5. Send confirmation
6. (Future) Trigger payment gateway
7. (Future) Send email notification

---

## 🔮 Future Enhancements

### Backend
- [ ] Payment gateway integration (Flutterwave, Paystack)
- [ ] Email notifications (SendGrid, AWS SES)
- [ ] SMS notifications for mobile money
- [ ] Inventory management
- [ ] Admin dashboard API
- [ ] Product reviews and ratings
- [ ] Wishlist functionality
- [ ] Discount codes and promotions

### Frontend
- [ ] User dashboard
- [ ] Order tracking
- [ ] Product reviews interface
- [ ] Wishlist page
- [ ] Live chat support
- [ ] Progressive Web App (PWA)
- [ ] Multi-language support
- [ ] Advanced filtering and search

### Infrastructure
- [ ] Redis caching
- [ ] CDN for images
- [ ] Load balancing
- [ ] Automated backups
- [ ] Monitoring and logging (Sentry, LogRocket)
- [ ] CI/CD pipeline

---

## 📝 Notes

### Current Limitations
1. **Payment Processing**: Simulated (not integrated with real gateways)
2. **Email Notifications**: Not implemented
3. **Inventory Tracking**: Basic (in_stock boolean only)
4. **Admin Panel**: No UI (API only)
5. **Image Storage**: External URLs (Dropbox)

### Development vs Production
- Development uses local MongoDB
- Production should use MongoDB Atlas or secured instance
- JWT secrets must be changed for production
- CORS origins must be restricted
- HTTPS required for production
- Environment variables must be secured

---

## 🤝 Integration Points

### Frontend ↔ Backend
- **Protocol**: HTTP/REST
- **Format**: JSON
- **Authentication**: JWT Bearer tokens
- **Base URL**: Configurable via environment variable

### Backend ↔ Database
- **Driver**: PyMongo
- **Connection**: MongoDB URI
- **Collections**: products, users, orders
- **Indexes**: email (unique), product_id, user_id

### External Services (Future)
- Payment Gateways (Flutterwave, Paystack)
- Email Service (SendGrid, AWS SES)
- SMS Service (Twilio, Africa's Talking)
- Cloud Storage (AWS S3, Cloudinary)

---

## 📚 Technology Decisions

### Why Flask?
- Lightweight and flexible
- Easy to learn and deploy
- Excellent for RESTful APIs
- Strong ecosystem

### Why MongoDB?
- Flexible schema for evolving product data
- Easy to scale horizontally
- JSON-like documents match frontend data
- Good for e-commerce catalogs

### Why React?
- Component reusability
- Large ecosystem
- Excellent developer experience
- Strong TypeScript support

### Why Vite?
- Fast development server
- Optimized production builds
- Modern tooling
- Better than Create React App

---

## 🎓 Learning Resources

### Backend
- Flask Documentation: https://flask.palletsprojects.com/
- MongoDB Python Driver: https://pymongo.readthedocs.io/
- JWT Best Practices: https://jwt.io/introduction

### Frontend
- React Documentation: https://react.dev/
- TypeScript Handbook: https://www.typescriptlang.org/docs/
- TailwindCSS: https://tailwindcss.com/docs
- shadcn/ui: https://ui.shadcn.com/

---

**Last Updated**: 2024
**Version**: 1.0.0
**Status**: Development
