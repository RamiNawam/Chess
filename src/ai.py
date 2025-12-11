import copy
import random
import time
from collections import defaultdict, namedtuple
from typing import Optional

from const import ROWS, COLS
from piece import Pawn, Knight, Bishop, Rook, Queen, King

# The user asked for a longer thinking time: give the AI 5 seconds per move.
DEFAULT_TIME_LIMIT = 5.0


# ============================================================
# Evaluation (tapered, positional heuristics)
# ============================================================
class Evaluator:
    """
    Position evaluator with tapered midgame/endgame scores.
    All values are returned from the perspective of the caller's color.
    """

    PIECE_VALUES = {
        'pawn': 100,
        'knight': 320,
        'bishop': 330,
        'rook': 500,
        'queen': 900,
        'king': 20000,
    }

    # Piece-square tables (centipawns)
    PAWN_MG = [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]
    PAWN_EG = [
        0, 0, 0, 0, 0, 0, 0, 0,
        10, 10, 10, 10, 10, 10, 10, 10,
        -10, -10, -10, -10, -10, -10, -10, -10,
        10, 10, 20, 30, 30, 20, 10, 10,
        20, 20, 30, 40, 40, 30, 20, 20,
        30, 30, 40, 50, 50, 40, 30, 30,
        80, 80, 80, 80, 80, 80, 80, 80,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    KNIGHT_MG = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    ]
    KNIGHT_EG = [
        -40, -25, -20, -20, -20, -20, -25, -40,
        -25, -10, 0, 0, 0, 0, -10, -25,
        -20, 0, 10, 15, 15, 10, 0, -20,
        -20, 5, 15, 20, 20, 15, 5, -20,
        -20, 0, 15, 20, 20, 15, 0, -20,
        -20, 5, 10, 15, 15, 10, 5, -20,
        -25, -10, 0, 5, 5, 0, -10, -25,
        -40, -25, -20, -20, -20, -20, -25, -40,
    ]

    BISHOP_MG = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ]
    BISHOP_EG = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 5, 5, 5, 5, -10,
        -10, 10, 0, 0, 0, 0, 10, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ]

    ROOK_MG = [
        0, 0, 5, 10, 10, 5, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]
    ROOK_EG = [
        0, 0, 5, 10, 10, 5, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        5, 10, 10, 10, 10, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    QUEEN_MG = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    ]
    QUEEN_EG = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    ]

    KING_MG = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20,
    ]
    KING_EG = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10, 0, 0, -10, -20, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50,
    ]

    CENTER_SQUARES = {(3, 3), (3, 4), (4, 3), (4, 4)}
    EXTENDED_CENTER = {(2, 2), (2, 3), (2, 4), (2, 5),
                       (3, 2), (3, 5), (4, 2), (4, 5),
                       (5, 2), (5, 3), (5, 4), (5, 5)}

    def evaluate(self, board, perspective_color):
        phase = self._game_phase(board)
        mg_weight = phase / 24.0
        eg_weight = 1.0 - mg_weight

        # Pre-compute attack/defense maps so we can reason about threats/defenses.
        friendly_attack_map = self._attack_map(board, perspective_color)
        opponent_color = 'white' if perspective_color == 'black' else 'black'
        opponent_attack_map = self._attack_map(board, opponent_color)

        mg = self._evaluate_phase(
            board, perspective_color, endgame=False,
            friendly_attack_map=friendly_attack_map,
            opponent_attack_map=opponent_attack_map
        )
        eg = self._evaluate_phase(
            board, perspective_color, endgame=True,
            friendly_attack_map=friendly_attack_map,
            opponent_attack_map=opponent_attack_map
        )
        return mg * mg_weight + eg * eg_weight

    def positional_gain(self, piece, target_row, target_col):
        if piece is None:
            return 0
        target_index = self._table_index(piece.color, target_row, target_col)
        table_mg, _ = self._piece_tables(piece)
        return table_mg[target_index]

    # helpers
    def _evaluate_phase(self, board, perspective_color, endgame,
                        friendly_attack_map, opponent_attack_map):
        own_score = self._evaluate_side(
            board, perspective_color, endgame,
            friendly_attack_map, opponent_attack_map
        )
        opp_color = 'white' if perspective_color == 'black' else 'black'
        opp_score = self._evaluate_side(
            board, opp_color, endgame,
            opponent_attack_map, friendly_attack_map
        )
        return own_score - opp_score

    def _evaluate_side(self, board, color, endgame,
                       friendly_attack_map, opponent_attack_map):
        material = 0
        pst_score = 0
        mobility = len(board.get_all_moves(color))
        king_safety = 0
        pawn_structure = 0
        center_control = 0
        development = 0

        pawn_files = {file_idx: 0 for file_idx in range(COLS)}
        pawn_positions = []
        king_position = None

        for row in range(ROWS):
            for col in range(COLS):
                sq = board.squares[row][col]
                if not sq.has_piece():
                    continue
                piece = sq.piece
                if piece.color != color:
                    continue

                material += self.PIECE_VALUES.get(piece.name, 0)
                table_mg, table_eg = self._piece_tables(piece)
                pst_index = self._table_index(color, row, col)
                pst_score += (table_eg if endgame else table_mg)[pst_index]

                if isinstance(piece, King):
                    king_position = (row, col)
                if isinstance(piece, Pawn):
                    pawn_files[col] += 1
                    pawn_positions.append((row, col))

                if (row, col) in self.CENTER_SQUARES:
                    center_control += 15
                elif (row, col) in self.EXTENDED_CENTER:
                    center_control += 5

                if not endgame and isinstance(piece, (Knight, Bishop)):
                    if (color == 'white' and row >= 6) or (color == 'black' and row <= 1):
                        development -= 10

        pawn_structure += self._pawn_structure_score(color, pawn_files, pawn_positions, board)
        king_safety += self._king_safety_score(color, king_position, board)

        # Threat / defense scoring:
        # - Heavy penalty if an undefended piece is under attack.
        # - Smaller penalty if defended.
        # - Small reward for defended pieces (encourages mutual protection).
        threat_penalty = 0
        defense_bonus = 0
        for row in range(ROWS):
            for col in range(COLS):
                sq = board.squares[row][col]
                if not sq.has_piece() or sq.piece.color != color:
                    continue
                piece = sq.piece
                attacked = opponent_attack_map[row][col] > 0
                defended = friendly_attack_map[row][col] > 0
                if attacked:
                    base_pen = self.PIECE_VALUES.get(piece.name, 0)
                    threat_penalty += base_pen * (0.6 if defended else 1.1)
                if defended:
                    defense_bonus += 6  # small encouragement for coordination

        mobility_weight = 4 if not endgame else 2
        center_weight = 3 if not endgame else 2  # make central control more important
        dev_weight = 6 if not endgame else 1
        king_safety_weight = 2 if endgame else 6
        pawn_structure_weight = 4

        # Material is already baked into "material"; it remains the dominant term.

        return (
            material +
            pst_score +
            mobility * mobility_weight +
            center_control * center_weight +
            development * dev_weight +
            king_safety * king_safety_weight +
            pawn_structure * pawn_structure_weight
            - threat_penalty
            + defense_bonus
        )

    def _pawn_structure_score(self, color, pawn_files, pawn_positions, board):
        score = 0
        for file_idx, count in pawn_files.items():
            if count > 1:
                score -= 15 * (count - 1)
            if count == 0:
                score -= 8

        for row, col in pawn_positions:
            # isolated
            if col not in (0, COLS - 1):
                if pawn_files[col - 1] == 0 and pawn_files[col + 1] == 0:
                    score -= 12

            # passed pawn
            direction = -1 if color == 'white' else 1
            files_to_check = [c for c in (col - 1, col, col + 1) if 0 <= c < COLS]
            enemy_pawns_ahead = False
            for f in files_to_check:
                r = row + direction
                while 0 <= r < ROWS:
                    sq = board.squares[r][f]
                    if sq.has_piece() and isinstance(sq.piece, Pawn) and sq.piece.color != color:
                        enemy_pawns_ahead = True
                        break
                    r += direction
            if not enemy_pawns_ahead:
                advance_bonus = (6 - row) if color == 'white' else row
                score += 10 + advance_bonus
        return score

    def _king_safety_score(self, color, king_pos, board):
        if king_pos is None:
            return -500

        row, col = king_pos
        pawn_shield = 0
        direction = -1 if color == 'white' else 1
        for dc in (-1, 0, 1):
            r = row + direction
            c = col + dc
            if 0 <= r < ROWS and 0 <= c < COLS:
                sq = board.squares[r][c]
                if sq.has_piece() and isinstance(sq.piece, Pawn) and sq.piece.color == color:
                    pawn_shield += 1
        safety = pawn_shield * 12
        if (row, col) in self.CENTER_SQUARES:
            safety -= 25
        return safety

    def _attack_map(self, board, color):
        """
        Squares this color attacks (used for threat/defense heuristics).
        Uses check_safety=False to approximate influence even if king would be in check.
        """
        attack = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        for r in range(ROWS):
            for c in range(COLS):
                sq = board.squares[r][c]
                if not sq.has_piece() or sq.piece.color != color:
                    continue
                piece = sq.piece
                # Generate raw moves ignoring self-check to approximate influence.
                board.calc_moves(piece, r, c, check_safety=False)
                for mv in piece.moves:
                    attack[mv.final.row][mv.final.col] += 1
        return attack

    def _table_index(self, color, row, col):
        if color == 'white':
            return (ROWS - 1 - row) * COLS + col
        return row * COLS + col

    def _piece_tables(self, piece):
        if isinstance(piece, Pawn):
            return self.PAWN_MG, self.PAWN_EG
        if isinstance(piece, Knight):
            return self.KNIGHT_MG, self.KNIGHT_EG
        if isinstance(piece, Bishop):
            return self.BISHOP_MG, self.BISHOP_EG
        if isinstance(piece, Rook):
            return self.ROOK_MG, self.ROOK_EG
        if isinstance(piece, Queen):
            return self.QUEEN_MG, self.QUEEN_EG
        if isinstance(piece, King):
            return self.KING_MG, self.KING_EG
        return [0] * 64, [0] * 64

    def _game_phase(self, board):
        phase = 0
        for row in range(ROWS):
            for col in range(COLS):
                sq = board.squares[row][col]
                if not sq.has_piece():
                    continue
                piece = sq.piece
                if isinstance(piece, (Knight, Bishop)):
                    phase += 1
                elif isinstance(piece, Rook):
                    phase += 2
                elif isinstance(piece, Queen):
                    phase += 4
        return min(phase, 24)


