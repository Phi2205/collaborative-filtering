"""
Script để test Performance Optimization
Chạy: python scripts/test_performance.py
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.services.collaborative_filtering import CollaborativeFiltering

def test_performance():
    """Test performance optimizations"""
    db = SessionLocal()
    
    try:
        print("🚀 Test Performance Optimization")
        print("=" * 60)
        
        # Test 1: Caching
        print("\n1️⃣ Test Caching:")
        cf = CollaborativeFiltering(db, enable_caching=True)
        
        # Lần đầu: Build matrix
        start = time.time()
        matrix1 = cf.build_user_tour_matrix()
        time1 = time.time() - start
        print(f"   Lần đầu build matrix: {time1:.3f}s")
        
        # Lần 2: Sử dụng cache
        start = time.time()
        matrix2 = cf.build_user_tour_matrix()
        time2 = time.time() - start
        print(f"   Lần 2 (cached): {time2:.3f}s")
        print(f"   Speedup: {time1/time2:.2f}x nhanh hơn")
        
        # Test 2: Similarity caching
        print("\n2️⃣ Test Similarity Caching:")
        
        # Lần đầu: Tính similarity
        start = time.time()
        user_sim1 = cf.calculate_user_similarity()
        time1 = time.time() - start
        print(f"   Lần đầu tính user similarity: {time1:.3f}s")
        
        # Lần 2: Sử dụng cache
        start = time.time()
        user_sim2 = cf.calculate_user_similarity()
        time2 = time.time() - start
        print(f"   Lần 2 (cached): {time2:.3f}s")
        print(f"   Speedup: {time1/time2:.2f}x nhanh hơn")
        
        # Test 3: Batch Processing
        print("\n3️⃣ Test Batch Processing:")
        user_ids = [2, 3, 4, 5, 6]
        
        # Sequential processing
        start = time.time()
        sequential_results = {}
        for user_id in user_ids:
            recs = cf.hybrid_recommendations(user_id, 5)
            sequential_results[user_id] = recs
        sequential_time = time.time() - start
        print(f"   Sequential: {sequential_time:.3f}s cho {len(user_ids)} users")
        
        # Batch processing
        start = time.time()
        batch_results = cf.batch_recommendations(user_ids, "hybrid", 5)
        batch_time = time.time() - start
        print(f"   Batch: {batch_time:.3f}s cho {len(user_ids)} users")
        print(f"   Speedup: {sequential_time/batch_time:.2f}x nhanh hơn")
        
        # Test 4: Cache Stats
        print("\n4️⃣ Test Cache Stats:")
        stats = cf.get_cache_stats()
        print(f"   Matrix built: {stats['matrix_built']}")
        print(f"   User similarity calculated: {stats['user_similarity_calculated']}")
        print(f"   Tour similarity calculated: {stats['tour_similarity_calculated']}")
        if 'matrix_size_mb' in stats:
            print(f"   Matrix size: {stats['matrix_size_mb']:.2f} MB")
        if 'user_similarity_size_mb' in stats:
            print(f"   User similarity size: {stats['user_similarity_size_mb']:.2f} MB")
        if 'cache_valid' in stats:
            print(f"   Cache valid: {stats['cache_valid']}")
        
        # Test 5: Cache Invalidation
        print("\n5️⃣ Test Cache Invalidation:")
        print(f"   Trước khi invalidate: matrix_built = {cf._matrix_built}")
        cf.invalidate_cache()
        print(f"   Sau khi invalidate: matrix_built = {cf._matrix_built}")
        
        # Test 6: Lazy Loading
        print("\n6️⃣ Test Lazy Loading:")
        cf2 = CollaborativeFiltering(db)
        print(f"   Matrix built ban đầu: {cf2._matrix_built}")
        
        # Chỉ build khi cần
        start = time.time()
        recs = cf2.user_based_recommendations(3, 5)
        lazy_time = time.time() - start
        print(f"   Lazy load + recommend: {lazy_time:.3f}s")
        print(f"   Matrix built sau khi cần: {cf2._matrix_built}")
        
        print("\n✅ Test hoàn thành!")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_performance()

