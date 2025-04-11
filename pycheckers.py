import pygame

from pygame.locals import (
    MOUSEBUTTONDOWN,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)
# Direction Constants
NORTHWEST = (-1, -1)
NORTHEAST = (-1, 1)
SOUTHWEST = (1, -1)
SOUTHEAST = (1, 1)

pygame.init()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True
selected_piece = None
turn = 'white'

# ----- Setup Menu Graphical Components -
'''
    Button Class:
        Parameterize button size, text, and color
        Add hover effect
        Add callback function for button click
'''
class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height) # Set button position and size
        self.text = text
        self.callback = callback    # set callback function
        self.font = pygame.font.Font(None, 36)
        self.color = (50, 150, 50)
        self.hover_color = (100, 200, 100)
        self.text_color = (255, 255, 255)

    def draw(self, surface):
        # Change the color if mouse hovers over button
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.color
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color
        # Draw the button and text
        pygame.draw.rect(surface, current_color, self.rect)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    # When button gets pressed by mouse, perform function
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

'''
wrap_text() Function:
    Wraps text to fit within a specified width
    Splits text into lines that fit within the max width
'''
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''
    
    for word in words:
        # Check if adding the next word exceeds the max width
        test_line = current_line + word + " "
        if font.size(test_line)[0] > max_width:
            # current_line is not empty, push it and start a new one
            if current_line != "":
                lines.append(current_line.strip())
            current_line = word + " "
        else:
            current_line = test_line
    # Add the last line if it exists 
    if current_line:
        lines.append(current_line)
    
    return lines

'''
    draw_instructions() Function:
        Draws the instructions on the screen
        Utilizes wrap_text to ensure text fits within the panel
'''
def draw_instructions(surface, instructions, font, color, x, y, max_width, line_spacing=5):
    # Wrap each instruction text to fit within the max width
    for text in instructions:
        wrapped_text = wrap_text(text, font, max_width)
        # Draw each line of wrapped text
        for line in wrapped_text:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x, y))
            y += text_surface.get_height() + line_spacing