# ============================================================
# Move ordering heuristics
# ============================================================
class MoveOrdering:
    """
    - Transposition table move
    - MVV-LVA for captures
    - Killer moves
    - History heuristic
    - Checks
    - Quiet move positional gain
    """

    PIECE_SORT_VALUE = {
        'pawn': 100,
        'knight': 300,
        'bishop': 320,
        'rook': 500,
        'queen': 900,
        'king': 20000,
    }

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator

    def move_id(self, move):
        return (move.initial.row, move.initial.col, move.final.row, move.final.col)

    def order_moves(self, board, moves, color_to_move, killer_moves, history_heuristic, ply, tt_move=None):
        scored_moves = []
        for move in moves:
            score = 0
            if tt_move and move == tt_move:
                score += 1_500_000

            attacker = board.squares[move.initial.row][move.initial.col].piece
            victim = move.final.piece or board.squares[move.final.row][move.final.col].piece

            if victim:
                score += 1_000_000 + self._mvv_lva(attacker, victim)
            elif ply in killer_moves and any(move == killer for killer in killer_moves[ply]):
                score += 800_000

            history_score = history_heuristic.get(self.move_id(move), 0)
            score += min(history_score, 70_000)

            if self._gives_check(board, move, color_to_move):
                score += 60_000

            score += self.evaluator.positional_gain(attacker, move.final.row, move.final.col)
            scored_moves.append((score, move))

        scored_moves.sort(key=lambda item: item[0], reverse=True)
        return [m for _, m in scored_moves]

    def _mvv_lva(self, attacker, victim):
        attacker_val = self.PIECE_SORT_VALUE.get(attacker.name, 0)
        victim_val = self.PIECE_SORT_VALUE.get(victim.name, 0)
        return victim_val * 10 - attacker_val

    def _gives_check(self, board, move, color_to_move):
        opponent = 'white' if color_to_move == 'black' else 'black'
        state = self._push(board, move)
        try:
            return board.in_check(opponent)
        finally:
            self._pop(board, move, state)

    def _push(self, board, move):
        initial_sq = board.squares[move.initial.row][move.initial.col]
        final_sq = board.squares[move.final.row][move.final.col]
        moving_piece = initial_sq.piece
        captured_piece = final_sq.piece
        initial_sq.piece = None
        final_sq.piece = moving_piece
        prev_next = board.next_player
        board.next_player = 'black' if prev_next == 'white' else 'white'
        return moving_piece, captured_piece, prev_next

    def _pop(self, board, move, state):
        moving_piece, captured_piece, prev_next = state
        initial_sq = board.squares[move.initial.row][move.initial.col]
        final_sq = board.squares[move.final.row][move.final.col]
        final_sq.piece = captured_piece
        initial_sq.piece = moving_piece
        board.next_player = prev_next


