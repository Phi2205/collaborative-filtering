import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.scoring import get_interaction_score
from datetime import datetime, timezone, timedelta
import warnings
import hashlib
import pickle
from functools import lru_cache
import threading

class CollaborativeFiltering:
    def __init__(
        self, 
        db: Session, 
        normalize: bool = True, 
        handle_sparse: bool = True, 
        remove_outliers: bool = True,
        use_time_decay: bool = True,
        time_decay_half_life_days: int = 30,
        use_diversity: bool = True,
        diversity_weight: float = 0.3,
        enable_explanation: bool = True,
        enable_caching: bool = True,
        cache_ttl_seconds: int = 3600
    ):
        """
        Collaborative Filtering với Data Preprocessing và Advanced Features
        
        Args:
            db: Database session
            normalize: Có normalize matrix không (mean centering)
            handle_sparse: Có xử lý sparse data không
            remove_outliers: Có loại bỏ outliers không
            use_time_decay: Có áp dụng time decay không (interactions gần đây quan trọng hơn)
            time_decay_half_life_days: Số ngày để giảm 50% trọng số (default: 30 days)
            use_diversity: Có áp dụng diversity không (tránh recommend quá giống nhau)
            diversity_weight: Trọng số diversity (0-1, default: 0.3)
            enable_explanation: Có tạo explanation không
            enable_caching: Có enable caching không (default: True)
            cache_ttl_seconds: Cache TTL trong giây (default: 3600 = 1 hour)
        """
        self.db = db
        self.user_tour_matrix = None  # Ma trận User-Tour
        self.user_tour_matrix_raw = None  # Ma trận gốc (chưa normalize)
        self.user_similarity = None
        self.tour_similarity = None  # Item similarity -> Tour similarity
        self.user_ids = None
        self.tour_ids = None  # item_ids -> tour_ids
        self.user_id_to_idx = None
        self.tour_id_to_idx = None  # item_id_to_idx -> tour_id_to_idx
        
        # Preprocessing flags
        self.normalize = normalize
        self.handle_sparse = handle_sparse
        self.remove_outliers = remove_outliers
        
        # Advanced Features flags
        self.use_time_decay = use_time_decay
        self.time_decay_half_life_days = time_decay_half_life_days
        self.use_diversity = use_diversity
        self.diversity_weight = diversity_weight
        self.enable_explanation = enable_explanation
        
        # Statistics for preprocessing
        self.user_means = None  # Mean của mỗi user (để denormalize)
        self.tour_means = None  # Mean của mỗi tour
        self.global_mean = None  # Global mean
        self.sparsity_threshold = 0.95  # Nếu > 95% là 0, coi là quá sparse
        
        # Cache for interactions with timestamps
        self.interactions_cache = None
        
        # Performance Optimization
        self.enable_caching = enable_caching
        self.cache_ttl_seconds = cache_ttl_seconds
        self._matrix_hash = None  # Hash của matrix để invalidate cache
        self._last_matrix_build_time = None
        self._cache_lock = threading.Lock()  # Thread-safe cache
        
        # Lazy loading flags
        self._matrix_built = False
        self._user_similarity_calculated = False
        self._tour_similarity_calculated = False
        
        # Batch processing
        self.batch_size = 100  # Số users xử lý cùng lúc
    
    def build_user_tour_matrix(self, force_rebuild: bool = False) -> np.ndarray:
        """
        Xây dựng ma trận User-Tour từ database
        Rows: Users, Columns: Tours, Values: Ratings/Interactions
        
        Bao gồm các bước preprocessing:
        1. Xây dựng ma trận gốc
        2. Loại bỏ outliers (nếu enabled)
        3. Xử lý sparse data (nếu enabled)
        4. Normalize (nếu enabled)
        
        Args:
            force_rebuild: Force rebuild matrix ngay cả khi đã có cache
            
        Returns:
            User-Tour matrix
        """
        # Lazy loading: Nếu đã build và không force rebuild, trả về cached
        if not force_rebuild and self._matrix_built and self.user_tour_matrix is not None:
            # Kiểm tra cache TTL
            if self._last_matrix_build_time:
                elapsed = (datetime.now(timezone.utc) - self._last_matrix_build_time).total_seconds()
                if elapsed < self.cache_ttl_seconds:
                    return self.user_tour_matrix
        
        # Check if data has changed (simple hash-based invalidation)
        if self.enable_caching and not force_rebuild:
            current_hash = self._get_data_hash()
            if current_hash == self._matrix_hash and self.user_tour_matrix is not None:
                return self.user_tour_matrix
            self._matrix_hash = current_hash
        # Lấy tất cả interactions
        interactions = self.db.query(UserTourInteraction).all()
        
        # Lấy danh sách unique users và tours
        users = self.db.query(UserProfile).all()
        tours = self.db.query(Tour).filter(
            Tour.is_active == True, 
            Tour.is_approved == True, 
            Tour.is_banned == False
        ).all()
        
        if not users or not tours:
            return np.array([])
        
        user_ids = [u.id for u in users]
        tour_ids = [t.id for t in tours]
        
        # Tạo ma trận
        matrix = np.zeros((len(user_ids), len(tour_ids)))
        user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        tour_id_to_idx = {tid: idx for idx, tid in enumerate(tour_ids)}
        
        # Lưu interactions để dùng cho time decay và explanation
        self.interactions_cache = {}
        
        # Điền dữ liệu vào ma trận
        for interaction in interactions:
            if interaction.user_id in user_id_to_idx and interaction.tour_id in tour_id_to_idx:
                user_idx = user_id_to_idx[interaction.user_id]
                tour_idx = tour_id_to_idx[interaction.tour_id]
                
                # Tính score với time decay nếu enabled
                base_score = float(interaction.score)
                
                if self.use_time_decay and interaction.created_at:
                    time_decay_factor = self._calculate_time_decay(interaction.created_at)
                    score = base_score * time_decay_factor
                else:
                    score = base_score
                
                # Nếu đã có interaction trước đó, lấy max (giữ interaction quan trọng nhất)
                if matrix[user_idx, tour_idx] > 0:
                    matrix[user_idx, tour_idx] = max(matrix[user_idx, tour_idx], score)
                else:
                    matrix[user_idx, tour_idx] = score
                
                # Lưu interaction info cho explanation
                key = (interaction.user_id, interaction.tour_id)
                if key not in self.interactions_cache:
                    self.interactions_cache[key] = []
                self.interactions_cache[key].append({
                    'type': interaction.interaction_type,
                    'score': base_score,
                    'created_at': interaction.created_at
                })
        
        # Lưu ma trận gốc
        self.user_tour_matrix_raw = matrix.copy()
        self.user_ids = user_ids
        self.tour_ids = tour_ids
        self.user_id_to_idx = user_id_to_idx
        self.tour_id_to_idx = tour_id_to_idx
        
        # Apply preprocessing
        matrix = self._preprocess_matrix(matrix)
        
        self.user_tour_matrix = matrix
        self._matrix_built = True
        self._last_matrix_build_time = datetime.now(timezone.utc)
        
        # Invalidate similarity caches khi matrix thay đổi
        self._user_similarity_calculated = False
        self._tour_similarity_calculated = False
        self.user_similarity = None
        self.tour_similarity = None
        
        return matrix
    
    def _get_data_hash(self) -> Optional[str]:
        """
        Tính hash của dữ liệu để detect changes
        Sử dụng để invalidate cache khi data thay đổi
        
        Returns:
            Hash string của dữ liệu
        """
        try:
            # Lấy count của interactions và tours để tạo hash
            interactions_count = self.db.query(UserTourInteraction).count()
            tours_count = self.db.query(Tour).filter(
                Tour.is_active == True,
                Tour.is_approved == True,
                Tour.is_banned == False
            ).count()
            users_count = self.db.query(UserProfile).count()
            
            # Lấy latest interaction timestamp
            latest_interaction = self.db.query(UserTourInteraction).order_by(
                UserTourInteraction.created_at.desc()
            ).first()
            latest_timestamp = latest_interaction.created_at.isoformat() if latest_interaction and latest_interaction.created_at else ""
            
            # Tạo hash từ counts và timestamp
            hash_data = f"{interactions_count}_{tours_count}_{users_count}_{latest_timestamp}"
            return hashlib.md5(hash_data.encode()).hexdigest()
        except Exception:
            return None
    
    def _preprocess_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """
        Áp dụng các bước preprocessing lên matrix
        
        Args:
            matrix: Ma trận User-Tour gốc
            
        Returns:
            Ma trận đã được preprocess
        """
        if matrix.size == 0:
            return matrix
        
        # 1. Remove outliers
        if self.remove_outliers:
            matrix = self._remove_outliers(matrix)
        
        # 2. Handle sparse data
        if self.handle_sparse:
            matrix = self._handle_sparse_data(matrix)
        
        # 3. Normalize (mean centering)
        if self.normalize:
            matrix = self._normalize_matrix(matrix)
        
        return matrix
    
    def _remove_outliers(self, matrix: np.ndarray) -> np.ndarray:
        """
        Loại bỏ outliers trong matrix
        Sử dụng IQR (Interquartile Range) method
        
        Args:
            matrix: Ma trận User-Tour
            
        Returns:
            Ma trận đã loại bỏ outliers
        """
        # Chỉ xử lý các giá trị > 0 (có interactions)
        non_zero_values = matrix[matrix > 0]
        
        if len(non_zero_values) == 0:
            return matrix
        
        # Tính Q1, Q3, IQR
        q1 = np.percentile(non_zero_values, 25)
        q3 = np.percentile(non_zero_values, 75)
        iqr = q3 - q1
        
        # Tính bounds
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Cap outliers (thay vì xóa, giới hạn giá trị)
        matrix_cleaned = matrix.copy()
        matrix_cleaned[matrix_cleaned > upper_bound] = upper_bound
        matrix_cleaned[matrix_cleaned < lower_bound] = matrix_cleaned[matrix_cleaned < lower_bound]  # Giữ nguyên giá trị âm nếu có
        
        # Log số outliers đã xử lý
        outliers_count = np.sum((matrix > upper_bound) | (matrix < lower_bound))
        if outliers_count > 0:
            warnings.warn(f"Đã xử lý {outliers_count} outliers (bounds: [{lower_bound:.2f}, {upper_bound:.2f}])")
        
        return matrix_cleaned
    
    def _handle_sparse_data(self, matrix: np.ndarray) -> np.ndarray:
        """
        Xử lý sparse data
        - Loại bỏ users/tours quá sparse (ít interactions)
        - Impute missing values nếu cần
        
        Args:
            matrix: Ma trận User-Tour
            
        Returns:
            Ma trận đã xử lý sparse data
        """
        if matrix.size == 0:
            return matrix
        
        matrix_processed = matrix.copy()
        
        # Tính sparsity
        total_elements = matrix.size
        non_zero_elements = np.count_nonzero(matrix)
        sparsity = 1 - (non_zero_elements / total_elements)
        
        # Nếu quá sparse (> 95%), cảnh báo
        if sparsity > self.sparsity_threshold:
            warnings.warn(
                f"Matrix rất sparse ({sparsity*100:.1f}% là 0). "
                f"Chất lượng recommendations có thể bị ảnh hưởng."
            )
        
        # Loại bỏ users quá sparse (ít hơn 2 interactions)
        user_interaction_counts = np.count_nonzero(matrix, axis=1)
        sparse_users = user_interaction_counts < 2
        
        if np.any(sparse_users):
            sparse_user_indices = np.where(sparse_users)[0]
            # Không xóa users, chỉ đánh dấu (vì có thể cần cho cold start)
            # Thay vào đó, set interactions của họ về 0
            for user_idx in sparse_user_indices:
                matrix_processed[user_idx, :] = 0
        
        # Loại bỏ tours quá sparse (ít hơn 2 interactions)
        tour_interaction_counts = np.count_nonzero(matrix, axis=0)
        sparse_tours = tour_interaction_counts < 2
        
        if np.any(sparse_tours):
            sparse_tour_indices = np.where(sparse_tours)[0]
            # Set interactions của tours này về 0
            for tour_idx in sparse_tour_indices:
                matrix_processed[:, tour_idx] = 0
        
        return matrix_processed
    
    def _normalize_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """
        Normalize matrix bằng mean centering
        Trừ đi mean của mỗi user để giảm user bias
        
        Args:
            matrix: Ma trận User-Tour
            
        Returns:
            Ma trận đã được normalize
        """
        if matrix.size == 0:
            return matrix
        
        matrix_normalized = matrix.copy()
        
        # Tính mean của mỗi user (chỉ tính trên các giá trị > 0)
        self.user_means = np.zeros(matrix.shape[0])
        for i in range(matrix.shape[0]):
            user_ratings = matrix[i, :]
            non_zero_ratings = user_ratings[user_ratings > 0]
            if len(non_zero_ratings) > 0:
                self.user_means[i] = np.mean(non_zero_ratings)
            else:
                self.user_means[i] = 0
        
        # Mean centering: trừ đi mean của mỗi user
        for i in range(matrix.shape[0]):
            if self.user_means[i] > 0:
                # Chỉ normalize các giá trị > 0
                mask = matrix[i, :] > 0
                matrix_normalized[i, mask] = matrix[i, mask] - self.user_means[i]
        
        # Tính global mean (để có thể denormalize sau)
        non_zero_values = matrix[matrix > 0]
        self.global_mean = np.mean(non_zero_values) if len(non_zero_values) > 0 else 0
        
        return matrix_normalized
    
    def denormalize_score(self, normalized_score: float, user_id: int) -> float:
        """
        Chuyển điểm đã normalize về điểm gốc
        
        Args:
            normalized_score: Điểm đã normalize
            user_id: ID của user
            
        Returns:
            Điểm gốc (chưa normalize)
        """
        if not self.normalize or self.user_means is None:
            return normalized_score
        
        if user_id not in self.user_id_to_idx:
            return normalized_score
        
        user_idx = self.user_id_to_idx[user_id]
        user_mean = self.user_means[user_idx]
        
        return normalized_score + user_mean
    
    def calculate_user_similarity(self, force_recalculate: bool = False) -> np.ndarray:
        """
        Tính toán độ tương đồng giữa các users (User-Based CF)
        Sử dụng Cosine Similarity với caching
        
        Args:
            force_recalculate: Force tính lại ngay cả khi đã có cache
            
        Returns:
            User similarity matrix
        """
        # Lazy loading: Chỉ tính nếu chưa tính hoặc force
        if not force_recalculate and self._user_similarity_calculated and self.user_similarity is not None:
            return self.user_similarity
        
        if self.user_tour_matrix is None:
            self.build_user_tour_matrix()
        
        if self.user_tour_matrix.size == 0:
            return np.array([])
        
        # Tính cosine similarity giữa các users
        with self._cache_lock:  # Thread-safe
            self.user_similarity = cosine_similarity(self.user_tour_matrix)
            self._user_similarity_calculated = True
        
        return self.user_similarity
    
    def calculate_tour_similarity(self, force_recalculate: bool = False) -> np.ndarray:
        """
        Tính toán độ tương đồng giữa các tours (Tour-Based CF)
        Sử dụng Cosine Similarity với caching
        
        Args:
            force_recalculate: Force tính lại ngay cả khi đã có cache
            
        Returns:
            Tour similarity matrix
        """
        # Lazy loading: Chỉ tính nếu chưa tính hoặc force
        if not force_recalculate and self._tour_similarity_calculated and self.tour_similarity is not None:
            return self.tour_similarity
        
        if self.user_tour_matrix is None:
            self.build_user_tour_matrix()
        
        if self.user_tour_matrix.size == 0:
            return np.array([])
        
        # Tính cosine similarity giữa các tours (transpose matrix)
        with self._cache_lock:  # Thread-safe
            self.tour_similarity = cosine_similarity(self.user_tour_matrix.T)
            self._tour_similarity_calculated = True
        
        return self.tour_similarity
    
    def user_based_recommendations(
        self, 
        user_id: int, 
        n_recommendations: int = 10,
        n_similar_users: int = 5
    ) -> List[Dict]:
        """
        User-Based Collaborative Filtering
        Tìm users tương tự → Gợi ý items mà họ đã thích
        """
        if self.user_similarity is None:
            self.calculate_user_similarity()
        
        if not self.user_ids or user_id not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id]
        
        # Lấy top N users tương tự (loại bỏ chính user đó)
        similar_users_idx = np.argsort(self.user_similarity[user_idx])[::-1][1:n_similar_users+1]
        
        # Tính điểm dự đoán cho từng tour
        user_ratings = self.user_tour_matrix[user_idx]
        predicted_scores = np.zeros(len(self.tour_ids))
        
        for tour_idx in range(len(self.tour_ids)):
            if user_ratings[tour_idx] == 0:  # Chỉ gợi ý tours user chưa tương tác
                # Tính điểm dự đoán dựa trên users tương tự
                similar_users_ratings = self.user_tour_matrix[similar_users_idx, tour_idx]
                similar_users_sim = self.user_similarity[user_idx, similar_users_idx]
                
                # Weighted average
                if np.sum(similar_users_sim) > 0:
                    predicted_scores[tour_idx] = np.sum(
                        similar_users_ratings * similar_users_sim
                    ) / np.sum(similar_users_sim)
                else:
                    # Fallback: Co-occurrence logic khi similarity = 0
                    # Dùng raw matrix (không normalize) để tìm interacted tours
                    # Vì normalized matrix có thể làm mất interacted tours
                    raw_matrix = self.user_tour_matrix_raw if self.user_tour_matrix_raw is not None else self.user_tour_matrix
                    user_raw_ratings = raw_matrix[user_idx]
                    interacted_tours_idx = np.where(user_raw_ratings > 0)[0]
                    if len(interacted_tours_idx) > 0:
                        # Tìm users đã xem cùng tours
                        co_occurrence_score = 0
                        for interacted_tour_idx in interacted_tours_idx:
                            users_who_saw_this_tour = np.where(
                                raw_matrix[:, interacted_tour_idx] > 0
                            )[0]
                            # Loại bỏ chính user hiện tại
                            users_who_saw_this_tour = users_who_saw_this_tour[
                                users_who_saw_this_tour != user_idx
                            ]
                            # Xem những users này có xem tour hiện tại không
                            if len(users_who_saw_this_tour) > 0:
                                ratings_from_co_users = raw_matrix[
                                    users_who_saw_this_tour, tour_idx
                                ]
                                if np.sum(ratings_from_co_users) > 0:
                                    # Tính điểm dựa trên số users cùng xem và ratings
                                    co_occurrence_score += np.mean(
                                        ratings_from_co_users[ratings_from_co_users > 0]
                                    ) * len(ratings_from_co_users[ratings_from_co_users > 0])
                        
                        if co_occurrence_score > 0:
                            predicted_scores[tour_idx] = co_occurrence_score / len(interacted_tours_idx)
        
        # Lấy top N recommendations
        top_tours_idx = np.argsort(predicted_scores)[::-1][:n_recommendations * 2]  # Lấy nhiều hơn để apply diversity
        
        recommendations = []
        for tour_idx in top_tours_idx:
            if predicted_scores[tour_idx] > 0:
                tour = self.db.query(Tour).filter(Tour.id == self.tour_ids[tour_idx]).first()
                if tour:
                    # Denormalize score nếu đã normalize
                    final_score = predicted_scores[tour_idx]
                    if self.normalize:
                        final_score = self.denormalize_score(final_score, user_id)
                    
                    recommendations.append({
                        "tour_id": tour.id,
                        "tour_title": tour.title,
                        "tour_slug": tour.slug,
                        "predicted_score": float(final_score),
                        "method": "user_based_cf"
                    })
        
        # Apply diversity và explanations
        if self.use_diversity and len(recommendations) > 1:
            recommendations = self._apply_diversity(recommendations, n_recommendations)
        
        if self.enable_explanation:
            recommendations = self._add_explanations(recommendations, user_id)
        
        return recommendations[:n_recommendations]
    
    def tour_based_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10
    ) -> List[Dict]:
        """
        Tour-Based Collaborative Filtering
        Tìm tours tương tự với tours user đã tương tác
        """
        if self.tour_similarity is None:
            self.calculate_tour_similarity()
        
        if not self.user_ids or user_id not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id]
        user_ratings = self.user_tour_matrix[user_idx]
        
        # Tính điểm dự đoán cho từng tour
        predicted_scores = np.zeros(len(self.tour_ids))
        
        for tour_idx in range(len(self.tour_ids)):
            if user_ratings[tour_idx] == 0:  # Chỉ gợi ý tours user chưa tương tác
                # Tính điểm dựa trên tours user đã tương tác
                interacted_tours_idx = np.where(user_ratings > 0)[0]
                
                if len(interacted_tours_idx) > 0:
                    similarities = self.tour_similarity[tour_idx, interacted_tours_idx]
                    ratings = user_ratings[interacted_tours_idx]
                    
                    if np.sum(similarities) > 0:
                        predicted_scores[tour_idx] = np.sum(
                            similarities * ratings
                        ) / np.sum(similarities)
                    else:
                        # Fallback: Co-occurrence logic khi similarity = 0
                        # Dùng raw matrix (không normalize) để tìm interacted tours
                        raw_matrix = self.user_tour_matrix_raw if self.user_tour_matrix_raw is not None else self.user_tour_matrix
                        user_raw_ratings = raw_matrix[user_idx]
                        interacted_tours_idx_raw = np.where(user_raw_ratings > 0)[0]
                        
                        # Tìm users đã xem tours user đã xem, xem họ có xem tour này không
                        co_occurrence_score = 0
                        for interacted_tour_idx in interacted_tours_idx_raw:
                            # Tìm users đã xem tour này
                            users_who_saw_this_tour = np.where(
                                raw_matrix[:, interacted_tour_idx] > 0
                            )[0]
                            # Loại bỏ chính user hiện tại
                            users_who_saw_this_tour = users_who_saw_this_tour[
                                users_who_saw_this_tour != user_idx
                            ]
                            # Xem những users này có xem tour hiện tại không
                            if len(users_who_saw_this_tour) > 0:
                                ratings_from_co_users = raw_matrix[
                                    users_who_saw_this_tour, tour_idx
                                ]
                                if np.sum(ratings_from_co_users) > 0:
                                    # Tính điểm dựa trên số users cùng xem và ratings
                                    co_occurrence_score += np.mean(
                                        ratings_from_co_users[ratings_from_co_users > 0]
                                    ) * len(ratings_from_co_users[ratings_from_co_users > 0])
                        
                        if co_occurrence_score > 0:
                            predicted_scores[tour_idx] = co_occurrence_score / len(interacted_tours_idx)
        
        # Lấy top N recommendations
        top_tours_idx = np.argsort(predicted_scores)[::-1][:n_recommendations * 2]  # Lấy nhiều hơn để apply diversity
        
        recommendations = []
        for tour_idx in top_tours_idx:
            if predicted_scores[tour_idx] > 0:
                tour = self.db.query(Tour).filter(Tour.id == self.tour_ids[tour_idx]).first()
                if tour:
                    # Denormalize score nếu đã normalize
                    final_score = predicted_scores[tour_idx]
                    if self.normalize:
                        final_score = self.denormalize_score(final_score, user_id)
                    
                    recommendations.append({
                        "tour_id": tour.id,
                        "tour_title": tour.title,
                        "tour_slug": tour.slug,
                        "predicted_score": float(final_score),
                        "method": "tour_based_cf"
                    })
        
        # Apply diversity và explanations
        if self.use_diversity and len(recommendations) > 1:
            recommendations = self._apply_diversity(recommendations, n_recommendations)
        
        if self.enable_explanation:
            recommendations = self._add_explanations(recommendations, user_id)
        
        return recommendations[:n_recommendations]
    
    def hybrid_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 10,
        user_weight: float = 0.5
    ) -> List[Dict]:
        """
        Kết hợp User-Based và Tour-Based CF
        """
        user_based = self.user_based_recommendations(user_id, n_recommendations * 2)
        tour_based = self.tour_based_recommendations(user_id, n_recommendations * 2)
        
        # Tạo dictionary để combine scores
        combined_scores = {}
        
        for rec in user_based:
            tour_id = rec["tour_id"]
            combined_scores[tour_id] = {
                "tour_id": tour_id,
                "tour_title": rec["tour_title"],
                "tour_slug": rec["tour_slug"],
                "user_score": rec["predicted_score"],
                "tour_score": 0.0
            }
        
        for rec in tour_based:
            tour_id = rec["tour_id"]
            if tour_id in combined_scores:
                combined_scores[tour_id]["tour_score"] = rec["predicted_score"]
            else:
                combined_scores[tour_id] = {
                    "tour_id": tour_id,
                    "tour_title": rec["tour_title"],
                    "tour_slug": rec["tour_slug"],
                    "user_score": 0.0,
                    "tour_score": rec["predicted_score"]
                }
        
        # Tính điểm tổng hợp
        recommendations = []
        for tour_id, data in combined_scores.items():
            final_score = (
                user_weight * data["user_score"] + 
                (1 - user_weight) * data["tour_score"]
            )
            recommendations.append({
                "tour_id": data["tour_id"],
                "tour_title": data["tour_title"],
                "tour_slug": data["tour_slug"],
                "predicted_score": final_score,
                "method": "hybrid_cf"
            })
        
        # Sắp xếp và lấy top N
        recommendations.sort(key=lambda x: x["predicted_score"], reverse=True)
        
        # Apply diversity nếu enabled
        if self.use_diversity and len(recommendations) > 1:
            recommendations = self._apply_diversity(recommendations, n_recommendations)
        
        # Add explanations nếu enabled
        if self.enable_explanation:
            recommendations = self._add_explanations(recommendations, user_id)
        
        return recommendations[:n_recommendations]
    
    def _calculate_time_decay(self, created_at: datetime) -> float:
        """
        Tính time decay factor dựa trên thời gian
        Sử dụng exponential decay: decay = exp(-days / half_life)
        
        Args:
            created_at: Thời gian tạo interaction
            
        Returns:
            Decay factor (0-1)
        """
        if not created_at:
            return 1.0
        
        try:
            # Tính số ngày từ lúc tạo đến bây giờ
            now = datetime.now(timezone.utc)
            
            # Xử lý timezone: đảm bảo cả 2 datetime đều có timezone
            if created_at.tzinfo is None:
                # Nếu không có timezone, giả sử là UTC
                created_at_aware = created_at.replace(tzinfo=timezone.utc)
            else:
                created_at_aware = created_at
            
            # Tính số ngày
            delta = now - created_at_aware
            days_ago = delta.days + delta.seconds / 86400  # Bao gồm cả phần thập phân
            
            # Exponential decay: decay = exp(-days / half_life)
            # Với half_life = 30 days, sau 30 ngày sẽ còn 50% trọng số
            decay = np.exp(-days_ago / self.time_decay_half_life_days)
            
            # Đảm bảo decay không nhỏ hơn 0.1 (giữ ít nhất 10% trọng số)
            return max(decay, 0.1)
        except Exception as e:
            # Nếu có lỗi, trả về 1.0 (không decay)
            warnings.warn(f"Lỗi khi tính time decay: {e}. Sử dụng decay = 1.0")
            return 1.0
    
    def _apply_diversity(self, recommendations: List[Dict], n_recommendations: int) -> List[Dict]:
        """
        Áp dụng diversity để đảm bảo recommendations đa dạng
        Sử dụng Maximal Marginal Relevance (MMR)
        
        Args:
            recommendations: Danh sách recommendations
            n_recommendations: Số lượng recommendations mong muốn
            
        Returns:
            Danh sách recommendations đã được diversify
        """
        if len(recommendations) <= 1:
            return recommendations
        
        # Nếu tour_similarity chưa được tính, tính nó
        if self.tour_similarity is None:
            self.calculate_tour_similarity()
        
        if self.tour_similarity is None or self.tour_similarity.size == 0:
            return recommendations[:n_recommendations]
        
        # MMR: Chọn tours có score cao nhưng khác biệt với các tours đã chọn
        selected = []
        remaining = recommendations.copy()
        
        # Chọn tour đầu tiên (có score cao nhất)
        if remaining:
            selected.append(remaining.pop(0))
        
        # Chọn các tours tiếp theo dựa trên MMR
        while len(selected) < n_recommendations and remaining:
            best_idx = 0
            best_mmr = -float('inf')
            
            for idx, rec in enumerate(remaining):
                # Tính relevance (score)
                relevance = rec['predicted_score']
                
                # Tính max similarity với các tours đã chọn
                max_similarity = 0.0
                if selected:
                    tour_id = rec['tour_id']
                    if tour_id in self.tour_id_to_idx:
                        tour_idx = self.tour_id_to_idx[tour_id]
                        
                        for selected_rec in selected:
                            selected_tour_id = selected_rec['tour_id']
                            if selected_tour_id in self.tour_id_to_idx:
                                selected_tour_idx = self.tour_id_to_idx[selected_tour_id]
                                similarity = self.tour_similarity[tour_idx, selected_tour_idx]
                                max_similarity = max(max_similarity, similarity)
                
                # MMR = λ * relevance - (1 - λ) * max_similarity
                # Với λ = 1 - diversity_weight
                lambda_param = 1 - self.diversity_weight
                mmr = lambda_param * relevance - self.diversity_weight * max_similarity
                
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = idx
            
            # Thêm tour tốt nhất vào selected
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    def _add_explanations(self, recommendations: List[Dict], user_id: int) -> List[Dict]:
        """
        Thêm explanations cho recommendations
        Giải thích tại sao tour được recommend
        
        Args:
            recommendations: Danh sách recommendations
            user_id: ID của user
            
        Returns:
            Danh sách recommendations có thêm explanations
        """
        if not self.user_ids or user_id not in self.user_id_to_idx:
            return recommendations
        
        user_idx = self.user_id_to_idx[user_id]
        user_ratings = self.user_tour_matrix[user_idx]
        
        # Lấy tours user đã tương tác
        interacted_tours_idx = np.where(user_ratings > 0)[0]
        interacted_tour_ids = [self.tour_ids[idx] for idx in interacted_tours_idx]
        
        for rec in recommendations:
            tour_id = rec['tour_id']
            explanation_parts = []
            
            # 1. Explanation từ User-Based CF
            if self.user_similarity is not None:
                similar_users = self._get_similar_users(user_id, top_n=3)
                if similar_users:
                    similar_user_names = [f"User {uid}" for uid, _ in similar_users]
                    explanation_parts.append(
                        f"Được recommend vì {len(similar_user_names)} users tương tự "
                        f"({', '.join(similar_user_names[:2])}) đã thích tour này"
                    )
            
            # 2. Explanation từ Tour-Based CF
            if self.tour_similarity is not None and interacted_tour_ids:
                similar_tours = self._get_similar_tours(tour_id, interacted_tour_ids, top_n=2)
                if similar_tours:
                    tour_titles = [t['title'][:30] + "..." if len(t['title']) > 30 else t['title'] 
                                 for t in similar_tours]
                    explanation_parts.append(
                        f"Tương tự với các tours bạn đã xem: {', '.join(tour_titles)}"
                    )
            
            # 3. Explanation từ interactions
            if (user_id, tour_id) in self.interactions_cache:
                interactions = self.interactions_cache[(user_id, tour_id)]
                interaction_types = [i['type'] for i in interactions if i['type']]
                if interaction_types:
                    unique_types = list(set(interaction_types))
                    explanation_parts.append(
                        f"Bạn đã có {len(interactions)} tương tác với tour này "
                        f"({', '.join(unique_types[:2])})"
                    )
            
            # 4. Default explanation
            if not explanation_parts:
                explanation_parts.append("Được recommend dựa trên sở thích của bạn và users tương tự")
            
            rec['explanation'] = " | ".join(explanation_parts)
        
        return recommendations
    
    def _get_similar_users(self, user_id: int, top_n: int = 3) -> List[Tuple[int, float]]:
        """
        Lấy danh sách users tương tự
        
        Args:
            user_id: ID của user
            top_n: Số lượng users tương tự
            
        Returns:
            List of (user_id, similarity_score) tuples
        """
        if self.user_similarity is None or user_id not in self.user_id_to_idx:
            return []
        
        user_idx = self.user_id_to_idx[user_id]
        similarities = self.user_similarity[user_idx]
        
        # Lấy top N users (loại bỏ chính user đó)
        top_indices = np.argsort(similarities)[::-1][1:top_n+1]
        
        similar_users = []
        for idx in top_indices:
            if similarities[idx] > 0:
                similar_user_id = self.user_ids[idx]
                similar_users.append((similar_user_id, float(similarities[idx])))
        
        return similar_users
    
    def _get_similar_tours(self, tour_id: int, interacted_tour_ids: List[int], top_n: int = 2) -> List[Dict]:
        """
        Lấy danh sách tours tương tự với tours user đã tương tác
        
        Args:
            tour_id: ID của tour cần tìm tours tương tự
            interacted_tour_ids: Danh sách tour IDs user đã tương tác
            top_n: Số lượng tours tương tự
            
        Returns:
            List of tour dicts với title và similarity
        """
        if self.tour_similarity is None or tour_id not in self.tour_id_to_idx:
            return []
        
        tour_idx = self.tour_id_to_idx[tour_id]
        similarities = self.tour_similarity[tour_idx]
        
        # Tìm tours tương tự trong danh sách interacted tours
        similar_tours = []
        for interacted_tour_id in interacted_tour_ids:
            if interacted_tour_id in self.tour_id_to_idx:
                interacted_tour_idx = self.tour_id_to_idx[interacted_tour_id]
                similarity = similarities[interacted_tour_idx]
                
                if similarity > 0:
                    tour = self.db.query(Tour).filter(Tour.id == interacted_tour_id).first()
                    if tour:
                        similar_tours.append({
                            'id': tour.id,
                            'title': tour.title,
                            'similarity': float(similarity)
                        })
        
        # Sắp xếp theo similarity và lấy top N
        similar_tours.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_tours[:top_n]
    
    def handle_cold_start_user(self, user_id: int, n_recommendations: int = 10) -> List[Dict]:
        """
        Xử lý Cold Start cho user mới (chưa có interactions)
        Trả về top tours phổ biến nhất
        
        Args:
            user_id: ID của user mới
            n_recommendations: Số lượng recommendations
            
        Returns:
            Danh sách recommendations
        """
        # Lấy top tours phổ biến nhất (dựa trên view_count, booked_count)
        popular_tours = self.db.query(Tour).filter(
            Tour.is_active == True,
            Tour.is_approved == True,
            Tour.is_banned == False
        ).order_by(
            Tour.view_count.desc(),
            Tour.booked_count.desc()
        ).limit(n_recommendations).all()
        
        recommendations = []
        for tour in popular_tours:
            score = float(tour.view_count + tour.booked_count * 2)
            recommendations.append({
                "tour_id": tour.id,
                "tour_title": tour.title,
                "tour_slug": tour.slug,
                "predicted_score": score,
                "method": "cold_start_popular",
                "explanation": "Tour phổ biến nhất - phù hợp cho người dùng mới"
            })
        
        return recommendations
    
    def handle_cold_start_tour(self, tour_id: int, n_similar: int = 5) -> List[Dict]:
        """
        Xử lý Cold Start cho tour mới (chưa có interactions)
        Trả về tours tương tự dựa trên content features
        
        Args:
            tour_id: ID của tour mới
            n_similar: Số lượng tours tương tự
            
        Returns:
            Danh sách tours tương tự
        """
        # Lấy tour mới
        new_tour = self.db.query(Tour).filter(Tour.id == tour_id).first()
        if not new_tour:
            return []
        
        # Tìm tours tương tự dựa trên category và các features khác
        similar_tours = self.db.query(Tour).filter(
            Tour.is_active == True,
            Tour.is_approved == True,
            Tour.is_banned == False,
            Tour.tour_category_id == new_tour.tour_category_id,
            Tour.id != tour_id
        ).order_by(
            Tour.view_count.desc()
        ).limit(n_similar).all()
        
        recommendations = []
        for tour in similar_tours:
            recommendations.append({
                "tour_id": tour.id,
                "tour_title": tour.title,
                "tour_slug": tour.slug,
                "predicted_score": float(tour.view_count),
                "method": "cold_start_similar",
                "explanation": f"Tương tự với tour '{new_tour.title[:50]}...' (cùng category)"
            })
        
        return recommendations
    
    def batch_recommendations(
        self,
        user_ids: List[int],
        method: str = "hybrid",
        n_recommendations: int = 10
    ) -> Dict[int, List[Dict]]:
        """
        Batch processing: Tính recommendations cho nhiều users cùng lúc
        Tối ưu bằng cách tính similarity một lần và reuse
        
        Args:
            user_ids: Danh sách user IDs
            method: Phương pháp CF (user_based, tour_based, hybrid)
            n_recommendations: Số lượng recommendations mỗi user
            
        Returns:
            Dictionary: {user_id: [recommendations]}
        """
        # Đảm bảo matrix và similarities đã được tính
        if self.user_tour_matrix is None:
            self.build_user_tour_matrix()
        
        if method in ["user_based", "hybrid"]:
            self.calculate_user_similarity()
        
        if method in ["tour_based", "hybrid"]:
            self.calculate_tour_similarity()
        
        # Batch process users
        results = {}
        
        # Chia users thành batches
        for i in range(0, len(user_ids), self.batch_size):
            batch_user_ids = user_ids[i:i + self.batch_size]
            
            for user_id in batch_user_ids:
                try:
                    if method == "user_based":
                        recommendations = self.user_based_recommendations(user_id, n_recommendations)
                    elif method == "tour_based":
                        recommendations = self.tour_based_recommendations(user_id, n_recommendations)
                    else:  # hybrid
                        recommendations = self.hybrid_recommendations(user_id, n_recommendations)
                    
                    results[user_id] = recommendations
                except Exception as e:
                    warnings.warn(f"Lỗi khi tính recommendations cho user {user_id}: {e}")
                    results[user_id] = []
        
        return results
    
    def invalidate_cache(self):
        """
        Invalidate tất cả caches
        Sử dụng khi data thay đổi
        """
        with self._cache_lock:
            self._matrix_built = False
            self._user_similarity_calculated = False
            self._tour_similarity_calculated = False
            self.user_tour_matrix = None
            self.user_similarity = None
            self.tour_similarity = None
            self._matrix_hash = None
            self._last_matrix_build_time = None
            self.interactions_cache = None
    
    def get_cache_stats(self) -> Dict:
        """
        Lấy thống kê về cache
        
        Returns:
            Dictionary với cache statistics
        """
        stats = {
            "matrix_built": self._matrix_built,
            "user_similarity_calculated": self._user_similarity_calculated,
            "tour_similarity_calculated": self._tour_similarity_calculated,
            "cache_enabled": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds
        }
        
        if self._last_matrix_build_time:
            elapsed = (datetime.now(timezone.utc) - self._last_matrix_build_time).total_seconds()
            stats["matrix_age_seconds"] = elapsed
            stats["cache_valid"] = elapsed < self.cache_ttl_seconds
        
        if self.user_tour_matrix is not None:
            stats["matrix_shape"] = self.user_tour_matrix.shape
            stats["matrix_size_mb"] = self.user_tour_matrix.nbytes / (1024 * 1024)
        
        if self.user_similarity is not None:
            stats["user_similarity_shape"] = self.user_similarity.shape
            stats["user_similarity_size_mb"] = self.user_similarity.nbytes / (1024 * 1024)
        
        if self.tour_similarity is not None:
            stats["tour_similarity_shape"] = self.tour_similarity.shape
            stats["tour_similarity_size_mb"] = self.tour_similarity.nbytes / (1024 * 1024)
        
        return stats

