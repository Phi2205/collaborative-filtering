"""Test User 11 recommendations sau khi fix"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.services.collaborative_filtering import CollaborativeFiltering

db = SessionLocal()
try:
    cf = CollaborativeFiltering(db)
    recs = cf.user_based_recommendations(11, 10)
    print(f"✅ Recommendations: {len(recs)}")
    for rec in recs:
        print(f"  Tour {rec['tour_id']}: {rec['tour_title'][:50]}... (score={rec['predicted_score']:.4f})")
finally:
    db.close()


