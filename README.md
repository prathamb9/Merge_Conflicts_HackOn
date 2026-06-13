# 🛒 QuickCommerce AI - Intelligent Shopping Assistant

> A fully local, AI-powered quick commerce platform with advanced features like semantic search, stock substitution, cart optimization, and contextual recommendations.

## 🌟 Key Features

- **🤖 AI-Powered Chat** - Natural language shopping with Groq's llama-3.3-70b
- **🎙️ Voice Search** - Hands-free shopping using voice recognition
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
python -m uvicorn main:app --reload --port 8000

# 6. Frontend Setup (new terminal)
cd frontend
npm install
npm run dev
```

### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

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
Natural language chat interface powered by Groq's llama-3.3-70b model.

### 2. Voice Search
Shop hands-free with built-in voice recognition and conversational AI.

### 3. Smart Substitution Engine
Automatically finds alternatives when products are unavailable.

### 3. Cart Value Optimizer
Helps users reach free delivery thresholds.

### 4. Contextual Recommendations
Adapts to real-world conditions like weather, time, and events.

### 5. Recipe-to-Cart
Parse recipes into shoppable ingredients.

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

## 🧪 Testing

### Test Chat Functionality
```bash
# Start servers
cd backend && python -m uvicorn main:app --reload --port 8000
cd frontend && npm run dev
```

### Test Backend API
```bash
# Health check
curl http://localhost:8000/health

# Get products
curl http://localhost:8000/api/products?limit=5
```

## 🚧 Roadmap

- [ ] Order placement and checkout flow
- [ ] Price drop alerts
- [ ] Image-based recipe recognition
- [ ] 7-day meal planner
- [ ] Loyalty points system
- [ ] Social sharing features
- [ ] Mobile app (React Native)

---

**Built with ❤️ by team Merge_Conflicts**