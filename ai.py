import random
from const import *
import logging
from move import Move
from square import Square

class AIPlayer:

    def __init__(self, color):
        self.color = color  # 'black' or 'white'

    def get_all_moves(self, board):
        """
        Calculate all possible moves for the AI's pieces.
        """
        all_moves = []

        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]
                if square.has_piece() and square.piece.color == self.color:
                    piece = square.piece
                    board.calc_moves(piece, row, col, check_safety=True)  # Calculate moves
                    all_moves.extend(piece.moves)
        print(f"AI ({self.color}) possible moves: {len(all_moves)} moves")
        return all_moves

    def get_best_move(self, possible_moves):
        """
        Get the best move for the AI.
        For now, we select a random move to keep it simple, but this can be
        replaced with more advanced logic (e.g., Minimax).
        """
        if not possible_moves:
            print("No possible moves for AI.")
            return None

        # Example: Random move selection (replace with smarter logic later)
        
        return random.choice(possible_moves)
