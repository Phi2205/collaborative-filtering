# Recommend Server

Hệ thống server cung cấp dịch vụ gợi ý (Recommendation Service) cho ứng dụng Vietour.

## 📋 Mục lục

- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Bắt đầu (Quick Start)](#-bắt-đầu-quick-start)
  - [Bước 1: Thiết lập môi trường Python](#bước-1-thiết-lập-môi-trường-python)
  - [Bước 2: Tạo cấu trúc thư mục dự án](#bước-2-tạo-cấu-trúc-thư-mục-dự-án)
  - [Bước 3: Tạo file cấu hình cơ bản](#bước-3-tạo-file-cấu-hình-cơ-bản)
  - [Bước 4: Tạo ứng dụng FastAPI cơ bản](#bước-4-tạo-ứng-dụng-fastapi-cơ-bản)
  - [Bước 5: Kết nối Database](#bước-5-kết-nối-database)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Sử dụng](#sử-dụng)
- [API Documentation](#api-documentation)
- [Quy trình hoạt động](#quy-trình-hoạt-động)
- [Testing](#testing)
- [Deployment](#deployment)
- [Đóng góp](#đóng-góp)

## 🎯 Giới thiệu

Recommend Server là một dịch vụ backend cung cấp các API để gợi ý nội dung, địa điểm, hoặc sản phẩm cho người dùng dựa trên các thuật toán machine learning và phân tích dữ liệu.

## ✨ Tính năng

- Gợi ý dựa trên hành vi người dùng
- Gợi ý dựa trên nội dung (Content-based)
- Gợi ý dựa trên cộng tác lọc (Collaborative Filtering)
- Xử lý dữ liệu thời gian thực
- API RESTful dễ sử dụng
- Hỗ trợ caching để tối ưu hiệu suất

## 💻 Yêu cầu hệ thống

- Python >= 3.8 (khuyến nghị Python 3.10+)
- Database: PostgreSQL >= 12.x
- Redis (cho caching, tùy chọn)
- RAM: Tối thiểu 2GB
- Disk: Tối thiểu 5GB

### Setup PostgreSQL trên Render

**Tạo PostgreSQL Database trên Render:**

1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → Chọn **"PostgreSQL"**
3. Điền thông tin:
   - **Name**: recommend-db (hoặc tên bạn muốn)
   - **Database**: recommend_db
   - **User**: (Render sẽ tự động tạo)
   - **Region**: Chọn region gần bạn nhất
   - **PostgreSQL Version**: Chọn phiên bản mới nhất
   - **Plan**: Chọn plan phù hợp (Free tier có sẵn)
4. Click **"Create Database"**
5. Sau khi tạo xong, Render sẽ cung cấp:
   - **Internal Database URL**: Dùng khi deploy trên Render
   - **External Database URL**: Dùng khi kết nối từ localhost
   - **Host, Port, Database, User, Password**: Thông tin chi tiết

**Lưu ý:** 
- Render cung cấp cả **Internal Database URL** (cho production) và **External Database URL** (cho development)
- External URL chỉ hoạt động khi bạn whitelist IP của mình trong Render dashboard
- Để kết nối từ localhost, bạn cần enable "Allow connections from outside Render" trong database settings

**Cài đặt PostgreSQL Local (cho development - tùy chọn):**

Nếu muốn chạy PostgreSQL local để development:

**Windows:**
1. Tải PostgreSQL từ: https://www.postgresql.org/download/windows/
2. Chạy installer và làm theo hướng dẫn
3. PostgreSQL sẽ chạy trên port mặc định `5432`

**Linux/MacOS:**
```bash
# Linux
sudo apt install postgresql postgresql-contrib

# MacOS
brew install postgresql
brew services start postgresql
```

## 🎬 Bắt đầu (Quick Start)

### Bước 1: Thiết lập môi trường Python

**1.1. Kiểm tra Python đã cài đặt:**
```bash
python --version
# hoặc
python3 --version
```

**1.2. Tạo virtual environment (môi trường ảo):**
```bash
# Windows
python -m venv venv

# Kích hoạt virtual environment
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**1.3. Cài đặt các thư viện cần thiết:**
```bash
# Cách 1: Sử dụng python -m pip (khuyến nghị trên Windows)
python -m pip install fastapi uvicorn python-dotenv psycopg2-binary sqlalchemy redis pandas numpy scikit-learn

# Cách 2: Sau khi kích hoạt virtual environment, có thể dùng pip trực tiếp
# Windows PowerShell (có thể cần set execution policy)
venv\Scripts\Activate.ps1
pip install fastapi uvicorn python-dotenv pymongo sqlalchemy redis pandas numpy scikit-learn

# Linux/Mac
source venv/bin/activate
pip install fastapi uvicorn python-dotenv pymongo sqlalchemy redis pandas numpy scikit-learn
```

**Lưu ý:** Nếu gặp lỗi "pip is not recognized" trên Windows, hãy sử dụng `python -m pip` thay vì `pip` trực tiếp.

### Bước 2: Tạo cấu trúc thư mục dự án

```bash
# Tạo các thư mục cơ bản
mkdir -p app
mkdir -p app/api
mkdir -p app/models
mkdir -p app/services
mkdir -p app/utils
mkdir -p tests
mkdir -p models
```

**Cấu trúc thư mục đề xuất:**
```
Recommend-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entry point của ứng dụng
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API routes
│   ├── models/
│   │   ├── __init__.py
│   │   └── recommendation.py  # ML models
│   ├── services/
│   │   ├── __init__.py
│   │   └── recommendation_service.py
│   └── utils/
│       ├── __init__.py
│       └── database.py
├── tests/
├── models/                  # Saved ML models
├── .env                     # Environment variables
├── .env.example
├── requirements.txt
├── README.md
└── .gitignore
```

### Bước 3: Tạo file cấu hình cơ bản

**3.1. Tạo file `.env.example`:**
```env
# Server Configuration
PORT=3000
ENVIRONMENT=development

# Database (PostgreSQL trên Render hoặc localhost)
# Cách 1: Sử dụng DATABASE_URL (khuyến nghị cho Render)
DATABASE_URL=postgresql://username:password@host:port/database

# Cách 2: Hoặc sử dụng các biến riêng lẻ
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=recommend_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Redis (Optional - cho caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Keys & Security
# API_KEY: Dùng để xác thực các request từ client (API authentication)
# SECRET_KEY: Dùng để mã hóa JWT tokens, session, hoặc các dữ liệu nhạy cảm
# 
# Cách tạo keys:
# 1. Tạo SECRET_KEY ngẫu nhiên (chạy trong terminal):
#    python -c "import secrets; print(secrets.token_urlsafe(32))"
# 
# 2. Tạo API_KEY ngẫu nhiên:
#    python -c "import secrets; print(secrets.token_urlsafe(24))"
#
# 3. Hoặc sử dụng online tools như: https://randomkeygen.com/
#
# Lưu ý: Trong production, nên sử dụng các keys mạnh và bảo mật
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# ML Model Configuration
MODEL_PATH=./models/recommendation_model

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**3.2. Tạo file `requirements.txt`:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
pydantic==2.5.0
```

**Lưu ý:** 
- `psycopg2-binary`: PostgreSQL adapter cho Python
- Nếu gặp lỗi khi cài `psycopg2-binary`, có thể thử `psycopg2` hoặc cài PostgreSQL development libraries

**3.3. Tạo file `.gitignore`:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Models
models/*.pkl
models/*.h5
*.model

# Logs
*.log
logs/
```

### Bước 4: Tạo ứng dụng FastAPI cơ bản

**4.1. Tạo file `app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Recommend Server",
    description="Recommendation Service API for Vietour",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Recommend Server API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
```

**4.2. Chạy server để kiểm tra:**
```bash
uvicorn app.main:app --reload --port 8000
```

Truy cập: `http://localhost:8000/docs` để xem Swagger UI

### Bước 5: Kết nối Database (PostgreSQL)

**5.1. Tạo file kết nối database `app/utils/database.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Lấy DATABASE_URL từ biến môi trường (Render cung cấp sẵn)
# Nếu không có DATABASE_URL, tạo từ các biến riêng lẻ
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    # Tạo connection string từ các biến riêng lẻ
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Tạo engine với pool_pre_ping để tự động reconnect khi connection bị mất
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Tự động reconnect
    pool_size=10,        # Số lượng connections trong pool
    max_overflow=20      # Số lượng connections tối đa có thể vượt quá pool_size
)

# Tạo session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho models
Base = declarative_base()

# Dependency để lấy database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**5.2. Kiểm tra kết nối:**
```python
# Thêm vào app/main.py
from app.utils.database import engine, Base

# Tạo tables (nếu chưa có)
# Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    try:
        # Kiểm tra kết nối database
        with engine.connect() as conn:
            return {
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
```

Sau khi hoàn thành các bước trên, bạn có thể tiếp tục với:
- Tạo các models và tables
- Tạo các API endpoints
- Implement thuật toán recommendation
- Testing và deployment

## 🚀 Cài đặt

### Clone repository

```bash
git clone <repository-url>
cd Recommend-server
```

### Cài đặt dependencies

```bash
# Kích hoạt virtual environment (nếu chưa kích hoạt)
# Windows
venv\Scripts\activate
# hoặc
venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate

# Cài đặt các thư viện
# Cách 1: Từ file requirements.txt (khuyến nghị)
python -m pip install -r requirements.txt

# Cách 2: Cài đặt trực tiếp (nếu chưa có requirements.txt)
python -m pip install fastapi uvicorn python-dotenv psycopg2-binary sqlalchemy redis pandas numpy scikit-learn

# Sau khi kích hoạt venv, có thể dùng pip trực tiếp
pip install -r requirements.txt
```

**Lưu ý:** Trên Windows, nếu gặp lỗi với `pip`, hãy sử dụng `python -m pip` thay thế.

## ⚙️ Cấu hình

Tạo file `.env` từ template `.env.example`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Cấu hình các biến môi trường trong file `.env`:

**Nếu sử dụng PostgreSQL trên Render:**
```env
# Server Configuration
PORT=3000
ENVIRONMENT=development

# Database (PostgreSQL trên Render)
# Cách 1: Sử dụng External Database URL từ Render (copy từ Render dashboard)
DATABASE_URL=postgresql://username:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/recommend_db

# Cách 2: Hoặc sử dụng các biến riêng lẻ
POSTGRES_HOST=dpg-xxxxx-a.oregon-postgres.render.com
POSTGRES_PORT=5432
POSTGRES_DB=recommend_db
POSTGRES_USER=your_username_from_render
POSTGRES_PASSWORD=your_password_from_render

# Redis (Optional - cho caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Keys & Security
API_KEY=elAg-6TW3PqA_q6mRlHtFCYXuiD0je9P
SECRET_KEY=TQB5mgaGpzAOBGpy3z4nWnoxhVJ5EIgjArVJciV1egQ

# ML Model Configuration
MODEL_PATH=./models/recommendation_model

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Nếu sử dụng PostgreSQL localhost:**
```env
# Server Configuration
PORT=3000
ENVIRONMENT=development

# Database (PostgreSQL localhost)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=recommend_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Redis (Optional - cho caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Keys & Security
API_KEY=elAg-6TW3PqA_q6mRlHtFCYXuiD0je9P
SECRET_KEY=TQB5mgaGpzAOBGpy3z4nWnoxhVJ5EIgjArVJciV1egQ

# ML Model Configuration
MODEL_PATH=./models/recommendation_model

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Lưu ý quan trọng:**
- Khi deploy lên Render, sử dụng **Internal Database URL** từ Render dashboard
- Render tự động cung cấp biến môi trường `DATABASE_URL` khi deploy
- Để kết nối từ localhost đến Render, cần enable "Allow connections from outside Render" và whitelist IP của bạn

**Lưu ý:** Đảm bảo file `.env` đã được thêm vào `.gitignore` để không commit lên repository.

## 📖 Sử dụng

### Chạy server (Cách đơn giản nhất) ⚡

**Windows (Khuyến nghị):**
```bash
# Cách 1: Chạy file batch - Dễ nhất! 🚀
run.bat

# Cách 2: Chạy Python script
python start.py

# Cách 3: Chạy trực tiếp với uvicorn
uvicorn app.main:app --reload --port 3000
```

**Linux/Mac:**
```bash
# Cách 1: Chạy shell script
chmod +x run.sh
./run.sh

# Cách 2: Chạy Python script
python start.py

# Cách 3: Chạy trực tiếp với uvicorn
uvicorn app.main:app --reload --port 3000
```

**Sau khi chạy server, truy cập:**
- 🌐 API: `http://localhost:3000`
- 📖 Swagger UI: `http://localhost:3000/docs`
- 📚 ReDoc: `http://localhost:3000/redoc`
- ❤️ Health Check: `http://localhost:3000/health`

### Chạy với port khác

Nếu muốn chạy trên port khác, sửa file `.env`:
```env
PORT=8000
```

Hoặc chạy trực tiếp:
```bash
uvicorn app.main:app --reload --port 8000
```

### Chạy production server

```bash
# Sử dụng gunicorn với uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3000

# Hoặc chỉ dùng uvicorn (không khuyến nghị cho production)
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Swagger UI
Truy cập Swagger UI để xem và test API: `http://localhost:8000/docs`

### ReDoc
Truy cập ReDoc để xem tài liệu API: `http://localhost:8000/redoc`

### Endpoints

#### 1. Lấy gợi ý cho người dùng
```http
GET /recommendations/:userId
```

**Parameters:**
- `userId` (path): ID của người dùng
- `limit` (query, optional): Số lượng gợi ý (mặc định: 10)
- `type` (query, optional): Loại gợi ý (content-based, collaborative, hybrid)

**Response:**
```json
{
  "success": true,
  "data": {
    "userId": "user123",
    "recommendations": [
      {
        "itemId": "item1",
        "score": 0.95,
        "reason": "Dựa trên lịch sử xem của bạn"
      }
    ],
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### 2. Cập nhật hành vi người dùng
```http
POST /users/:userId/behavior
```

**Request Body:**
```json
{
  "action": "view",
  "itemId": "item123",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 3. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

## 🔄 Quy trình hoạt động

### 1. Thu thập dữ liệu
- Hệ thống thu thập hành vi người dùng (views, clicks, purchases, ratings)
- Lưu trữ vào database để phân tích

### 2. Xử lý và phân tích
- Xử lý dữ liệu thô thành features có ý nghĩa
- Áp dụng các thuật toán ML để tạo model
- Tính toán similarity scores giữa users và items

### 3. Tạo gợi ý
- Dựa trên model đã train, tạo danh sách gợi ý
- Kết hợp nhiều nguồn gợi ý (content-based + collaborative)
- Ranking và filtering kết quả

### 4. Cache và tối ưu
- Cache kết quả gợi ý để tăng tốc độ phản hồi
- Cập nhật cache định kỳ hoặc khi có dữ liệu mới

### 5. API Response
- Trả về kết quả gợi ý cho client
- Logging và monitoring để theo dõi hiệu suất

## 🎯 Hướng dẫn Implement Collaborative Filtering

### Collaborative Filtering là gì?

Collaborative Filtering là thuật toán gợi ý dựa trên hành vi của người dùng tương tự. Có 2 loại chính:

1. **User-Based CF**: Tìm users tương tự → Gợi ý items mà họ đã thích
2. **Item-Based CF**: Tìm items tương tự → Gợi ý items dựa trên items user đã tương tác

### Các bước implement Collaborative Filtering

#### Bước 1: Tạo Database Schema

Tạo các bảng để lưu trữ dữ liệu:

**File: `app/models/schema.py`**
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interactions = relationship("UserItemInteraction", back_populates="user")

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interactions = relationship("UserItemInteraction", back_populates="item")

class UserItemInteraction(Base):
    __tablename__ = "user_item_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    rating = Column(Float)  # 1.0 - 5.0
    interaction_type = Column(String)  # 'view', 'click', 'purchase', 'rating'
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    item = relationship("Item", back_populates="interactions")
```

#### Bước 2: Tạo Service cho Collaborative Filtering

**File: `app/services/collaborative_filtering.py`**
```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from app.models.schema import UserItemInteraction, User, Item

class CollaborativeFiltering:
    def __init__(self, db: Session):
        self.db = db
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None
    
    def build_user_item_matrix(self) -> np.ndarray:
        """
        Xây dựng ma trận User-Item từ database
        Rows: Users, Columns: Items, Values: Ratings
        """
        # Lấy tất cả interactions
        interactions = self.db.query(UserItemInteraction).all()
        
        # Lấy danh sách unique users và items
        users = self.db.query(User).all()
        items = self.db.query(Item).all()
        
        user_ids = [u.id for u in users]
        item_ids = [i.id for i in items]
        
        # Tạo ma trận
        matrix = np.zeros((len(user_ids), len(item_ids)))
        user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        item_id_to_idx = {iid: idx for idx, iid in enumerate(item_ids)}
        
        # Điền dữ liệu vào ma trận
        for interaction in interactions:
            if interaction.user_id in user_id_to_idx and interaction.item_id in item_id_to_idx:
                user_idx = user_id_to_idx[interaction.user_id]
                item_idx = item_id_to_idx[interaction.item_id]
                
                # Sử dụng rating nếu có, nếu không dùng điểm mặc định
                if interaction.rating:
                    matrix[user_idx, item_idx] = interaction.rating
                else:
                    # Gán điểm dựa trên interaction type
                    scores = {'view': 1.0, 'click': 2.0, 'purchase': 4.0, 'rating': interaction.rating or 3.0}
                    matrix[user_idx, item_idx] = scores.get(interaction.interaction_type, 1.0)
        
        self.user_item_matrix = matrix
        self.user_ids = user_ids
        self.item_ids = item_ids
        self.user_id_to_idx = user_id_to_idx
        self.item_id_to_idx = item_id_to_idx
        
        return matrix
    
    def calculate_user_similarity(self) -> np.ndarray:
        """
        Tính toán độ tương đồng giữa các users (User-Based CF)
        Sử dụng Cosine Similarity
        """
        if self.user_item_matrix is None:
            self.build_user_item_matrix()
        
        # Tính cosine similarity giữa các users
        self.user_similarity = cosine_similarity(self.user_item_matrix)
        return self.user_similarity
    
    def calculate_item_similarity(self) -> np.ndarray:
        """
        Tính toán độ tương đồng giữa các items (Item-Based CF)
        Sử dụng Cosine Similarity
        """
        if self.user_item_matrix is None:
            self.build_user_item_matrix()
        
        # Tính cosine similarity giữa các items (transpose matrix)
        self.item_similarity = cosine_similarity(self.user_item_matrix.T)
        return self.item_similarity
    
    def user_based_recommendations(
        self, 
        user_id: int, 
        n_recommendations: int = 10,
        n_similar_users: int = 5
    ) -> List[Dict]:
        """
        User-Based Collaborative Filtering
        Tìm users tương tự → Gợi ý items mà họ đã thích
        """
        if self.user_similarity is None:
            self.calculate_user_similarity()
        
        if user_id not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id]
        
        # Lấy top N users tương tự (loại bỏ chính user đó)
        similar_users_idx = np.argsort(self.user_similarity[user_idx])[::-1][1:n_similar_users+1]
        
        # Tính điểm dự đoán cho từng item
        user_ratings = self.user_item_matrix[user_idx]
        predicted_scores = np.zeros(len(self.item_ids))
        
        for item_idx in range(len(self.item_ids)):
            if user_ratings[item_idx] == 0:  # Chỉ gợi ý items user chưa tương tác
                # Tính điểm dự đoán dựa trên users tương tự
                similar_users_ratings = self.user_item_matrix[similar_users_idx, item_idx]
                similar_users_sim = self.user_similarity[user_idx, similar_users_idx]
                
                # Weighted average
                if np.sum(similar_users_sim) > 0:
                    predicted_scores[item_idx] = np.sum(
                        similar_users_ratings * similar_users_sim
                    ) / np.sum(similar_users_sim)
        
        # Lấy top N recommendations
        top_items_idx = np.argsort(predicted_scores)[::-1][:n_recommendations]
        
        recommendations = []
        for item_idx in top_items_idx:
            if predicted_scores[item_idx] > 0:
                item = self.db.query(Item).filter(Item.id == self.item_ids[item_idx]).first()
                if item:
                    recommendations.append({
                        "item_id": item.id,
                        "item_name": item.name,
                        "predicted_score": float(predicted_scores[item_idx]),
                        "method": "user_based_cf"
                    })
        
        return recommendations
    
    def item_based_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10
    ) -> List[Dict]:
        """
        Item-Based Collaborative Filtering
        Tìm items tương tự với items user đã tương tác
        """
        if self.item_similarity is None:
            self.calculate_item_similarity()
        
        if user_id not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id]
        user_ratings = self.user_item_matrix[user_idx]
        
        # Tính điểm dự đoán cho từng item
        predicted_scores = np.zeros(len(self.item_ids))
        
        for item_idx in range(len(self.item_ids)):
            if user_ratings[item_idx] == 0:  # Chỉ gợi ý items user chưa tương tác
                # Tính điểm dựa trên items user đã tương tác
                interacted_items_idx = np.where(user_ratings > 0)[0]
                
                if len(interacted_items_idx) > 0:
                    similarities = self.item_similarity[item_idx, interacted_items_idx]
                    ratings = user_ratings[interacted_items_idx]
                    
                    if np.sum(similarities) > 0:
                        predicted_scores[item_idx] = np.sum(
                            similarities * ratings
                        ) / np.sum(similarities)
        
        # Lấy top N recommendations
        top_items_idx = np.argsort(predicted_scores)[::-1][:n_recommendations]
        
        recommendations = []
        for item_idx in top_items_idx:
            if predicted_scores[item_idx] > 0:
                item = self.db.query(Item).filter(Item.id == self.item_ids[item_idx]).first()
                if item:
                    recommendations.append({
                        "item_id": item.id,
                        "item_name": item.name,
                        "predicted_score": float(predicted_scores[item_idx]),
                        "method": "item_based_cf"
                    })
        
        return recommendations
    
    def hybrid_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        user_weight: float = 0.5
    ) -> List[Dict]:
        """
        Kết hợp User-Based và Item-Based CF
        """
        user_based = self.user_based_recommendations(user_id, n_recommendations * 2)
        item_based = self.item_based_recommendations(user_id, n_recommendations * 2)
        
        # Tạo dictionary để combine scores
        combined_scores = {}
        
        for rec in user_based:
            item_id = rec["item_id"]
            combined_scores[item_id] = {
                "item_id": item_id,
                "item_name": rec["item_name"],
                "user_score": rec["predicted_score"],
                "item_score": 0.0
            }
        
        for rec in item_based:
            item_id = rec["item_id"]
            if item_id in combined_scores:
                combined_scores[item_id]["item_score"] = rec["predicted_score"]
            else:
                combined_scores[item_id] = {
                "item_id": item_id,
                "item_name": rec["item_name"],
                "user_score": 0.0,
                "item_score": rec["predicted_score"]
            }
        
        # Tính điểm tổng hợp
        recommendations = []
        for item_id, data in combined_scores.items():
            final_score = (
                user_weight * data["user_score"] + 
                (1 - user_weight) * data["item_score"]
            )
            recommendations.append({
                "item_id": data["item_id"],
                "item_name": data["item_name"],
                "predicted_score": final_score,
                "method": "hybrid_cf"
            })
        
        # Sắp xếp và lấy top N
        recommendations.sort(key=lambda x: x["predicted_score"], reverse=True)
        return recommendations[:n_recommendations]
```

#### Bước 3: Tạo API Endpoints

**File: `app/api/recommendations.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.utils.database import get_db
from app.services.collaborative_filtering import CollaborativeFiltering

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/collaborative/{user_id}")
async def get_collaborative_recommendations(
    user_id: int,
    method: str = Query("hybrid", regex="^(user_based|item_based|hybrid)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Lấy gợi ý dựa trên Collaborative Filtering
    
    - **user_id**: ID của người dùng
    - **method**: Phương pháp CF (user_based, item_based, hybrid)
    - **limit**: Số lượng gợi ý (1-50)
    """
    cf = CollaborativeFiltering(db)
    
    try:
        if method == "user_based":
            recommendations = cf.user_based_recommendations(user_id, limit)
        elif method == "item_based":
            recommendations = cf.item_based_recommendations(user_id, limit)
        else:  # hybrid
            recommendations = cf.hybrid_recommendations(user_id, limit)
        
        return {
            "success": True,
            "user_id": user_id,
            "method": method,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Bước 4: Đăng ký Router trong main.py

**Cập nhật `app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api import recommendations
import os

load_dotenv()

app = FastAPI(
    title="Recommend Server",
    description="Recommendation Service API for Vietour",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendations.router)

@app.get("/")
async def root():
    return {"message": "Recommend Server API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }
```

#### Bước 5: Tạo Database Tables

**File: `app/utils/init_db.py`**
```python
from app.utils.database import engine, Base
from app.models.schema import User, Item, UserItemInteraction

def init_db():
    """Tạo tất cả các tables trong database"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
```

### Tóm tắt các bước:

1. ✅ **Tạo Database Schema** - Định nghĩa tables (users, items, interactions)
2. ✅ **Implement Collaborative Filtering Service** - Logic tính toán similarity và recommendations
3. ✅ **Tạo API Endpoints** - Expose API để lấy recommendations
4. ✅ **Đăng ký Router** - Kết nối API với FastAPI app
5. ✅ **Khởi tạo Database** - Tạo tables trong database

### Cách sử dụng:

```bash
# 1. Tạo database tables
python -m app.utils.init_db

# 2. Chạy server
python start.py

# 3. Test API
# GET http://localhost:3000/recommendations/collaborative/1?method=hybrid&limit=10
```

## 🧪 Testing

### Cài đặt testing dependencies
```bash
# Windows (khuyến nghị)
python -m pip install pytest pytest-asyncio pytest-cov httpx

# Sau khi kích hoạt virtual environment, có thể dùng pip trực tiếp
pip install pytest pytest-asyncio pytest-cov httpx
```

### Chạy unit tests
```bash
# Windows (khuyến nghị - đảm bảo virtual environment đã được kích hoạt)
python -m pytest
# hoặc chạy với verbose
python -m pytest -v

# Sau khi kích hoạt virtual environment, có thể dùng pytest trực tiếp
pytest
pytest -v
```

### Chạy integration tests
```bash
# Windows
python -m pytest tests/integration

# Hoặc sau khi kích hoạt venv
pytest tests/integration
```

### Chạy với coverage
```bash
# Windows
python -m pytest --cov=app --cov-report=html

# Hoặc sau khi kích hoạt venv
pytest --cov=app --cov-report=html

# Xem báo cáo coverage tại: htmlcov/index.html
```

**Lưu ý:** 
- Trên Windows, nếu gặp lỗi "pytest is not recognized", hãy:
  1. Kích hoạt virtual environment: `venv\Scripts\Activate.ps1`
  2. Hoặc sử dụng `python -m pytest` thay vì `pytest` trực tiếp

## 🚢 Deployment (Tùy chọn - Chỉ khi cần)

> **Lưu ý:** Phần này là **TÙY CHỌN**. Nếu bạn đang trong giai đoạn development, có thể **BỎ QUA** phần này và quay lại sau khi code đã hoàn thiện.

### Tại sao cần deploy lên Render?

**Khi chạy trên localhost:**
- ❌ Chỉ bạn mới truy cập được: `http://localhost:3000`
- ❌ Không thể chia sẻ với người khác
- ❌ Phải mở máy tính 24/7 để server chạy
- ❌ Không có domain/URL công khai

**Khi deploy lên Render:**
- ✅ Có URL công khai: `https://your-app.onrender.com`
- ✅ Ai cũng có thể truy cập từ internet
- ✅ Server chạy 24/7 trên cloud (không cần mở máy tính)
- ✅ Tự động deploy khi push code lên GitHub
- ✅ Có SSL/HTTPS miễn phí
- ✅ Dễ dàng scale khi cần

**Khi nào cần deploy:**
- Khi muốn chia sẻ API cho frontend/mobile app
- Khi muốn test từ thiết bị khác
- Khi muốn đưa vào production
- Khi muốn có server chạy 24/7

### Deploy lên Render

**Bước 1: Chuẩn bị repository**
1. Push code lên GitHub/GitLab/Bitbucket
2. Đảm bảo có file `requirements.txt` và `app/main.py`

**Bước 2: Tạo Web Service trên Render**
1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → Chọn **"Web Service"**
3. Kết nối repository của bạn
4. Điền thông tin:
   - **Name**: recommend-server (hoặc tên bạn muốn)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Chọn plan phù hợp

**Bước 3: Cấu hình Environment Variables**
Trong Render dashboard, thêm các biến môi trường:
- `DATABASE_URL`: Render tự động cung cấp nếu bạn đã link PostgreSQL database
- `API_KEY`: Copy từ file `.env` local
- `SECRET_KEY`: Copy từ file `.env` local
- `ENVIRONMENT`: `production`
- Các biến khác nếu cần

**Bước 4: Link PostgreSQL Database**
1. Trong Web Service settings, tìm phần **"Connections"**
2. Click **"Link Resource"** → Chọn PostgreSQL database đã tạo
3. Render sẽ tự động thêm `DATABASE_URL` vào environment variables

**Bước 5: Deploy**
1. Click **"Create Web Service"**
2. Render sẽ tự động build và deploy
3. Sau khi deploy xong, bạn sẽ có URL: `https://your-app-name.onrender.com`

**Lưu ý:**
- Render sẽ tự động detect Python và cài đặt dependencies từ `requirements.txt`
- Free tier có thể bị sleep sau 15 phút không có traffic
- Để tránh sleep, có thể setup health check endpoint hoặc upgrade plan

### Docker

**Tạo file `Dockerfile`:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build và chạy:**
```bash
# Build image
docker build -t recommend-server .

# Run container
docker run -p 8000:8000 --env-file .env recommend-server
```

### Docker Compose

```bash
docker-compose up -d
```

### Production Checklist

- [ ] Cấu hình environment variables
- [ ] Setup database connection
- [ ] Enable logging và monitoring
- [ ] Setup reverse proxy (Nginx)
- [ ] Configure SSL/TLS
- [ ] Setup backup strategy
- [ ] Configure auto-scaling (nếu cần)

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📝 License

[Specify your license here]

## 👥 Authors

- [Your Name] - [Your Email]

## 🙏 Acknowledgments

- Cảm ơn tất cả contributors đã đóng góp cho project này

---

**Lưu ý:** README này là template. Vui lòng cập nhật với thông tin cụ thể về quy trình và kiến trúc của dự án của bạn.


#   c o l l a b o r a t i v e - f i l t e r i n g 
 
 