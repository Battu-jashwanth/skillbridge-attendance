from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth
from src.config import MONITORING_API_KEY

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(payload: schemas.SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="Email already registered")

    if payload.institution_id:
        inst = db.query(models.Institution).filter(models.Institution.id == payload.institution_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Institution not found")

    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token(user.id, user.role.value)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_access_token(user.id, user.role.value)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/monitoring-token", response_model=schemas.TokenResponse)
def get_monitoring_token(
    payload: schemas.MonitoringTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Login JWT required")

    token_data = auth.decode_token(credentials.credentials)
    if token_data.get("role") != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Only monitoring officers can request this token")

    if payload.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    monitoring_token = auth.create_monitoring_token(token_data["user_id"])
    return {"access_token": monitoring_token, "token_type": "bearer"}
