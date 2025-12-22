"""
Script để test Advanced Features
Chạy: python scripts/test_advanced_features.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.collaborative_filtering import CollaborativeFiltering
from datetime import datetime, timezone, timedelta

def test_advanced_features():
    """Test các advanced features"""
    db = SessionLocal()
    
    try:
        print("🚀 Test Advanced Features")
        print("=" * 60)
        
        # Test với advanced features enabled
        print("\n1️⃣ Test với Advanced Features ENABLED:")
        cf_advanced = CollaborativeFiltering(
            db,
            normalize=True,
            use_time_decay=True,
            time_decay_half_life_days=30,
            use_diversity=True,
            diversity_weight=0.3,
            enable_explanation=True
        )
        
        user_id = 3
        recommendations = cf_advanced.hybrid_recommendations(user_id, 5)
        
        print(f"   Recommendations cho user {user_id}:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['tour_title'][:50]}...")
            print(f"      Score: {rec['predicted_score']:.2f}")
            if 'explanation' in rec:
                print(f"      Explanation: {rec['explanation']}")
            print()
        
        # Test Time Decay
        print("\n2️⃣ Test Time Decay:")
        interaction = db.query(UserTourInteraction).first()
        if interaction and interaction.created_at:
            # Xử lý timezone
            now = datetime.now(timezone.utc)
            created_at = interaction.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            days_ago = (now - created_at).days
            decay = cf_advanced._calculate_time_decay(interaction.created_at)
            print(f"   Interaction từ {days_ago} ngày trước")
            print(f"   Time decay factor: {decay:.3f}")
            print(f"   Original score: {interaction.score}")
            print(f"   Decayed score: {interaction.score * decay:.3f}")
        
        # Test Cold Start User
        print("\n3️⃣ Test Cold Start User:")
        # Tìm user không có interactions
        all_users = db.query(UserProfile).all()
        users_with_interactions = db.query(UserTourInteraction.user_id).distinct().all()
        users_with_interactions_ids = [u[0] for u in users_with_interactions]
        
        cold_start_user = None
        for user in all_users:
            if user.id not in users_with_interactions_ids:
                cold_start_user = user
                break
        
        if cold_start_user:
            print(f"   User mới: {cold_start_user.first_name} {cold_start_user.last_name} (ID: {cold_start_user.id})")
            cold_start_recs = cf_advanced.handle_cold_start_user(cold_start_user.id, 5)
            print(f"   Recommendations: {len(cold_start_recs)}")
            for rec in cold_start_recs[:3]:
                print(f"      - {rec['tour_title'][:50]}... (score: {rec['predicted_score']:.2f})")
                if 'explanation' in rec:
                    print(f"        {rec['explanation']}")
        else:
            print("   Không tìm thấy user mới để test")
        
        # Test Diversity
        print("\n4️⃣ Test Diversity:")
        print("   Recommendations không có diversity:")
        cf_no_diversity = CollaborativeFiltering(
            db,
            use_diversity=False
        )
        recs_no_div = cf_no_diversity.hybrid_recommendations(user_id, 5)
        for rec in recs_no_div:
            print(f"      - {rec['tour_title'][:50]}...")
        
        print("\n   Recommendations có diversity:")
        recs_with_div = cf_advanced.hybrid_recommendations(user_id, 5)
        for rec in recs_with_div:
            print(f"      - {rec['tour_title'][:50]}...")
        
        print("\n✅ Test hoàn thành!")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_advanced_features()

