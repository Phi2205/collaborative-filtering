# 📋 QUY TRÌNH ĐỀ XUẤT CỦA HỆ THỐNG

## 🔄 Tổng quan Flow

```
API Request → Kiểm tra User → Cold Start Check → Chọn Method → 
Data Preprocessing → Tính Similarity → Tính Predicted Scores → 
Apply Advanced Features → Return Recommendations
```

---

## 📥 1. API ENTRY POINT

**Endpoint:** `GET /recommendations/collaborative/{user_id}`

**Parameters:**
- `user_id`: ID của user cần recommend
- `method`: `user_based` | `tour_based` | `hybrid` (mặc định: `hybrid`)
- `limit`: Số lượng recommendations (1-50, mặc định: 10)

**Bước 1.1: Kiểm tra User tồn tại**
```python
user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
if not user:
    raise HTTPException(404, "User không tồn tại")
```

**Bước 1.2: Khởi tạo CollaborativeFiltering**
```python
cf = CollaborativeFiltering(
    db,
    normalize=True,           # Mean centering
    handle_sparse=True,        # Xử lý sparse data
    remove_outliers=True,      # Loại bỏ outliers
    use_time_decay=True,       # Time decay
    use_diversity=True,        # Diversity
    enable_explanation=True    # Explanations
)
```

---

## 🧊 2. COLD START CHECK

**Bước 2.1: Kiểm tra User có interactions không**
```python
user_interactions_count = db.query(UserTourInteraction).filter(
    UserTourInteraction.user_id == user_id
).count()
```

**Bước 2.2: Nếu user chưa có interactions (count = 0)**
```python
if user_interactions_count == 0:
    recommendations = cf.handle_cold_start_user(user_id, limit)
    # → Trả về popular tours (dựa trên view_count, booked_count)
    return recommendations
```

**Cold Start Logic:**
- Lấy top N tours phổ biến nhất
- Sắp xếp theo: `view_count DESC, booked_count DESC`
- Chỉ lấy tours: `is_active=True, is_approved=True, is_banned=False`

---

## 🎯 3. CHỌN METHOD VÀ XỬ LÝ

### 3.1. USER-BASED CF

**Flow:**
```
1. Build User-Tour Matrix
2. Tính User Similarity (Cosine Similarity)
3. Tìm Top N Similar Users
4. Tính Predicted Scores cho từng tour
5. Apply Fallback nếu cần
6. Apply Advanced Features
```

**Chi tiết:**

**Bước 3.1.1: Build Matrix & Tính Similarity**
```python
# Lazy loading: Chỉ build nếu chưa có cache
matrix = cf.build_user_tour_matrix()  # Shape: (n_users, n_tours)
user_similarity = cf.calculate_user_similarity()  # Shape: (n_users, n_users)
```

**Bước 3.1.2: Tìm Similar Users**
```python
user_idx = user_id_to_idx[user_id]
similar_users_idx = np.argsort(user_similarity[user_idx])[::-1][1:n_similar_users+1]
# Lấy top N users tương tự (loại bỏ chính user đó)
```

**Bước 3.1.3: Tính Predicted Scores**

**Logic chính:**
```python
for tour_idx in range(n_tours):
    if user_ratings[tour_idx] == 0:  # Chỉ tours user chưa xem
        similar_users_ratings = matrix[similar_users_idx, tour_idx]
        similar_users_sim = user_similarity[user_idx, similar_users_idx]
        
        if np.sum(similar_users_sim) > 0:
            # Weighted Average
            predicted_score = np.sum(
                similar_users_ratings * similar_users_sim
            ) / np.sum(similar_users_sim)
        else:
            # FALLBACK: Co-occurrence Logic
            # Tìm users đã xem cùng tours với user này
            # → Recommend tours mà những users đó đã xem
```

**Co-occurrence Fallback (MỚI):**
```python
# Ví dụ: User 11 đã xem Tour 1
# → Tìm users đã xem Tour 1: User 4
# → User 4 đã xem Tour 2
# → Recommend Tour 2 cho User 11 ✅
```

