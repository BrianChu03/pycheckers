import pygame

from pygame.locals import (
    MOUSEBUTTONUP,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

pygame.init()
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True

######## NEEEEED COMMMMENTNTNSLNTLBDGKJBSDGK:JBF:LJBALG: #########
class Tile:
    def __init__(self, x_start, y_start, width_height, is_white):
        self.x_start = x_start
        self.y_start = y_start
        self.width_height = width_height
        self.is_white = is_white

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
            color = (237, 232, 208)
        else:
            color = (112, 66, 20)

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

#def set_checkers(board_x, board_y, tile_size):


tile_size = 80

board_width = 8 * tile_size
board_height = 8 * tile_size
board_x = (SCREEN_WIDTH - board_width) // 2
board_y = (SCREEN_HEIGHT - board_height) // 2

board = create_board(board_x, board_y, tile_size)

while running:
    # If user quits game (click x to close window)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((128, 128, 128))

    for row in board:
        for tile in row:
            tile.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
