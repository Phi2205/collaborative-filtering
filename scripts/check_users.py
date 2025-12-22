"""
Script để kiểm tra users và tours trong database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserProfile, Tour, UserTourInteraction

db = SessionLocal()

try:
    # Lấy tất cả users
    users = db.query(UserProfile).limit(10).all()
    print(f"👥 Danh sách users (10 đầu tiên):")
    for user in users:
        interactions_count = db.query(UserTourInteraction).filter(
            UserTourInteraction.user_id == user.id
        ).count()
        print(f"   ID: {user.id} | {user.first_name} {user.last_name} | Interactions: {interactions_count}")
    
    print()
    
    # Lấy tất cả tours
    tours = db.query(Tour).filter(
        Tour.is_active == True,
        Tour.is_approved == True,
        Tour.is_banned == False
    ).limit(10).all()
    
    print(f"🎯 Danh sách tours active (10 đầu tiên):")
    for tour in tours:
        interactions_count = db.query(UserTourInteraction).filter(
            UserTourInteraction.tour_id == tour.id
        ).count()
        print(f"   ID: {tour.id} | {tour.title[:50]}... | Interactions: {interactions_count}")
    
    print()
    
    # Tổng quan
    total_users = db.query(UserProfile).count()
    total_tours = db.query(Tour).filter(
        Tour.is_active == True,
        Tour.is_approved == True,
        Tour.is_banned == False
    ).count()
    total_interactions = db.query(UserTourInteraction).count()
    
    print(f"📊 Tổng quan:")
    print(f"   - Tổng users: {total_users}")
    print(f"   - Tổng tours active: {total_tours}")
    print(f"   - Tổng interactions: {total_interactions}")
    
    # Tìm user có nhiều interactions nhất
    print()
    print("🔍 User có nhiều interactions nhất:")
    from sqlalchemy import func
    top_user = db.query(
        UserTourInteraction.user_id,
        func.count(UserTourInteraction.id).label('count')
    ).group_by(UserTourInteraction.user_id).order_by(func.count(UserTourInteraction.id).desc()).first()
    
    if top_user:
        user = db.query(UserProfile).filter(UserProfile.id == top_user.user_id).first()
        print(f"   User ID: {top_user.user_id} | {user.first_name if user else 'N/A'} | Interactions: {top_user.count}")
        print(f"   💡 Thử API với user_id = {top_user.user_id}")
    
except Exception as e:
    print(f"❌ Lỗi: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()