'''
    show_win_screen_and_reset() Function:
        Displays a win message for the winner
        Counts down 5 seconds before resetting the game
        Allows user to exit during countdown
'''
def show_win_screen_and_reset(game_over_status):
    global screen, clock, running

    if game_over_status == 'draw':
        win_message = "It's a Draw!"
    elif game_over_status in ['white', 'red']:
        win_message = f"{game_over_status.capitalize()} Wins!"
    else: # Should not happen, but just in case
        win_message = "Game Over!"

    box_width = 400
    box_height = 200
    box_x = (SCREEN_WIDTH - box_width) // 2
    box_y = (SCREEN_HEIGHT - box_height) // 2
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

    box_color = (50, 50, 150)
    text_color = (255, 255, 255)

    start_time = pygame.time.get_ticks()
    duration = 5000 # 5 seconds in milliseconds

    while pygame.time.get_ticks() < start_time + duration:
        # Allow closing during wait
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False # Signal the main loop to terminate
                return # Exit this function immediately
            if event.type == KEYDOWN:
                 if event.key == K_ESCAPE: # Allow escape to quit too
                     running = False
                     return

        # Calculate Remaining Time
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_ms = duration - elapsed_time
        remaining_sec = max(0, (remaining_ms + 999) // 1000)

        # Draw the message box
        pygame.draw.rect(screen, box_color, box_rect, border_radius=15)
        pygame.draw.rect(screen, text_color, box_rect, width=2, border_radius=15) # Optional border

        # Render and position text
        win_text_surface = win_font_large.render(win_message, True, text_color)
        win_text_rect = win_text_surface.get_rect(center=(box_rect.centerx, box_rect.centery - 30))

        countdown_text = f"Resetting in {remaining_sec} seconds..."
        countdown_surface = win_font_small.render(countdown_text, True, text_color)
        countdown_rect = countdown_surface.get_rect(center=(box_rect.centerx, box_rect.centery + 40))

        screen.blit(win_text_surface, win_text_rect)
        screen.blit(countdown_surface, countdown_rect)

        # update display
        pygame.display.flip()

        # loop speed
        clock.tick(30) # Update roughly 30 times per second

    # reset game when loop is finished
    if running: # Only reset if the user didn't quit during the countdown
        reset_game()

# ----- Setup Board and Checker Graphical Components ----- #
'''
    Tile Class:
        Represents each square on the board
        Has a color (white/red) and a checker (if present)
'''
class Tile:
    def __init__(self, x_start, y_start, width_height, is_white, hasChecker = None):
        self.x_start = x_start
        self.y_start = y_start
        self.width_height = width_height
        self.is_white = is_white
        self.hasChecker = hasChecker

    def draw(self, surface):
        if self.is_white:
            color = (255, 255, 255)
        else:
            color = (0, 0, 0)
        pygame.draw.rect(surface, color, (self.x_start, self.y_start, self.width_height, self.width_height))

'''
    Checker Class:
        Represents each checker piece
        Has a position, radius, and color (white/red)
        Can be a king (if it reaches the opposite side)
'''
class Checker:
    def __init__(self, x_pos, y_pos, radius, king, is_white):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.king = king
        self.radius = radius
        self.is_white = is_white
        

    def draw(self, surface):
        if self.is_white:
            color = (255, 0, 0)  
        else:
            color = (255, 255,255)

        # Add a border to the king piece
        if self.king:
            border_color = (255, 223, 0)
            border_thickness = 3          
            # Draw the border circle first
            pygame.draw.circle(surface, border_color, (self.x_pos, self.y_pos), self.radius + border_thickness, 0)

        pygame.draw.circle(surface, color, (self.x_pos, self.y_pos), self.radius, 0)

'''
    create_board() Function:
        Create 8x8 Checker board using Tile objects
        Each tile is either white or red
'''
def create_board(board_x, board_y, tile_size):
    board = []
    for row in range(8):
        board_row = []
        for col in range(8):
            is_white = (row + col) % 2 == 0
            tile = Tile(board_x + col * tile_size, board_y + row * tile_size, tile_size, is_white)
            board_row.append(tile)
        board.append(board_row)
    return board

'''
    set_checkers() Function:
        Sets up the initial positions of the checkers on the board
        Creates Checker objects and assigns them to the appropriate tiles
'''
def set_checkers(board, tile_size):
    checkers = []
    
    radius = tile_size // 2 - 10

    for row_i, row in enumerate(board):
        for tile in row:
            tile.hasChecker = None
            if not tile.is_white:
                x_pos = tile.x_start + tile.width_height // 2
                y_pos = tile.y_start + tile.width_height // 2
                checker_obj = None
                # Assign color based on row index
                if row_i < 3:
                    checker_obj = Checker(x_pos, y_pos, radius, False, False)
                elif row_i > 4:
                    checker_obj = Checker(x_pos, y_pos, radius, False, True)
                
                # Assign checker to tile and add to checkers list
                if checker_obj:
                    checkers.append(checker_obj)
                    tile.hasChecker = checker_obj
    return checkers


# ----- Game State Logic and Behavior ----- #
'''
    GameState Class:
        Logic for game state
        Tracks the current state
        Handles piece selection, movement, and turn switching
'''
class GameState:
    def __init__(self, board):
        self.selected_piece = None
        self.turn = 'white'  # white moves first (your red pieces)
        self.valid_moves = []
        self.must_capture = False  # Track if a capture is mandatory
        self.board = board
        self.moves_since_last_capture = 0  # Track moves since last capture

    """Returns coordinates relative to pixel in given direction"""
    def rel(self, dir, pixel):
        return (pixel[0] + dir[0], pixel[1] + dir[1])
    """Check if coordinates are within board bounds"""
    def on_board(self, pixel):
        return 0 <= pixel[0] < 8 and 0 <= pixel[1] < 8

    """Returns possible move directions from a position without checking board state"""
    def blind_legal_moves(self, pixel):
        
        x, y = pixel
        tile = self.board[x][y]
        
        if not tile.hasChecker:
            return []
            
        checker = tile.hasChecker
        moves = []
        
        # Regular pieces can only move forward
        if not checker.king:
            if checker.is_white:  # White moves "up" (negative row)
                moves.extend([self.rel(NORTHWEST, (x,y)), self.rel(NORTHEAST, (x,y))])
            else:  # Red moves "down" (positive row)
                moves.extend([self.rel(SOUTHWEST, (x,y)), self.rel(SOUTHEAST, (x,y))])
        else:  # Kings can move in all directions
            moves.extend([
                self.rel(NORTHWEST, (x,y)), 
                self.rel(NORTHEAST, (x,y)),
                self.rel(SOUTHWEST, (x,y)), 
                self.rel(SOUTHEAST, (x,y))
            ])
            
        return moves

    """Returns actual legal moves considering board state"""
    def legal_moves(self, pixel, hop=False):
        x, y = pixel
        tile = self.board[x][y]
        
        if not tile.hasChecker:
            return []
            
        checker = tile.hasChecker
        blind_moves = self.blind_legal_moves(pixel)
        legal_moves = []
        capture_moves = []
        
        for move in blind_moves:
            if not self.on_board(move):
                continue
                
            mx, my = move
            target_tile = self.board[mx][my]
            
            # Normal move to empty space
            if not hop and not target_tile.hasChecker:
                legal_moves.append(move)
                
            # Capture move
            elif target_tile.hasChecker and target_tile.hasChecker.is_white != checker.is_white:
                # Calculate landing position after jump
                jump_x = mx + (mx - x)
                jump_y = my + (my - y)
                
                if self.on_board((jump_x, jump_y)):
                    jump_tile = self.board[jump_x][jump_y]
                    if not jump_tile.hasChecker:
                        capture_moves.append((jump_x, jump_y))
        
        # In checkers, captures are mandatory
        if capture_moves:
            return capture_moves
        elif not hop:  # Only return normal moves if no captures available
            return legal_moves
        else:
            return []
    
    """ check legal_moves method to check if a player has any legal moves left"""
    def has_legal_moves(self, player_color_turn):
        is_white_turn = (player_color_turn == 'white')
        for row in range(8):
            for col in range(8):
                tile = self.board[row][col]
                if tile.hasChecker and tile.hasChecker.is_white == is_white_turn:
                    # found a piece belonging to the current player, check its moves
                    moves = self.legal_moves((row, col))
                    if moves: # if nonempty, found at least one legal move
                        return True
        return False
    
    """Move a piece from from_pos to to_pos, handling captures and promotions"""
    def move_piece(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos

        from_tile = self.board[from_row][from_col]
        to_tile = self.board[to_row][to_col]

        checker = from_tile.hasChecker

        # ----- Draw Counter Logic ------ #
        captured_piece = False # Flag to track if a capture happened this move

        # Handle captures
        if abs(to_row - from_row) == 2:  # This is a capture move
            captured_piece = True # Set the flag
            self.moves_since_last_capture = 0 # <<< RESET counter on capture
            jumped_row = (from_row + to_row) // 2
            jumped_col = (from_col + to_col) // 2
            jumped_tile = self.board[jumped_row][jumped_col]

            # Remove the captured checker from the checkers list
            global checkers # Need access to modify the global list
            checker_to_remove = jumped_tile.hasChecker
            if checker_to_remove in checkers: # Ensure it's actually in the list
                 checkers.remove(checker_to_remove)
            else:
                 # Fallback check if instance comparison fails (less likely needed now)
                 for i, c in enumerate(checkers):
                      if c.x_pos == jumped_tile.x_start + tile_size // 2 and \
                         c.y_pos == jumped_tile.y_start + tile_size // 2:
                           checkers.pop(i)
                           break

            jumped_tile.hasChecker = None

            # Move the piece *after* handling capture details
            from_tile.hasChecker = None
            to_tile.hasChecker = checker
            checker.x_pos = board_x + to_col * tile_size + tile_size // 2
            checker.y_pos = board_y + to_row * tile_size + tile_size // 2

            # Check for additional captures
            self.valid_moves = self.legal_moves(to_pos, hop=True)
            if self.valid_moves:
                self.selected_piece = to_pos
                self.must_capture = True
                # We don't increment moves_since_last_capture here as it was reset
                return False # Turn isn't over yet

        else: # Normal move (no capture)
             from_tile.hasChecker = None
             to_tile.hasChecker = checker
             checker.x_pos = board_x + to_col * tile_size + tile_size // 2
             checker.y_pos = board_y + to_row * tile_size + tile_size // 2
             # <<< INCREMENT counter only on non-capture moves
             self.moves_since_last_capture += 1

        # Handle king promotion
        promoted = False
        if not checker.king:
            if (checker.is_white and to_row == 0) or (not checker.is_white and to_row == 7):
                checker.king = True
                promoted = True
                # Removed radius increase as per previous request for border

        # reset ONLY on capture
        # if captured_piece or promoted:
        #     self.moves_since_last_capture = 0

        self.must_capture = False
        print(f"Moves since last capture: {self.moves_since_last_capture}")
        return True  # Turn is complete

    """Checks all game over conditions: win, draw, no moves."""
    def check_game_over(self):
        global checkers # Need global checkers list for piece count

        # Check Win by Elimination
        white_pieces = 0
        red_pieces = 0
        for checker in checkers:
             if checker.is_white: red_pieces += 1
             else: white_pieces += 1

        if red_pieces == 0: return 'white'
        if white_pieces == 0: return 'red'

        # Check Draw by 40 Moves Rule (40 ply without capture)
        if self.moves_since_last_capture >= 40:
             print(f"Draw condition met: {self.moves_since_last_capture} moves.")
             return 'draw'

        # Check Win by No Legal Moves (for the player whose turn it CURRENTLY is)
        if not self.has_legal_moves(self.turn):
             # If the current player has no moves, the *other* player wins
             print(f"No legal moves for {self.turn}. Winner: {'red' if self.turn == 'white' else 'white'}")
             return 'red' if self.turn == 'white' else 'white'

        # No game over condition met
        return None


# ----- Reset Game Button Behavior ----- #
'''
    reset_game() Function:
        Initialize game board
        Used when reset button is clicked
'''
def reset_game():
    global board, checkers, game_state
    board = create_board(board_x, board_y, tile_size)
    checkers = set_checkers(board, tile_size)
    game_state = GameState(board)
    print("Game reset")

# ----- Initialize Game State ----- #
# Initialization of panel dimensions for menu
PANEL_WIDTH = 300
panel_x = 50
panel_y = 50
panel_rect = pygame.Rect(panel_x, panel_y, PANEL_WIDTH, SCREEN_HEIGHT - 100)

# Font initialization for win screen
win_font_large = pygame.font.Font(None, 72)
win_font_small = pygame.font.Font(None, 36)

# Instruction Board dimensions and placement
tile_size = 80
board_width = 8 * tile_size
board_height = 8 * tile_size
# Create board sligtly to the right of the instruction panel
board_x = panel_x + PANEL_WIDTH + 20
board_y = (SCREEN_HEIGHT - board_height) // 2

# Instructions text in panel
instruction_font = pygame.font.Font(None, 24)
instructions = [
    "Instructions:",
    "- Red moves first.",
    "- Click a piece to select it. Valid moves are highlighted green.",
    "- Click a highlighted square to move.",
    "- Pieces move diagonally forward to the next empty dark square.",
    "- Jump over an opponent's piece diagonally to capture it.",
    "- Multiple jumps in one turn are possible if available.",
    "- Captures are mandatory! If a jump exists, that is the only move you can make.",
    "- Reach the opponent's back row to promote a piece to a King.",
    "- Kings can move diagonally forward AND backward.",
    "- Win when the opponent has no pieces left or cannot move.",
    "- A draw occurs if neither player makes a capture after 40 moves.",
    "- Click 'New Game' to reset the game anytime."
]

# Initial creation of board and checkers
reset_game()

# Initial creation of side panel
new_game_button = Button(panel_x + PANEL_WIDTH/6, panel_y + 550, 200, 50, "New Game", reset_game)


# ----- Main Game Loop ----- #
while running:
    game_over_status = None

    # If user quits game (click x to close window)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Let button process the event first
        new_game_button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over_status:
            pos = pygame.mouse.get_pos()
            # Convert to board coordinates
            col = (pos[0] - board_x) // tile_size
            row = (pos[1] - board_y) // tile_size
            
            if not (0 <= row < 8 and 0 <= col < 8):
                # Clicked outside board
                game_state.selected_piece = None
                game_state.valid_moves = []
                continue
                
            
            if game_state.must_capture and (row, col) != game_state.selected_piece:
                 # If a capture is found, only allow clicking the forced piece or its valid capture moves
                 if game_state.selected_piece and (row, col) not in game_state.valid_moves:
                      print("Must complete capture sequence.")
                      continue # Ignore clicks elsewhere during multi-capture
            
            tile = game_state.board[row][col]

            if tile.hasChecker and tile.hasChecker.is_white == (game_state.turn == 'white'):
                # Check if any piece for this turn has a mandatory capture available
                must_capture_overall = False
                for r_check in range(8):
                    for c_check in range(8):
                        check_tile = game_state.board[r_check][c_check]
                        if check_tile.hasChecker and check_tile.hasChecker.is_white == (game_state.turn == 'white'):
                            piece_capture_moves = game_state.legal_moves((r_check, c_check), hop=False)
                            if any(abs(move[0] - r_check) == 2 for move in piece_capture_moves):
                                must_capture_overall = True

                if must_capture_overall:
                    if any(abs(move[0] - row) == 2 for move in game_state.legal_moves((row, col))):
                        game_state.selected_piece = (row, col)
                        game_state.valid_moves = game_state.legal_moves((row, col))
                        print(f"Selected piece {(row,col)} for mandatory capture.")
                    else:
                        print("Cannot select this piece, a capture is mandatory elsewhere.")
                else:
                    game_state.selected_piece = (row, col)
                    game_state.valid_moves = game_state.legal_moves((row, col))
                    print(f"Selected piece {(row,col)}.")
                continue

            if game_state.selected_piece:
                print(f"Attempting move from {game_state.selected_piece} to {(row, col)}") # Debug
                if (row, col) in game_state.valid_moves:
                    turn_complete = game_state.move_piece(game_state.selected_piece, (row, col))

                    if turn_complete:
                        # --- Turn potentially ends, check game over ---
                        game_state.turn = 'red' if game_state.turn == 'white' else 'white'
                        game_state.selected_piece = None
                        game_state.valid_moves = []
                        game_over_status = game_state.check_game_over()
                        if game_over_status:
                            print(f"Game Over! Result: {game_over_status}")
                    else:
                        print(f"Continue capture sequence from {game_state.selected_piece}")
                else:
                    # Invalid move clicked
                    print(f"Invalid move to {(row, col)}. Valid: {game_state.valid_moves}")

    # Default screen color (gray)
    screen.fill((128, 128, 128))

    # Draw Board and Checkers (Left Side)
    for row in board:
        for tile in row:
            tile.draw(screen)

    for checker in checkers:
        checker.draw(screen)

    # Draw Right-side Panel (Holding Reset)
    pygame.draw.rect(screen, (200,200,200), panel_rect)
    padding = 10
    # Render instructions
    draw_instructions(screen, instructions, instruction_font, (0,0,0), panel_x + padding, panel_y + padding, PANEL_WIDTH - (2 * padding))

    # Draw reset button
    new_game_button.draw(screen)

    # Draw Highlights (Selected piece and valid moves)
    if game_state.selected_piece:
        s_row, s_col = game_state.selected_piece
        selected_tile = game_state.board[s_row][s_col]
        pygame.draw.rect(screen, (255,255,0), (selected_tile.x_start, selected_tile.y_start, selected_tile.width_height, selected_tile.width_height), 3) # Yellow outline

    if game_state.valid_moves:
        if game_state.must_capture:
            # Toggle flash every 500ms to signal mandatory capture
            flash_on = pygame.time.get_ticks() % 1000 < 500
            if flash_on:
                flash_color = (255, 0, 0)  # Red flash
            else:
                flash_color = (255, 255, 0)
            for move in game_state.valid_moves:
                v_row, v_col = move
                valid_tile = game_state.board[v_row][v_col]
                pygame.draw.rect(screen, flash_color, (valid_tile.x_start, valid_tile.y_start, valid_tile.width_height, valid_tile.width_height), 3)
        else: # No mandatory capture available
            for move in game_state.valid_moves:
                v_row, v_col = move
                valid_tile = game_state.board[v_row][v_col]
                pygame.draw.rect(screen, (0, 255, 0), (valid_tile.x_start, valid_tile.y_start, valid_tile.width_height, valid_tile.width_height), 3)

    # --- Check and Display Win Screen ---
    if game_over_status:
         show_win_screen_and_reset(game_over_status)
         game_over_status = None # Clear status after handling

    pygame.display.flip()
    clock.tick(60)

pygame.quit()