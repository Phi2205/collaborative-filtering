"""
Debug realtime để xem tại sao User 11 không được recommend Tour 2
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import SessionLocal
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.collaborative_filtering import CollaborativeFiltering
import numpy as np

def debug_realtime():
    """Debug realtime"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("DEBUG: Tại sao User 11 không được recommend Tour 2?")
        print("=" * 70)
        print()
        
        # 1. Kiểm tra data
        print("1. KIỂM TRA DATA:")
        print("-" * 70)
        interactions = db.query(UserTourInteraction).all()
        print(f"Tổng interactions: {len(interactions)}")
        for i in interactions:
            print(f"  User {i.user_id} → Tour {i.tour_id} ({i.interaction_type}, score={i.score})")
        print()
        
        # 2. Test User-Based CF
        print("2. TEST USER-BASED CF:")
        print("-" * 70)
        cf = CollaborativeFiltering(db)
        
        # Build matrix
        matrix = cf.build_user_tour_matrix()
        print(f"Matrix shape: {matrix.shape}")
        print(f"Matrix:\n{matrix}")
        print()
        
        # Check user và tour indices
        if 11 in cf.user_id_to_idx and 2 in cf.tour_id_to_idx:
            user11_idx = cf.user_id_to_idx[11]
            tour2_idx = cf.tour_id_to_idx[2]
            print(f"User 11 index: {user11_idx}")
            print(f"Tour 2 index: {tour2_idx}")
            print(f"User 11 rating cho Tour 2: {matrix[user11_idx, tour2_idx]}")
            print()
            
            # Tính similarity
            user_sim = cf.calculate_user_similarity()
            print(f"User similarity shape: {user_sim.shape}")
            print(f"User similarity matrix:\n{user_sim}")
            print()
            
            # Tìm similar users
            similar_users_idx = np.argsort(user_sim[user11_idx])[::-1][1:6]
            print(f"Similar users indices: {similar_users_idx}")
            for idx in similar_users_idx:
                user_id = cf.user_ids[idx]
                sim = user_sim[user11_idx, idx]
                print(f"  User {user_id} (idx={idx}): similarity = {sim:.6f}")
            print()
            
            # Tính predicted scores
            user_ratings = matrix[user11_idx]
            predicted_scores = np.zeros(len(cf.tour_ids))
            
            print("Tính predicted scores cho từng tour:")
            for tour_idx in range(len(cf.tour_ids)):
                tour_id = cf.tour_ids[tour_idx]
                if user_ratings[tour_idx] == 0:  # Chỉ tours user chưa xem
                    print(f"\n  Tour {tour_id} (idx={tour_idx}):")
                    
                    # Logic chính
                    similar_users_ratings = matrix[similar_users_idx, tour_idx]
                    similar_users_sim = user_sim[user11_idx, similar_users_idx]
                    
                    print(f"    Similar users ratings: {similar_users_ratings}")
                    print(f"    Similar users sim: {similar_users_sim}")
                    print(f"    Sum of sim: {np.sum(similar_users_sim):.6f}")
                    
                    if np.sum(similar_users_sim) > 0:
                        predicted_score = np.sum(
                            similar_users_ratings * similar_users_sim
                        ) / np.sum(similar_users_sim)
                        predicted_scores[tour_idx] = predicted_score
                        print(f"    ✅ Predicted score (main): {predicted_score:.6f}")
                    else:
                        print(f"    ⚠️ Sum of sim = 0, dùng fallback...")
                        
                        # Fallback logic
                        interacted_tours_idx = np.where(user_ratings > 0)[0]
                        print(f"    Interacted tours idx: {interacted_tours_idx}")
                        
                        if len(interacted_tours_idx) > 0:
                            co_occurrence_score = 0
                            for interacted_tour_idx in interacted_tours_idx:
                                users_who_saw_this_tour = np.where(
                                    matrix[:, interacted_tour_idx] > 0
                                )[0]
                                users_who_saw_this_tour = users_who_saw_this_tour[
                                    users_who_saw_this_tour != user11_idx
                                ]
                                print(f"      Users who saw tour {cf.tour_ids[interacted_tour_idx]}: {users_who_saw_this_tour}")
                                
                                if len(users_who_saw_this_tour) > 0:
                                    ratings_from_co_users = matrix[users_who_saw_this_tour, tour_idx]
                                    print(f"      Ratings from co-users: {ratings_from_co_users}")
                                    
                                    if np.sum(ratings_from_co_users) > 0:
                                        mean_rating = np.mean(ratings_from_co_users[ratings_from_co_users > 0])
                                        count = len(ratings_from_co_users[ratings_from_co_users > 0])
                                        co_score = mean_rating * count
                                        co_occurrence_score += co_score
                                        print(f"      Co-occurrence score += {co_score:.6f}")
                            
                            if co_occurrence_score > 0:
                                predicted_score = co_occurrence_score / len(interacted_tours_idx)
                                predicted_scores[tour_idx] = predicted_score
                                print(f"    ✅ Predicted score (fallback): {predicted_score:.6f}")
                            else:
                                print(f"    ❌ Co-occurrence score = 0")
                        else:
                            print(f"    ❌ No interacted tours")
            
            print(f"\nPredicted scores: {predicted_scores}")
            print(f"Max score: {np.max(predicted_scores):.6f}")
            print(f"Scores > 0: {np.sum(predicted_scores > 0)}")
            
            # Test actual recommendation
            print("\n3. TEST ACTUAL RECOMMENDATION:")
            print("-" * 70)
            recommendations = cf.user_based_recommendations(11, 10)
            print(f"Số recommendations: {len(recommendations)}")
            for rec in recommendations:
                print(f"  Tour {rec['tour_id']}: {rec['tour_title'][:50]}... (score={rec['predicted_score']:.6f})")
        else:
            print("❌ User 11 hoặc Tour 2 không có trong matrix!")
            if 11 not in cf.user_id_to_idx:
                print("  User 11 không có trong matrix")
            if 2 not in cf.tour_id_to_idx:
                print("  Tour 2 không có trong matrix")
                print(f"  Available tours: {cf.tour_ids}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_realtime()


