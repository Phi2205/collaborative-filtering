# Quick Fix - Password Authentication Failed

## ⚠️ Lỗi: "password authentication failed for user phiduong"

### Nguyên nhân
File `.env` thiếu `POSTGRES_PASSWORD` hoặc password không đúng.

### Cách sửa nhanh

#### Bước 1: Lấy password từ Render

1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com/)
2. Click vào PostgreSQL database của bạn
3. Tìm phần **"Connections"** → **"External Database URL"**
4. Copy URL có dạng:
   ```
   postgresql://phiduong:PASSWORD_HERE@dpg-d52osah5pdvs73el15tg-a.singapore-postgres.render.com:5432/vietour_iumb
   ```
5. Hoặc tìm phần **"Info"** → Copy **Password** riêng

#### Bước 2: Cập nhật file `.env`

**Cách đơn giản nhất - Dùng DATABASE_URL:**

Mở file `.env` và thêm/sửa dòng:

```env
DATABASE_URL=postgresql://phiduong:YOUR_PASSWORD@dpg-d52osah5pdvs73el15tg-a.singapore-postgres.render.com:5432/vietour_iumb?sslmode=require
```

Thay `YOUR_PASSWORD` bằng password thực tế từ Render.

**Hoặc dùng các biến riêng lẻ:**

```env
POSTGRES_HOST=dpg-d52osah5pdvs73el15tg-a.singapore-postgres.render.com
POSTGRES_PORT=5432
POSTGRES_DB=vietour_iumb
POSTGRES_USER=phiduong
POSTGRES_PASSWORD=YOUR_PASSWORD_HERE
```

#### Bước 3: Test lại

```bash
python scripts/test_connection.py
```

Nếu thành công, bạn sẽ thấy:
```
✅ Kết nối database thành công!
```

---

## 🔍 Kiểm tra file .env

Chạy lệnh này để kiểm tra:

```bash
python scripts/test_connection.py
```

Script sẽ cho biết:
- ✅ Các biến nào đã có
- ❌ Các biến nào còn thiếu
- 🔌 Kết quả test kết nối

---

## 💡 Tips

1. **Nếu password có ký tự đặc biệt** (`@`, `#`, `%`):
   - Trong DATABASE_URL: Cần URL encode
   - Trong POSTGRES_PASSWORD: Không cần encode

2. **Không commit file .env lên Git:**
   - File `.env` đã có trong `.gitignore`
   - Đảm bảo không commit password lên repository

3. **Reset password trên Render:**
   - Nếu quên password, có thể reset trong Render dashboard
   - Vào Database → Settings → Reset Password

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15

