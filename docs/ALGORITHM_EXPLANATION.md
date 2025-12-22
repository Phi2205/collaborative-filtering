# Giải Thích Chi Tiết Thuật Toán Collaborative Filtering

## Tổng Quan

Hệ thống Recommendation sử dụng **Collaborative Filtering (CF)** để đề xuất tours cho users dựa trên hành vi tương tác của các users khác. Có 3 phương pháp chính:

1. **User-Based CF**: Tìm users tương tự, đề xuất tours mà họ đã thích
2. **Tour-Based CF**: Tìm tours tương tự với tours user đã xem
3. **Hybrid CF**: Kết hợp cả 2 phương pháp trên

---

## 1. Data Preprocessing (Tiền Xử Lý Dữ Liệu)

### 1.1. Build User-Tour Matrix

**Mục đích**: Chuyển đổi dữ liệu interactions thành ma trận số học để tính toán.

**Cách hoạt động**:
```
Matrix[user_idx, tour_idx] = score
```

**Ví dụ**:
```
        Tour 1  Tour 2  Tour 3
User 4    1       1       0
User 11   1       0       0
```

**Lưu ý**: 
- Lưu **raw matrix** (`user_tour_matrix_raw`) trước khi preprocessing
- Áp dụng **time decay** nếu enabled: `score *= decay_factor`

### 1.2. Remove Outliers (Loại Bỏ Giá Trị Ngoại Lai)

**Mục đích**: Loại bỏ các điểm số bất thường (quá cao/quá thấp) để tránh ảnh hưởng đến tính toán.

**Phương pháp**: IQR (Interquartile Range)
```
Q1 = percentile(25%)
Q3 = percentile(75%)
IQR = Q3 - Q1
Lower Bound = Q1 - 1.5 * IQR
Upper Bound = Q3 + 1.5 * IQR
```

**Cách xử lý**: Cap giá trị ngoài bounds về bounds (không xóa)

**Ví dụ**:
- Nếu score = 10 nhưng upper_bound = 6 → cap về 6
- Nếu score = -5 nhưng lower_bound = 1 → cap về 1

### 1.3. Handle Sparse Data (Xử Lý Dữ Liệu Thưa)

**Mục đích**: Cảnh báo khi dữ liệu quá thưa (nhiều giá trị 0).

**Cách tính Sparsity**:
```
Sparsity = 1 - (số giá trị khác 0 / tổng số phần tử)
```

**Ví dụ**:
- Matrix 12x14 = 168 phần tử
- Chỉ có 3 interactions → Sparsity = 1 - (3/168) = 98.2%

**Xử lý**:
- Nếu Sparsity > 95% → Warning
- Có thể loại bỏ users/tours quá ít interactions (nếu cần)

### 1.4. Normalize Matrix (Chuẩn Hóa Ma Trận)

**Mục đích**: Giảm bias giữa các users (một số users rate cao hơn, một số rate thấp hơn).

**Phương pháp**: Mean Centering
```
Normalized_Score = Original_Score - User_Mean
```

**Ví dụ**:
```
User 4: [1, 1, 0] → Mean = 0.67 → Normalized: [0.33, 0.33, -0.67]
User 11: [1, 0, 0] → Mean = 0.33 → Normalized: [0.67, -0.33, -0.33]
```

**Lưu ý quan trọng**:
- Sau khi normalize, nhiều giá trị có thể = 0 hoặc âm
- **Phải lưu raw matrix** để dùng cho fallback logic
- Khi denormalize: `Final_Score = Normalized_Score + User_Mean`

---

## 2. User-Based Collaborative Filtering

### 2.1. Tính User Similarity (Độ Tương Đồng Giữa Users)

**Mục đích**: Tìm users có hành vi tương tự nhau.

**Phương pháp**: Cosine Similarity
```
Similarity(User_A, User_B) = cos(θ) = (A · B) / (||A|| * ||B||)
```

**Công thức chi tiết**:
```
Similarity = Σ(A_i * B_i) / (√(ΣA_i²) * √(ΣB_i²))
```

**Ví dụ**:
```
User 4:  [1, 1, 0]
User 11: [1, 0, 0]

Dot Product = 1*1 + 1*0 + 0*0 = 1
||User 4|| = √(1² + 1² + 0²) = √2
||User 11|| = √(1² + 0² + 0²) = 1
Similarity = 1 / (√2 * 1) = 0.707
```

**Kết quả**: Ma trận similarity `[n_users x n_users]`, giá trị từ -1 đến 1

### 2.2. Tìm Similar Users

**Cách làm**: 
1. Lấy hàng của user trong similarity matrix
2. Sắp xếp giảm dần
3. Lấy top N users (loại bỏ chính user đó)

**Ví dụ**:
```
User 11 similarity với:
- User 4: 0.707
- User 5: 0.500
- User 6: 0.000
→ Top 2 similar users: [User 4, User 5]
```

