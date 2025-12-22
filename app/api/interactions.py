from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.utils.database import get_db
from app.models.schema import UserTourInteraction, UserProfile, Tour
from app.services.scoring import get_interaction_score
from app.api.deps import verify_internal_key

router = APIRouter(
    prefix="/interactions",
    tags=["interactions"],
    dependencies=[Depends(verify_internal_key)],
)

class InteractionCreate(BaseModel):
    """Schema để tạo interaction mới"""
    user_id: int = Field(..., description="ID của user")
    tour_id: int = Field(..., description="ID của tour")
    interaction_type: str = Field(..., description="Loại interaction: view, click, book, paid, rating")
    rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Rating từ 1-5 sao (nếu là rating)")
    score: Optional[int] = Field(None, description="Điểm số (tự động tính nếu không cung cấp)")

@router.post("/")
async def create_interaction(
    interaction: InteractionCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Tạo interaction mới giữa user và tour
    
    - **user_id**: ID của user
    - **tour_id**: ID của tour
    - **interaction_type**: Loại interaction (view, click, book, paid, rating)
    - **rating**: Rating từ 1-5 sao (chỉ cần khi interaction_type = 'rating')
    """
    # Kiểm tra user tồn tại
    user = db.query(UserProfile).filter(UserProfile.id == interaction.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User với ID {interaction.user_id} không tồn tại")
    
    # Kiểm tra tour tồn tại
    tour = db.query(Tour).filter(Tour.id == interaction.tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail=f"Tour với ID {interaction.tour_id} không tồn tại")
    
    # Kiểm tra interaction_type hợp lệ
    valid_types = ['view', 'click', 'book', 'booking', 'paid', 'rating', 'favorite']
    if interaction.interaction_type.lower() not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"interaction_type phải là một trong: {', '.join(valid_types)}"
        )
    
    # Nếu là rating thì phải có rating value
    if interaction.interaction_type.lower() == 'rating' and not interaction.rating:
        raise HTTPException(status_code=400, detail="Rating interaction phải có giá trị rating")
    
    # Tính score nếu chưa được cung cấp
    if interaction.score is None:
        score = int(get_interaction_score(
            interaction_type=interaction.interaction_type,
            rating=interaction.rating
        ))
    else:
        score = interaction.score
    
    # Tạo interaction mới
    new_interaction = UserTourInteraction(
        user_id=interaction.user_id,
        tour_id=interaction.tour_id,
        interaction_type=interaction.interaction_type.lower(),
        score=score,  # Score đã được tính
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)
    
    return {
        "success": True,
        "message": "Interaction đã được tạo thành công",
            "interaction": {
                "id": new_interaction.id,
                "user_id": new_interaction.user_id,
                "tour_id": new_interaction.tour_id,
                "interaction_type": new_interaction.interaction_type,
                "score": new_interaction.score,
                "created_at": new_interaction.created_at.isoformat()
            }
    }

@router.get("/user/{user_id}")
async def get_user_interactions(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả interactions của một user
    """
    interactions = db.query(UserTourInteraction)\
        .filter(UserTourInteraction.user_id == user_id)\
        .order_by(UserTourInteraction.created_at.desc())\
        .limit(limit)\
        .all()
    
    return {
        "success": True,
        "user_id": user_id,
        "count": len(interactions),
        "interactions": [
            {
                "id": i.id,
                "tour_id": i.tour_id,
                "interaction_type": i.interaction_type,
                "score": i.score,
                "created_at": i.created_at.isoformat()
            }
            for i in interactions
        ]
    }

@router.get("/tour/{tour_id}")
async def get_tour_interactions(
    tour_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Lấy tất cả interactions của một tour
    """
    interactions = db.query(UserTourInteraction)\
        .filter(UserTourInteraction.tour_id == tour_id)\
        .order_by(UserTourInteraction.created_at.desc())\
        .limit(limit)\
        .all()
    
    return {
        "success": True,
        "tour_id": tour_id,
        "count": len(interactions),
        "interactions": [
            {
                "id": i.id,
                "user_id": i.user_id,
                "interaction_type": i.interaction_type,
                "score": i.score,
                "created_at": i.created_at.isoformat()
            }
            for i in interactions
        ]
    }

@router.delete("/clean")
async def clean_all_interactions(
    confirm: bool = Query(False, description="Phải set confirm=true để xác nhận xóa"),
    db: Session = Depends(get_db)
):
    """
    Xóa TẤT CẢ interactions trong bảng user_tour_interaction
    
    ⚠️ CẢNH BÁO: Hành động này không thể hoàn tác!
    
    - **confirm**: Phải set confirm=true để xác nhận xóa
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Phải set confirm=true để xác nhận xóa tất cả interactions"
        )
    
    try:
        # Đếm số lượng interactions trước khi xóa
        count_before = db.query(UserTourInteraction).count()
        
        # Xóa tất cả interactions
        db.query(UserTourInteraction).delete()
        db.commit()
        
        # Invalidate cache của CollaborativeFiltering
        try:
            from app.services.collaborative_filtering import CollaborativeFiltering
            cf = CollaborativeFiltering(db)
            cf.invalidate_cache()
        except Exception:
            pass  # Ignore cache invalidation errors
        
        return {
            "success": True,
            "message": f"Đã xóa {count_before} interactions",
            "deleted_count": count_before
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa interactions: {str(e)}")

@router.delete("/user/{user_id}/clean")
async def clean_user_interactions(
    user_id: int,
    confirm: bool = Query(False, description="Phải set confirm=true để xác nhận xóa"),
    db: Session = Depends(get_db)
):
    """
    Xóa tất cả interactions của một user cụ thể
    
    - **user_id**: ID của user
    - **confirm**: Phải set confirm=true để xác nhận xóa
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Phải set confirm=true để xác nhận xóa interactions của user"
        )
    
    # Kiểm tra user tồn tại
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User với ID {user_id} không tồn tại")
    
    try:
        # Đếm số lượng interactions trước khi xóa
        count_before = db.query(UserTourInteraction).filter(
            UserTourInteraction.user_id == user_id
        ).count()
        
        # Xóa interactions của user
        db.query(UserTourInteraction).filter(
            UserTourInteraction.user_id == user_id
        ).delete()
        db.commit()
        
        # Invalidate cache
        try:
            from app.services.collaborative_filtering import CollaborativeFiltering
            cf = CollaborativeFiltering(db)
            cf.invalidate_cache()
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"Đã xóa {count_before} interactions của user {user_id}",
            "user_id": user_id,
            "deleted_count": count_before
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa interactions: {str(e)}")

@router.delete("/tour/{tour_id}/clean")
async def clean_tour_interactions(
    tour_id: int,
    confirm: bool = Query(False, description="Phải set confirm=true để xác nhận xóa"),
    db: Session = Depends(get_db)
):
    """
    Xóa tất cả interactions của một tour cụ thể
    
    - **tour_id**: ID của tour
    - **confirm**: Phải set confirm=true để xác nhận xóa
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Phải set confirm=true để xác nhận xóa interactions của tour"
        )
    
    # Kiểm tra tour tồn tại
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail=f"Tour với ID {tour_id} không tồn tại")
    
    try:
        # Đếm số lượng interactions trước khi xóa
        count_before = db.query(UserTourInteraction).filter(
            UserTourInteraction.tour_id == tour_id
        ).count()
        
        # Xóa interactions của tour
        db.query(UserTourInteraction).filter(
            UserTourInteraction.tour_id == tour_id
        ).delete()
        db.commit()
        
        # Invalidate cache
        try:
            from app.services.collaborative_filtering import CollaborativeFiltering
            cf = CollaborativeFiltering(db)
            cf.invalidate_cache()
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"Đã xóa {count_before} interactions của tour {tour_id}",
            "tour_id": tour_id,
            "deleted_count": count_before
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa interactions: {str(e)}")

