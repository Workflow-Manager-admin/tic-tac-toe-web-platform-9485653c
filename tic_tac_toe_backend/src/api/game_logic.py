from typing import List, Optional, Tuple
import random

def empty_board() -> List[List[Optional[str]]]:
    """Create and return an empty 3x3 tic tac toe board."""
    return [[None for _ in range(3)] for _ in range(3)]

# PUBLIC_INTERFACE
def validate_move(board: List[List[Optional[str]]], row: int, col: int) -> bool:
    """Is the move legal (cell empty and in bounds)."""
    if 0 <= row < 3 and 0 <= col < 3:
        return board[row][col] is None
    return False

# PUBLIC_INTERFACE
def apply_move(board: List[List[Optional[str]]], row: int, col: int, symbol: str):
    """Apply given move to the board."""
    new_board = [r.copy() for r in board]
    new_board[row][col] = symbol
    return new_board

# PUBLIC_INTERFACE
def check_winner(board: List[List[Optional[str]]]) -> Optional[str]:
    """Return 'X', 'O', or None if no winner yet."""
    lines = []

    # Rows and columns
    for i in range(3):
        lines.append(board[i])
        lines.append([board[0][i], board[1][i], board[2][i]])

    # Diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        if line[0] is not None and line[0] == line[1] == line[2]:
            return line[0]
    return None

# PUBLIC_INTERFACE
def is_board_full(board: List[List[Optional[str]]]) -> bool:
    """True if no empty cells on the board."""
    return all(cell is not None for row in board for cell in row)

# PUBLIC_INTERFACE
def next_turn(current: str) -> str:
    """Get next turn symbol."""
    return "O" if current == "X" else "X"

# PUBLIC_INTERFACE
def best_ai_move(board: List[List[Optional[str]]], ai_symbol: str, user_symbol: str) -> Tuple[int, int]:
    """Simple AI: win if possible, block if must, else random empty."""
    # Try to win
    for r in range(3):
        for c in range(3):
            if board[r][c] is None:
                temp = [row.copy() for row in board]
                temp[r][c] = ai_symbol
                if check_winner(temp) == ai_symbol:
                    return (r, c)
    # Try to block user's win
    for r in range(3):
        for c in range(3):
            if board[r][c] is None:
                temp = [row.copy() for row in board]
                temp[r][c] = user_symbol
                if check_winner(temp) == user_symbol:
                    return (r, c)
    # Pick random empty
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if empty:
        return random.choice(empty)
    else:
        raise Exception("No moves left")

