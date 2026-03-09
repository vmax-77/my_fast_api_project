from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import json

from app.database import get_db
from app import models
from app.redis_client import redis_client

router = APIRouter()

@router.get("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    # Check cache first
    cached = redis_client.get(f"link:{short_code}")
    if cached:
        data = json.loads(cached)
        # Update clicks in background
        link = db.query(models.Link).filter(
            or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code),
            models.Link.is_active == True
        ).first()
        if link:
            link.clicks += 1
            link.last_accessed = datetime.utcnow()
            db.commit()
            # Update cache
            redis_client.setex(
                f"link:{short_code}",
                3600,
                json.dumps({"original_url": link.original_url, "clicks": link.clicks})
            )
        return RedirectResponse(url=data["original_url"])
    
    # If not in cache, get from DB
    link = db.query(models.Link).filter(
        or_(models.Link.short_code == short_code, models.Link.custom_alias == short_code),
        models.Link.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    
    # Check if expired
    if link.expires_at and link.expires_at < datetime.utcnow():
        link.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="Link has expired")
    
    # Update stats
    link.clicks += 1
    link.last_accessed = datetime.utcnow()
    db.commit()
    
    # Cache for future requests
    redis_client.setex(
        f"link:{short_code}",
        3600,
        json.dumps({"original_url": link.original_url, "clicks": link.clicks})
    )
    
    return RedirectResponse(url=link.original_url)