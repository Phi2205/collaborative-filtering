# 🔢 CÁC BƯỚC TÍNH TOÁN: User 11 → Tour 2

## 📊 Dữ liệu ban đầu

```
Interactions trong database:
- User 11 → Tour 1 (view, score=1)
- User 4  → Tour 1 (view, score=1)
- User 4  → Tour 2 (view, score=1)
```

---

## 🎯 MỤC TIÊU

**Tính toán để User 11 được recommend Tour 2**

---

## 📐 BƯỚC 1: BUILD USER-TOUR MATRIX

### 1.1. Lấy tất cả Users và Tours

```python
# Users có interactions
users = [4, 11]  # Chỉ users có interactions
# Tours có interactions  
tours = [1, 2]   # Chỉ tours có interactions
```

### 1.2. Tạo Matrix

```
Matrix shape: (2 users, 2 tours)

        Tour 1    Tour 2
User 4    1        1
User 11   1        0
```

**Code:**
```python
matrix = np.array([
    [1, 1],  # User 4: Tour 1=1, Tour 2=1
    [1, 0]   # User 11: Tour 1=1, Tour 2=0
])
```

### 1.3. Mapping IDs

```python
user_id_to_idx = {4: 0, 11: 1}
tour_id_to_idx = {1: 0, 2: 1}
user_ids = [4, 11]
tour_ids = [1, 2]
```

---

## 📐 BƯỚC 2: DATA PREPROCESSING

### 2.1. Normalization (Mean Centering)

**User 4:**
```python
user4_ratings = [1, 1]
mean_4 = (1 + 1) / 2 = 1.0
normalized_4 = [1 - 1.0, 1 - 1.0] = [0.0, 0.0]
```

**User 11:**
```python
user11_ratings = [1, 0]
mean_11 = 1 / 1 = 1.0  # Chỉ tính ratings > 0
normalized_11 = [1 - 1.0, 0 - 1.0] = [0.0, -1.0]
```

**Normalized Matrix:**
```
        Tour 1    Tour 2
User 4    0.0      0.0
User 11   0.0     -1.0
```

**Lưu ý:** Với data quá sparse, normalization có thể không hiệu quả. Hệ thống sẽ dùng raw matrix cho fallback.

### 2.2. Outlier Removal

```python
# Tất cả scores = 1 → Không có outliers
# Bỏ qua bước này
```

### 2.3. Sparse Data Handling

```python
sparsity = (số 0) / (tổng cells) = 1 / 4 = 25%
# < 95% → OK, không cần filter
```

---

## 📐 BƯỚC 3: USER-BASED CF CALCULATION

### 3.1. Tính User Similarity (Cosine)

**Raw Matrix (không normalize):**
```
        Tour 1    Tour 2
User 4    1        1
User 11   1        0
```

**Vector User 4:** `[1, 1]`  
**Vector User 11:** `[1, 0]`

**Cosine Similarity:**
```python
dot_product = (1 * 1) + (1 * 0) = 1
magnitude_4 = sqrt(1² + 1²) = sqrt(2) ≈ 1.414
magnitude_11 = sqrt(1² + 0²) = sqrt(1) = 1.0

similarity(4, 11) = dot_product / (magnitude_4 * magnitude_11)
                   = 1 / (1.414 * 1.0)
                   = 1 / 1.414
                   ≈ 0.707
```

**Similarity Matrix:**
```
        User 4    User 11
User 4    1.0      0.707
User 11   0.707    1.0
```

**⚠️ VẤN ĐỀ:** Nếu dùng normalized matrix, similarity có thể = 0!

---

### 3.2. Tìm Similar Users cho User 11

```python
user11_idx = 1
similarity_scores = [0.707, 1.0]  # Với User 4 và chính User 11
# Loại bỏ chính User 11 → Chỉ còn User 4
similar_users_idx = [0]  # User 4
```

---

### 3.3. Tính Predicted Score cho Tour 2

**Logic chính (nếu similarity > 0):**
```python
tour2_idx = 1
user11_rating_tour2 = matrix[1, 1] = 0  # User 11 chưa xem Tour 2

# Lấy ratings của similar users cho Tour 2
similar_users_ratings = matrix[0, 1] = 1  # User 4 đã xem Tour 2
similar_users_sim = similarity[1, 0] = 0.707

# Weighted Average
predicted_score = (similar_users_ratings * similar_users_sim) / similar_users_sim
                = (1 * 0.707) / 0.707
                = 0.707 / 0.707
                = 1.0 ✅
```

**✅ KẾT QUẢ:** Predicted Score = 1.0

---

### 3.4. Fallback Logic (nếu similarity = 0)

**Nếu cosine similarity = 0 (do normalization), hệ thống sẽ dùng Co-occurrence:**

