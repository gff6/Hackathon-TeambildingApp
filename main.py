"""
sidequest backend (FastAPI + SQLAlchemy 2.0)

Run:
    pip install fastapi uvicorn sqlalchemy pydantic
    python main.py            # http://127.0.0.1:8000

The database URL is read from the DATABASE_URL environment variable.
  * now (default):            SQLite  -> sqlite:///./sidequest.db
  * PostgreSQL later:         pip install "psycopg[binary]"
        DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/sidequest
No code changes needed — tables are created automatically (create_all).
Use Alembic for migrations in the future.
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import (JSON, BigInteger, DateTime, ForeignKey, Integer, String,
                        create_engine, select)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'sidequest.db'}")
DEFAULT_PLAYER_ID = "alex"

# JSON on SQLite, JSONB on PostgreSQL
JsonType = JSON().with_variant(JSONB(), "postgresql")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------- models
class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Alex Morgan")
    title: Mapped[str] = mapped_column(String(120), default="Knowledge seeker")
    level: Mapped[int] = mapped_column(Integer, default=12)
    xp: Mapped[int] = mapped_column(Integer, default=750)
    xp_to_next: Mapped[int] = mapped_column(Integer, default=1000)
    hp: Mapped[int] = mapped_column(Integer, default=80)
    max_hp: Mapped[int] = mapped_column(Integer, default=100)
    coins: Mapped[int] = mapped_column(Integer, default=30)
    cheat_days: Mapped[int] = mapped_column(Integer, default=2)
    commitments: Mapped[int] = mapped_column(Integer, default=3)
    commitments_per_day: Mapped[int] = mapped_column(Integer, default=5)
    streak: Mapped[int] = mapped_column(Integer, default=5)
    quests_done: Mapped[int] = mapped_column(Integer, default=47)
    duels_won: Mapped[int] = mapped_column(Integer, default=6)
    outfit_color: Mapped[str] = mapped_column(String(16), default="#6444d8")
    paused_until: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # ms epoch
    owned: Mapped[list] = mapped_column(JsonType, default=lambda: ["hoodie", "dark", "glasses"])
    equipped: Mapped[dict] = mapped_column(
        JsonType, default=lambda: {"outfit": "hoodie", "hair": "dark", "extra": "glasses"})
    game: Mapped[dict] = mapped_column(JsonType, default=dict)       # quest / duel progress
    my_posts: Mapped[list] = mapped_column(JsonType, default=list)   # team feed posts
    liked: Mapped[list] = mapped_column(JsonType, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class GameRun(Base):
    """History of finished games (victory / defeat)."""
    __tablename__ = "game_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), index=True)
    game: Mapped[str] = mapped_column(String(32))
    outcome: Mapped[str] = mapped_column(String(16))
    player_hp: Mapped[int] = mapped_column(Integer, default=0)
    enemy_hp: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# camelCase (frontend) -> column
USER_FIELDS = {
    "name": "name", "title": "title", "level": "level", "xp": "xp", "xpToNext": "xp_to_next",
    "hp": "hp", "maxHp": "max_hp", "coins": "coins", "cheatDays": "cheat_days",
    "commitments": "commitments", "commitmentsPerDay": "commitments_per_day", "streak": "streak",
    "questsDone": "quests_done", "duelsWon": "duels_won", "outfitColor": "outfit_color",
    "pausedUntil": "paused_until", "owned": "owned", "equipped": "equipped",
}
NON_NEGATIVE = {"level", "xp", "xp_to_next", "hp", "max_hp", "coins", "cheat_days",
                "commitments", "streak", "quests_done", "duels_won"}


def player_to_state(p: Player) -> Dict[str, Any]:
    return {
        "user": {"id": p.id, **{camel: getattr(p, col) for camel, col in USER_FIELDS.items()}},
        "game": p.game or {},
        "myPosts": p.my_posts or [],
        "liked": p.liked or [],
    }


def apply_state(p: Player, data: Dict[str, Any]) -> None:
    for camel, value in (data.get("user") or {}).items():
        col = USER_FIELDS.get(camel)
        if not col:
            continue  # ignore unknown fields
        if col in NON_NEGATIVE:
            value = max(0, int(value))
        setattr(p, col, value)
    p.hp = min(p.hp, p.max_hp)
    if isinstance(data.get("game"), dict):
        p.game = data["game"]
    if isinstance(data.get("myPosts"), list):
        p.my_posts = data["myPosts"][:20]
    if isinstance(data.get("liked"), list):
        p.liked = data["liked"]


# ----------------------------------------------------------- dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_player(db: Session = Depends(get_db),
               x_player_id: str = Header(default=DEFAULT_PLAYER_ID)) -> Player:
    """Single default player; replace with real authentication later."""
    player = db.get(Player, x_player_id)
    if player is None:
        player = Player(id=x_player_id)
        db.add(player)
        db.commit()
    return player


# ------------------------------------------------------------- application
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Sidequest Backend", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class StatePayload(BaseModel):
    user: Optional[Dict[str, Any]] = None
    game: Optional[Dict[str, Any]] = None
    myPosts: Optional[list] = None
    liked: Optional[list] = None


class FinishPayload(BaseModel):
    outcome: str  # "victory" | "defeat"
    player_hp: int = 0
    enemy_hp: int = 0


class ActionPayload(BaseModel):
    action: str
    payload: Dict[str, Any] = {}


@app.get("/")
def serve_index():
    for name in ("sidequest.html", "sidequest_standalone.html", "index.html"):
        path = BASE_DIR / name
        if path.is_file():
            return FileResponse(path, media_type="text/html; charset=utf-8")
    raise HTTPException(404, "HTML file not found next to main.py")


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": engine.dialect.name}


@app.get("/api/state")
def get_state(player: Player = Depends(get_player)):
    return player_to_state(player)


@app.put("/api/state")
@app.patch("/api/state")
def save_state(payload: StatePayload, db: Session = Depends(get_db),
               player: Player = Depends(get_player)):
    apply_state(player, payload.model_dump(exclude_none=True))
    db.merge(player)
    db.commit()
    return player_to_state(player)


@app.post("/api/games/dragon/restart")
def restart_dragon(db: Session = Depends(get_db), player: Player = Depends(get_player)):
    """Full health for both the player and the dragon — start the battle from scratch."""
    player.hp = player.max_hp
    player.game = {**(player.game or {}), "dragonHp": 100, "dragonQIndex": 0}
    db.merge(player)
    db.commit()
    return {"ok": True, "player_hp": player.hp, "dragon_hp": 100}


@app.post("/api/games/{game}/finish")
def finish_game(game: str, body: FinishPayload, db: Session = Depends(get_db),
                player: Player = Depends(get_player)):
    if body.outcome not in ("victory", "defeat"):
        raise HTTPException(400, "outcome must be 'victory' or 'defeat'")
    run = GameRun(player_id=player.id, game=game, outcome=body.outcome,
                  player_hp=body.player_hp, enemy_hp=body.enemy_hp)
    db.add(run)
    db.commit()
    return {"ok": True, "id": run.id}


@app.get("/api/games/history")
def game_history(limit: int = 20, db: Session = Depends(get_db),
                 player: Player = Depends(get_player)):
    rows = db.scalars(select(GameRun).where(GameRun.player_id == player.id)
                      .order_by(GameRun.id.desc()).limit(min(limit, 100))).all()
    return [{"id": r.id, "game": r.game, "outcome": r.outcome, "player_hp": r.player_hp,
             "enemy_hp": r.enemy_hp, "created_at": r.created_at.isoformat()} for r in rows]


@app.post("/api/action")
def handle_action(req: ActionPayload, db: Session = Depends(get_db),
                  player: Player = Depends(get_player)):
    if req.action != "reset_state":
        raise HTTPException(400, f"Unknown action: {req.action}")
    db.delete(player)
    db.commit()
    fresh = Player(id=player.id)
    db.add(fresh)
    db.commit()
    return {"ok": True, "message": "State reset to defaults.", **player_to_state(fresh)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), reload=True)
