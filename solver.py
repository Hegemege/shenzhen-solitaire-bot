import PIL
import pyscreenshot as ImageGrab
import time

from game_state import GameState

# Constants used to crop the game view from the whole screen
# Works properly if game is in native resolution
GAME_WIDTH = 1300
GAME_HEIGHT = 870

def main():
    intro_print()
    # time.sleep(5)
    
    solve()

def intro_print():
    print("Launching in 5 seconds")
    print("Make sure the game is opened in fullscreen on the main window")
    print("To exit, close the script between games")

def solve():
    image = ImageGrab.grab()
    image = crop(image)

    # Initialize beginning game state
    state = GameState()

    # Parse the image and populate the state
    populate_state(image, state)


    # TEMP TESTING
    state.stacks[0].append(("red", 1))
    state.stacks[0].append(("green", 1))
    state.stacks[0].append(("black", 1))
    state.stacks[1].append(("rose", 0))
    state.stacks[1].append(("red", 2))
    state.stacks[1].append(("green", 3))

    print(state)

    state.auto_resolve()

    print(state)



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

if __name__ == "__main__":
    main()