# ============================================================
# Search (iterative deepening + alpha-beta + quiescence)
# ============================================================
class SearchTimeout(Exception):
    """Raised when the search runs out of its allotted time."""


TTEntry = namedtuple('TTEntry', ['depth', 'score', 'flag', 'best_move'])


class SearchEngine:
    INF = 10_000_000
    MATE_VALUE = 9_000_000

    def __init__(self, evaluator: Evaluator, ordering: MoveOrdering, ai_color: str, time_buffer: float = 0.05):
        self.evaluator = evaluator
        self.ordering = ordering
        self.ai_color = ai_color
        self.time_buffer = time_buffer

        self.tt = {}
        self.killer_moves = defaultdict(list)
        self.history_heuristic = {}

        rng = random.Random(13)
        self.z_side = rng.getrandbits(64)
        piece_names = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        self.z_table = {
            (name, color, idx): rng.getrandbits(64)
            for name in piece_names
            for color in colors
            for idx in range(64)
        }

    # iterative deepening
    def iterative_deepening(self, board, time_limit: float):
        start = time.time()
        best_move = None
        depth = 1

        while True:
            elapsed = time.time() - start
            if elapsed >= max(0.01, time_limit - self.time_buffer):
                break
            try:
                score, move = self.search_root(board, depth, start, time_limit)
                if move:
                    best_move = move
                depth += 1
            except SearchTimeout:
                break

        return best_move or self._fallback_move(board)

    def search_root(self, board, depth, start_time, time_limit):
        color_to_move = board.next_player
        alpha, beta = -self.INF, self.INF
        tt_entry = self.tt.get(self._hash(board))
        tt_move = tt_entry.best_move if tt_entry else None

        moves = board.get_all_moves(color_to_move)
        if not moves:
            if board.in_check(color_to_move):
                return (-self.MATE_VALUE, None)
            return 0, None

        ordered = self.ordering.order_moves(
            board, moves, color_to_move, self.killer_moves, self.history_heuristic, 0, tt_move=tt_move
        )

        best_move = None
        alpha_orig = alpha
        for move in ordered:
            self._ensure_time(start_time, time_limit)

            state = self._make_move(board, move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, start_time, time_limit, ply=1)
            self._undo_move(board, move, state)

            if score > alpha:
                alpha = score
                best_move = move

            if alpha >= beta:
                self._store_killer(move, ply=0)
                self._update_history(move, depth, ply=0)
                break

        flag = 'EXACT'
        if alpha <= alpha_orig:
            flag = 'UPPER'
        elif alpha >= beta:
            flag = 'LOWER'
        self.tt[self._hash(board)] = TTEntry(depth, alpha, flag, best_move)

        return alpha, best_move

    def _negamax(self, board, depth, alpha, beta, start_time, time_limit, ply):
        self._ensure_time(start_time, time_limit)

        key = self._hash(board)
        entry = self.tt.get(key)
        if entry and entry.depth >= depth:
            if entry.flag == 'EXACT':
                return entry.score
            if entry.flag == 'LOWER':
                alpha = max(alpha, entry.score)
            elif entry.flag == 'UPPER':
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score

        if depth <= 0:
            return self._quiescence(board, alpha, beta, start_time, time_limit, ply)

        color_to_move = board.next_player
        moves = board.get_all_moves(color_to_move)
        if not moves:
            if board.in_check(color_to_move):
                return -self.MATE_VALUE + ply
            return 0

        tt_move = entry.best_move if entry else None
        ordered_moves = self.ordering.order_moves(
            board, moves, color_to_move, self.killer_moves, self.history_heuristic, ply, tt_move=tt_move
        )

        alpha_orig = alpha
        best_move = None
        for idx, move in enumerate(ordered_moves):
            is_capture = move.final.piece is not None
            reduction = 0
            if depth >= 3 and idx >= 3 and not is_capture:
                reduction = 1  # LMR for quiet late moves

            state = self._make_move(board, move)
            score = -self._negamax(board, depth - 1 - reduction, -beta, -alpha, start_time, time_limit, ply + 1)
            self._undo_move(board, move, state)

            if score > alpha:
                alpha = score
                best_move = move
            if alpha >= beta:
                if not is_capture:
                    self._store_killer(move, ply)
                    self._update_history(move, depth, ply)
                break

        flag = 'EXACT'
        if alpha <= alpha_orig:
            flag = 'UPPER'
        elif alpha >= beta:
            flag = 'LOWER'
        self.tt[key] = TTEntry(depth, alpha, flag, best_move)
        return alpha

    def _quiescence(self, board, alpha, beta, start_time, time_limit, ply):
        self._ensure_time(start_time, time_limit)

        sign = 1 if board.next_player == self.ai_color else -1
        stand_pat = sign * self.evaluator.evaluate(board, self.ai_color)

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        color_to_move = board.next_player
        moves = board.get_all_moves(color_to_move)
        tactical = [m for m in moves if m.final.piece is not None or self._is_checking_move(board, m, color_to_move)]
        ordered = self.ordering.order_moves(
            board, tactical, color_to_move, self.killer_moves, self.history_heuristic, ply, tt_move=None
        )

        for move in ordered:
            self._ensure_time(start_time, time_limit)
            state = self._make_move(board, move)
            score = -self._quiescence(board, -beta, -alpha, start_time, time_limit, ply + 1)
            self._undo_move(board, move, state)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    # move helpers
    def _make_move(self, board, move):
        initial_sq = board.squares[move.initial.row][move.initial.col]
        final_sq = board.squares[move.final.row][move.final.col]
        moving_piece = initial_sq.piece
        captured_piece = final_sq.piece

        prev_last_move = board.last_move
        prev_next = board.next_player
        prev_moved_flag = moving_piece.moved

        initial_sq.piece = None
        final_sq.piece = moving_piece
        moving_piece.moved = True

        board.last_move = move
        board.next_player = 'black' if prev_next == 'white' else 'white'
        return moving_piece, captured_piece, prev_last_move, prev_next, prev_moved_flag

    def _undo_move(self, board, move, state):
        moving_piece, captured_piece, prev_last_move, prev_next, prev_moved_flag = state
        initial_sq = board.squares[move.initial.row][move.initial.col]
        final_sq = board.squares[move.final.row][move.final.col]
        initial_sq.piece = moving_piece
        final_sq.piece = captured_piece
        moving_piece.moved = prev_moved_flag
        board.last_move = prev_last_move
        board.next_player = prev_next

    def _store_killer(self, move, ply):
        killers = self.killer_moves[ply]
        if move in killers:
            return
        killers.insert(0, move)
        if len(killers) > 2:
            killers.pop()

    def _update_history(self, move, depth, ply):
        key = self.ordering.move_id(move)
        self.history_heuristic[key] = self.history_heuristic.get(key, 0) + depth * depth

    def _fallback_move(self, board):
        moves = board.get_all_moves(board.next_player)
        return moves[0] if moves else None

    def _is_checking_move(self, board, move, color_to_move):
        opponent = 'white' if color_to_move == 'black' else 'black'
        state = self._make_move(board, move)
        try:
            return board.in_check(opponent)
        finally:
            self._undo_move(board, move, state)

    # hashing and time
    def _hash(self, board):
        h = 0
        for r in range(8):
            for c in range(8):
                piece = board.squares[r][c].piece
                if not piece:
                    continue
                idx = r * 8 + c
                h ^= self.z_table.get((piece.name, piece.color, idx), 0)
        if board.next_player == 'white':
            h ^= self.z_side
        return h

    def _ensure_time(self, start_time, time_limit):
        if time.time() - start_time > time_limit - self.time_buffer:
            raise SearchTimeout()


# ============================================================
# Public AI wrapper
# ============================================================
class AIPlayer:
    """
    High-level wrapper for the search pipeline:
    - Iterative deepening with alpha-beta + quiescence
    - Move ordering (MVV-LVA, killer, history, checks)
    - Transposition table with Zobrist hashing
    """

    def __init__(self, color, time_limit: float = DEFAULT_TIME_LIMIT):
        self.color = color
        self.time_limit = time_limit

        evaluator = Evaluator()
        ordering = MoveOrdering(evaluator)
        self.search = SearchEngine(evaluator, ordering, ai_color=color)

    def choose_move(self, board, time_limit: Optional[float] = None):
        """
        Public entry point used by the game loop.
        A clone of the board is searched so the UI state is never mutated.
        """
        limit = time_limit or self.time_limit
        board_copy = copy.deepcopy(board)
        board_copy.next_player = board.next_player
        return self.search.iterative_deepening(board_copy, limit)

    # Legacy helpers kept for compatibility with existing call sites
    def get_all_moves(self, board):
        return board.get_all_moves(self.color)

    def get_best_move(self, board):
        return self.choose_move(board, self.time_limit)
