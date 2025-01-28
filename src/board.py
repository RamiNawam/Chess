from const import *
from square import Square
from piece import *
from move import Move
from sound import Sound
import copy
import os

class Board:

    def __init__(self):
        self.squares = [[0, 0, 0, 0, 0, 0, 0, 0] for col in range(COLS)]
        self.last_move = None
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    def move(self, piece, move, testing=False):
        initial = move.initial
        final = move.final

        en_passant_empty = self.squares[final.row][final.col].isempty()

        # console board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            # en passant capture
            diff = final.col - initial.col
            if diff != 0 and en_passant_empty:
                # console board move update
                self.squares[initial.row][initial.col + diff].piece = None
                self.squares[final.row][final.col].piece = piece
                if not testing:
                    sound = Sound(
                        os.path.join('assets/sounds/capture.wav'))
                    sound.play()
            
            # pawn promotion
            else:
                self.check_promotion(piece, final)

        # king castling
        if isinstance(piece, King):
            if self.castling(initial, final) and not testing:
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook, rook.moves[-1])

        # move
        piece.moved = True

        # clear valid moves
        piece.clear_moves()

        # set last move
        self.last_move = move

    def valid_move(self, piece, move):
        return move in piece.moves

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def castling(self, initial, final):
        return abs(initial.col - final.col) == 2

    def set_true_en_passant(self, piece):
        
        if not isinstance(piece, Pawn):
            return

        for row in range(ROWS):
            for col in range(COLS):
                if isinstance(self.squares[row][col].piece, Pawn):
                    self.squares[row][col].piece.en_passant = False
        
        piece.en_passant = True

    def in_check(self, piece, move):
        temp_piece = copy.deepcopy(piece)
        temp_board = copy.deepcopy(self)
        temp_board.move(temp_piece, move, testing=True)
        
        for row in range(ROWS):
            for col in range(COLS):
                if temp_board.squares[row][col].has_enemy_piece(piece.color):
                    p = temp_board.squares[row][col].piece
                    temp_board.calc_moves(p, row, col, check_safety=False)
                    for m in p.moves:
                        if isinstance(m.final.piece, King):
                            return True
        
        return False

    def calc_moves(self, piece, row, col, check_safety=True):
        """
        Optimized move calculation for all pieces.
        """
        def is_within_bounds(r, c):
            return 0 <= r < ROWS and 0 <= c < COLS

        def add_move_if_valid(r, c):
            if is_within_bounds(r, c):
                target_square = self.squares[r][c]
                if target_square.isempty_or_enemy(piece.color):
                    move = Move(Square(row, col), Square(r, c, target_square.piece))
                    if not check_safety or not self.in_check(piece, move):
                        piece.add_move(move)

        def generate_straightline_moves(directions):
            for dr, dc in directions:
                r, c = row, col
                while True:
                    r += dr
                    c += dc
                    if not is_within_bounds(r, c):
                        break
                    target_square = self.squares[r][c]
                    if target_square.isempty():
                        add_move_if_valid(r, c)
                    elif target_square.has_enemy_piece(piece.color):
                        add_move_if_valid(r, c)
                        break
                    else:
                        break

        piece.clear_moves()

        if isinstance(piece, Pawn):
            direction = piece.dir
            if is_within_bounds(row + direction, col) and self.squares[row + direction][col].isempty():
                add_move_if_valid(row + direction, col)
                if not piece.moved and is_within_bounds(row + 2 * direction, col) and self.squares[row + 2 * direction][col].isempty():
                    add_move_if_valid(row + 2 * direction, col)
            for dc in [-1, 1]:
                if is_within_bounds(row + direction, col + dc) and self.squares[row + direction][col + dc].has_enemy_piece(piece.color):
                    add_move_if_valid(row + direction, col + dc)

        elif isinstance(piece, Knight):
            knight_moves = [
                (row - 2, col + 1), (row - 2, col - 1), (row + 2, col + 1), (row + 2, col - 1),
                (row - 1, col + 2), (row - 1, col - 2), (row + 1, col + 2), (row + 1, col - 2)
            ]
            for r, c in knight_moves:
                add_move_if_valid(r, c)

        elif isinstance(piece, Bishop):
            generate_straightline_moves([(-1, -1), (-1, 1), (1, -1), (1, 1)])

        elif isinstance(piece, Rook):
            generate_straightline_moves([(-1, 0), (1, 0), (0, -1), (0, 1)])

        elif isinstance(piece, Queen):
            generate_straightline_moves([
                (-1, -1), (-1, 1), (1, -1), (1, 1),
                (-1, 0), (1, 0), (0, -1), (0, 1)
            ])

        elif isinstance(piece, King):
            king_moves = [
                (row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1),
                (row - 1, col - 1), (row - 1, col + 1), (row + 1, col - 1), (row + 1, col + 1)
            ]
            for r, c in king_moves:
                add_move_if_valid(r, c)

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6, 7) if color == 'white' else (1, 0)

        # pawns
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        # knights
        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        # bishops
        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        # rooks
        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        # queen
        self.squares[row_other][3] = Square(row_other, 3, Queen(color))

        # king
        self.squares[row_other][4] = Square(row_other, 4, King(color))