**Bước 3.1.4: Lấy Top N Recommendations**
```python
top_tours_idx = np.argsort(predicted_scores)[::-1][:n_recommendations * 2]
# Lấy nhiều hơn để apply diversity sau
```

**Bước 3.1.5: Denormalize Scores**
```python
if normalize:
    final_score = denormalize_score(predicted_score, user_id)
    # Chuyển từ normalized score về original scale
```

---

### 3.2. TOUR-BASED CF

**Flow:**
```
1. Build User-Tour Matrix
2. Tính Tour Similarity (Cosine Similarity trên transpose)
3. Tìm Tours User đã tương tác
4. Tính Predicted Scores dựa trên Tour Similarity
5. Apply Fallback nếu cần
6. Apply Advanced Features
```

**Chi tiết:**

**Bước 3.2.1: Tính Tour Similarity**
```python
tour_similarity = cf.calculate_tour_similarity()
# Tính cosine similarity trên transpose matrix
# Shape: (n_tours, n_tours)
```

**Bước 3.2.2: Tính Predicted Scores**

**Logic chính:**
```python
for tour_idx in range(n_tours):
    if user_ratings[tour_idx] == 0:  # Chỉ tours user chưa xem
        interacted_tours_idx = np.where(user_ratings > 0)[0]
        
        similarities = tour_similarity[tour_idx, interacted_tours_idx]
        ratings = user_ratings[interacted_tours_idx]
        
        if np.sum(similarities) > 0:
            # Weighted Average
            predicted_score = np.sum(
                similarities * ratings
            ) / np.sum(similarities)
        else:
            # FALLBACK: Co-occurrence Logic
            # Tìm users đã xem tours user đã xem
            # → Recommend tours mà những users đó đã xem
```

**Co-occurrence Fallback (MỚI):**
```python
# Ví dụ: User 11 đã xem Tour 1
# → Tìm users đã xem Tour 1: User 4
# → User 4 đã xem Tour 2
# → Recommend Tour 2 cho User 11 ✅
```

---

### 3.3. HYBRID CF

**Flow:**
```
1. Gọi User-Based CF → Lấy recommendations
2. Gọi Tour-Based CF → Lấy recommendations
3. Combine Scores từ cả 2 methods
4. Tính Final Score = weighted average
5. Apply Advanced Features
```

**Chi tiết:**

**Bước 3.3.1: Gọi cả 2 methods**
```python
user_based_recs = cf.user_based_recommendations(user_id, limit * 2)
tour_based_recs = cf.tour_based_recommendations(user_id, limit * 2)
```

**Bước 3.3.2: Combine Scores**
```python
combined_scores = {}
for rec in user_based_recs:
    combined_scores[rec["tour_id"]] = {
        "user_score": rec["predicted_score"],
        "tour_score": 0.0
    }

for rec in tour_based_recs:
    if rec["tour_id"] in combined_scores:
        combined_scores[rec["tour_id"]]["tour_score"] = rec["predicted_score"]
    else:
        combined_scores[rec["tour_id"]] = {
            "user_score": 0.0,
            "tour_score": rec["predicted_score"]
        }
```

**Bước 3.3.3: Tính Final Score**
```python
final_score = (
    user_weight * user_score + 
    (1 - user_weight) * tour_score
)
# Mặc định: user_weight = 0.5 (50% mỗi method)
```

---

## 🔧 4. DATA PREPROCESSING

**Áp dụng trước khi tính similarity:**

### 4.1. Normalization (Mean Centering)
```python
# Giảm user bias
user_mean = np.mean(user_ratings[user_ratings > 0])
normalized_ratings = user_ratings - user_mean
```

### 4.2. Outlier Removal
```python
# Sử dụng IQR method
Q1, Q3 = np.percentile(scores, [25, 75])
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
# Cap scores ngoài bounds
```

### 4.3. Sparse Data Handling
```python
# Warning nếu sparsity > 95%
# Filter users/tours có < 2 interactions
```

---

## ✨ 5. ADVANCED FEATURES

**Áp dụng sau khi có recommendations:**

### 5.1. Time Decay
```python
# Interactions gần đây quan trọng hơn
decay_factor = 2 ** (-days_ago / half_life_days)
weighted_score = score * decay_factor
```

