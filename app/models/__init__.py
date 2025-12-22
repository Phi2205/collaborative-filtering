from app.models.schema import UserProfile, Tour, UserTourInteraction

__all__ = ["UserProfile", "Tour", "UserTourInteraction"]

# Alias để tương thích với code cũ
User = UserProfile
Item = Tour  # Alias cho tour
UserItemInteraction = UserTourInteraction  # Alias

