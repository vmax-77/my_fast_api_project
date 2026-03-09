from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timedelta
import json

from app.database import get_db
from app import models, schemas, utils, auth
from app.config import settings
from app.redis_client import redis_client

router = APIRouter()

@router.post("/shorten", response_model=schemas.LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(auth.oauth2_scheme_optional)
):
    # Получаем пользователя из токена если есть
    user = None
    if token:
        try:
            user = await auth.get_current_user(token, db)
        except:
            pass
    
    # Check for expired links first
    utils.check_expired_links(db)
    
    # Determine short code
    short_code = None
    if link.custom_alias:
        # Check if custom alias is unique
        if not utils.is_code_unique(db, link.custom_alias):
            raise HTTPException(status_code=400, detail="Custom alias already exists")
        short_code = link.custom_alias
    else:
        short_code = utils.create_unique_code(db)
    
    # Create link
    db_link = models.Link(
        original_url=str(link.original_url),
        short_code=short_code,
        custom_alias=link.custom_alias if link.custom_alias else None,
        expires_at=link.expires_at,
        user_id=user.id if user else None
    )
    
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    
    # Cache the link
    redis_client.setex(
        f"link:{short_code}",
        3600,
        json.dumps({"original_url": db_link.original_url, "clicks": db_link.clicks})
    )
    
    return schemas.LinkResponse(
        short_code=db_link.short_code,
        original_url=db_link.original_url,
        short_url=f"{settings.BASE_URL}/{db_link.short_code}",
        created_at=db_link.created_at,
        expires_at=db_link.expires_at,
        clicks=db_link.clicks,
        is_active=db_link.is_active,
        custom_alias=db_link.custom_alias
    )

# ЭНДПОЙНТ ДЛЯ СТАТИСТИКИ - ДОБАВЬТЕ ЭТО
@router.get("/{short_code}/stats", response_model=schemas.LinkStats)
async def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(
        or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    created_by = link.owner.username if link.owner else "anonymous"
    
    return schemas.LinkStats(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        clicks=link.clicks,
        is_active=link.is_active,
        custom_alias=link.custom_alias,
        last_accessed=link.last_accessed,
        created_by=created_by
    )

# ЭНДПОЙНТ ДЛЯ РЕДИРЕКТА (уже есть в redirect.py, но можно оставить и здесь)
@router.get("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    # Check cache first
    cached = redis_client.get(f"link:{short_code}")
    if cached:
        data = json.loads(cached)
        link = db.query(models.Link).filter(
            or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code),
            models.Link.is_active == True
        ).first()
        if link:
            link.clicks += 1
            link.last_accessed = datetime.utcnow()
            db.commit()
            redis_client.setex(
                f"link:{short_code}",
                3600,
                json.dumps({"original_url": link.original_url, "clicks": link.clicks})
            )
        return RedirectResponse(url=data["original_url"])
    
    link = db.query(models.Link).filter(
        or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code),
        models.Link.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    
    if link.expires_at and link.expires_at < datetime.utcnow():
        link.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="Link has expired")
    
    link.clicks += 1
    link.last_accessed = datetime.utcnow()
    db.commit()
    
    redis_client.setex(
        f"link:{short_code}",
        3600,
        json.dumps({"original_url": link.original_url, "clicks": link.clicks})
    )
    
    return RedirectResponse(url=link.original_url)

@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    link = db.query(models.Link).filter(
        or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this link")
    
    redis_client.delete(f"link:{short_code}")
    db.delete(link)
    db.commit()

@router.put("/{short_code}", response_model=schemas.LinkResponse)
async def update_link(
    short_code: str,
    link_update: schemas.LinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    link = db.query(models.Link).filter(
        or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this link")
    
    link.original_url = str(link_update.original_url)
    db.commit()
    db.refresh(link)
    
    redis_client.setex(
        f"link:{short_code}",
        3600,
        json.dumps({"original_url": link.original_url, "clicks": link.clicks})
    )
    
    return schemas.LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=f"{settings.BASE_URL}/{link.short_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        clicks=link.clicks,
        is_active=link.is_active,
        custom_alias=link.custom_alias
    )

@router.get("/search", response_model=list[schemas.LinkResponse])
async def search_by_original_url(
    original_url: str = Query(..., description="Original URL to search for"),
    db: Session = Depends(get_db)
):
    links = db.query(models.Link).filter(
        models.Link.original_url.contains(original_url),
        models.Link.is_active == True
    ).all()
    
    return [
        schemas.LinkResponse(
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=f"{settings.BASE_URL}/{link.short_code}",
            created_at=link.created_at,
            expires_at=link.expires_at,
            clicks=link.clicks,
            is_active=link.is_active,
            custom_alias=link.custom_alias
        ) for link in links
    ]

@router.delete("/cleanup/unused", status_code=status.HTTP_200_OK)
async def cleanup_unused_links(
    days: int = Query(30, description="Delete links not accessed in N days"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    unused_links = db.query(models.Link).filter(
        models.Link.last_accessed < cutoff_date,
        models.Link.is_active == True
    ).all()
    
    count = len(unused_links)
    for link in unused_links:
        link.is_active = False
        redis_client.delete(f"link:{link.short_code}")
    
    db.commit()
    return {"message": f"Deactivated {count} unused links"}

@router.get("/history/expired", response_model=list[schemas.LinkResponse])
async def get_expired_links(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    expired_links = db.query(models.Link).filter(
        models.Link.is_active == False
    ).all()
    
    return [
        schemas.LinkResponse(
            short_code=link.short_code,
            original_url=link.original_url,
            short_url=f"{settings.BASE_URL}/{link.short_code}",
            created_at=link.created_at,
            expires_at=link.expires_at,
            clicks=link.clicks,
            is_active=link.is_active,
            custom_alias=link.custom_alias
        ) for link in expired_links
    ]