"""
Script để debug recommendations
Chạy: python scripts/debug_recommendations.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.collaborative_filtering import CollaborativeFiltering

def debug_recommendations(user_id: int = 1):
    """Debug recommendations cho một user"""
    db = SessionLocal()
    
    try:
        print(f"🔍 Debug recommendations cho user_id = {user_id}")
        print("=" * 60)
        
        # Kiểm tra user tồn tại
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not user:
            print(f"❌ User với ID {user_id} không tồn tại")
            return
        
        print(f"✅ User: {user.first_name} {user.last_name} (ID: {user.id})")
        print()
        
        # Kiểm tra interactions của user
        user_interactions = db.query(UserTourInteraction).filter(
            UserTourInteraction.user_id == user_id
        ).all()
        
        print(f"📊 Số interactions của user: {len(user_interactions)}")
        if user_interactions:
            print("   Các interactions:")
            for i in user_interactions[:5]:  # Hiển thị 5 đầu tiên
                tour = db.query(Tour).filter(Tour.id == i.tour_id).first()
                tour_title = tour.title if tour else f"Tour ID {i.tour_id}"
                print(f"   - Tour: {tour_title} | Type: {i.interaction_type} | Score: {i.score}")
        else:
            print("   ⚠️ User chưa có interactions nào")
        print()
        
        # Kiểm tra tổng số users và tours
        total_users = db.query(UserProfile).count()
        total_tours = db.query(Tour).filter(
            Tour.is_active == True,
            Tour.is_approved == True,
            Tour.is_banned == False
        ).count()
        total_interactions = db.query(UserTourInteraction).count()
        
        print(f"📈 Tổng quan dữ liệu:")
        print(f"   - Tổng số users: {total_users}")
        print(f"   - Tổng số tours active: {total_tours}")
        print(f"   - Tổng số interactions: {total_interactions}")
        print()
        
        # Test Collaborative Filtering
        print("🧪 Test Collaborative Filtering...")
        cf = CollaborativeFiltering(db)
        
        # Build matrix
        print("   Đang build user-tour matrix...")
        matrix = cf.build_user_tour_matrix()
        
        if matrix.size == 0:
            print("   ❌ Matrix rỗng - không có dữ liệu")
            return
        
        print(f"   ✅ Matrix size: {matrix.shape} (users x tours)")
        print(f"   ✅ Số users trong matrix: {len(cf.user_ids)}")
        print(f"   ✅ Số tours trong matrix: {len(cf.tour_ids)}")
        print()
        
        # Kiểm tra user có trong matrix không
        if user_id not in cf.user_id_to_idx:
            print(f"   ❌ User {user_id} không có trong matrix")
            print(f"   💡 User này chưa có interactions")
            return
        
        user_idx = cf.user_id_to_idx[user_id]
        user_ratings = matrix[user_idx]
        interacted_tours = len([r for r in user_ratings if r > 0])
        
        print(f"   ✅ User có trong matrix (index: {user_idx})")
        print(f"   📊 User đã tương tác với {interacted_tours}/{len(cf.tour_ids)} tours")
        print()
        
        # Test recommendations
        print("🎯 Test User-Based Recommendations...")
        user_based = cf.user_based_recommendations(user_id, 10)
        print(f"   Kết quả: {len(user_based)} recommendations")
        if user_based:
            for rec in user_based[:3]:
                print(f"   - {rec['tour_title']} (score: {rec['predicted_score']:.2f})")
        print()
        
        print("🎯 Test Tour-Based Recommendations...")
        tour_based = cf.tour_based_recommendations(user_id, 10)
        print(f"   Kết quả: {len(tour_based)} recommendations")
        if tour_based:
            for rec in tour_based[:3]:
                print(f"   - {rec['tour_title']} (score: {rec['predicted_score']:.2f})")
        print()
        
        print("🎯 Test Hybrid Recommendations...")
        hybrid = cf.hybrid_recommendations(user_id, 10)
        print(f"   Kết quả: {len(hybrid)} recommendations")
        if hybrid:
            for rec in hybrid[:5]:
                print(f"   - {rec['tour_title']} (score: {rec['predicted_score']:.2f})")
        else:
            print("   ⚠️ Không có recommendations")
            print()
            print("💡 Nguyên nhân có thể:")
            print("   1. User đã tương tác với tất cả tours")
            print("   2. Không có users tương tự")
            print("   3. Không có tours tương tự")
            print("   4. Dữ liệu interactions chưa đủ")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    debug_recommendations(user_id)


