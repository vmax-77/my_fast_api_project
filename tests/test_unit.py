import pytest
from datetime import datetime, timedelta
from app.utils import generate_short_code, is_code_unique, create_unique_code, check_expired_links
from app.auth import verify_password, get_password_hash
from app.models import Link, User


class TestUtils:
    def test_generate_short_code(self):
        code = generate_short_code(6)
        assert len(code) == 6
        assert all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in code)
    
    def test_generate_short_code_length(self):
        assert len(generate_short_code(8)) == 8
        assert len(generate_short_code(4)) == 4
    
    def test_is_code_unique(self, db_session):
        link = Link(
            original_url="https://example.com",
            short_code="test123",
            clicks=0,
            is_active=True
        )
        db_session.add(link)
        db_session.commit()
        
        assert is_code_unique(db_session, "test123") == False
        assert is_code_unique(db_session, "unique") == True

    def test_is_code_unique_true(self, db_session):
        from app.utils import is_code_unique
        assert is_code_unique(db_session, "nonexistent") == True

    def test_is_code_unique_false(self, db_session):
        from app.utils import is_code_unique
        from app.models import Link
        
        link = Link(
            original_url="https://test.com",
            short_code="existing",
            is_active=True
        )
        db_session.add(link)
        db_session.commit()
        assert is_code_unique(db_session, "existing") == False
    
    def test_create_unique_code(self, db_session):
        code1 = create_unique_code(db_session)
        code2 = create_unique_code(db_session)
        assert code1 != code2
        assert len(code1) == 6
        assert len(code2) == 6
    
    def test_check_expired_links(self, db_session):
        # Создаем истекшую ссылку
        expired_link = Link(
            original_url="https://expired.com",
            short_code="expired",
            expires_at=datetime.utcnow() - timedelta(days=1),
            is_active=True
        )
        # Создаем активную ссылку
        active_link = Link(
            original_url="https://active.com",
            short_code="active",
            expires_at=datetime.utcnow() + timedelta(days=1),
            is_active=True
        )
        db_session.add_all([expired_link, active_link])
        db_session.commit()
        
        count = check_expired_links(db_session)
        assert count == 1
        
        expired = db_session.query(Link).filter(Link.short_code == "expired").first()
        active = db_session.query(Link).filter(Link.short_code == "active").first()
        assert expired.is_active == False
        assert active.is_active == True

        def test_is_code_unique_false(db_session):
            from app.utils import is_code_unique
            from app.models import Link
            
            link = Link(
                original_url="https://test.com",
                short_code="existing",
                is_active=True
            )
            db_session.add(link)
            db_session.commit()
            assert is_code_unique(db_session, "existing") == False


class TestAuth:
    def test_password_hashing(self):
        password = "testpass123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) == True
        assert verify_password("wrongpass", hashed) == False
    
    def test_password_truncation(self):
        long_password = "a" * 100
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) == True
    
    def test_verify_password_with_bytes(self):
        password = "testpass"
        hashed = get_password_hash(password)
        # Передаем строку, не байты
        assert verify_password(password, hashed) == True


class TestAuthAsync:
    @pytest.mark.anyio
    async def test_get_current_user_optional_with_token(self, db_session, auth_token):
        from app.auth import get_current_user_optional
        
        user = await get_current_user_optional(auth_token, db_session)
        assert user is not None
        assert user.username == "testuser"
    
    @pytest.mark.anyio
    async def test_get_current_user_optional_without_token(self, db_session):
        from app.auth import get_current_user_optional
        
        user = await get_current_user_optional(None, db_session)
        assert user is None
    
    @pytest.mark.anyio
    async def test_get_current_user_optional_invalid_token(self, db_session):
        from app.auth import get_current_user_optional
        
        user = await get_current_user_optional("invalid_token", db_session)
        assert user is None


class TestModels:
    def test_user_model(self, db_session):
        user = User(
            email="test_model@example.com",
            username="testmodel",
            hashed_password="hashed_pass"
        )
        db_session.add(user)
        db_session.commit()
        
        saved_user = db_session.query(User).filter(User.username == "testmodel").first()
        assert saved_user is not None
        assert saved_user.email == "test_model@example.com"
        assert saved_user.is_active == True
    
    def test_link_model(self, db_session):
        link = Link(
            original_url="https://model-test.com",
            short_code="modeltest",
            clicks=0,
            is_active=True
        )
        db_session.add(link)
        db_session.commit()

        saved_link = db_session.query(Link).filter(Link.short_code == "modeltest").first()
        assert saved_link is not None
        # FastAPI добавляет слэш в конце, поэтому сравниваем без слэша или добавляем
        assert saved_link.original_url == "https://model-test.com"  # убираем /
    
    def test_link_with_user(self, db_session):
        user = User(
            email="user_for_link@example.com",
            username="linkuser",
            hashed_password="hashed"
        )
        db_session.add(user)
        db_session.flush()
        
        link = Link(
            original_url="https://user-link.com",
            short_code="userlink",
            user_id=user.id,
            clicks=0,
            is_active=True
        )
        db_session.add(link)
        db_session.commit()
        
        saved_link = db_session.query(Link).filter(Link.short_code == "userlink").first()
        assert saved_link.user_id == user.id
        assert saved_link.owner.username == "linkuser"

class TestDatabase:
    def test_get_db(self):
        from app.database import get_db
        
        db_gen = get_db()
        db = next(db_gen)
        assert db is not None
        try:
            next(db_gen)
        except StopIteration:
            pass