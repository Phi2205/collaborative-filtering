# Documentation - Recommend Server

Tài liệu đầy đủ về Recommend Server cho hệ thống đặt tour Vietour.

## 📚 Tài liệu có sẵn

### 1. [API Documentation](./API_DOCUMENTATION.md)
Hướng dẫn chi tiết về tất cả API endpoints:
- Interactions API (tạo, lấy interactions)
- Recommendations API (lấy gợi ý tour)
- Scoring System (cách tính điểm)
- Examples và best practices

### 2. [Setup Guide](./SETUP_GUIDE.md)
Hướng dẫn setup và chạy hệ thống:
- Cài đặt dependencies
- Cấu hình database
- Tạo database tables
- Chạy server
- Troubleshooting

## 🚀 Quick Start

### 1. Setup cơ bản

```bash
# Clone repository
git clone <repository-url>
cd Recommend-server

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
python -m pip install -r requirements.txt

# Cấu hình .env
copy .env.example .env
# Điền thông tin database vào .env

# Tạo database tables
python -m app.utils.init_db

# Chạy server
python start.py
```

### 2. Test API

Truy cập Swagger UI: `http://localhost:3000/docs`

## 📖 Tài liệu chính

### API Endpoints

#### Interactions
- `POST /interactions/` - Tạo interaction mới
- `GET /interactions/user/{user_id}` - Lấy interactions của user
- `GET /interactions/tour/{tour_id}` - Lấy interactions của tour

#### Recommendations
- `GET /recommendations/collaborative/{user_id}` - Lấy gợi ý tour

### Scoring System

| Hành vi | Điểm |
|---------|------|
| View | +1 |
| Rating (5 sao) | +4 |
| Rating (4 sao) | +3 |
| Rating (3 sao) | +1 |
| Rating (2 sao) | -1 |
| Rating (1 sao) | -3 |
| Book | +5 |
| Paid | +6 |

## 🔗 Links hữu ích

- [API Documentation](./API_DOCUMENTATION.md) - Chi tiết về API
- [Setup Guide](./SETUP_GUIDE.md) - Hướng dẫn setup
- [Main README](../README.md) - README chính của project

## 💡 Tips

1. **Luôn gửi interaction khi user xem tour** - Giúp hệ thống học được hành vi
2. **Sử dụng hybrid method** - Cho kết quả tốt nhất
3. **Cache recommendations** - Tăng performance
4. **Monitor interactions** - Đảm bảo dữ liệu đầy đủ

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15

