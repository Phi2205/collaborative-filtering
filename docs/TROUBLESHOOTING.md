# Troubleshooting Guide

Hướng dẫn xử lý các lỗi thường gặp khi sử dụng Recommend Server.

## 🔴 Lỗi Database Connection

### Lỗi: "password authentication failed"

**Nguyên nhân:**
- Password trong `.env` không có hoặc không đúng
- Username không đúng
- Database credentials đã thay đổi

**Giải pháp:**

1. **Lấy password từ Render Dashboard:**
   - Vào [Render Dashboard](https://dashboard.render.com/)
   - Click vào PostgreSQL database của bạn
   - Tìm phần **"Connections"** hoặc **"Info"**
   - Copy **External Database URL** (có dạng: `postgresql://user:password@host:port/db`)
   - Hoặc copy **Password** riêng lẻ

2. **Cập nhật file `.env`:**
   
   **Cách 1: Sử dụng External Database URL (Khuyến nghị - Dễ nhất)**
   ```env
   # Copy toàn bộ External Database URL từ Render và thêm ?sslmode=require
   DATABASE_URL=postgresql://phiduong:YOUR_PASSWORD_HERE@dpg-d52osah5pdvs73el15tg-a.singapore-postgres.render.com:5432/vietour_iumb?sslmode=require
   ```
   
   **Cách 2: Sử dụng các biến riêng lẻ**
   ```env
   POSTGRES_HOST=dpg-d52osah5pdvs73el15tg-a.singapore-postgres.render.com
   POSTGRES_PORT=5432
   POSTGRES_DB=vietour_iumb
   POSTGRES_USER=phiduong
   POSTGRES_PASSWORD=YOUR_PASSWORD_HERE  # ⚠️ QUAN TRỌNG: Thêm password vào đây
   ```

3. **Lưu ý về Password:**
   - Password có thể chứa ký tự đặc biệt
   - Nếu password có `@`, `#`, `%`, cần URL encode trong DATABASE_URL:
     - `@` → `%40`
     - `#` → `%23`
     - `%` → `%25`
   - Nếu dùng các biến riêng lẻ, không cần encode

4. **Test lại kết nối:**
   ```bash
   python scripts/test_connection.py
   ```

3. **Lưu ý:**
   - Password có thể chứa ký tự đặc biệt, cần URL encode
   - Nếu password có `@`, `#`, `%`, cần encode:
     - `@` → `%40`
     - `#` → `%23`
     - `%` → `%25`

---

### Lỗi: "SSL/TLS required"

**Nguyên nhân:**
- Render yêu cầu SSL connection nhưng connection string chưa có SSL mode

**Giải pháp:**

1. **Thêm `?sslmode=require` vào DATABASE_URL:**
   ```env
   DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require
   ```

2. **Hoặc file `app/utils/database.py` đã tự động thêm SSL mode** (đã được cập nhật)

3. **Test kết nối:**
   ```python
   from app.utils.database import engine
   try:
       with engine.connect() as conn:
           print("✅ Kết nối database thành công!")
   except Exception as e:
       print(f"❌ Lỗi: {e}")
   ```

---

### Lỗi: "connection to server failed"

**Nguyên nhân:**
- Database trên Render chưa enable "Allow connections from outside Render"
- IP của bạn chưa được whitelist

**Giải pháp:**

1. **Enable External Connections:**
   - Vào Render Dashboard → PostgreSQL database
   - Tìm phần **"Connections"**
   - Enable **"Allow connections from outside Render"**

2. **Whitelist IP (nếu cần):**
   - Tìm phần **"IP Whitelist"**
   - Thêm IP của bạn (hoặc để trống để cho phép tất cả)

3. **Kiểm tra Firewall:**
   - Đảm bảo firewall không chặn port 5432

---

## 🔴 Lỗi Python/Pip

### Lỗi: "pip is not recognized"

**Giải pháp:**
```bash
# Sử dụng python -m pip thay vì pip trực tiếp
python -m pip install -r requirements.txt
```

---

### Lỗi: "pytest is not recognized"

**Giải pháp:**
```bash
# Kích hoạt virtual environment trước
venv\Scripts\Activate.ps1  # Windows

# Hoặc dùng
python -m pytest
```

---

## 🔴 Lỗi API

### Lỗi: "User với ID X không tồn tại"

**Nguyên nhân:**
- User ID không tồn tại trong bảng `user_profile`
- Đang dùng `account_id` thay vì `id` từ `user_profile`

**Giải pháp:**

1. **Kiểm tra user tồn tại:**
   ```sql
   SELECT id, first_name, last_name FROM user_profile WHERE id = 1;
   ```

2. **Lưu ý:**
   - Dùng `id` từ bảng `user_profile`
   - Không dùng `account_id`

---

### Lỗi: "Tour với ID X không tồn tại"

**Nguyên nhân:**
- Tour ID không tồn tại
- Tour chưa được approve hoặc đã bị banned

**Giải pháp:**

1. **Kiểm tra tour:**
   ```sql
   SELECT id, title, is_active, is_approved, is_banned 
   FROM tour 
   WHERE id = 1;
   ```

2. **Đảm bảo:**
   - `is_active = true`
   - `is_approved = true`
   - `is_banned = false`

---

### Recommendations trả về rỗng

**Nguyên nhân:**
- User chưa có interactions
- Không có users tương tự
- Không có tours tương tự

**Giải pháp:**

1. **Tạo interactions cho user:**
   ```bash
   POST /interactions/
   {
     "user_id": 1,
     "tour_id": 1,
     "interaction_type": "view"
   }
   ```

2. **Tạo dữ liệu mẫu:**
   ```bash
   python scripts/create_sample_data.py
   ```

3. **Kiểm tra dữ liệu:**
   ```sql
   -- Xem số lượng interactions
   SELECT COUNT(*) FROM user_tour_interaction;
   
   -- Xem interactions của user
   SELECT * FROM user_tour_interaction WHERE user_id = 1;
   ```

---

## 🔴 Lỗi Database Tables

### Lỗi: "Table user_tour_interaction does not exist"

**Giải pháp:**
```bash
python -m app.utils.init_db
```

---

### Lỗi: "Table user_profile does not exist"

**Nguyên nhân:**
- Bảng `user_profile` chưa được tạo trong database
- Tên database trong `.env` không đúng

**Giải pháp:**

1. **Kiểm tra database name trong `.env`**
2. **Kiểm tra bảng tồn tại:**
   ```sql
   \dt  -- PostgreSQL
   -- hoặc
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

---

## 🔴 Lỗi Server

### Lỗi: "Address already in use"

**Nguyên nhân:**
- Port 3000 đã được sử dụng

**Giải pháp:**

1. **Đổi port trong `.env`:**
   ```env
   PORT=3001
   ```

2. **Hoặc kill process đang dùng port:**
   ```bash
   # Windows
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F
   
   # Linux/Mac
   lsof -ti:3000 | xargs kill
   ```

---

## 📝 Checklist Debug

Khi gặp lỗi, kiểm tra theo thứ tự:

- [ ] Virtual environment đã được kích hoạt chưa?
- [ ] Dependencies đã cài đặt đầy đủ chưa?
- [ ] File `.env` đã tạo và cấu hình đúng chưa?
- [ ] Database connection thành công chưa?
- [ ] Bảng `user_tour_interaction` đã tạo chưa?
- [ ] User ID và Tour ID tồn tại trong database chưa?
- [ ] Server đã chạy thành công chưa?

---

## 🆘 Vẫn không giải quyết được?

1. **Kiểm tra logs:**
   - Xem error message chi tiết
   - Check terminal output

2. **Test từng phần:**
   ```python
   # Test database connection
   from app.utils.database import engine
   with engine.connect() as conn:
       print("✅ Database OK")
   
   # Test models
   from app.models.schema import UserProfile, Tour
   print("✅ Models OK")
   ```

3. **Kiểm tra version:**
   ```bash
   python --version
   pip list | grep -i sqlalchemy
   pip list | grep -i psycopg
   ```

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15

