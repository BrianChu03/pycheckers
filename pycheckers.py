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

# https://github.com/everestwitman/Pygame-Checkers/blob/master/checkers.py#L378

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
    for text in instructions:
        wrapped_text = wrap_text(text, font, max_width)
        for line in wrapped_text:
            text_surface = font.render(line, True, color)
            surface.blit(text_surface, (x, y))
            y += text_surface.get_height() + line_spacing


# ----- Setup Board and Checker Graphical Components ----- #
'''
    Tile Class:
        Represents each square on the board
        Has a color (white/black) and a checker (if present)
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
            color = (47,79,79)

        pygame.draw.circle(surface, color, (self.x_pos, self.y_pos), self.radius, 0)


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
                if row_i < 3:
                    checker_obj = Checker(x_pos, y_pos, radius, False, False)
                elif row_i > 4:
                    checker_obj = Checker(x_pos, y_pos, radius, False, True)
                
                if checker_obj:
                    checkers.append(checker_obj)
                    tile.hasChecker = checker_obj
    return checkers


# ----- Game State Logic and Behavior ----- #
class GameState:
    def __init__(self, board):
        self.selected_piece = None
        self.turn = 'white'  # white moves first (your red pieces)
        self.valid_moves = []
        self.must_capture = False  # Track if a capture is mandatory
        self.board = board

    def rel(self, dir, pixel):
        """Returns coordinates relative to pixel in given direction"""
        return (pixel[0] + dir[0], pixel[1] + dir[1])

    def on_board(self, pixel):
        """Check if coordinates are within board bounds"""
        return 0 <= pixel[0] < 8 and 0 <= pixel[1] < 8

    def blind_legal_moves(self, pixel):
        """
        Returns possible move directions from a position without checking board state
        """
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
            else:  # Black moves "down" (positive row)
                moves.extend([self.rel(SOUTHWEST, (x,y)), self.rel(SOUTHEAST, (x,y))])
        else:  # Kings can move in all directions
            moves.extend([
                self.rel(NORTHWEST, (x,y)), 
                self.rel(NORTHEAST, (x,y)),
                self.rel(SOUTHWEST, (x,y)), 
                self.rel(SOUTHEAST, (x,y))
            ])
            
        return moves

    def legal_moves(self, pixel, hop=False):
        """
        Returns actual legal moves considering board state
        hop: True if we're looking for capture moves only
        """
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
        
    def move_piece(self, from_pos, to_pos):
        """Move a piece from from_pos to to_pos, handling captures and promotions"""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        from_tile = self.board[from_row][from_col]
        to_tile = self.board[to_row][to_col]
        
        # Move the checker
        checker = from_tile.hasChecker
        from_tile.hasChecker = None
        to_tile.hasChecker = checker
        
        # Update checker's position (for drawing)
        checker.x_pos = board_x + to_col * tile_size + tile_size // 2
        checker.y_pos = board_y + to_row * tile_size + tile_size // 2
        
        # Handle captures
        if abs(to_row - from_row) == 2:  # This is a capture move
            jumped_row = (from_row + to_row) // 2
            jumped_col = (from_col + to_col) // 2
            jumped_tile = self.board[jumped_row][jumped_col]
            
            # Remove the captured checker from the checkers list
            for i, c in enumerate(checkers):
                if c.x_pos == jumped_tile.x_start + tile_size // 2 and \
                   c.y_pos == jumped_tile.y_start + tile_size // 2:
                    checkers.pop(i)
                    break
            
            jumped_tile.hasChecker = None
            
            # Check for additional captures
            self.valid_moves = self.legal_moves(to_pos, hop=True)
            if self.valid_moves:  # If there are more captures available
                self.selected_piece = to_pos
                self.must_capture = True
                return False  # Turn isn't over yet
                
        # Handle king promotion
        if not checker.king:
            if (checker.is_white and to_row == 0) or (not checker.is_white and to_row == 7):
                checker.king = True
                checker.radius += 3  # Make kings visually distinct
                
        self.must_capture = False
        return True  # Turn is complete
        


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

# Board dimensions and placement
tile_size = 80
board_width = 8 * tile_size
board_height = 8 * tile_size
# Create board sligtly to the right of the instruction panel
board_x = panel_x + PANEL_WIDTH + 20
board_y = (SCREEN_HEIGHT - board_height) // 2

# Instructions text in panel
instruction_font = pygame.font.Font(None, 24)
instructions = [
    "Instructions: ",
    "1) Click on a checker to select it.",
    "2) Click on a highlighted square to move the checker.",
    "3) White moves first.",
    "4) Capture opponent's checkers by jumping over them.",
    "5) King your pieces by reaching the opponent's back row.",
    "6) Click 'New Game' to reset the game at any time."
]

# Initial creation of board and checkers
reset_game()

# Initial creation of button and gamestate logic
new_game_button = Button(panel_x + 20, panel_y + 300, 200, 50, "New Game", reset_game)



# ----- Main Game Loop ----- #
while running:
    # If user quits game (click x to close window)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Let button process the event first
        new_game_button.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            # Convert to board coordinates
            col = (pos[0] - board_x) // tile_size
            row = (pos[1] - board_y) // tile_size
            
            if not (0 <= row < 8 and 0 <= col < 8):
                # Clicked outside board
                game_state.selected_piece = None
                game_state.valid_moves = []
                continue
                
            if game_state.selected_piece is None:
                # Select a piece
                tile = board[row][col]
                if tile.hasChecker:
                    # Check if it's the correct player's turn
                    if (tile.hasChecker.is_white and game_state.turn == 'white') or \
                    (not tile.hasChecker.is_white and game_state.turn == 'red'):
                        game_state.selected_piece = (row, col)
                        game_state.valid_moves = game_state.legal_moves((row, col))

            else:
                # Try to move the selected piece
                print('Selected piece:', game_state.selected_piece)
                if (row, col) in game_state.valid_moves:
                    turn_complete = game_state.move_piece(game_state.selected_piece, (row, col))
                    
                    if turn_complete:
                        # Switch turns
                        game_state.turn = 'red' if game_state.turn == 'white' else 'white'
                        game_state.selected_piece = None
                        game_state.valid_moves = []
                    else:
                        # Player must continue capturing
                        pass
                else:
                    # Invalid move, deselect
                    game_state.selected_piece = None
                    game_state.valid_moves = []
                    print('Invalid move')

    # Default screen color (gray)
    screen.fill((128, 128, 128))

    # Draw Board and Checkers (Left Side)
    for row in board:
        for tile in row:
            tile.draw(screen)

    for checker in checkers:
        checker.draw(screen)

    # Draw Right-side Panel (Holding Reset)
    pygame.draw.rect(screen, (200, 200, 200), panel_rect)
    padding = 10
    # Render instructions
    draw_instructions(screen, instructions, instruction_font, (0, 0, 0), panel_x + padding, panel_y + padding, PANEL_WIDTH - (2 * padding))

    # Draw reset button
    new_game_button.draw(screen)

    if game_state.selected_piece:
        row, col = game_state.selected_piece
        tile = board[row][col]
        pygame.draw.rect(screen, (255, 255, 0),  # Yellow highlight
                    (tile.x_start, tile.y_start, tile.width_height, tile.width_height), 3)
    
    # Highlight valid moves
    for move in game_state.valid_moves:
        row, col = move
        tile = board[row][col]
        pygame.draw.rect(screen, (0, 255, 0),(tile.x_start, tile.y_start, tile.width_height, tile.width_height), 3)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
