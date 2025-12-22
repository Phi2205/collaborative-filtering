from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, foreign
from datetime import datetime, timezone
from app.utils.database import Base

class UserProfile(Base):
    """
    Schema khớp với bảng user_profile trong database
    """
    __tablename__ = "user_profile"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(200), nullable=False)
    last_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    ward = Column(String(200))
    district = Column(String(200))
    province = Column(String(200))
    address = Column(String(200))
    avatar = Column(Text)
    account_id = Column(Integer, ForeignKey("account.id"), unique=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships (không có foreign key constraint trong DB, cần chỉ định primaryjoin với foreign())
    interactions = relationship(
        "UserTourInteraction", 
        primaryjoin="UserProfile.id == foreign(UserTourInteraction.user_id)",
        back_populates="user_profile"
    )

class Tour(Base):
    """
    Schema khớp với bảng tour trong database
    """
    __tablename__ = "tour"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    poster_url = Column(Text, nullable=False)
    provider_id = Column(Integer, ForeignKey("provider_profile.id"), nullable=False)
    capacity = Column(Integer, nullable=False)
    transportation = Column(String(200), nullable=False)
    accommodation = Column(String(200), nullable=False)
    destination_intro = Column(Text, nullable=False)
    tour_info = Column(Text, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    tour_category_id = Column(Integer, ForeignKey("tour_category.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    total_star = Column(Integer, default=0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    live_commentary = Column(String(200), nullable=False)
    duration = Column(String(200), nullable=False)
    booked_count = Column(Integer, default=0, nullable=False)
    starting_point = Column(String(200), nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    
    # Relationships (không có foreign key constraint trong DB, cần chỉ định primaryjoin với foreign())
    interactions = relationship(
        "UserTourInteraction", 
        primaryjoin="Tour.id == foreign(UserTourInteraction.tour_id)",
        back_populates="tour"
    )

class UserTourInteraction(Base):
    """
    Bảng lưu tương tác giữa user và tour
    Schema khớp với bảng user_tour_interaction trong database
    """
    __tablename__ = "user_tour_interaction"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Foreign key đến user_profile.id
    tour_id = Column(Integer, nullable=False)  # Foreign key đến tour.id
    score = Column(Integer, nullable=False)  # Điểm số (đã được tính sẵn)
    interaction_type = Column(Text)  # 'view', 'click', 'book', 'paid', 'rating', etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Timestamp
    
    # Relationships (không có foreign key constraint trong DB, cần chỉ định primaryjoin với foreign())
    user_profile = relationship(
        "UserProfile", 
        primaryjoin="foreign(UserTourInteraction.user_id) == UserProfile.id",
        back_populates="interactions"
    )
    tour = relationship(
        "Tour", 
        primaryjoin="foreign(UserTourInteraction.tour_id) == Tour.id",
        back_populates="interactions"
    )

