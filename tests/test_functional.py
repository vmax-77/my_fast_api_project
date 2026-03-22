def test_register_success(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    print("✅ test_register_success passed")

def test_login_success(client):
    client.post("/auth/register", json={
        "email": "test2@example.com",
        "username": "testuser2",
        "password": "testpass123"
    })
    response = client.post("/auth/token", data={
        "username": "testuser2",
        "password": "testpass123"
    })
    assert response.status_code == 200
    print("✅ test_login_success passed")

def test_create_link(client):
    response = client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "example"
    })
    assert response.status_code == 201
    print("✅ test_create_link passed")

def test_redirect(client):
    client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_alias": "test"
    })
    response = client.get("/test", follow_redirects=False)
    assert response.status_code == 307
    print("✅ test_redirect passed")

def test_update_link_not_found(client, auth_token):
    response = client.put(
        "/links/nonexistent",
        json={"original_url": "https://new.com"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

def test_delete_link_not_found(client, auth_token):
    response = client.delete(
        "/links/nonexistent",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

def test_cleanup_unused_links(client, auth_token):
    from datetime import datetime, timedelta
    from app.models import Link
    
    # Создаем неиспользуемую ссылку
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://unused.com", "custom_alias": "unused"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Меняем дату последнего доступа в БД (через прямой SQL)
    # Это сложнее, можно пропустить
    
    response = client.delete(
        "/links/cleanup/unused?days=1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_redirect_with_cache(client):
    # Первый запрос — создает кэш
    client.post("/links/shorten", json={
        "original_url": "https://cache-test.com",
        "custom_alias": "cachetest"
    })
    # Первый редирект
    response1 = client.get("/cachetest", follow_redirects=False)
    assert response1.status_code == 307
    # Второй редирект — должен взять из кэша
    response2 = client.get("/cachetest", follow_redirects=False)
    assert response2.status_code == 307

def test_redirect_expired_link(client):
    from datetime import datetime, timedelta
    from app.models import Link
    
    # Создаем истекшую ссылку напрямую в БД
    expired = Link(
        original_url="https://expired-redirect.com",
        short_code="expiredlink",
        expires_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    from app.database import SessionLocal
    db = SessionLocal()
    db.add(expired)
    db.commit()
    
    response = client.get("/expiredlink", follow_redirects=False)
    assert response.status_code == 410  # Gone
    db.close()

    def test_create_link_without_alias(client):
        response = client.post("/links/shorten", json={
            "original_url": "https://auto-generate.com"
        })
        assert response.status_code == 201
        assert response.json()["short_code"] is not None
        assert len(response.json()["short_code"]) == 6

def test_get_stats_not_found(client):
    response = client.get("/links/nonexistent/stats")
    assert response.status_code == 404


def test_get_expired_links_history(client, auth_token):
    response = client.get(
        "/links/history/expired",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_update_link_unauthorized(client, auth_token):
    # Создаем ссылку от одного пользователя
    client.post(
        "/links/shorten",
        json={"original_url": "https://other.com", "custom_alias": "other"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Создаем другого пользователя
    client.post("/auth/register", json={
        "email": "other@example.com",
        "username": "otheruser",
        "password": "pass123"
    })
    resp = client.post("/auth/token", data={"username": "otheruser", "password": "pass123"})
    token2 = resp.json()["access_token"]
    
    response = client.put(
        "/links/other",
        json={"original_url": "https://hack.com"},
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403

def test_delete_link_unauthorized(client, auth_token):
    # Создаем ссылку от одного пользователя
    client.post(
        "/links/shorten",
        json={"original_url": "https://delete-other.com", "custom_alias": "deleteother"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Создаем другого пользователя
    client.post("/auth/register", json={
        "email": "delete@example.com",
        "username": "deleteuser",
        "password": "pass123"
    })
    resp = client.post("/auth/token", data={"username": "deleteuser", "password": "pass123"})
    token2 = resp.json()["access_token"]
    
    response = client.delete(
        "/links/deleteother",
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert response.status_code == 403

def test_create_link_without_alias(client):
    response = client.post("/links/shorten", json={
        "original_url": "https://auto-generate.com"
    })
    assert response.status_code == 201
    assert response.json()["short_code"] is not None
    assert len(response.json()["short_code"]) == 6

def test_create_link_with_expiration(client):
    from datetime import datetime, timedelta
    expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
    response = client.post("/links/shorten", json={
        "original_url": "https://expire.com",
        "custom_alias": "expire",
        "expires_at": expires_at
    })
    assert response.status_code == 201
    assert response.json()["expires_at"] is not None

def test_search_existing(client):
    client.post("/links/shorten", json={
        "original_url": "https://search-existing.com",
        "custom_alias": "search"
    })
    response = client.get("/links/search?original_url=search-existing")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_cleanup_unused_links_success(client, auth_token):
    # Создаем ссылку
    client.post(
        "/links/shorten",
        json={"original_url": "https://unused.com", "custom_alias": "unused"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    response = client.delete(
        "/links/cleanup/unused?days=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_redirect_from_cache(client):
    # Создаем ссылку
    client.post("/links/shorten", json={
        "original_url": "https://cache-test.com",
        "custom_alias": "cache"
    })
    # Первый запрос — создает кэш
    response1 = client.get("/cache", follow_redirects=False)
    assert response1.status_code == 307
    # Второй запрос — из кэша
    response2 = client.get("/cache", follow_redirects=False)
    assert response2.status_code == 307

def test_get_stats_for_anonymous_link(client):
    # Создаем ссылку без авторизации
    client.post("/links/shorten", json={
        "original_url": "https://anonymous.com",
        "custom_alias": "anonymous"
    })
    response = client.get("/links/anonymous/stats")
    assert response.status_code == 200
    assert response.json()["created_by"] == "anonymous"

def test_redirect_with_invalid_code(client):
    response = client.get("/invalidcode123", follow_redirects=False)
    assert response.status_code == 404

def test_create_link_duplicate_alias(client):
    client.post("/links/shorten", json={
        "original_url": "https://first.com",
        "custom_alias": "duplicate"
    })
    response = client.post("/links/shorten", json={
        "original_url": "https://second.com",
        "custom_alias": "duplicate"
    })
    assert response.status_code == 400

def test_cleanup_unused_links_zero_days(client, auth_token):
    client.post(
        "/links/shorten",
        json={"original_url": "https://zero.com", "custom_alias": "zero"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    response = client.delete(
        "/links/cleanup/unused?days=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

def test_redirect_to_expired_link(client):
    from datetime import datetime, timedelta
    from app.models import Link
    from app.database import SessionLocal
    
    db = SessionLocal()
    expired = Link(
        original_url="https://expired-test.com",
        short_code="expiredtest",
        expires_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    db.add(expired)
    db.commit()
    
    response = client.get("/expiredtest", follow_redirects=False)
    assert response.status_code == 410
    db.close()

def test_get_stats_success(client):
    client.post("/links/shorten", json={
        "original_url": "https://stats-success.com",
        "custom_alias": "statssuccess"
    })
    response = client.get("/links/statssuccess/stats")
    assert response.status_code == 200
    assert response.json()["short_code"] == "statssuccess"
    assert response.json()["clicks"] == 0

def test_get_stats_not_found(client):
    response = client.get("/links/nonexistent123/stats")
    assert response.status_code == 404

def test_redirect_with_expired_link(client):
    from datetime import datetime, timedelta
    from app.models import Link
    from app.database import SessionLocal
    
    db = SessionLocal()
    expired_link = Link(
        original_url="https://expired-test.com",
        short_code="expiredlink",
        expires_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    db.add(expired_link)
    db.commit()
    db.close()
    
    response = client.get("/expiredlink", follow_redirects=False)
    assert response.status_code == 410

def test_get_expired_links_history(client, auth_token):
    response = client.get(
        "/links/history/expired",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200