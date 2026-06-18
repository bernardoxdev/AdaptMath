from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from backend.core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

from backend.database.connection import SessionLocal
from backend.database.models.refresh_token import RefreshToken

ALGORITHM = "HS256"

def create_access_token(data: dict):
    payload = data.copy()
    
    payload.update({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    })

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    payload = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload.update({
        "exp": expire,
        "type": "refresh"
    })

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("type") != "refresh":
            return None

        return create_access_token({
            "sub": payload["sub"]
        })

    except JWTError:
        return None

def validar_refresh_token(token: str):
    db = SessionLocal()

    try:
        refresh = db.query(RefreshToken).filter(RefreshToken.token == token, RefreshToken.revogado == False).first()

        if not refresh:
            return None

        if refresh.expires_at < datetime.now(timezone.utc):
            return None

        return refresh

    finally:
        db.close()

def renovar_tokens(refresh_token_atual: str):
    db = SessionLocal()

    try:

        refresh_db = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token == refresh_token_atual,
                RefreshToken.revogado == False
            )
            .first()
        )

        if not refresh_db:
            return None

        if refresh_db.expires_at < datetime.now(timezone.utc):

            refresh_db.revogado = True
            db.commit()

            return None

        try:

            payload = jwt.decode(
                refresh_token_atual,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

        except JWTError:

            refresh_db.revogado = True
            db.commit()

            return None

        if payload.get("type") != "refresh":
            return None

        user_id = int(payload["sub"])

        refresh_db.revogado = True

        novo_access = create_access_token({
            "sub": str(user_id)
        })

        novo_refresh = create_refresh_token({
            "sub": str(user_id)
        })

        novo_refresh_db = RefreshToken(
            token=novo_refresh,
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        db.add(novo_refresh_db)

        db.commit()

        return {
            "access_token": novo_access,
            "refresh_token": novo_refresh,
            "user_id": user_id
        }

    except Exception as e:
        db.rollback()

        return None

    finally:
        db.close()

if __name__ == '__main__':
    pass