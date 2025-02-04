import random
from const import *
from move import Move
from square import Square

class AIPlayer:

    def __init__(self, color, depth=3):
        self.color = color  # 'black' or 'white'
        self.depth = depth  # Depth of the minimax search

    def get_all_moves(self, board):
        
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

    def get_best_move(self, board):
       
        best_score = float('-inf')
        best_move = None
        all_moves = self.get_all_moves(board)

        for move in all_moves:
            # Make the move
            piece = board.squares[move.initial.row][move.initial.col].piece
            board.move(piece, move, testing=True)
            # Recursively get the score of the move
            score = self.minimax(board, self.depth - 1, float('-inf'), float('inf'), False)
            # Undo the move
            board.undo_move()
            # Update best move if a better score is found
            if score > best_score:
                best_score = score
                best_move = move

        # If no best move is found, select a random move
        if best_move is None:
            best_move = random.choice(all_moves)

        return best_move

    def minimax(self, board, depth, alpha, beta, is_maximizing):
        
        if depth == 0 or board.is_game_over():
            return self.evaluate_board(board)

        if is_maximizing:
            max_eval = float('-inf')
            all_moves = self.get_all_moves(board)
            for move in all_moves:
                piece = board.squares[move.initial.row][move.initial.col].piece
                board.move(piece, move, testing=True)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.undo_move()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            opponent_color = 'white' if self.color == 'black' else 'black'
            opponent_moves = self.get_all_moves(board)
            for move in opponent_moves:
                piece = board.squares[move.initial.row][move.initial.col].piece
                board.move(piece, move, testing=True)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.undo_move()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate_board(self, board):
        
        score = 0
        for row in range(ROWS):
            for col in range(COLS):
                square = board.squares[row][col]
                if square.has_piece():
                    piece = square.piece
                    piece_value = self.get_piece_value(piece)
                    if piece.color == self.color:
                        score += piece_value
                    else:
                        score -= piece_value
        return score

    def get_piece_value(self, piece):
        
        if piece.name == 'pawn':
            return 1
        elif piece.name in ['knight', 'bishop']:
            return 3
        elif piece.name == 'rook':
            return 5
        elif piece.name == 'queen':
            return 9
        elif piece.name == 'king':
            return 100
        return 0