```python
# User 11 đã xem Tour 1
interacted_tours_idx = [0]  # Tour 1

# Tìm users đã xem Tour 1
users_who_saw_tour1 = np.where(matrix[:, 0] > 0) = [0, 1]
# Loại bỏ chính User 11
users_who_saw_tour1 = [0]  # User 4

# Xem User 4 có xem Tour 2 không
ratings_from_user4 = matrix[0, 1] = 1  # ✅ Có!

# Tính co-occurrence score
co_occurrence_score = mean(ratings) * count(users)
                    = 1.0 * 1
                    = 1.0

predicted_score = co_occurrence_score / len(interacted_tours_idx)
                = 1.0 / 1
                = 1.0 ✅
```

**✅ KẾT QUẢ:** Predicted Score = 1.0 (từ fallback)

---

## 📐 BƯỚC 4: TOUR-BASED CF CALCULATION

### 4.1. Tính Tour Similarity (Cosine trên transpose)

**Transpose Matrix:**
```
        User 4    User 11
Tour 1    1        1
Tour 2    1        0
```

**Vector Tour 1:** `[1, 1]`  
**Vector Tour 2:** `[1, 0]`

**Cosine Similarity:**
```python
dot_product = (1 * 1) + (1 * 0) = 1
magnitude_1 = sqrt(1² + 1²) = sqrt(2) ≈ 1.414
magnitude_2 = sqrt(1² + 0²) = sqrt(1) = 1.0

similarity(Tour1, Tour2) = dot_product / (magnitude_1 * magnitude_2)
                        = 1 / (1.414 * 1.0)
                        = 1 / 1.414
                        ≈ 0.707
```

**Similarity Matrix:**
```
        Tour 1    Tour 2
Tour 1    1.0      0.707
Tour 2    0.707    1.0
```

---

### 4.2. Tính Predicted Score cho Tour 2

**Logic chính (nếu similarity > 0):**
```python
tour2_idx = 1
user11_rating_tour2 = matrix[1, 1] = 0  # User 11 chưa xem Tour 2

# User 11 đã xem Tour 1
interacted_tours_idx = [0]  # Tour 1
user11_ratings = [1]  # Rating cho Tour 1

# Similarity giữa Tour 2 và Tour 1
similarities = [0.707]  # similarity(Tour2, Tour1)

# Weighted Average
predicted_score = sum(similarities * ratings) / sum(similarities)
                = (0.707 * 1) / 0.707
                = 0.707 / 0.707
                = 1.0 ✅
```

**✅ KẾT QUẢ:** Predicted Score = 1.0

---

### 4.3. Fallback Logic (nếu similarity = 0)

**Nếu cosine similarity = 0, hệ thống sẽ dùng Co-occurrence:**

```python
# User 11 đã xem Tour 1
interacted_tours_idx = [0]  # Tour 1

# Tìm users đã xem Tour 1
users_who_saw_tour1 = np.where(matrix[:, 0] > 0) = [0, 1]
# Loại bỏ chính User 11
users_who_saw_tour1 = [0]  # User 4

# Xem User 4 có xem Tour 2 không
ratings_from_user4 = matrix[0, 1] = 1  # ✅ Có!

# Tính co-occurrence score
co_occurrence_score = mean(ratings) * count(users)
                    = 1.0 * 1
                    = 1.0

predicted_score = co_occurrence_score / len(interacted_tours_idx)
                = 1.0 / 1
                = 1.0 ✅
```

**✅ KẾT QUẢ:** Predicted Score = 1.0 (từ fallback)

---

## 📐 BƯỚC 5: HYBRID CF CALCULATION

### 5.1. Combine Scores từ 2 methods

**User-Based CF Score:** `1.0`  
**Tour-Based CF Score:** `1.0`

**Hybrid Score:**
```python
user_weight = 0.5
tour_weight = 0.5

final_score = (user_weight * user_score) + (tour_weight * tour_score)
            = (0.5 * 1.0) + (0.5 * 1.0)
            = 0.5 + 0.5
            = 1.0 ✅
```

**✅ KẾT QUẢ:** Final Score = 1.0

---

## 📐 BƯỚC 6: DENORMALIZATION (nếu đã normalize)

**Nếu matrix đã được normalize:**
```python
user11_mean = 1.0
denormalized_score = predicted_score + user11_mean
                   = 1.0 + 1.0
                   = 2.0
```

**Nhưng với fallback logic, hệ thống dùng raw scores → không cần denormalize**

---

## 📐 BƯỚC 7: APPLY ADVANCED FEATURES

### 7.1. Time Decay (nếu có)

