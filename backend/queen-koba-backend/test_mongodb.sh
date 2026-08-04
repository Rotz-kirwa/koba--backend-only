#!/bin/bash
echo "🧪 Testing Queen Koba MongoDB API"
echo "=================================="

API="http://localhost:5000"

echo "1. Health check..."
curl -s $API/health | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'✅ Health: {data[\"status\"]}')
    print(f'   Database: {data[\"database\"][:20]}...')
    print(f'   Products: {data[\"counts\"][\"products\"]}')
except:
    print('❌ API not responding')
"

echo -e "\n2. Get products..."
curl -s $API/products | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data['status'] == 'success':
        print(f'✅ Found {data[\"count\"]} products')
        for p in data['products'][:2]:
            print(f'   • {p[\"name\"]}')
            print(f'     USD: ${p[\"base_price_usd\"]}')
            if 'prices' in p and 'KES' in p['prices']:
                print(f'     KES: {p[\"prices\"][\"KES\"][\"amount\"]} {p[\"prices\"][\"KES\"][\"symbol\"]}')
    else:
        print(f'❌ Error: {data.get(\"error\", \"Unknown\")}')
except Exception as e:
    print(f'❌ Failed: {e}')
"

echo -e "\n3. Register test user..."
curl -s -X POST $API/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@queenkoba.com",
    "password": "test123",
    "country": "Kenya"
  }' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data['status'] == 'success':
        print(f'✅ Registration successful')
        print(f'   User: {data[\"user\"][\"username\"]}')
        token = data['access_token']
        with open('/tmp/qk_token.txt', 'w') as f:
            f.write(token)
    else:
        print(f'⚠️ Registration: {data.get(\"error\", \"Failed\")}')
except Exception as e:
    print(f'⚠️ Registration test: {e}')
"

echo -e "\n4. Login with admin..."
curl -s -X POST $API/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@queenkoba.com",
    "password": "admin123"
  }' | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data['status'] == 'success':
        print(f'✅ Login successful')
        print(f'   User: {data[\"user\"][\"email\"]}')
        admin_token = data['access_token']
        with open('/tmp/qk_admin_token.txt', 'w') as f:
            f.write(admin_token)
    else:
        print(f'❌ Login failed: {data.get(\"error\", \"Unknown\")}')
except Exception as e:
    print(f'❌ Login test failed: {e}')
"

echo -e "\n5. Test payment methods for Kenya..."
curl -s "$API/payment-methods/Kenya" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data['status'] == 'success':
        print(f'✅ Payment methods for {data[\"country\"]}:')
        for method in data['methods']:
            print(f'   • {method[\"name\"]}')
    else:
        print(f'❌ Failed to get payment methods')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo -e "\n🎯 API is ready!"
echo -e "\n📚 Key Endpoints:"
echo "   GET    /products              - Browse products"
echo "   POST   /auth/register         - Create account"
echo "   POST   /auth/login            - Login"
echo "   GET    /cart                  - View cart (needs auth)"
echo "   POST   /cart/add              - Add to cart (needs auth)"
echo "   POST   /checkout              - Checkout (needs auth)"
echo "   GET    /orders                - View orders (needs auth)"
echo "   GET    /payment-methods/{country} - Payment options"
