# Setup Guide - Recommend Server

Hướng dẫn chi tiết để setup và chạy Recommend Server cho hệ thống đặt tour Vietour.

## 📋 Mục lục

- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình Database](#cấu-hình-database)
- [Tạo Database Tables](#tạo-database-tables)
- [Chạy Server](#chạy-server)
- [Test hệ thống](#test-hệ-thống)
- [Troubleshooting](#troubleshooting)

## 💻 Yêu cầu hệ thống

- Python >= 3.8 (khuyến nghị Python 3.10+)
- PostgreSQL >= 12.x (đã có trên Render)
- RAM: Tối thiểu 2GB
- Disk: Tối thiểu 5GB

## 🚀 Cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd Recommend-server
```

### Bước 2: Tạo Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt Dependencies

```bash
# Windows (khuyến nghị)
python -m pip install -r requirements.txt

# Sau khi kích hoạt venv
pip install -r requirements.txt
```

## ⚙️ Cấu hình Database

### Tạo file `.env`

Copy từ `.env.example` và điền thông tin:

```env
# Server Configuration
PORT=3000
ENVIRONMENT=development

# Database (PostgreSQL trên Render)
DATABASE_URL=postgresql://username:password@host:port/database

# Hoặc sử dụng các biến riêng lẻ
POSTGRES_HOST=your_postgres_host
POSTGRES_PORT=5432
POSTGRES_DB=recommend_db
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# API Keys
API_KEY=elAg-6TW3PqA_q6mRlHtFCYXuiD0je9P
SECRET_KEY=TQB5mgaGpzAOBGpy3z4nWnoxhVJ5EIgjArVJciV1egQ
```

### Lấy thông tin Database từ Render

1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com/)
2. Vào PostgreSQL database của bạn
3. Copy **External Database URL** hoặc các thông tin:
   - Host
   - Port
   - Database name
   - Username
   - Password

**Lưu ý:** 
- Để kết nối từ localhost, cần enable "Allow connections from outside Render"
- Whitelist IP của bạn trong Render dashboard

## 🗄️ Tạo Database Tables

### Bước 1: Kiểm tra bảng hiện có

Bạn đã có các bảng:
- ✅ `user_profile` - Thông tin user
- ✅ `tour` - Thông tin tour

### Bước 2: Tạo bảng `user_tour_interaction`

```bash
python -m app.utils.init_db
```

Lệnh này sẽ tạo bảng `user_tour_interaction` để lưu các interactions.

**Lưu ý:** 
- Bảng `user_profile` và `tour` đã tồn tại, sẽ không bị tạo lại
- Chỉ tạo bảng `user_tour_interaction` nếu chưa có

## 🏃 Chạy Server

### Cách 1: Sử dụng script (Khuyến nghị)

```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh
./run.sh
```

### Cách 2: Sử dụng Python script

```bash
python start.py
```

### Cách 3: Chạy trực tiếp với uvicorn

```bash
uvicorn app.main:app --reload --port 3000
```

### Kiểm tra server đã chạy

Truy cập:
- 🌐 API: `http://localhost:3000`
- 📖 Swagger UI: `http://localhost:3000/docs`
- ❤️ Health Check: `http://localhost:3000/health`

## 🧪 Test hệ thống

### Bước 1: Tạo dữ liệu mẫu (Tùy chọn)

```bash
python scripts/create_sample_data.py
```

Script này sẽ tạo các interactions mẫu để test.

**Lưu ý:** 
- Cần có ít nhất 1 user trong bảng `user_profile`
- Cần có ít nhất 1 tour trong bảng `tour` (is_active=true, is_approved=true)

### Bước 2: Test API qua Swagger UI

1. Truy cập: `http://localhost:3000/docs`
2. Test endpoint `POST /interactions/`:
   ```json
   {
     "user_id": 1,
     "tour_id": 1,
     "interaction_type": "view"
   }
   ```
3. Test endpoint `GET /recommendations/collaborative/1`

### Bước 3: Test với cURL

```bash
# Tạo interaction
curl -X POST "http://localhost:3000/interactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "tour_id": 1,
    "interaction_type": "view"
  }'

# Lấy recommendations
curl "http://localhost:3000/recommendations/collaborative/1?method=hybrid&limit=10"
```

## 🔧 Troubleshooting

### Lỗi: "pip is not recognized"

**Giải pháp:**
```bash
python -m pip install -r requirements.txt
```

### Lỗi: "pytest is not recognized"

**Giải pháp:**
```bash
# Kích hoạt venv trước
venv\Scripts\Activate.ps1

# Hoặc dùng
python -m pytest
```

### Lỗi: "Database connection failed"

**Kiểm tra:**
1. File `.env` đã có đúng thông tin database chưa?
2. Database trên Render đã enable "Allow connections from outside Render" chưa?
3. IP của bạn đã được whitelist chưa?
4. Thử ping database host

**Test kết nối:**
```python
from app.utils.database import engine
with engine.connect() as conn:
    print("✅ Kết nối database thành công!")
```

### Lỗi: "Table user_profile does not exist"

**Giải pháp:**
- Bảng `user_profile` phải tồn tại trong database
- Kiểm tra tên database trong `.env` có đúng không

### Lỗi: "User với ID X không tồn tại"

**Giải pháp:**
- Kiểm tra user_id có tồn tại trong bảng `user_profile` không
- Lưu ý: Dùng `id` từ `user_profile`, không phải `account_id`

### Lỗi: "Tour với ID X không tồn tại"

**Giải pháp:**
- Kiểm tra tour_id có tồn tại trong bảng `tour` không
- Kiểm tra tour có `is_active=true`, `is_approved=true`, `is_banned=false` không

### Recommendations trả về rỗng

**Nguyên nhân:**
- User chưa có interactions
- Không có users tương tự
- Không có tours tương tự

**Giải pháp:**
1. Tạo thêm interactions cho user
2. Tạo dữ liệu mẫu: `python scripts/create_sample_data.py`
3. Đảm bảo có đủ dữ liệu (ít nhất 5-10 users và tours)

## 📊 Kiểm tra Database

### Xem số lượng interactions

```sql
SELECT COUNT(*) FROM user_tour_interaction;
```

### Xem interactions của user

```sql
SELECT * FROM user_tour_interaction 
WHERE user_id = 1 
ORDER BY timestamp DESC;
```

### Xem interactions của tour

```sql
SELECT * FROM user_tour_interaction 
WHERE tour_id = 1 
ORDER BY timestamp DESC;
```

## ✅ Checklist Setup

- [ ] Python đã cài đặt
- [ ] Virtual environment đã tạo và kích hoạt
- [ ] Dependencies đã cài đặt (`pip install -r requirements.txt`)
- [ ] File `.env` đã tạo và cấu hình đúng
- [ ] Database connection thành công
- [ ] Bảng `user_tour_interaction` đã tạo
- [ ] Server chạy thành công (`python start.py`)
- [ ] Swagger UI truy cập được (`http://localhost:3000/docs`)
- [ ] Test API thành công

## 🎯 Next Steps

Sau khi setup xong:

1. ✅ Tạo interactions cho users
2. ✅ Test API recommendations
3. ✅ Tích hợp vào frontend
4. ✅ Monitor và optimize performance

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15