@router.delete("/old")
async def clean_old_interactions(
    days: int = Query(30, ge=1, description="Xóa interactions cũ hơn N ngày"),
    confirm: bool = Query(False, description="Phải set confirm=true để xác nhận xóa"),
    db: Session = Depends(get_db)
):
    """
    Xóa interactions cũ hơn N ngày
    
    - **days**: Số ngày (mặc định: 30)
    - **confirm**: Phải set confirm=true để xác nhận xóa
    
    Ví dụ: days=30 sẽ xóa tất cả interactions cũ hơn 30 ngày
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Phải set confirm=true để xác nhận xóa interactions cũ"
        )
    
    try:
        # Tính ngày cutoff
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Đếm số lượng interactions sẽ bị xóa
        count_before = db.query(UserTourInteraction).filter(
            UserTourInteraction.created_at < cutoff_date
        ).count()
        
        if count_before == 0:
            return {
                "success": True,
                "message": f"Không có interactions nào cũ hơn {days} ngày",
                "deleted_count": 0
            }
        
        # Xóa interactions cũ
        db.query(UserTourInteraction).filter(
            UserTourInteraction.created_at < cutoff_date
        ).delete()
        db.commit()
        
        # Invalidate cache
        try:
            from app.services.collaborative_filtering import CollaborativeFiltering
            cf = CollaborativeFiltering(db)
            cf.invalidate_cache()
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"Đã xóa {count_before} interactions cũ hơn {days} ngày",
            "cutoff_date": cutoff_date.isoformat(),
            "deleted_count": count_before
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi xóa interactions: {str(e)}")

@router.get("/stats")
async def get_interaction_stats(db: Session = Depends(get_db)):
    """
    Lấy thống kê về interactions
    
    Trả về:
    - Tổng số interactions
    - Số interactions theo user
    - Số interactions theo tour
    - Số interactions theo loại
    """
    try:
        # Tổng số interactions
        total_count = db.query(UserTourInteraction).count()
        
        # Số interactions theo loại
        type_counts = db.query(
            UserTourInteraction.interaction_type,
            func.count(UserTourInteraction.id).label('count')
        ).group_by(UserTourInteraction.interaction_type).all()
        
        type_stats = {item[0] or 'unknown': item[1] for item in type_counts}
        
        # Số users có interactions
        unique_users = db.query(func.count(func.distinct(UserTourInteraction.user_id))).scalar()
        
        # Số tours có interactions
        unique_tours = db.query(func.count(func.distinct(UserTourInteraction.tour_id))).scalar()
        
        # Interactions mới nhất và cũ nhất
        oldest = db.query(UserTourInteraction).order_by(UserTourInteraction.created_at.asc()).first()
        newest = db.query(UserTourInteraction).order_by(UserTourInteraction.created_at.desc()).first()
        
        return {
            "success": True,
            "stats": {
                "total_interactions": total_count,
                "unique_users": unique_users,
                "unique_tours": unique_tours,
                "by_type": type_stats,
                "oldest_interaction": oldest.created_at.isoformat() if oldest else None,
                "newest_interaction": newest.created_at.isoformat() if newest else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê: {str(e)}")

