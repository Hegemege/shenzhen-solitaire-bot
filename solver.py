import PIL
import pyscreenshot as ImageGrab
import time
import functools
import math

from game_state import GameState

# Constants used to crop the game view from the whole screen
# Works properly if game is in native resolution

GAME_WIDTH = 1300
GAME_HEIGHT = 870

# Colors

RED_COLOR = (175, 51, 28)
GREEN_COLOR = (26, 113, 79)
BLACK_COLOR = (8, 8, 8)

CARD_BASE_COLOR = (195, 196, 180)

RED_TOKEN_COLOR = (180, 91, 70)
GREEN_TOKEN_COLOR = (61, 131, 100)
BLACK_TOKEN_COLOR = (56, 57, 52)

ROSE_GREEN_COLOR = (31, 117, 84)
ROSE_RED_COLOR = (179, 94, 73)

# Image parsing parameters

BOARD_TOP_LEFT = (93, 284)
BOARD_HORIZONTAL_DELIMITER = 152
BOARD_VERTICAL_DELIMITER = 31

CARD_VALUE_OFFSET = (12, 10)
CARD_VALUE_SIZE = (12, 21)

COLOR_MATCH_THRESHOLD = 30

def main():
    intro_print()
    # time.sleep(5)
    
    solve()

def intro_print():
    print("Launching in 5 seconds")
    print("Make sure the game is opened in fullscreen on the main window")
    print("To exit, close the script between games")

def solve():
    #image = ImageGrab.grab()
    #image = crop(image)
    image = PIL.Image.open("reference_img.bmp")

    # Initialize beginning game state
    state = GameState()

    # Parse the image and populate the state
    populate_state(image, state)

    state.auto_resolve()

    print(state)

    color_set = {}
    
    # TEMP get all values, save as image with the color as filename
    for i in range(8):
        for j in range(5):
            left = BOARD_TOP_LEFT[0] + i * BOARD_HORIZONTAL_DELIMITER + CARD_VALUE_OFFSET[0]
            top = BOARD_TOP_LEFT[1] + j * BOARD_VERTICAL_DELIMITER + CARD_VALUE_OFFSET[1]
            right = left + CARD_VALUE_SIZE[0]
            bottom = top + CARD_VALUE_SIZE[1]
            card_value = image.crop((left, top, right, bottom))
            pixels = list(card_value.getdata())
            avg_color = avg_color_list(pixels)

            if (avg_color in color_set):
                print("Clash", i, j, color_set[avg_color])

            color_set[avg_color] = (i, j)

            fname = str(i) + "_" + str(j) + "_" + "_".join(map(str, avg_color)) + ".bmp"
            #card_value.save(fname)

    print(color_set)
    print(len(color_set))


# Crop the image to only contain the game view
# Define the game view as a defined rectangle around the center of the screen
# Assume the game is in native resolution
# Confirmed to work in 1080p and 1440p
def crop(image):
    width = image.size[0]
    height = image.size[1]
    game_width = GAME_WIDTH
    game_height = GAME_HEIGHT

    game_left = (width - game_width)/2.0
    game_top = (height - game_height)/2.0

    return image.crop((game_left, game_top, width - game_left, height - game_top))

# Parse the image and populate the given game state
def populate_state(image, state):
    pass

# Sample an average color from the image at the given position
# Averages a 3x3 kernel around the pixel
def sample_avg_color(image, position):
    kernel = []
    topleft = (position[0] - 1, position[1] - 1)
    for i in range(3):
        for j in range(3):
            kernel.append(image.getpixel((topleft[0] + j, topleft[1] + i)))
    return avg_color_list(kernel)

# Returns the average color of 
def avg_color_list(color_list):
    colors = tuple(functools.reduce(lambda x, y: tuple(map(lambda a, b: a + b, x, y)), color_list))
    colors = tuple(map(lambda x: x // len(color_list), colors))
    return colors

def color_distance(from_color, to_color):
    return math.sqrt((from_color[0] - to_color[0]) ** 2 + (from_color[1] - to_color[1]) ** 2 + (from_color[2] - to_color[2]) ** 2)

if __name__ == "__main__":
    main()