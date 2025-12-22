"""
Script để test Data Preprocessing
Chạy: python scripts/test_preprocessing.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.collaborative_filtering import CollaborativeFiltering
import numpy as np

def test_preprocessing():
    """Test các bước preprocessing"""
    db = SessionLocal()
    
    try:
        print("🧪 Test Data Preprocessing")
        print("=" * 60)
        
        # Test 1: Không có preprocessing
        print("\n1️⃣ Test KHÔNG có preprocessing:")
        cf_no_preprocess = CollaborativeFiltering(
            db, 
            normalize=False, 
            handle_sparse=False, 
            remove_outliers=False
        )
        matrix_no_preprocess = cf_no_preprocess.build_user_tour_matrix()
        
        if matrix_no_preprocess.size > 0:
            non_zero = np.count_nonzero(matrix_no_preprocess)
            sparsity = 1 - (non_zero / matrix_no_preprocess.size)
            print(f"   - Matrix shape: {matrix_no_preprocess.shape}")
            print(f"   - Sparsity: {sparsity*100:.1f}%")
            print(f"   - Min value: {np.min(matrix_no_preprocess[matrix_no_preprocess > 0]):.2f}")
            print(f"   - Max value: {np.max(matrix_no_preprocess):.2f}")
            print(f"   - Mean: {np.mean(matrix_no_preprocess[matrix_no_preprocess > 0]):.2f}")
        
        # Test 2: Có đầy đủ preprocessing
        print("\n2️⃣ Test CÓ đầy đủ preprocessing:")
        cf_with_preprocess = CollaborativeFiltering(
            db, 
            normalize=True, 
            handle_sparse=True, 
            remove_outliers=True
        )
        matrix_with_preprocess = cf_with_preprocess.build_user_tour_matrix()
        
        if matrix_with_preprocess.size > 0:
            non_zero = np.count_nonzero(matrix_with_preprocess)
            sparsity = 1 - (non_zero / matrix_with_preprocess.size)
            print(f"   - Matrix shape: {matrix_with_preprocess.shape}")
            print(f"   - Sparsity: {sparsity*100:.1f}%")
            print(f"   - Min value: {np.min(matrix_with_preprocess[matrix_with_preprocess != 0]):.2f}")
            print(f"   - Max value: {np.max(matrix_with_preprocess):.2f}")
            print(f"   - Mean (normalized): {np.mean(matrix_with_preprocess[matrix_with_preprocess != 0]):.2f}")
            print(f"   - User means: {len(cf_with_preprocess.user_means)} users")
            print(f"   - Global mean: {cf_with_preprocess.global_mean:.2f}")
        
        # Test 3: So sánh recommendations
        print("\n3️⃣ So sánh Recommendations:")
        user_id = 3  # User có interactions
        
        # Recommendations không có preprocessing
        recs_no_preprocess = cf_no_preprocess.hybrid_recommendations(user_id, 5)
        print(f"   Không preprocessing: {len(recs_no_preprocess)} recommendations")
        if recs_no_preprocess:
            for rec in recs_no_preprocess[:3]:
                print(f"      - {rec['tour_title'][:50]}... (score: {rec['predicted_score']:.2f})")
        
        # Recommendations có preprocessing
        recs_with_preprocess = cf_with_preprocess.hybrid_recommendations(user_id, 5)
        print(f"   Có preprocessing: {len(recs_with_preprocess)} recommendations")
        if recs_with_preprocess:
            for rec in recs_with_preprocess[:3]:
                print(f"      - {rec['tour_title'][:50]}... (score: {rec['predicted_score']:.2f})")
        
        # Test 4: Test denormalize
        print("\n4️⃣ Test Denormalize:")
        if cf_with_preprocess.normalize and user_id in cf_with_preprocess.user_id_to_idx:
            user_idx = cf_with_preprocess.user_id_to_idx[user_id]
            user_mean = cf_with_preprocess.user_means[user_idx]
            print(f"   - User {user_id} mean: {user_mean:.2f}")
            
            # Test denormalize một score
            normalized_score = 2.5
            denormalized = cf_with_preprocess.denormalize_score(normalized_score, user_id)
            print(f"   - Normalized score: {normalized_score:.2f}")
            print(f"   - Denormalized score: {denormalized:.2f}")
            print(f"   - Difference: {denormalized - normalized_score:.2f}")
        
        print("\n✅ Test hoàn thành!")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_preprocessing()

