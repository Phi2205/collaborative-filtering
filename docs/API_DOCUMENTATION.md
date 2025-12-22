# API Documentation - Recommend Server

Tài liệu đầy đủ về các API endpoints của Recommend Server cho hệ thống đặt tour Vietour.

## 📋 Mục lục

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Interactions API](#interactions-api)
  - [Recommendations API](#recommendations-api)
- [Scoring System](#scoring-system)
- [Examples](#examples)

## 🌐 Base URL

```
Development: http://localhost:3000
Production: https://your-domain.com
```

## 🔐 Authentication

Hiện tại API chưa có authentication. Trong production, nên thêm API key hoặc JWT token.

## 📚 Endpoints

### Interactions API

#### 1. Tạo Interaction mới

**Endpoint:** `POST /interactions/`

**Mô tả:** Tạo một interaction mới giữa user và tour (view, click, book, rating, etc.)

**Request Body:**
```json
{
  "user_id": 1,
  "tour_id": 5,
  "interaction_type": "view",
  "rating": null
}
```

**Parameters:**
- `user_id` (integer, required): ID của user từ bảng `user_profile`
- `tour_id` (integer, required): ID của tour từ bảng `tour`
- `interaction_type` (string, required): Loại interaction
  - `view`: User xem tour (+1 điểm)
  - `click`: User click vào tour (+1 điểm)
  - `book`: User đặt tour (+5 điểm)
  - `paid`: User đã thanh toán (+6 điểm)
  - `rating`: User đánh giá tour (cần có `rating`)
  - `favorite`: User yêu thích tour (+2 điểm)
- `rating` (float, optional): Rating từ 1-5 sao (chỉ cần khi `interaction_type = "rating"`)

**Response Success (200):**
```json
{
  "success": true,
  "message": "Interaction đã được tạo thành công",
  "interaction": {
    "id": 123,
    "user_id": 1,
    "tour_id": 5,
    "interaction_type": "view",
    "rating": null,
    "timestamp": "2024-01-15T10:30:00.000000"
  }
}
```

**Response Error (404):**
```json
{
  "detail": "User với ID 1 không tồn tại"
}
```

**Response Error (400):**
```json
{
  "detail": "interaction_type phải là một trong: view, click, book, booking, paid, rating, favorite"
}
```

**Ví dụ sử dụng:**

```bash
# User xem tour
curl -X POST "http://localhost:3000/interactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "tour_id": 5,
    "interaction_type": "view"
  }'

# User đánh giá tour 5 sao
curl -X POST "http://localhost:3000/interactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "tour_id": 5,
    "interaction_type": "rating",
    "rating": 5
  }'

# User đặt tour
curl -X POST "http://localhost:3000/interactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "tour_id": 5,
    "interaction_type": "book"
  }'

# User đã thanh toán
curl -X POST "http://localhost:3000/interactions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "tour_id": 5,
    "interaction_type": "paid"
  }'
```

---

#### 2. Lấy Interactions của User

**Endpoint:** `GET /interactions/user/{user_id}`

**Mô tả:** Lấy tất cả interactions của một user

**Path Parameters:**
- `user_id` (integer, required): ID của user

**Query Parameters:**
- `limit` (integer, optional): Số lượng interactions tối đa (mặc định: 50)

**Response Success (200):**
```json
{
  "success": true,
  "user_id": 1,
  "count": 10,
  "interactions": [
    {
      "id": 123,
      "tour_id": 5,
      "interaction_type": "view",
      "rating": null,
      "timestamp": "2024-01-15T10:30:00.000000"
    },
    {
      "id": 124,
      "tour_id": 5,
      "interaction_type": "rating",
      "rating": 5.0,
      "timestamp": "2024-01-15T11:00:00.000000"
    }
  ]
}
```

**Ví dụ sử dụng:**
```bash
curl "http://localhost:3000/interactions/user/1?limit=20"
```

---

#### 3. Lấy Interactions của Tour

**Endpoint:** `GET /interactions/tour/{tour_id}`

**Mô tả:** Lấy tất cả interactions của một tour

**Path Parameters:**
- `tour_id` (integer, required): ID của tour

**Query Parameters:**
- `limit` (integer, optional): Số lượng interactions tối đa (mặc định: 50)

**Response Success (200):**
```json
{
  "success": true,
  "tour_id": 5,
  "count": 25,
  "interactions": [
    {
      "id": 123,
      "user_id": 1,
      "interaction_type": "view",
      "rating": null,
      "timestamp": "2024-01-15T10:30:00.000000"
    }
  ]
}
```

**Ví dụ sử dụng:**
```bash
curl "http://localhost:3000/interactions/tour/5?limit=50"
```

---

### Recommendations API

#### 1. Lấy Recommendations (Collaborative Filtering)

**Endpoint:** `GET /recommendations/collaborative/{user_id}`

**Mô tả:** Lấy danh sách tour được gợi ý cho user dựa trên Collaborative Filtering

**Path Parameters:**
- `user_id` (integer, required): ID của user

**Query Parameters:**
- `method` (string, optional): Phương pháp CF
  - `user_based`: Dựa trên users tương tự (mặc định)
  - `tour_based`: Dựa trên tours tương tự
  - `hybrid`: Kết hợp cả 2 phương pháp
- `limit` (integer, optional): Số lượng gợi ý (1-50, mặc định: 10)

**Response Success (200):**
```json
{
  "success": true,
  "user_id": 1,
  "method": "hybrid",
  "count": 10,
  "recommendations": [
    {
      "tour_id": 15,
      "tour_title": "Tour Đà Lạt 3 ngày 2 đêm",
      "tour_slug": "tour-da-lat-3-ngay-2-dem",
      "predicted_score": 4.5,
      "method": "hybrid_cf"
    },
    {
      "tour_id": 23,
      "tour_title": "Tour Sapa mùa lúa chín",
      "tour_slug": "tour-sapa-mua-lua-chin",
      "predicted_score": 4.2,
      "method": "hybrid_cf"
    }
  ]
}
```

**Response Error (500):**
```json
{
  "detail": "User không tồn tại hoặc chưa có interactions"
}
```

**Ví dụ sử dụng:**

```bash
# User-based CF
curl "http://localhost:3000/recommendations/collaborative/1?method=user_based&limit=10"

# Tour-based CF
curl "http://localhost:3000/recommendations/collaborative/1?method=tour_based&limit=10"

# Hybrid CF (khuyến nghị)
curl "http://localhost:3000/recommendations/collaborative/1?method=hybrid&limit=10"
```

---

## 🎯 Scoring System

Hệ thống tính điểm cho các interactions:

| Hành vi | Điểm số | Mô tả |
|---------|---------|-------|
| View | +1 | User xem tour |
| Click | +1 | User click vào tour |
| Rating (5 sao) | +4 | User đánh giá 5 sao |
| Rating (4 sao) | +3 | User đánh giá 4 sao |
| Rating (3 sao) | +1 | User đánh giá 3 sao |
| Rating (2 sao) | -1 | User đánh giá 2 sao |
| Rating (1 sao) | -3 | User đánh giá 1 sao |
| Book | +5 | User đặt tour |
| Paid | +6 | User đã thanh toán |

**Lưu ý:**
- Điểm số càng cao = User càng quan tâm đến tour
- Rating âm (1-2 sao) giúp hệ thống tránh gợi ý tour không phù hợp
- Paid có điểm cao nhất vì thể hiện sự cam kết thực sự

---

## 📖 Examples

### Workflow hoàn chỉnh

#### Bước 1: User xem tour
```bash
POST /interactions/
{
  "user_id": 1,
  "tour_id": 5,
  "interaction_type": "view"
}
```

#### Bước 2: User đánh giá tour
```bash
POST /interactions/
{
  "user_id": 1,
  "tour_id": 5,
  "interaction_type": "rating",
  "rating": 5
}
```

#### Bước 3: User đặt tour
```bash
POST /interactions/
{
  "user_id": 1,
  "tour_id": 5,
  "interaction_type": "book"
}
```

#### Bước 4: User thanh toán
```bash
POST /interactions/
{
  "user_id": 1,
  "tour_id": 5,
  "interaction_type": "paid"
}
```

#### Bước 5: Lấy recommendations cho user
```bash
GET /recommendations/collaborative/1?method=hybrid&limit=10
```

---

## 🔍 Testing với Swagger UI

Truy cập Swagger UI để test API trực tiếp:

```
http://localhost:3000/docs
```

Tại đây bạn có thể:
- Xem tất cả endpoints
- Test API trực tiếp
- Xem request/response examples
- Xem schema validation

---

## ⚠️ Error Codes

| Status Code | Mô tả |
|-------------|-------|
| 200 | Success |
| 400 | Bad Request - Dữ liệu không hợp lệ |
| 404 | Not Found - User/Tour không tồn tại |
| 500 | Internal Server Error - Lỗi server |

---

## 📝 Notes

1. **User ID**: Phải là ID từ bảng `user_profile`, không phải `account_id`
2. **Tour ID**: Phải là tour đã được approve và không bị banned
3. **Rating**: Chỉ cần khi `interaction_type = "rating"`
4. **Timestamp**: Tự động set khi tạo interaction
5. **Recommendations**: Cần có đủ dữ liệu interactions để có kết quả tốt

---

## 🚀 Best Practices

1. **Luôn gửi interaction khi user xem tour**: Giúp hệ thống học được hành vi
2. **Sử dụng hybrid method**: Cho kết quả tốt nhất
3. **Limit hợp lý**: Không nên lấy quá nhiều recommendations (10-20 là tốt)
4. **Cache recommendations**: Có thể cache kết quả để tăng performance
5. **Update interactions real-time**: Gửi interaction ngay khi user thực hiện hành động

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15

