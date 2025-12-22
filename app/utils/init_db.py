from app.utils.database import engine, Base
# Import models để đăng ký với Base
from app.models.schema import UserProfile, Tour, UserTourInteraction

def init_db():
    """
    Tạo các tables trong database
    Lưu ý: Bảng user_profile và tour đã tồn tại, chỉ tạo user_tour_interaction
    """
    try:
        # Chỉ tạo bảng user_tour_interaction (các bảng khác đã có)
        UserTourInteraction.__table__.create(bind=engine, checkfirst=True)
        print("✅ Database tables created/verified successfully!")
        print("📋 Bảng user_tour_interaction đã sẵn sàng")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    init_db()

