"""
Script để tạo dữ liệu mẫu cho testing
Chạy: python scripts/create_sample_data.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.scoring import get_interaction_score
from datetime import datetime, timedelta, timezone
import random

def create_sample_interactions():
    """Tạo các interactions mẫu"""
    db = SessionLocal()
    
    try:
        # Lấy tất cả users và tours
        users = db.query(UserProfile).all()
        tours = db.query(Tour).filter(
            Tour.is_active == True,
            Tour.is_approved == True,
            Tour.is_banned == False
        ).all()
        
        if not users:
            print("❌ Không có users trong database. Vui lòng tạo users trước.")
            return
        
        if not tours:
            print("❌ Không có tours trong database. Vui lòng tạo tours trước.")
            return
        
        print(f"📊 Tìm thấy {len(users)} users và {len(tours)} tours")
        
        # Tạo interactions mẫu
        interaction_types = ['view', 'click', 'book', 'paid', 'rating']
        interactions_created = 0
        
        # Mỗi user sẽ có một số interactions ngẫu nhiên
        for user in users[:10]:  # Chỉ tạo cho 10 users đầu tiên
            # Mỗi user sẽ tương tác với 5-15 tours ngẫu nhiên
            num_interactions = random.randint(5, 15)
            selected_tours = random.sample(tours, min(num_interactions, len(tours)))
            
            for tour in selected_tours:
                # Chọn interaction type ngẫu nhiên
                interaction_type = random.choice(interaction_types)
                
                # Nếu là rating, tạo rating ngẫu nhiên
                rating = None
                if interaction_type == 'rating':
                    rating = random.choice([1, 2, 3, 4, 5])
                
                # Tính score
                score = int(get_interaction_score(
                    interaction_type=interaction_type,
                    rating=float(rating) if rating else None
                ))
                
                # Kiểm tra xem interaction đã tồn tại chưa
                existing = db.query(UserTourInteraction).filter(
                    UserTourInteraction.user_id == user.id,
                    UserTourInteraction.tour_id == tour.id,
                    UserTourInteraction.interaction_type == interaction_type
                ).first()
                
                if not existing:
                    # Tạo timestamp ngẫu nhiên trong 30 ngày qua
                    days_ago = random.randint(0, 30)
                    created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
                    
                    interaction = UserTourInteraction(
                        user_id=user.id,
                        tour_id=tour.id,
                        interaction_type=interaction_type,
                        score=score,  # Score đã được tính
                        created_at=created_at
                    )
                    
                    db.add(interaction)
                    interactions_created += 1
        
        db.commit()
        print(f"✅ Đã tạo {interactions_created} interactions mẫu")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Bắt đầu tạo dữ liệu mẫu...")
    create_sample_interactions()
    print("✅ Hoàn thành!")