### 5.2. Diversity (MMR)
```python
# Maximal Marginal Relevance
# Đảm bảo recommendations không quá giống nhau
# Balance giữa relevance và diversity
```

### 5.3. Explanations
```python
# Tạo lý do cho mỗi recommendation
# Ví dụ: "Users tương tự với bạn đã xem tour này"
```

---

## 🎯 6. FINAL FALLBACK

**Nếu không có recommendations:**

**Bước 6.1: Kiểm tra User đã xem bao nhiêu % tours**
```python
user_interactions_count = ...
total_tours = ...
coverage = user_interactions_count / total_tours
```

**Bước 6.2: Nếu coverage >= 80%**
```python
if coverage >= 0.8:
    # User đã xem hầu hết tours
    # → Trả về popular tours làm fallback
    recommendations = get_popular_tours(limit)
```

---

## 📊 7. RESPONSE FORMAT

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
      "predicted_score": 1.5,
      "method": "hybrid_cf",
      "explanation": "Users tương tự với bạn đã xem tour này"
    }
  ],
  "count": 1
}
```

---

## 🔍 VÍ DỤ CỤ THỂ: User 11

### Input:
- User 11 đã xem Tour 1
- User 4 đã xem Tour 1 và Tour 2

### Flow:

**1. Cold Start Check:**
- User 11 có 1 interaction → Không phải cold start

**2. Chọn Method:**
- Method = "hybrid" (mặc định)

**3. User-Based CF:**
- Tính similarity(User 11, User 4) = 0 (quá sparse)
- **Fallback:** Co-occurrence logic
  - User 11 đã xem Tour 1
  - User 4 đã xem Tour 1 → Co-occurrence ✅
  - User 4 đã xem Tour 2 → Recommend Tour 2 ✅
- Score: 1.0

**4. Tour-Based CF:**
- Tính similarity(Tour 1, Tour 2) = 0 (quá sparse)
- **Fallback:** Co-occurrence logic
  - User 11 đã xem Tour 1
  - User 4 đã xem Tour 1 → Co-occurrence ✅
  - User 4 đã xem Tour 2 → Recommend Tour 2 ✅
- Score: 1.0

**5. Hybrid CF:**
- Combine: 0.5 * 1.0 + 0.5 * 1.0 = 1.0
- Final Score: 1.0

**6. Result:**
- ✅ Tour 2 được recommend với score = 1.0

---

## 📝 TÓM TẮT QUY TRÌNH

1. **API Entry** → Kiểm tra user, khởi tạo CF
2. **Cold Start** → Nếu user mới → Popular tours
3. **Build Matrix** → User-Tour interaction matrix
4. **Preprocessing** → Normalize, remove outliers, handle sparse
5. **Calculate Similarity** → User similarity hoặc Tour similarity
6. **Predict Scores** → Dựa trên similarity hoặc co-occurrence fallback
7. **Combine** (nếu hybrid) → Weighted average của 2 methods
8. **Advanced Features** → Time decay, diversity, explanations
9. **Final Fallback** → Popular tours nếu không có recommendations
10. **Return** → Top N recommendations

---

## 🎯 ĐIỂM QUAN TRỌNG

### ✅ Co-occurrence Fallback (MỚI)
- **Khi nào:** Khi cosine similarity = 0 (data quá sparse)
- **Logic:** Tìm users cùng xem tours → Recommend tours họ đã xem
- **Ví dụ:** User 11 + User 4 cùng xem Tour 1 → Recommend Tour 2 (User 4 đã xem)

### ✅ Caching
- Matrix và similarity được cache
- TTL: 3600 giây (1 giờ)
- Thread-safe với locks

### ✅ Performance
- Lazy loading: Chỉ tính khi cần
- Batch processing: Tính nhiều users cùng lúc
- Cache invalidation: Khi data thay đổi

---

## 🔗 LIÊN KẾT

- [API Documentation](./API_DOCUMENTATION.md)
- [Setup Guide](./SETUP_GUIDE.md)
- [Troubleshooting](./TROUBLESHOOTING.md)

