from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.services.collaborative_filtering import CollaborativeFiltering
from app.models.schema import UserProfile, Tour
from app.api.deps import verify_internal_key

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
    dependencies=[Depends(verify_internal_key)],
)

@router.get("/collaborative/{user_id}")
async def get_collaborative_recommendations(
    user_id: int,
    method: str = Query("hybrid", regex="^(user_based|tour_based|hybrid)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Lấy gợi ý dựa trên Collaborative Filtering
    
    - **user_id**: ID của người dùng
    - **method**: Phương pháp CF (user_based, tour_based, hybrid)
    - **limit**: Số lượng gợi ý (1-50)
    """
    # Kiểm tra user tồn tại
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail=f"User với ID {user_id} không tồn tại. Vui lòng kiểm tra lại user_id."
        )
    
    # Tạo CF instance với preprocessing và advanced features enabled
    cf = CollaborativeFiltering(
        db, 
        normalize=True,  # Mean centering để giảm user bias
        handle_sparse=True,  # Xử lý sparse data
        remove_outliers=True,  # Loại bỏ outliers
        use_time_decay=True,  # Interactions gần đây quan trọng hơn
        time_decay_half_life_days=30,  # 30 ngày để giảm 50% trọng số
        use_diversity=True,  # Đảm bảo recommendations đa dạng
        diversity_weight=0.3,  # 30% trọng số cho diversity
        enable_explanation=True  # Tạo explanations cho recommendations
    )
    
    try:
        # Kiểm tra cold start (user chưa có interactions)
        from app.models.schema import UserTourInteraction
        user_interactions_count = db.query(UserTourInteraction).filter(
            UserTourInteraction.user_id == user_id
        ).count()
        
        # Nếu user chưa có interactions, dùng cold start
        if user_interactions_count == 0:
            recommendations = cf.handle_cold_start_user(user_id, limit)
        elif method == "user_based":
            recommendations = cf.user_based_recommendations(user_id, limit)
        elif method == "tour_based":
            recommendations = cf.tour_based_recommendations(user_id, limit)
        else:  # hybrid
            recommendations = cf.hybrid_recommendations(user_id, limit)
        
        # Nếu không có recommendations và user đã tương tác với nhiều tours,
        # có thể user đã xem hết tours. Trả về top tours phổ biến nhất làm fallback
        if len(recommendations) == 0:
            # Kiểm tra số tours user đã tương tác
            from app.models.schema import UserTourInteraction
            user_interactions_count = db.query(UserTourInteraction).filter(
                UserTourInteraction.user_id == user_id
            ).count()
            
            total_tours = db.query(Tour).filter(
                Tour.is_active == True,
                Tour.is_approved == True,
                Tour.is_banned == False
            ).count()
            
            # Nếu user đã tương tác với >= 80% tours, trả về top tours phổ biến
            if user_interactions_count >= total_tours * 0.8:
                # Lấy top tours phổ biến nhất (dựa trên view_count hoặc booked_count)
                popular_tours = db.query(Tour).filter(
                    Tour.is_active == True,
                    Tour.is_approved == True,
                    Tour.is_banned == False
                ).order_by(
                    Tour.view_count.desc(),
                    Tour.booked_count.desc()
                ).limit(limit).all()
                
                recommendations = [{
                    "tour_id": tour.id,
                    "tour_title": tour.title,
                    "tour_slug": tour.slug,
                    "predicted_score": float(tour.view_count + tour.booked_count * 2),
                    "method": "popular_fallback",
                    "reason": "User đã tương tác với hầu hết tours, trả về tours phổ biến nhất"
                } for tour in popular_tours]
        
        return {
            "success": True,
            "user_id": user_id,
            "method": method,
            "recommendations": recommendations,
            "count": len(recommendations),
            "message": "Không có recommendations phù hợp" if len(recommendations) == 0 else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collaborative/batch")
async def get_batch_recommendations(
    user_ids: List[int],
    method: str = Query("hybrid", regex="^(user_based|tour_based|hybrid)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Batch recommendations cho nhiều users cùng lúc
    Tối ưu performance bằng cách tính similarity một lần
    
    - **user_ids**: Danh sách user IDs (trong request body)
    - **method**: Phương pháp CF (user_based, tour_based, hybrid)
    - **limit**: Số lượng gợi ý mỗi user (1-50)
    """
    if not user_ids or len(user_ids) == 0:
        raise HTTPException(status_code=400, detail="user_ids không được rỗng")
    
    if len(user_ids) > 100:
        raise HTTPException(status_code=400, detail="Tối đa 100 users mỗi lần")
    
    # Tạo CF instance
    cf = CollaborativeFiltering(
        db, 
        normalize=True,
        handle_sparse=True,
        remove_outliers=True,
        use_time_decay=True,
        use_diversity=True,
        enable_explanation=True
    )
    
    try:
        # Batch processing
        results = cf.batch_recommendations(user_ids, method, limit)
        
        return {
            "success": True,
            "method": method,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/collaborative/cache/stats")
async def get_cache_stats(db: Session = Depends(get_db)):
    """
    Lấy thống kê về cache performance
    """
    cf = CollaborativeFiltering(db)
    stats = cf.get_cache_stats()
    
    return {
        "success": True,
        "cache_stats": stats
    }

@router.post("/collaborative/cache/invalidate")
async def invalidate_cache(db: Session = Depends(get_db)):
    """
    Invalidate cache (force rebuild)
    Sử dụng khi data thay đổi
    """
    cf = CollaborativeFiltering(db)
    cf.invalidate_cache()
    
    return {
        "success": True,
        "message": "Cache đã được invalidate"
    }

