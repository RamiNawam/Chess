import pygame
import sys

from const import *
from game import Game
from square import Square
from move import Move
from ai import AIPlayer  # Import the AI player class
import logging

class Main:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        self.game = None  # Initialize later depending on the mode

    def draw_text(self, text, font, color, x, y, centered=False):
        """Helper function to render text."""
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(x, y) if centered else None)
        self.screen.blit(surface, rect if centered else (x, y))

    def draw_button(self, rect, text, font, color, text_color, border_color, border_radius=20):
        """Helper function to render a button with text."""
        pygame.draw.rect(self.screen, border_color, rect, border_radius=border_radius)
        pygame.draw.rect(self.screen, color, rect.inflate(-6, -6), border_radius=border_radius)
        self.draw_text(text, font, text_color, rect.centerx, rect.centery, centered=True)

    def show_menu(self):
        screen = self.screen
        clock = pygame.time.Clock()

        # Fonts
        title_font = pygame.font.Font(None, 100)  # Large font for the title
        button_font = pygame.font.Font(None, 50)  # Font for buttons

        # Colors
        bg_color = (30, 30, 30)
        title_color = (240, 240, 240)
        button_color = (60, 120, 180)
        button_hover_color = (80, 140, 200)
        button_text_color = (255, 255, 255)
        border_color = (255, 255, 255)

        # Button dimensions and positions
        button_width, button_height = 250, 100
        spacing = 40
        pvp_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height - spacing, button_width, button_height)
        ai_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + spacing, button_width, button_height)

        while True:
            # Draw background
            screen.fill(bg_color)

            # Title
            self.draw_text("CHESS GAME", title_font, title_color, WIDTH // 2, HEIGHT // 4, centered=True)

            # Handle events
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if pvp_button_rect.collidepoint(mouse_pos):
                        return "pvp"
                    elif ai_button_rect.collidepoint(mouse_pos):
                        return "ai"

            # Draw buttons
            pvp_color = button_hover_color if pvp_button_rect.collidepoint(mouse_pos) else button_color
            ai_color = button_hover_color if ai_button_rect.collidepoint(mouse_pos) else button_color

            self.draw_button(pvp_button_rect, "PvP", button_font, pvp_color, button_text_color, border_color)
            self.draw_button(ai_button_rect, "AI", button_font, ai_color, button_text_color, border_color)

            pygame.display.update()
            clock.tick(60)

    def mainloop(self):
        # Show the menu and get the selected mode
        mode = self.show_menu()

        if mode == "pvp":
            self.game = Game()  # Initialize the PvP game
            self.start_pvp_game()
        elif mode == "ai":
            self.game = Game()  # Initialize the game for AI mode
            ai = AIPlayer('black')  # AI plays as black
            self.start_ai_game()

    def start_pvp_game(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger

        while True:
            # Show methods
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            for event in pygame.event.get():

                # Mouse click
                if event.type == pygame.MOUSEBUTTONDOWN:
                    dragger.update_mouse(event.pos)

                    clicked_row = dragger.mouseY // SQSIZE
                    clicked_col = dragger.mouseX // SQSIZE

                    # If clicked square has a piece
                    if board.squares[clicked_row][clicked_col].has_piece():
                        piece = board.squares[clicked_row][clicked_col].piece
                        # Valid piece (color)?
                        if piece.color == game.next_player:
                            board.calc_moves(piece, clicked_row, clicked_col, check_safety=True)
                            dragger.save_initial(event.pos)
                            dragger.drag_piece(piece)
                            # Show methods 
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_moves(screen)
                            game.show_pieces(screen)

                # Mouse motion
                elif event.type == pygame.MOUSEMOTION:
                    motion_row = event.pos[1] // SQSIZE
                    motion_col = event.pos[0] // SQSIZE

                    game.set_hover(motion_row, motion_col)

                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        # Show methods
                        game.show_bg(screen)
                        game.show_last_move(screen)
                        game.show_moves(screen)
                        game.show_pieces(screen)
                        game.show_hover(screen)
                        dragger.update_blit(screen)

                # Mouse release
                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)

                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE

                        # Create possible move
                        initial = Square(dragger.initial_row, dragger.initial_col)
                        final = Square(released_row, released_col)
                        move = Move(initial, final)

                        # Valid move?
                        if board.valid_move(dragger.piece, move):
                            # Normal capture
                            captured = board.squares[released_row][released_col].has_piece()
                            board.move(dragger.piece, move)

                            board.set_true_en_passant(dragger.piece)

                            # Sounds
                            game.play_sound(captured)
                            # Show methods
                            game.show_bg(screen)
                            game.show_last_move(screen)
                            game.show_pieces(screen)
                            # Next turn
                            game.next_turn()

                    dragger.undrag_piece()

                # Key press
                elif event.type == pygame.KEYDOWN:
                    # Changing themes
                    if event.key == pygame.K_t:
                        game.change_theme()

                    # Resetting the game
                    if event.key == pygame.K_r:
                        game.reset()
                        game = self.game
                        board = self.game.board
                        dragger = self.game.dragger

                # Quit application
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            pygame.display.update()

    def start_ai_game(self):
        screen = self.screen
        game = self.game
        board = self.game.board
        dragger = self.game.dragger
        ai = AIPlayer('black')  # Initialize the AI as black

        while True:
            # Render the game elements
            game.show_bg(screen)
            game.show_last_move(screen)
            game.show_moves(screen)
            game.show_pieces(screen)
            game.show_hover(screen)

            if dragger.dragging:
                dragger.update_blit(screen)

            for event in pygame.event.get():
                # Quit the game
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Player's turn
                if game.next_player == 'white':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        dragger.update_mouse(event.pos)
                        clicked_row = dragger.mouseY // SQSIZE
                        clicked_col = dragger.mouseX // SQSIZE

                        # Check if clicked square has a piece
                        if board.squares[clicked_row][clicked_col].has_piece():
                            piece = board.squares[clicked_row][clicked_col].piece
                            if piece.color == 'white':  # Player can only move white pieces
                                board.calc_moves(piece, clicked_row, clicked_col, check_safety=True)
                                dragger.save_initial(event.pos)
                                dragger.drag_piece(piece)

                    elif event.type == pygame.MOUSEMOTION:
                        motion_row = event.pos[1] // SQSIZE
                        motion_col = event.pos[0] // SQSIZE
                        game.set_hover(motion_row, motion_col)

                        if dragger.dragging:
                            dragger.update_mouse(event.pos)

                    elif event.type == pygame.MOUSEBUTTONUP:
                        if dragger.dragging:
                            dragger.update_mouse(event.pos)
                            released_row = dragger.mouseY // SQSIZE
                            released_col = dragger.mouseX // SQSIZE
                            initial = Square(dragger.initial_row, dragger.initial_col)
                            final = Square(released_row, released_col)
                            move = Move(initial, final)

                            # Validate and execute the move
                            if board.valid_move(dragger.piece, move):
                                captured = board.squares[released_row][released_col].has_piece()
                                board.move(dragger.piece, move)
                                board.set_true_en_passant(dragger.piece)
                                game.play_sound(captured)
                                game.next_turn()  # Switch to AI's turn

                        dragger.undrag_piece()

            # AI's turn
                elif game.next_player == 'black':
                    # Get all possible moves for AI
                    all_moves = ai.get_all_moves(board)

                    # Check for checkmate or stalemate
                    if not all_moves:
                        if board.in_check(board.get_king('black'), None):  # Check if Black is in check
                            print("Checkmate! White wins!")
                        else:
                            print("Stalemate! It's a draw!")
                        pygame.quit()
                        sys.exit()

                    # Select the best move
                    best_move = ai.get_best_move(all_moves)

                    if best_move:
                        initial = best_move.initial
                        final = best_move.final
                        piece = board.squares[initial.row][initial.col].piece

                        # Execute the move
                        board.move(piece, best_move)
                        board.set_true_en_passant(piece)
                        game.play_sound(captured=final.has_piece())
                        game.next_turn()  # Switch to player's turn

            pygame.display.update()








main = Main()
main.mainloop()
