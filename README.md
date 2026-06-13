# 🛒 QuickCommerce AI - Intelligent Shopping Assistant

> A fully local, AI-powered quick commerce platform with advanced features like semantic search, stock substitution, cart optimization, and contextual recommendations.

## 🌟 Key Features

- **🤖 AI-Powered Chat** - Natural language shopping with Groq's llama-3.3-70b
- **🔄 Smart Substitution** - Automatically suggests alternatives for out-of-stock items
- **💰 Cart Optimizer** - Proactively helps users hit free delivery thresholds
- **🌤️ Context-Aware** - Weather, time, and event-based recommendations
- **👨‍🍳 Recipe-to-Cart** - Parse recipes into shoppable ingredient lists
- **🔍 Semantic Search** - ChromaDB-powered product discovery
- **📦 Order History** - Track purchases for personalized suggestions
- **🏠 100% Local** - No cloud dependencies, runs on SQLite

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Groq API key (free at https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd QuickCommerce

# 2. Backend Setup
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# 3. Configure Environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 4. Initialize ChromaDB (optional but recommended)
python -c "from services.rag_service import get_rag_collection; get_rag_collection()"

# 5. Start Backend
python -m uvicorn main:app --reload --port 8080

# 6. Frontend Setup (new terminal)
cd frontend
npm install
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs

## 📚 Documentation

- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Detailed setup guide
- **[FEATURE_SUMMARY.md](FEATURE_SUMMARY.md)** - Complete feature breakdown
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Code examples for advanced features

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (React + Vite)                │
│  - Chat Interface                       │
│  - Product Catalog                      │
│  - Shopping Cart                        │
└──────────────┬──────────────────────────┘
               │ REST API
┌──────────────┴──────────────────────────┐
│  Backend (FastAPI)                      │
│  ┌────────────────────────────────────┐ │
│  │ LLM Service (Groq)                 │ │
│  │ - Chat recommendations             │ │
│  │ - Recipe parsing                   │ │
│  │ - Context integration              │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ RAG Service (ChromaDB)             │ │
│  │ - Semantic search                  │ │
│  │ - Stock substitution               │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Context Service                    │ │
│  │ - Weather, time, events            │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ SQLite Database                    │ │
│  │ - Users, Cart, Orders              │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🎯 Core Features

### 1. AI Shopping Assistant
Natural language chat interface powered by Groq's llama-3.3-70b model:
```
User: "I need breakfast items"
Bot: "It's Saturday morning! Here are fresh breakfast essentials:
     - Eggs (₹36)
     - Milk (₹60)
     - Bread (₹45)
     Total: ₹141"
```

### 2. Smart Substitution Engine
Automatically finds alternatives when products are unavailable:
```python
# If "Amul Milk" is out of stock
→ Suggests "Mother Dairy Milk" (same category, similar price)
```

### 3. Cart Value Optimizer
Helps users reach free delivery thresholds:
```
Cart Total: ₹360
Gap: ₹39 to free delivery
Suggestion: "Add Britannia Biscuits (₹40) to save ₹49 on delivery!"
```

### 4. Contextual Recommendations
Adapts to real-world conditions:
- **Weather**: Hot → Cold drinks, Rain → Hot snacks
- **Time**: Morning → Breakfast, Evening → Dinner ingredients
- **Events**: Weekend → Family packs, Cricket match → Snacks

### 5. Recipe-to-Cart
Parse recipes into shoppable ingredients:
```
Input: "Paneer Butter Masala for 3 people"
Output: [Paneer, Butter, Tomatoes, Cream, ...]
         (Omits items bought recently like Salt, Oil)
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Local database
- **Groq** - Free LLM API (llama-3.3-70b-versatile)
- **ChromaDB** - Vector database for semantic search
- **Sentence Transformers** - Embedding model (all-MiniLM-L6-v2)

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client

## 📊 Database Schema

```sql
-- Users & Authentication
users (id, username, email, hashed_password, created_at)
user_profiles (id, user_id, dietary_preferences, budget)

-- Shopping Cart
cart_items (id, user_id, product_id, quantity, added_at)

-- Order History (for frequency analysis)
orders (id, user_id, total_amount, status, created_at)
order_items (id, order_id, product_id, quantity, price)
```

## 🔧 Configuration

### Environment Variables (`backend/.env`)
```env
# Required
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_jwt_secret_key

# Optional
WEATHER_API_KEY=your_openweathermap_key
FREE_DELIVERY_THRESHOLD=399.0
DELIVERY_CHARGE=49.0
```

## 🧪 Testing

### Test Chat Functionality
```bash
# Start servers
cd backend && python -m uvicorn main:app --reload --port 8080
cd frontend && npm run dev

# Test queries in chat:
- "I need breakfast items"
- "Give me cold drinks"
- "Help me save on delivery" (with items in cart)
```

### Test Backend API
```bash
# Health check
curl http://localhost:8080/health

# Get products
curl http://localhost:8080/api/products?limit=5

# Chat (requires auth token)
curl -X POST http://localhost:8080/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "I need snacks", "history": []}'
```

## 📈 Performance

- **Response Time**: 1-3 seconds per chat request
- **Groq Free Tier**: 30 requests/minute
- **ChromaDB**: <100ms semantic search
- **SQLite**: Handles 100+ concurrent users
- **Product Catalog**: 194 items across 24 categories

## 🎨 Customization

### Add New Product Categories
Edit `backend/data/products.json` and run:
```bash
python -c "from services.rag_service import get_rag_collection; get_rag_collection()"
```

### Adjust Business Rules
Edit `backend/config.py`:
```python
FREE_DELIVERY_THRESHOLD = 399.0  # Change threshold
DELIVERY_CHARGE = 49.0            # Change delivery fee
```

### Enable Real Weather
1. Get API key from https://openweathermap.org/api
2. Add to `.env`: `WEATHER_API_KEY=your_key`
3. Uncomment API call in `backend/services/context_service.py`

## 🚧 Roadmap

- [ ] Order placement and checkout flow
- [ ] Price drop alerts
- [ ] Voice shopping interface
- [ ] Image-based recipe recognition
- [ ] 7-day meal planner
- [ ] Loyalty points system
- [ ] Social sharing features
- [ ] Mobile app (React Native)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Groq** - Free LLM API
- **ChromaDB** - Open-source vector database
- **Sentence Transformers** - Embedding models
- **DummyJSON** - Product data source

## 📧 Support

For issues and questions:
- Open a GitHub issue
- Check [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) for troubleshooting
- Read [FEATURE_SUMMARY.md](FEATURE_SUMMARY.md) for feature details

---

**Built with ❤️ for the future of AI-powered commerce**
