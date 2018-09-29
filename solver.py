import PIL
import pyscreenshot as ImageGrab
import time

def main():
    intro_print()
    # time.sleep(5)
    
    solve()

def intro_print():
    print("Launching in 5 seconds")
    print("Make sure the game is opened in fullscreen on the main window")
    print("To exit, close the script between games")

def solve():
    im = ImageGrab.grab()

    # Crop the image to only contain the game view
    # Define the game view as a defined rectangle around the center of the screen
    # Assume the game is in native resolution
    # Confirmed to work in 1080p and 1440p
    width = im.size[0]
    height = im.size[1]
    game_width = 1300
    game_height = 870

    game_left = (width - game_width)/2.0
    game_top = (height - game_height)/2.0

    im = im.crop((game_left, game_top, width - game_left, height - game_top))


if __name__ == "__main__":
    main()