"""
Scoring system cho Collaborative Filtering
Mapping điểm số theo hành vi của người dùng
"""

# Mapping điểm số cho các hành vi
BEHAVIOR_SCORES = {
    # View hành vi
    'view': 1.0,
    'click': 1.0,  # Click tương đương view
    
    # Rating hành vi (theo số sao)
    'rating_5': 4.0,   # Rating 5 sao = +4
    'rating_4': 3.0,   # Rating 4 sao = +3
    'rating_3': 1.0,   # Rating 3 sao = +1
    'rating_2': -1.0,  # Rating 2 sao = -1
    'rating_1': -3.0,  # Rating 1 sao = -3
    
    # Booking hành vi
    'book': 5.0,       # Book = +5
    'booking': 5.0,   # Booking = +5 (alias)
    
    # Payment hành vi
    'paid': 6.0,       # Paid = +6
    
    # Other hành vi
    'favorite': 2.0,   # Favorite = +2 (tùy chọn)
    'review': 3.0,     # Review (không có rating) = +3
}

def get_rating_score(rating: float) -> float:
    """
    Tính điểm dựa trên rating (số sao)
    
    Args:
        rating: Số sao từ 1-5
        
    Returns:
        Điểm số tương ứng
    """
    rating_int = int(rating)
    rating_map = {
        5: 4.0,
        4: 3.0,
        3: 1.0,
        2: -1.0,
        1: -3.0
    }
    return rating_map.get(rating_int, 0.0)

def get_interaction_score(interaction_type: str, rating: float = None) -> float:
    """
    Tính điểm cho một interaction
    
    Args:
        interaction_type: Loại interaction ('view', 'book', 'paid', etc.)
        rating: Rating nếu có (1-5 sao)
        
    Returns:
        Điểm số tương ứng
    """
    # Nếu có rating, ưu tiên dùng điểm rating
    if rating:
        return get_rating_score(rating)
    
    # Nếu không có rating, dùng điểm theo interaction type
    interaction_type_lower = interaction_type.lower() if interaction_type else 'view'
    return BEHAVIOR_SCORES.get(interaction_type_lower, 1.0)

