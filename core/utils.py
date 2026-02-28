# core/utils.py

def is_valid_position(row: int, col: int) -> bool:
    """
        Check whether a pair (row, col) is in the 8x8 chess board or not.
    """
    return 0 <= row < 8 and 0 <= col < 8