```python
# Giả sử interaction cách đây 5 ngày
days_ago = 5
half_life = 30

decay_factor = 2 ** (-days_ago / half_life)
             = 2 ** (-5 / 30)
             = 2 ** (-0.167)
             ≈ 0.89

final_score = predicted_score * decay_factor
            = 1.0 * 0.89
            = 0.89
```

**Lưu ý:** Time decay chỉ áp dụng khi có timestamp. Với data hiện tại, có thể bỏ qua.

### 7.2. Diversity (MMR)

**Nếu có nhiều recommendations:**
- Chọn tours có score cao nhưng khác biệt với nhau
- Balance giữa relevance và diversity

**Với chỉ 1 recommendation (Tour 2):**
- Không cần apply diversity

### 7.3. Explanations

```python
explanation = "Users tương tự với bạn đã xem tour này"
# Hoặc
explanation = "Tour này tương tự với tour bạn đã xem"
```

---

## 📐 BƯỚC 8: FINAL RANKING

### 8.1. Sắp xếp theo Score

```python
recommendations = [
    {
        "tour_id": 2,
        "predicted_score": 1.0,
        "method": "hybrid_cf"
    }
]

# Sắp xếp theo score DESC
sorted_recommendations = sorted(recommendations, key=lambda x: x["predicted_score"], reverse=True)
```

### 8.2. Lấy Top N

```python
limit = 10
top_recommendations = sorted_recommendations[:limit]
# → Tour 2 được recommend ✅
```

---

## ✅ KẾT QUẢ CUỐI CÙNG

```json
{
  "success": true,
  "user_id": 11,
  "method": "hybrid",
  "recommendations": [
    {
      "tour_id": 2,
      "tour_title": "TOUR MIỀN TÂY TẾT DƯƠNG LỊCH 3N2Đ",
      "tour_slug": "tour-mien-tay-tet-duong-lich-3n2d",
      "predicted_score": 1.0,
      "method": "hybrid_cf",
      "explanation": "Users tương tự với bạn đã xem tour này"
    }
  ],
  "count": 1
}
```

---

## 📊 TÓM TẮT CÁC BƯỚC

| Bước | Method | Score | Kết quả |
|------|--------|-------|---------|
| 1 | Build Matrix | - | Matrix (2x2) |
| 2 | Preprocessing | - | Normalized (nếu cần) |
| 3.1 | User Similarity | 0.707 | User 4 tương tự User 11 |
| 3.2 | User-Based CF | 1.0 | ✅ Recommend Tour 2 |
| 4.1 | Tour Similarity | 0.707 | Tour 1 tương tự Tour 2 |
| 4.2 | Tour-Based CF | 1.0 | ✅ Recommend Tour 2 |
| 5 | Hybrid CF | 1.0 | ✅ Final Score = 1.0 |
| 6 | Denormalize | - | Không cần (raw scores) |
| 7 | Advanced Features | - | Time decay, explanations |
| 8 | Final Ranking | 1.0 | ✅ Tour 2 được recommend |

---

## 🔍 CÁC TRƯỜNG HỢP ĐẶC BIỆT

### Trường hợp 1: Cosine Similarity = 0

**Nguyên nhân:** Normalization làm cho vectors trở thành zero vectors

**Giải pháp:** Co-occurrence Fallback
- Tìm users cùng xem tours → Recommend tours họ đã xem
- ✅ Vẫn recommend được Tour 2

### Trường hợp 2: Chỉ có 1 user xem cả 2 tours

**Nguyên nhân:** Data quá sparse

**Giải pháp:** Co-occurrence Fallback
- User 4 xem cả Tour 1 và Tour 2
- User 11 xem Tour 1
- → Recommend Tour 2 cho User 11 ✅

### Trường hợp 3: Nhiều users cùng xem

**Nếu có thêm User 5 xem Tour 1 và Tour 2:**
```python
co_occurrence_score = mean([1, 1]) * 2  # 2 users
                   = 1.0 * 2
                   = 2.0
# Score cao hơn → Ưu tiên hơn
```

---

## 💡 ĐIỂM QUAN TRỌNG

1. **Co-occurrence Fallback là chìa khóa:**
   - Khi cosine similarity = 0, fallback vẫn hoạt động
   - Đảm bảo recommendations ngay cả với sparse data

2. **Hybrid CF tăng độ chính xác:**
   - Kết hợp cả User-Based và Tour-Based
   - Giảm false negatives

3. **Normalization có thể gây vấn đề:**
   - Với sparse data, normalization → zero vectors
   - Fallback logic giải quyết vấn đề này

---

## 🔗 LIÊN KẾT

- [Recommendation Flow](./RECOMMENDATION_FLOW.md)
- [API Documentation](./API_DOCUMENTATION.md)

