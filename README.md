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
- Database: MongoDB / PostgreSQL / MySQL
- Redis (cho caching, tùy chọn)
- RAM: Tối thiểu 2GB
- Disk: Tối thiểu 5GB

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
python -m pip install fastapi uvicorn python-dotenv pymongo sqlalchemy redis pandas numpy scikit-learn

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
PORT=8000
NODE_ENV=development

# Database
DB_HOST=localhost
DB_PORT=27017
DB_NAME=recommend_db
DB_USER=your_username
DB_PASSWORD=your_password

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Keys
API_KEY=your_api_key
SECRET_KEY=your_secret_key

# ML Model Configuration
MODEL_PATH=./models/recommendation_model
```

**3.2. Tạo file `requirements.txt`:**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
pymongo==4.6.0
sqlalchemy==2.0.23
redis==5.0.1
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
pydantic==2.5.0
```

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

### Bước 5: Kết nối Database

Sau khi hoàn thành các bước trên, bạn có thể tiếp tục với:
- Kết nối database (MongoDB/PostgreSQL)
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
python -m pip install fastapi uvicorn python-dotenv pymongo sqlalchemy redis pandas numpy scikit-learn

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

```env
# Server Configuration
PORT=8000
ENVIRONMENT=development

# Database (MongoDB)
DB_HOST=localhost
DB_PORT=27017
DB_NAME=recommend_db
DB_USER=your_username
DB_PASSWORD=your_password

# Database (PostgreSQL - nếu sử dụng)
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=recommend_db
# POSTGRES_USER=your_username
# POSTGRES_PASSWORD=your_password

# Redis (Optional - cho caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# API Keys
API_KEY=your_api_key
SECRET_KEY=your_secret_key

# ML Model Configuration
MODEL_PATH=./models/recommendation_model

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

**Lưu ý:** Đảm bảo file `.env` đã được thêm vào `.gitignore` để không commit lên repository.

## 📖 Sử dụng

### Chạy development server

```bash
# Đảm bảo virtual environment đã được kích hoạt
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Chạy với uvicorn (auto-reload)
uvicorn app.main:app --reload --port 8000

# Hoặc chạy với Python
python -m uvicorn app.main:app --reload --port 8000
```

Sau khi chạy, truy cập:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Chạy production server

```bash
# Sử dụng gunicorn với uvicorn workers
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Hoặc chỉ dùng uvicorn (không khuyến nghị cho production)
uvicorn app.main:app --host 0.0.0.0 --port 8000
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

## 🧪 Testing

### Cài đặt testing dependencies
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

### Chạy unit tests
```bash
pytest
# hoặc chạy với verbose
pytest -v
```

### Chạy integration tests
```bash
pytest tests/integration
```

### Chạy với coverage
```bash
pytest --cov=app --cov-report=html
# Xem báo cáo coverage tại: htmlcov/index.html
```

## 🚢 Deployment

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


#   c o l l a b o r a t i v e - f i l t e r i n g  
 