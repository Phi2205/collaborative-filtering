# Công Thức Tính Toán - Hệ Thống Recommendation

Tài liệu này mô tả chi tiết các công thức toán học được sử dụng trong hệ thống Collaborative Filtering, kèm ví dụ tính toán cụ thể.

---

## Mục Lục

1. [Hệ Thống Điểm Số (Scoring System)](#1-hệ-thống-điểm-số-scoring-system)
2. [Time Decay (Phân Rã Theo Thời Gian)](#2-time-decay-phân-rã-theo-thời-gian)
3. [Xử Lý Outliers (IQR Method)](#3-xử-lý-outliers-iqr-method)
4. [Normalization (Mean Centering)](#4-normalization-mean-centering)
5. [Cosine Similarity](#5-cosine-similarity)
6. [User-Based Collaborative Filtering](#6-user-based-collaborative-filtering)
7. [Tour-Based Collaborative Filtering](#7-tour-based-collaborative-filtering)
8. [Hybrid Collaborative Filtering](#8-hybrid-collaborative-filtering)
9. [Diversity (Maximal Marginal Relevance - MMR)](#9-diversity-maximal-marginal-relevance-mmr)
10. [Fallback Co-occurrence Logic](#10-fallback-co-occurrence-logic)
11. [Filtering Tours Đã Xem (Loại Bỏ Hoàn Toàn)](#11-filtering-tours-đã-xem-loại-bỏ-hoàn-toàn)
12. [Ví Dụ Tính Toán Đầy Đủ](#12-ví-dụ-tính-toán-đầy-đủ)

---

## 1. Hệ Thống Điểm Số (Scoring System)

### Công Thức

Mỗi loại tương tác được gán một điểm số cố định:

```
view/click:        score = 1.0
rating_5:          score = 4.0
rating_4:          score = 3.0
rating_3:          score = 1.0
rating_2:          score = -1.0
rating_1:          score = -3.0
book/booking:      score = 5.0
paid:              score = 6.0
favorite:          score = 2.0
review:            score = 3.0
```

### Ví Dụ

- User xem tour → `score = 1.0`
- User đánh giá 5 sao → `score = 4.0`
- User đặt tour → `score = 5.0`
- User thanh toán → `score = 6.0`

---

## 2. Time Decay (Phân Rã Theo Thời Gian)

### Công Thức

Time decay giúp tăng trọng số cho các tương tác gần đây:

```
decay_factor = exp(-days_ago / half_life_days)
weighted_score = raw_score × decay_factor
```

Trong đó:
- `days_ago`: Số ngày từ lúc tương tác đến hiện tại
- `half_life_days`: Thời gian để giảm 50% trọng số (mặc định: 30 ngày)
- `decay_factor`: Hệ số phân rã (tối thiểu 0.1)

### Ví Dụ Tính Toán

**Giả sử:**
- `half_life_days = 30`
- Tương tác cách đây 20 ngày với `raw_score = 5.0`

**Tính toán:**
```
days_ago = 20
decay_factor = exp(-20 / 30) = exp(-0.667) ≈ 0.513
weighted_score = 5.0 × 0.513 ≈ 2.57
```

**Bảng tham khảo:**
| Ngày trước | Decay Factor | Score gốc | Score sau decay |
|------------|--------------|-----------|------------------|
| 0          | 1.000        | 5.0       | 5.00             |
| 7          | 0.790        | 5.0       | 3.95             |
| 15         | 0.607        | 5.0       | 3.04             |
| 30         | 0.368        | 5.0       | 1.84             |
| 60         | 0.135        | 5.0       | 0.68             |

---

## 3. Xử Lý Outliers (IQR Method)

### Công Thức

Sử dụng phương pháp Interquartile Range (IQR) để phát hiện và giới hạn outliers:

```
Q1 = percentile(values, 25)
Q3 = percentile(values, 75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 × IQR
upper_bound = Q3 + 1.5 × IQR

# Giới hạn giá trị
if value > upper_bound:
    value = upper_bound
if value < lower_bound:
    value = lower_bound
```

### Ví Dụ Tính Toán

**Giả sử các điểm số:** `[1, 2, 3, 4, 5, 6, 7, 8, 9, 50]`

**Tính toán:**
```
Q1 = percentile([1,2,3,4,5,6,7,8,9,50], 25) = 3.25
Q3 = percentile([1,2,3,4,5,6,7,8,9,50], 75) = 7.75
IQR = 7.75 - 3.25 = 4.5

lower_bound = 3.25 - 1.5 × 4.5 = -3.5
upper_bound = 7.75 + 1.5 × 4.5 = 14.5
```

**Kết quả:**
- Giá trị `50` (outlier) → được giới hạn thành `14.5`
- Các giá trị khác giữ nguyên

---

## 4. Normalization (Mean Centering)

### Công Thức

Mean centering giúp loại bỏ bias của từng user:

```
# Tính mean cho mỗi user
user_mean[i] = mean(user_ratings[i])

# Normalize
normalized_matrix[i, j] = raw_matrix[i, j] - user_mean[i]

# Denormalize (khi cần)
denormalized_score = normalized_score + user_mean[i]
```

### Ví Dụ Tính Toán

**Ma trận gốc (raw):**
```
        Tour1  Tour2  Tour3
User1:   4.0    5.0    0.0
User2:   3.0    0.0    2.0
User3:   0.0    1.0    1.0
```

**Tính mean cho mỗi user:**
```
User1_mean = (4.0 + 5.0 + 0.0) / 2 = 4.5  (chỉ tính các giá trị > 0)
User2_mean = (3.0 + 2.0) / 2 = 2.5
User3_mean = (1.0 + 1.0) / 2 = 1.0
```

**Ma trận sau normalize:**
```
        Tour1    Tour2    Tour3
User1:  -0.5     0.5      0.0
User2:   0.5     0.0     -0.5
User3:   0.0     0.0      0.0
```

**Denormalize (ví dụ cho User1, Tour1):**
```
normalized_score = -0.5
denormalized_score = -0.5 + 4.5 = 4.0
```

---

## 5. Cosine Similarity

### Công Thức

Cosine similarity đo độ tương đồng giữa hai vector:

```
cosine_similarity(A, B) = (A · B) / (||A|| × ||B||)
```

Trong đó:
- `A · B`: Dot product của hai vector
- `||A||`: Norm (độ dài) của vector A
- `||B||`: Norm (độ dài) của vector B

### Ví Dụ Tính Toán

**Vector User1:** `[4.0, 5.0, 0.0]  
**Vector User2:** `[3.0, 0.0, 2.0]`**

**Tính toán:**
```
A · B = 4.0×3.0 + 5.0×0.0 + 0.0×2.0 = 12.0

||A|| = sqrt(4.0² + 5.0² + 0.0²) = sqrt(16 + 25) = sqrt(41) ≈ 6.40
||B|| = sqrt(3.0² + 0.0² + 2.0²) = sqrt(9 + 4) = sqrt(13) ≈ 3.61

cosine_similarity = 12.0 / (6.40 × 3.61) ≈ 0.52
```

**Kết quả:** User1 và User2 có độ tương đồng **0.52** (tương đối tương đồng)

---

## 6. User-Based Collaborative Filtering

### Công Thức

Dự đoán điểm cho tour `j` của user `i` dựa trên các users tương tự:

```
predicted_score[i, j] = Σ(similarity[i, k] × rating[k, j]) / Σ|similarity[i, k]|
```

Trong đó:
- `similarity[i, k]`: Độ tương đồng giữa user `i` và user `k`
- `rating[k, j]`: Điểm của user `k` cho tour `j`
- Tổng chỉ tính trên các users `k` đã tương tác với tour `j`

**⚠️ Lưu ý quan trọng:** Tours đã xem bị **LOẠI BỎ HOÀN TOÀN** khỏi recommendations (không phải giảm điểm dần). Nếu `user_ratings[i, j] != 0` (user đã tương tác với tour), thì `predicted_score[i, j] = 0` và tour đó sẽ không xuất hiện trong danh sách gợi ý.

### Ví Dụ Tính Toán

**Dữ liệu:**
- User1 cần gợi ý Tour2
- User1 đã xem: Tour1 (4.0), Tour3 (5.0)
- User2 (tương đồng 0.8): Tour1 (3.0), Tour2 (5.0), Tour3 (4.0)
- User3 (tương đồng 0.6): Tour1 (2.0), Tour2 (4.0)

**Tính toán:**
```
predicted_score[User1, Tour2] = 
    (0.8 × 5.0 + 0.6 × 4.0) / (0.8 + 0.6)
  = (4.0 + 2.4) / 1.4
  = 6.4 / 1.4
  ≈ 4.57
```

**Kết quả:** User1 được dự đoán sẽ thích Tour2 với điểm **4.57**

---

## 7. Tour-Based Collaborative Filtering

### Công Thức

Dự đoán điểm cho tour `j` của user `i` dựa trên các tours tương tự mà user đã tương tác:

```
predicted_score[i, j] = Σ(similarity[j, k] × rating[i, k]) / Σ|similarity[j, k]|
```

Trong đó:
- `similarity[j, k]`: Độ tương đồng giữa tour `j` và tour `k`
- `rating[i, k]`: Điểm của user `i` cho tour `k`
- Tổng chỉ tính trên các tours `k` mà user `i` đã tương tác

**⚠️ Lưu ý quan trọng:** Tours đã xem bị **LOẠI BỎ HOÀN TOÀN** khỏi recommendations (không phải giảm điểm dần). Nếu `user_ratings[i, j] != 0` (user đã tương tác với tour), thì `predicted_score[i, j] = 0` và tour đó sẽ không xuất hiện trong danh sách gợi ý.

### Ví Dụ Tính Toán

**Dữ liệu:**
- User1 cần gợi ý Tour2
- User1 đã xem: Tour1 (4.0), Tour3 (5.0)
- Tour2 tương đồng với Tour1: 0.7
- Tour2 tương đồng với Tour3: 0.5

**Tính toán:**
```
predicted_score[User1, Tour2] = 
    (0.7 × 4.0 + 0.5 × 5.0) / (0.7 + 0.5)
  = (2.8 + 2.5) / 1.2
  = 5.3 / 1.2
  ≈ 4.42
```

**Kết quả:** User1 được dự đoán sẽ thích Tour2 với điểm **4.42**

---

## 8. Hybrid Collaborative Filtering

### Công Thức

Kết hợp User-Based và Tour-Based:

```
hybrid_score = α × user_based_score + (1 - α) × tour_based_score
```

Trong đó:
- `α`: Trọng số cho User-Based (mặc định: 0.5)
- `user_based_score`: Điểm từ User-Based
- `tour_based_score`: Điểm từ Tour-Based

### Ví Dụ Tính Toán

**Dữ liệu:**
- User-Based score: 4.57
- Tour-Based score: 4.42
- `α = 0.5`

**Tính toán:**
```
hybrid_score = 0.5 × 4.57 + 0.5 × 4.42
            = 2.285 + 2.21
            = 4.495
```

**Kết quả:** Hybrid score là **4.495**

---

## 9. Diversity (Maximal Marginal Relevance - MMR)

### Công Thức

MMR đảm bảo recommendations đa dạng, không quá giống nhau:

```
MMR(tour) = λ × relevance(tour) - (1 - λ) × max_similarity(tour, selected_tours)
```

Trong đó:
- `λ = 1 - diversity_weight` (mặc định: `diversity_weight = 0.3`, nên `λ = 0.7`)
- `relevance(tour)`: Điểm dự đoán của tour
- `max_similarity(tour, selected_tours)`: Độ tương đồng tối đa với các tours đã chọn

### Ví Dụ Tính Toán

**Dữ liệu:**
- Tour A: `relevance = 5.0`, `max_similarity = 0.9` (rất giống tours đã chọn)
- Tour B: `relevance = 4.5`, `max_similarity = 0.3` (ít giống tours đã chọn)
- `diversity_weight = 0.3`, nên `λ = 0.7`

**Tính toán:**
```
MMR(Tour A) = 0.7 × 5.0 - 0.3 × 0.9
            = 3.5 - 0.27
            = 3.23

MMR(Tour B) = 0.7 × 4.5 - 0.3 × 0.3
            = 3.15 - 0.09
            = 3.06
```

**Kết quả:** Mặc dù Tour A có relevance cao hơn, nhưng Tour B có MMR gần bằng (3.06 vs 3.23), và vì Tour B đa dạng hơn nên có thể được ưu tiên.

---

## 10. Fallback Co-occurrence Logic

### Công Thức

Khi User-Based hoặc Tour-Based không có đủ dữ liệu (similarity = 0), hệ thống sử dụng logic co-occurrence:

```
co_occurrence_score[tour_j] = 
    Σ(mean_rating(users_who_saw_tour_i_and_tour_j) × count) / count(interacted_tours)
```

Trong đó:
- `users_who_saw_tour_i_and_tour_j`: Users đã xem cả tour `i` (user đã xem) và tour `j` (tour cần gợi ý)
- `mean_rating`: Điểm trung bình của các users này cho tour `j`
- `count`: Số lượng users
- Tổng tính trên tất cả các tours `i` mà user đã tương tác

### Ví Dụ Tính Toán

**Dữ liệu:**
- User1 đã xem: Tour1
- Cần gợi ý: Tour2
- User2 đã xem Tour1 và Tour2 (rating Tour2 = 5.0)
- User3 đã xem Tour1 và Tour2 (rating Tour2 = 4.0)

**Tính toán:**
```
co_occurrence_score[Tour2] = 
    mean([5.0, 4.0]) × 2 / 1
  = 4.5 × 2 / 1
  = 9.0
```

**Kết quả:** Tour2 có co-occurrence score là **9.0**

---

## 11. Filtering Tours Đã Xem (Loại Bỏ Hoàn Toàn)

### Cơ Chế

Hệ thống **KHÔNG** giảm điểm dần cho tours đã xem. Thay vào đó, **tours đã xem bị loại bỏ hoàn toàn** khỏi danh sách recommendations.

### Công Thức Logic

```python
# Chỉ tính điểm cho tours user CHƯA tương tác
if user_ratings[tour_idx] == 0:  # Chưa tương tác
    predicted_scores[tour_idx] = calculate_score(...)  # Tính điểm
else:  # Đã tương tác (view, book, paid, rating, ...)
    predicted_scores[tour_idx] = 0  # Loại bỏ hoàn toàn
```

### Ví Dụ

**Tình huống:**
- User1 đã xem Tour1 (score = 4.0)
- User1 đã book Tour2 (score = 5.0)
- User1 chưa xem Tour3

**Kết quả:**
- Tour1: `predicted_score = 0` → **KHÔNG** xuất hiện trong recommendations
- Tour2: `predicted_score = 0` → **KHÔNG** xuất hiện trong recommendations
- Tour3: `predicted_score = 4.5` → **CÓ** xuất hiện trong recommendations

### Lý Do

1. **Tránh gợi ý lại:** User đã xem/book tour rồi, không cần gợi ý lại.
2. **Tập trung vào tours mới:** Chỉ gợi ý những tours user chưa biết.
3. **Tăng trải nghiệm:** User không bị làm phiền bởi những tours đã xem.

### So Sánh: Giảm Điểm vs Loại Bỏ

| Phương Pháp | Cách Hoạt Động | Ưu Điểm | Nhược Điểm |
|-------------|----------------|---------|------------|
| **Giảm điểm dần** | Tours đã xem vẫn có điểm, nhưng thấp hơn | Có thể gợi ý lại nếu user muốn xem lại | Làm phiền user với tours đã xem |
| **Loại bỏ hoàn toàn** (hiện tại) | Tours đã xem có điểm = 0, không xuất hiện | Tập trung vào tours mới, trải nghiệm tốt hơn | Không thể gợi ý lại tours đã xem |

**Hệ thống hiện tại sử dụng phương pháp "Loại bỏ hoàn toàn".**

### ⚠️ Vấn Đề: Vĩnh Viễn Không Gợi Ý Lại

**Hiện tại:** Một khi user đã có bất kỳ tương tác nào với tour (view, book, paid, rating), tour đó sẽ **VĨNH VIỄN** không xuất hiện trong recommendations nữa.

**Vấn đề này có thể gây ra:**
1. **User chỉ "view" nhưng muốn book lại:** User xem tour nhưng chưa book, sau đó muốn tìm lại để book → không tìm thấy trong recommendations.
2. **User muốn book lại tour đã từng xem:** Tour phù hợp nhưng đã xem trước đó → không được gợi ý.
3. **Không có cơ hội "rediscovery":** Tours tốt nhưng đã xem lâu rồi không được gợi ý lại.

### 💡 Giải Pháp Đề Xuất

Có thể cải thiện bằng các cách sau:

#### **Giải pháp 1: Chỉ loại bỏ tours đã "paid"**
```python
# Chỉ loại bỏ tours đã thanh toán (paid)
if user_ratings[tour_idx] == 0 or is_paid_only(tour_idx):
    predicted_scores[tour_idx] = calculate_score(...)
```
- ✅ Cho phép gợi ý lại tours chỉ "view" hoặc "book" nhưng chưa "paid"
- ✅ Vẫn loại bỏ tours đã thanh toán (không cần book lại)

#### **Giải pháp 2: Time-based re-recommendation**
```python
# Gợi ý lại tours đã xem sau một thời gian (ví dụ: 90 ngày)
if user_ratings[tour_idx] == 0 or is_old_interaction(tour_idx, days=90):
    predicted_scores[tour_idx] = calculate_score(...)
```
- ✅ Cho phép "rediscovery" sau một thời gian
- ✅ Tours cũ có thể được gợi ý lại nếu vẫn phù hợp

#### **Giải pháp 3: Giảm điểm thay vì loại bỏ**
```python
# Giảm điểm cho tours đã xem thay vì loại bỏ hoàn toàn
if user_ratings[tour_idx] == 0:
    predicted_scores[tour_idx] = calculate_score(...)
else:
    # Giảm điểm dựa trên loại tương tác
    penalty = get_interaction_penalty(user_ratings[tour_idx])
    predicted_scores[tour_idx] = calculate_score(...) * penalty
```
- ✅ Vẫn có thể gợi ý lại nhưng với điểm thấp hơn
- ✅ Tours đã "paid" có penalty cao nhất (gần như loại bỏ)

#### **Giải pháp 4: Filter theo loại tương tác**
```python
# Chỉ loại bỏ tours đã "paid" hoặc "book"
interaction_type = get_interaction_type(user_id, tour_idx)
if interaction_type not in ['paid', 'book']:
    predicted_scores[tour_idx] = calculate_score(...)
```
- ✅ Cho phép gợi ý lại tours chỉ "view"
- ✅ Loại bỏ tours đã "book" hoặc "paid"

### 📊 So Sánh Các Giải Pháp

| Giải Pháp | Tours "view" | Tours "book" | Tours "paid" | Độ Phức Tạp |
|-----------|--------------|--------------|--------------|--------------|
| **Hiện tại (Loại bỏ hoàn toàn)** | ❌ Không gợi ý | ❌ Không gợi ý | ❌ Không gợi ý | ⭐ Đơn giản |
| **Chỉ loại bỏ "paid"** | ✅ Có gợi ý | ✅ Có gợi ý | ❌ Không gợi ý | ⭐⭐ Trung bình |
| **Time-based (90 ngày)** | ✅ Có gợi ý lại | ✅ Có gợi ý lại | ✅ Có gợi ý lại | ⭐⭐⭐ Phức tạp |
| **Giảm điểm** | ✅ Gợi ý (điểm thấp) | ✅ Gợi ý (điểm thấp) | ✅ Gợi ý (điểm rất thấp) | ⭐⭐⭐ Phức tạp |
| **Filter theo loại** | ✅ Có gợi ý | ❌ Không gợi ý | ❌ Không gợi ý | ⭐⭐ Trung bình |

### 🎯 Khuyến Nghị

**Nên sử dụng "Giải pháp 1" hoặc "Giải pháp 4":**
- ✅ Đơn giản, dễ implement
- ✅ Cho phép gợi ý lại tours chỉ "view" (user có thể muốn book)
- ✅ Vẫn loại bỏ tours đã "paid" (không cần book lại)
- ✅ Cân bằng giữa trải nghiệm và logic nghiệp vụ

---

## 12. Ví Dụ Tính Toán Đầy Đủ

### Tình Huống

**3 Tours:** T1 (Đà Nẵng), T2 (Nha Trang), T3 (Đà Lạt)  
**2 Users:** U1 (cần gợi ý), U2 (user tham chiếu)

**Tương tác:**
- U1: 20 ngày trước view T1 → score_raw = 1.0
- U1: 7 ngày trước book T1 → score_raw = 5.0
- U2: 5 ngày trước rating 4* T1 → score_raw = 3.0
- U2: 2 ngày trước paid T2 → score_raw = 6.0

**Tham số:**
- `half_life_days = 30`
- `diversity_weight = 0.3`

### Bước 1: Tính Time Decay và Ma Trận Gốc

**U1 - T1:**
```
decay_1 = exp(-20/30) ≈ 0.513 → weighted = 1.0 × 0.513 ≈ 0.51
decay_2 = exp(-7/30) ≈ 0.790 → weighted = 5.0 × 0.790 ≈ 3.95
Tổng U1-T1 = 0.51 + 3.95 = 4.46
```

**U2 - T1:**
```
decay = exp(-5/30) ≈ 0.850 → weighted = 3.0 × 0.850 ≈ 2.55
```

**U2 - T2:**
```
decay = exp(-2/30) ≈ 0.935 → weighted = 6.0 × 0.935 ≈ 5.61
```

**Ma trận gốc (raw):**
```
        T1     T2     T3
U1:   4.46   0.00   0.00
U2:   2.55   5.61   0.00
```

### Bước 2: Normalization (Mean Centering)

**Tính mean:**
```
U1_mean = 4.46 / 1 = 4.46
U2_mean = (2.55 + 5.61) / 2 = 4.08
```

**Ma trận normalized:**
```
        T1      T2      T3
U1:   0.00   0.00    0.00  (4.46 - 4.46 = 0)
U2:  -1.53   1.53    0.00  (2.55 - 4.08 = -1.53, 5.61 - 4.08 = 1.53)
```

### Bước 3: Tính User Similarity

**Cosine similarity giữa U1 và U2:**
```
U1 = [0.00, 0.00, 0.00]
U2 = [-1.53, 1.53, 0.00]

U1 · U2 = 0.00×(-1.53) + 0.00×1.53 + 0.00×0.00 = 0.00
||U1|| = 0.00
||U2|| = sqrt((-1.53)² + 1.53²) = sqrt(4.68) ≈ 2.16

similarity = 0.00 / (0.00 × 2.16) = undefined (0/0)
```

**Vấn đề:** U1 có vector toàn 0 → similarity không tính được → **chuyển sang Fallback**

### Bước 4: Fallback Co-occurrence

**U1 đã xem T1, cần gợi ý T2:**
```
U2 đã xem cả T1 và T2 (rating T2 = 5.61)

co_occurrence_score[T2] = 
    mean([5.61]) × 1 / 1
  = 5.61
```

**Kết quả:** T2 được gợi ý với điểm **5.61**

### Bước 5: Tour-Based CF (Thay Thế)

**Tính tour similarity (dùng ma trận raw):**
```
T1 = [4.46, 2.55]
T2 = [0.00, 5.61]

T1 · T2 = 4.46×0.00 + 2.55×5.61 = 14.31
||T1|| = sqrt(4.46² + 2.55²) = sqrt(19.90 + 6.50) = sqrt(26.40) ≈ 5.14
||T2|| = 5.61

similarity(T2, T1) = 14.31 / (5.14 × 5.61) ≈ 0.50
```

**Dự đoán cho U1 - T2:**
```
U1 đã xem T1 với điểm 4.46 (raw)

predicted_score = similarity × rating
                 = 0.50 × 4.46
                 ≈ 2.23
```

**Denormalize:**
```
denormalized = 2.23 + 4.46 = 6.69
```

### Bước 6: Hybrid (Nếu Áp Dụng)

**Kết hợp:**
```
user_based_score = 5.61 (từ fallback)
tour_based_score = 6.69
α = 0.5

hybrid_score = 0.5 × 5.61 + 0.5 × 6.69
            = 2.805 + 3.345
            = 6.15
```

### Kết Quả Cuối Cùng

**Recommendations cho U1:**
1. **T2 (Nha Trang)** - Score: **6.15** (hybrid) hoặc **5.61** (user-based fallback)
2. T3 không được gợi ý vì không có dữ liệu liên quan

---

## Tóm Tắt Các Công Thức

| Công Thức | Mục Đích | Công Thức Toán Học |
|-----------|----------|-------------------|
| **Time Decay** | Tăng trọng số cho tương tác gần đây | `decay = exp(-days/half_life)` |
| **Normalization** | Loại bỏ bias của user | `normalized = raw - user_mean` |
| **Cosine Similarity** | Đo độ tương đồng | `cos(A,B) = (A·B)/(\|A\|\|B\|)` |
| **User-Based CF** | Dự đoán dựa trên users tương tự | `pred = Σ(sim×rating)/Σ\|sim\|` |
| **Tour-Based CF** | Dự đoán dựa trên tours tương tự | `pred = Σ(sim×rating)/Σ\|sim\|` |
| **Hybrid CF** | Kết hợp User và Tour | `hybrid = α×user + (1-α)×tour` |
| **MMR (Diversity)** | Đảm bảo đa dạng | `MMR = λ×rel - (1-λ)×max_sim` |
| **Co-occurrence** | Fallback khi thiếu dữ liệu | `score = mean(rating)×count/count_tours` |

---

## Lưu Ý Quan Trọng

1. **Tours đã xem bị loại bỏ hoàn toàn:** Hệ thống **KHÔNG** giảm điểm dần cho tours đã xem. Thay vào đó, nếu user đã tương tác với tour (view, book, paid, rating), tour đó sẽ có `predicted_score = 0` và **KHÔNG xuất hiện** trong danh sách recommendations. Logic này được áp dụng ở cả User-Based và Tour-Based CF:
   ```python
   if user_ratings[tour_idx] == 0:  # Chỉ tính điểm cho tours chưa tương tác
       predicted_scores[tour_idx] = ...  # Tính điểm
   # Nếu != 0 (đã tương tác), predicted_scores[tour_idx] = 0 (mặc định)
   ```

2. **Normalization có thể làm mất thông tin:** Khi user chỉ có 1 interaction, vector normalized có thể thành toàn 0 → cần dùng raw matrix cho fallback.

3. **Time Decay giảm dần theo thời gian:** Tương tác càng cũ, trọng số càng thấp. Tuy nhiên, điều này chỉ ảnh hưởng đến việc tính điểm trong ma trận, không ảnh hưởng đến việc loại bỏ tours đã xem.

4. **Diversity giảm điểm cho tours quá giống nhau:** Giúp recommendations đa dạng hơn.

5. **Fallback logic quan trọng:** Khi dữ liệu sparse, co-occurrence giúp vẫn có recommendations.

6. **Denormalize trước khi trả về:** Điểm cuối cùng phải được denormalize để có ý nghĩa thực tế.

---

*Tài liệu này được tạo tự động dựa trên code trong `app/services/collaborative_filtering.py`*


