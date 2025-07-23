from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from .models import (
    UserRegister, UserOut, Token,
    Move, GameState, GameRecord,
    UserStats, LeaderboardEntry, SessionInfo
)
from .db import get_db, Base, engine
from .models_sql import User, Game
from .security import (
    get_password_hash, create_access_token, get_current_user, authenticate_user
)
from .game_logic import (
    empty_board, validate_move, apply_move, check_winner,
    is_board_full, next_turn, best_ai_move
)

# import os  # Unused

tags_metadata = [
    {
        "name": "auth",
        "description": "User registration, login, and session management"
    },
    {
        "name": "game",
        "description": "Tic Tac Toe play, moves, PvP and Player vs AI"
    },
    {
        "name": "history",
        "description": "User/game history"
    },
    {
        "name": "leaderboard",
        "description": "Leaderboard and player stats"
    },
]

app = FastAPI(
    title="Tic Tac Toe API",
    description="Backend for a persistent Tic Tac Toe game application. Implements users, authentication, PvP and AI games, persistent stats.",
    version="1.0.0",
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB schema (for demonstration - in prod: use migration)
Base.metadata.create_all(bind=engine)

#---------- User Registration/Login/Auth ----------

# PUBLIC_INTERFACE
@app.post("/auth/register", response_model=UserOut, tags=["auth"], summary="Register a new user")
def register_user(reg: UserRegister, db: Session = Depends(get_db)):
    """Register a new user. Usernames must be unique."""
    existing = db.query(User).filter(User.username == reg.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username taken")
    user = User(
        username=reg.username,
        hashed_password=get_password_hash(reg.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, username=user.username)

# PUBLIC_INTERFACE
@app.post("/auth/token", response_model=Token, tags=["auth"], summary="Login and get Auth Token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user and issue JWT token for session management.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=1)
    )
    return Token(access_token=access_token)

# PUBLIC_INTERFACE
@app.get("/auth/me", response_model=UserOut, tags=["auth"], summary="Get current user info")
def get_me(current_user: User = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return UserOut(id=current_user.id, username=current_user.username)

# PUBLIC_INTERFACE
@app.get("/auth/session", response_model=SessionInfo, tags=["auth"], summary="Session info")
def get_session_info(current_user: User = Depends(get_current_user)):
    """Fetch session info about current session."""
    # No explicit expiry in DB since it's JWT, but return 1-day validity for UI
    now = datetime.utcnow()
    return SessionInfo(
        user_id=current_user.id,
        username=current_user.username,
        valid_until=now + timedelta(days=1)
    )

#---------- Game APIs (Core Play) ----------

# PUBLIC_INTERFACE
@app.post("/game/start", response_model=GameState, tags=["game"], summary="Start a new game")
def start_game(
    pvp: bool = Body(..., embed=True, description="True for PvP, False for vs AI"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new game session. PvP (user will be 'X'), or vs AI (user='X', AI='O').
    """
    board = empty_board()
    game = Game(
        user_x_id=current_user.id,
        user_o_id=None if pvp else None,  # PvP handled later
        moves=[],
        winner=None,
        is_pvp=pvp
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    state = GameState(
        board=board,
        current_turn="X",
        is_over=False,
        winner=None
    )
    return state

# PUBLIC_INTERFACE
@app.post("/game/move", response_model=GameState, tags=["game"], summary="Make a move (PvP or vs AI)")
def make_move(
    game_id: int = Body(..., embed=True),
    row: int = Body(..., embed=True),
    col: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Make a move on the specified game. Handles PvP and AI. Returns updated board, turn, winner, etc.
    """
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    moves = game.moves or []
    # Rebuild board
    board = empty_board()
    turn = "X"
    for m in moves:
        board = apply_move(board, m['row'], m['col'], m['player'])
        turn = next_turn(turn)
    # Check if this is user's turn
    if (turn == "X" and game.user_x_id != current_user.id) or \
       (turn == "O" and game.user_o_id and game.user_o_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not your turn")
    # Validate and apply move
    if not validate_move(board, row, col):
        raise HTTPException(status_code=400, detail="Invalid move")
    moves.append({"row": row, "col": col, "player": turn})
    board = apply_move(board, row, col, turn)
    winner = check_winner(board)
    is_over = winner is not None or is_board_full(board)
    # If vs AI and not over, let AI play
    if not game.is_pvp and not is_over and next_turn(turn) == "O":
        ai_row, ai_col = best_ai_move(board, "O", "X")
        moves.append({"row": ai_row, "col": ai_col, "player": "O"})
        board = apply_move(board, ai_row, ai_col, "O")
        winner = check_winner(board)
        is_over = winner is not None or is_board_full(board)
    # Update game record
    game.moves = moves
    game.winner = winner
    db.commit()
    return GameState(
        board=board,
        current_turn=next_turn(turn) if not is_over else turn,
        is_over=is_over,
        winner=winner
    )

#---------- Game History APIs ----------

# PUBLIC_INTERFACE
@app.get("/history/my", response_model=List[GameRecord], tags=["history"], summary="My games history")
def my_games(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return game records (limited fields) for current user (as X or O).
    """
    games = db.query(Game).filter(
        (Game.user_x_id == current_user.id) | (Game.user_o_id == current_user.id)
    ).order_by(Game.created_at.desc()).all()
    records = []
    for g in games:
        user_x = db.query(User).filter(User.id == g.user_x_id).first()
        user_o = db.query(User).filter(User.id == g.user_o_id).first() if g.user_o_id else None
        records.append(GameRecord(
            id=g.id,
            created_at=g.created_at,
            user_x=user_x.username if user_x else None,
            user_o=user_o.username if user_o else ("AI" if not g.is_pvp else None),
            winner=g.winner,
            moves=[Move(**m) for m in g.moves] if g.moves else [],
            is_pvp=g.is_pvp
        ))
    return records

# PUBLIC_INTERFACE
@app.get("/history/all", response_model=List[GameRecord], tags=["history"], summary="All games history")
def all_games(db: Session = Depends(get_db)):
    """
    Return all game records (admin/stats).
    """
    games = db.query(Game).order_by(Game.created_at.desc()).all()
    records = []
    for g in games:
        user_x = db.query(User).filter(User.id == g.user_x_id).first()
        user_o = db.query(User).filter(User.id == g.user_o_id).first() if g.user_o_id else None
        records.append(GameRecord(
            id=g.id,
            created_at=g.created_at,
            user_x=user_x.username if user_x else None,
            user_o=user_o.username if user_o else ("AI" if not g.is_pvp else None),
            winner=g.winner,
            moves=[Move(**m) for m in g.moves] if g.moves else [],
            is_pvp=g.is_pvp
        ))
    return records

#---------- Leaderboard & Stats ----------

# PUBLIC_INTERFACE
@app.get("/leaderboard", response_model=List[LeaderboardEntry], tags=["leaderboard"], summary="Top players")
def leaderboard(db: Session = Depends(get_db)):
    """
    Leaderboard by total wins (PvP and vs AI combined).
    """
    # Simpler: count each user's games won
    all_users = db.query(User).all()
    win_counts = {u.username: 0 for u in all_users}
    games = db.query(Game).filter(Game.winner.in_(["X", "O"])).all()
    for g in games:
        if g.winner == "X" and g.user_x_id:
            u = db.query(User).filter(User.id == g.user_x_id).first()
            if u: win_counts[u.username] += 1
        if g.winner == "O" and g.user_o_id:
            u = db.query(User).filter(User.id == g.user_o_id).first()
            if u: win_counts[u.username] += 1
    entries = [LeaderboardEntry(username=k, wins=v) for k, v in sorted(win_counts.items(), key=lambda iv: -iv[1])]
    return entries

# PUBLIC_INTERFACE
@app.get("/users/me/stats", response_model=UserStats, tags=["leaderboard"], summary="My stats")
def user_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return stats (games played, wins, losses, draws) for logged in user.
    """
    user_id = current_user.id
    games = db.query(Game).filter(
        (Game.user_x_id == user_id) | (Game.user_o_id == user_id)
    ).all()
    wins, draws, losses = 0, 0, 0
    for g in games:
        user_symbol = None
        if g.user_x_id == user_id:
            user_symbol = "X"
        elif g.user_o_id == user_id:
            user_symbol = "O"
        if g.winner == user_symbol:
            wins += 1
        elif g.winner is None:
            draws += 1
        elif g.winner in ["X", "O"]:
            losses += 1
    return UserStats(
        username=current_user.username,
        games_played=len(games),
        wins=wins,
        draws=draws,
        losses=losses
    )

#---------- Health ----------

@app.get("/", tags=["default"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