### 2.3. Tính Predicted Score (Điểm Dự Đoán)

**Công thức**: Weighted Average
```
Predicted_Score(Tour_j) = Σ(Similarity_i * Rating_i_j) / Σ(Similarity_i)
```

**Ví dụ**:
```
User 11 muốn predict Tour 2:
- User 4 (similarity=0.707) đã rate Tour 2 = 1
- User 5 (similarity=0.500) đã rate Tour 2 = 0

Predicted_Score = (0.707 * 1 + 0.500 * 0) / (0.707 + 0.500)
                 = 0.707 / 1.207
                 = 0.586
```

**Lưu ý**: 
- Chỉ tính cho tours user **chưa tương tác** (`user_ratings[tour_idx] == 0`)
- Nếu `Σ(Similarity_i) == 0` → Chuyển sang **Fallback Logic**

### 2.4. Fallback Logic (Khi Similarity = 0)

**Vấn đề**: Khi data quá sparse, cosine similarity có thể = 0 cho tất cả users.

**Giải pháp**: Co-occurrence Based Recommendation

**Cách hoạt động**:
1. Tìm các tours user đã tương tác (dùng **raw matrix**, không normalize)
2. Với mỗi tour đã tương tác:
   - Tìm users khác đã xem tour đó
   - Xem những users này có xem tour đang predict không
   - Tính điểm dựa trên số lượng và ratings
3. Tổng hợp điểm từ tất cả tours đã tương tác

**Ví dụ chi tiết**:
```
User 11 đã xem Tour 1 (score=1)

Để predict Tour 2:
1. Tìm users đã xem Tour 1: [User 4]
2. User 4 có xem Tour 2 không? → Có (score=1)
3. Co-occurrence score = mean(ratings) * count
                      = 1.0 * 1 = 1.0
4. Predicted_Score(Tour 2) = 1.0 / 1 = 1.0
```

**Công thức**:
```
Co_Occurrence_Score = Σ(
    mean(ratings_from_co_users) * count(co_users)
) / count(interacted_tours)
```

---

## 3. Tour-Based Collaborative Filtering

### 3.1. Tính Tour Similarity (Độ Tương Đồng Giữa Tours)

**Mục đích**: Tìm tours tương tự nhau dựa trên users đã xem chúng.

**Phương pháp**: Cosine Similarity trên **transpose matrix**
```
Tour_Similarity = Cosine_Similarity(Matrix^T)
```

**Ví dụ**:
```
        User 4  User 11
Tour 1    1       1
Tour 2    1       0

Similarity(Tour 1, Tour 2) = (1*1 + 1*0) / (√2 * 1) = 0.707
```

### 3.2. Tìm Similar Tours

**Cách làm**:
1. Với mỗi tour user đã xem
2. Tìm top N tours tương tự nhất
3. Tính predicted score dựa trên ratings user đã cho các tours tương tự

**Ví dụ**:
```
User 11 đã xem Tour 1 (rating=1)
Tour 1 tương tự với:
- Tour 2: similarity=0.707
- Tour 3: similarity=0.500

Predicted_Score(Tour 2) = Rating(Tour 1) * Similarity(Tour 1, Tour 2)
                         = 1 * 0.707 = 0.707
```

### 3.3. Fallback Logic

Tương tự User-Based CF, nếu similarity = 0 → dùng co-occurrence logic.

---

## 4. Hybrid Collaborative Filtering

**Mục đích**: Kết hợp cả User-Based và Tour-Based để tăng độ chính xác.

**Cách làm**:
1. Tính recommendations từ User-Based CF
2. Tính recommendations từ Tour-Based CF
3. Kết hợp scores:
   ```
   Final_Score = α * User_Based_Score + (1-α) * Tour_Based_Score
   ```
   Với `α = 0.5` (cân bằng)

**Ví dụ**:
```
Tour 2:
- User-Based Score = 0.586
- Tour-Based Score = 0.707
- Final Score = 0.5 * 0.586 + 0.5 * 0.707 = 0.647
```

---

## 5. Advanced Features

### 5.1. Time Decay (Suy Giảm Theo Thời Gian)

**Mục đích**: Interactions gần đây quan trọng hơn interactions cũ.

**Công thức**:
```
Decay_Factor = 2^(-days_ago / half_life_days)
```

**Ví dụ** (half_life = 30 days):
```
Interaction 1 ngày trước: decay = 2^(-1/30) = 0.977
Interaction 30 ngày trước: decay = 2^(-30/30) = 0.5
Interaction 60 ngày trước: decay = 2^(-60/30) = 0.25
```

**Áp dụng**: `Final_Score = Original_Score * Decay_Factor`

### 5.2. Diversity (Đa Dạng Hóa)

