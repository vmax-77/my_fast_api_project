import random
import string
from datetime import datetime
from sqlalchemy.orm import Session
from app import models

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def is_code_unique(db: Session, code: str):
    return not db.query(models.Link).filter(
        (models.Link.short_code == code) | (models.Link.custom_alias == code)
    ).first()

def create_unique_code(db: Session, length=6):
    while True:
        code = generate_short_code(length)
        if is_code_unique(db, code):
            return code

def check_expired_links(db: Session):
    expired_links = db.query(models.Link).filter(
        models.Link.expires_at < datetime.utcnow(),
        models.Link.is_active == True
    ).all()
    
    for link in expired_links:
        link.is_active = False
    db.commit()
    return len(expired_links)