**Mục đích**: Tránh recommend các tours quá giống nhau.

**Phương pháp**: Maximal Marginal Relevance (MMR)
```
MMR_Score = λ * Relevance - (1-λ) * Max_Similarity_To_Selected
```

**Cách làm**:
1. Chọn tour có relevance cao nhất
2. Với mỗi tour tiếp theo:
   - Tính similarity với tours đã chọn
   - Giảm score nếu quá giống
3. Lặp lại cho đến khi đủ N tours

### 5.3. Explanation (Giải Thích)

**Mục đích**: Giải thích tại sao recommend tour này.

**Cách làm**:
- User-Based: "Vì users tương tự bạn đã thích tour này"
- Tour-Based: "Vì tour này tương tự với tours bạn đã xem"
- Co-occurrence: "Vì users đã xem cùng tours với bạn cũng xem tour này"

### 5.4. Cold Start Handling

**Vấn đề**: User mới hoặc tour mới không có đủ data.

**Giải pháp**:
- **New User**: Recommend popular tours (tours được xem nhiều nhất)
- **New Tour**: Recommend cho users đã xem tours cùng category

---

## 6. Quy Trình Hoàn Chỉnh

### Bước 1: Build Matrix
```
Interactions → Raw Matrix → Preprocessing → Normalized Matrix
```

### Bước 2: Tính Similarity
```
User-Based: Cosine(Matrix) → User Similarity Matrix
Tour-Based: Cosine(Matrix^T) → Tour Similarity Matrix
```

### Bước 3: Predict Scores
```
For each tour user chưa xem:
    If similarity > 0:
        Score = Weighted Average
    Else:
        Score = Co-occurrence Fallback
```

### Bước 4: Apply Advanced Features
```
If time_decay: Score *= Decay_Factor
If diversity: Apply MMR
If explanation: Add explanation text
```

### Bước 5: Denormalize (nếu đã normalize)
```
Final_Score = Normalized_Score + User_Mean
```

### Bước 6: Sort & Return Top N
```
Sort by Final_Score descending
Return top N recommendations
```

---

## 7. Ví Dụ Cụ Thể: User 11 → Tour 2

### Data:
```
User 11 → Tour 1 (score=1)
User 4 → Tour 1 (score=1)
User 4 → Tour 2 (score=1)
```

### Bước 1: Build Matrix
```
Raw Matrix:
        Tour 1  Tour 2
User 4    1       1
User 11   1       0
```

### Bước 2: Normalize (nếu enabled)
```
User 4 Mean = 1.0 → Normalized: [0, 0]
User 11 Mean = 0.5 → Normalized: [0.5, -0.5]
```

**⚠️ Lưu ý**: Sau normalize, User 11 không còn interacted tours trong normalized matrix!
→ **Phải dùng raw matrix cho fallback**

### Bước 3: Tính User Similarity
```
User 11 vs User 4:
- Dot Product = 0.5*0 + (-0.5)*0 = 0
- Similarity = 0 / (||User 11|| * ||User 4||) = 0
```

**Vấn đề**: Similarity = 0 → Không thể dùng weighted average!

### Bước 4: Fallback Logic
```
1. Tìm tours User 11 đã xem (dùng raw matrix):
   → Tour 1 (score=1)

2. Tìm users đã xem Tour 1:
   → User 4

3. User 4 có xem Tour 2 không?
   → Có (score=1)

4. Tính co-occurrence score:
   Co_Score = mean([1]) * count([1]) = 1.0 * 1 = 1.0
   Predicted_Score = 1.0 / 1 = 1.0
```

### Bước 5: Return Recommendation
```
Tour 2: Predicted Score = 1.0
→ Recommend Tour 2 cho User 11 ✅
```

---

## 8. Tối Ưu Hiệu Suất

### 8.1. Caching
- Cache user-tour matrix với TTL
- Cache similarity matrices
- Hash-based invalidation khi data thay đổi

### 8.2. Lazy Loading
- Chỉ build matrix khi cần
- Chỉ tính similarity khi cần

### 8.3. Batch Processing
- Xử lý recommendations cho nhiều users cùng lúc
- Giảm số lần query database

---

## 9. Kết Luận

Thuật toán Collaborative Filtering hoạt động dựa trên nguyên lý:
- **"Users tương tự sẽ thích những thứ tương tự"**
- **"Tours tương tự sẽ được users tương tự thích"**

Với data sparse, fallback logic đảm bảo vẫn có recommendations dựa trên co-occurrence patterns.

**Điểm mạnh**:
- Không cần thông tin về tours (chỉ cần interactions)
- Có thể phát hiện patterns ẩn
- Fallback logic xử lý được cold start

**Điểm yếu**:
- Cần nhiều data để hoạt động tốt
- Khó xử lý khi data quá sparse
- Tính toán phức tạp với dataset lớn

