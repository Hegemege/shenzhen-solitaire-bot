import PIL
import pyscreenshot as ImageGrab
import time
import functools
import math
from pynput.mouse import Button, Controller

from game_state import GameState, STACK_COUNT, OPEN_SLOT_COUNT, SUIT_STACK_COUNT, INITIAL_STACK_SIZE, MAX_STACK_SIZE

# Constants used to crop the game view from the whole screen
# Works properly if game is in native resolution

GAME_WIDTH = 1300
GAME_HEIGHT = 870

# Will be calculated by code
GAME_LEFT = 1000
GAME_TOP = 500

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

SUIT_STACK_LEFT = 853
SUIT_STACK_TOP = 19

COLOR_MATCH_THRESHOLD = 2

# Autoplay parmeters
CLICK_TOKEN_DISCARD_BUTTONS = {
    "red": (578, 55),
    "green": (578, 140),
    "black": (578, 225)
}

CLICK_OPEN_SLOTS = [
    (100, 30),
    (256, 30),
    (410, 30)
]

CLICK_SUIT_STACKS = {

}

CLICK_SUIT_STACK_POSITIONS = [
    (862, 30),
    (1015, 30),
    (1168, 30)
]

CLICK_STACKS = [[(0, 0) for j in range(MAX_STACK_SIZE)] for i in range(STACK_COUNT)]

# Color average lookup
CARD_LOOKUP = {}
CARD_LOOKUP["red"] = [
    (190, 156, 139, 193, 195, 179),
    (190, 157, 139, 177, 67, 44),
    (187, 136, 117, 175, 56, 33),
    (187, 135, 116, 175, 54, 31),
    (186, 132, 113, 193, 194, 178),
    (186, 134, 115, 179, 88, 66),
    (186, 133, 114, 191, 177, 161),
    (188, 143, 125, 180, 92, 70),
    (185, 125, 105, 175, 57, 33),
    (186, 133, 114, 175, 55, 31)
]
CARD_LOOKUP["green"] = [
    (121, 160, 137, 148, 173, 152),
    (148, 173, 152, 45, 123, 91),
    (123, 161, 138, 32, 117, 83),
    (122, 161, 137, 30, 116, 82),
    (119, 159, 135, 193, 194, 178),
    (121, 160, 136, 69, 134, 105),
    (119, 159, 136, 173, 185, 167),
    (132, 165, 143, 74, 137, 108),
    (110, 155, 130, 32, 117, 83),
    (120, 160, 136, 30, 116, 82)
]
CARD_LOOKUP["black"] = [
    (131, 132, 122, 68, 69, 63),
    (147, 148, 136, 30, 30, 27),
    (120, 121, 111, 16, 16, 14),
    (119, 120, 110, 13, 13, 12),
    (115, 116, 107, 193, 194, 178),
    (117, 118, 109, 56, 56, 52),
    (116, 117, 108, 171, 172, 158),
    (129, 130, 120, 61, 62, 57),
    (106, 106, 98, 16, 16, 15),
    (116, 117, 108, 13, 14, 12)
]
CARD_LOOKUP["rose"] = [(171, 142, 121, 193, 195, 179)]

SUIT_STACKS_LOOKUP = {}
SUIT_STACKS_LOOKUP["red"] = [
    (190, 160, 143, 182, 110, 89),
    (187, 136, 117, 175, 56, 33),
    (187, 135, 116, 179, 87, 65)
]
SUIT_STACKS_LOOKUP["green"] = [
    (152, 175, 155, 95, 147, 120),
    (123, 161, 138, 32, 117, 83),
    (121, 160, 137, 68, 134, 104)
]
SUIT_STACKS_LOOKUP["black"] = [
    (152, 153, 141, 85, 85, 78),
    (120, 121, 111, 16, 16, 14),
    (118, 119, 110, 55, 55, 51)
]

MAX_SOLUTION_LENGTH = 35

REPLAY_WAIT_BETWEEN_ACTIONS = 0.15
REPLAY_MOUSE_MOVE_TIME = 0.15
REPLAY_AUTORESOLVE_WAIT_PER_ACTION = 0.30


def main():
    intro_print()
    # time.sleep(5)

    solve()


def intro_print():
    """
        Prints introductory test of the program's features
    """
    print("Launching in 5 seconds")
    print("Make sure the game is opened in fullscreen on the main window")
    print("To exit, close the script between games")


def solve():
    """
        Solves the current game configuration
    """
    image = ImageGrab.grab()
    image = crop(image)

    #image = PIL.Image.open("reference_img4.bmp")

    # Initialize the beginning game state
    state = GameState()

    # Parse the image and populate the state
    populate_state(image, state)

    # Validate the game state, in case of auto-resolved cards at the beginning of the game
    state.validate_state()

    # Setup lookups and other structures for the main solving loop
    state_history = {}
    search_stack = []

    # Initialize the search stack
    search_stack.append((state, [], 0))
    shortest_solution = [0 for i in range(10000)]
    shortest_solution_suit_order = []

    original_state = state.clone()
    highest_heuristic = -999

    # Start the main solving loop
    states_searched = 0
    last_states_searched_print = 0
    last_states_searched_sort = 0

    while True:
        if states_searched > 50000:
            break
        if states_searched - last_states_searched_print > 10000:
            print("Heuristic:", highest_heuristic)
            last_states_searched_print = states_searched
            print(len(search_stack), states_searched)

        if states_searched - last_states_searched_sort > 100:
            search_stack.sort(key=lambda item: item[2])

        if len(search_stack) == 0 and len(state_history) > 0:
            print("Unable to find solution")
            break

        # Take state from the end of stack
        current_search_item = search_stack.pop()
        current_state = current_search_item[0]
        current_history = current_search_item[1]

        if len(current_history) > MAX_SOLUTION_LENGTH and current_search_item[2] < 100:
            continue

        if current_search_item[2] >= 100:  # current_state.is_won() or :
            if len(current_history) < len(shortest_solution):
                shortest_solution = current_history
                print("New shortest solution", len(current_history))
                print("States searched:", states_searched)
                print("Stack size:", len(search_stack))
                print()
            break

        current_actions = current_state.get_legal_actions()

        for action in current_actions:
            clone = current_state.clone()
            clone.apply_action(action)
            resolved_count = clone.auto_resolve()

            # Hash the state, make sure we don't revisit a state
            clone_hash = hash(clone)
            if clone_hash in state_history:
                if state_history[clone_hash] == clone:
                    continue
            state_history[clone_hash] = clone

            heuristic_score = clone.get_heuristic_value()

            if heuristic_score >= highest_heuristic:
                highest_heuristic = heuristic_score
                shortest_solution = current_history + [action]
                shortest_solution_suit_order = clone.suit_insert_order

            new_history = list(current_history)
            new_history += [action]
            if resolved_count > 0:
                new_history += [((None, None), ("resolve", resolved_count))]

            search_stack.append((clone, new_history, heuristic_score))
            states_searched += 1

        # Sort the last 100 entries
        #split_off = int(len(search_stack)/2)
        #search_stack_start = search_stack[:-split_off]
        #search_stack_end = search_stack[-split_off:]
        #search_stack_end.sort(key=lambda item: item[2])
        #search_stack = search_stack_start + search_stack_end

        #search_stack.sort(key=lambda item: item[2])

    # print(original_state)
    # for action in shortest_solution:
    #    print(action)

    # Resolve the suit stack order
    cloned_suit_stack_positions = list(CLICK_SUIT_STACK_POSITIONS)
    for i in range(len(shortest_solution_suit_order)):
        suit = shortest_solution_suit_order[i]
        CLICK_SUIT_STACKS[suit] = cloned_suit_stack_positions.pop(0)

    replay_actions(shortest_solution)


def replay_actions(actions):
    """
        Plays the solved actions on the board
    """
    mouse = Controller()

    print("Replaying", len(actions), "actions")
    time.sleep(1)

    for action in actions:
        print(action)
        if action[0][0] is None:
            # Discard suit tokens
            if action[1][0] == "token":
                suit = action[1][1]
                drag_from_to(mouse, CLICK_TOKEN_DISCARD_BUTTONS[suit], CLICK_TOKEN_DISCARD_BUTTONS[suit])
            # Auto-resolve
            else:
                time.sleep(0.5 + REPLAY_AUTORESOLVE_WAIT_PER_ACTION * action[1][1])
        else:
            if action[0][0] == -1:

                # Move from open slot to stack
                if action[1][0] == "stack":
                    from_position = CLICK_OPEN_SLOTS[action[0][1]]
                    to_position = CLICK_STACKS[action[1][1]][5]
                    drag_from_to(mouse, from_position, to_position)

                # Move from open slot to suit stack
                else:
                    from_position = CLICK_OPEN_SLOTS[action[0][1]]
                    to_position = CLICK_SUIT_STACKS[action[1][1]]
                    drag_from_to(mouse, from_position, to_position)
            else:
                # Stack to stack
                if action[1][0] == "stack":
                    from_position = CLICK_STACKS[action[0][0]][action[0][1]]
                    # Always drag onto the 6th card, which will cover all vertical positions
                    to_position = CLICK_STACKS[action[1][1]][5]
                    drag_from_to(mouse, from_position, to_position)

                # Stack to suit stack
                elif action[1][0] == "suit":
                    from_position = CLICK_STACKS[action[0][0]][action[0][1]]
                    to_position = CLICK_SUIT_STACKS[action[1][1]]
                    drag_from_to(mouse, from_position, to_position)

                # Stack to open slot
                else:
                    from_position = CLICK_STACKS[action[0][0]][action[0][1]]
                    to_position = CLICK_OPEN_SLOTS[action[1][1]]
                    drag_from_to(mouse, from_position, to_position)


def click_on(mouse, position__):
    position = game_to_screen(position__)
    mouse.position = position
    time.sleep(REPLAY_MOUSE_MOVE_TIME)
    mouse.click(Button.left, 1)
    time.sleep(REPLAY_MOUSE_MOVE_TIME)


def drag_from_to(mouse, from_position__, to_position__):
    from_position = game_to_screen(from_position__)
    to_position = game_to_screen(to_position__)
    mouse.position = from_position
    mouse.press(Button.left)
    time.sleep(REPLAY_MOUSE_MOVE_TIME)
    mouse.position = to_position
    time.sleep(REPLAY_MOUSE_MOVE_TIME)
    mouse.release(Button.left)
    time.sleep(REPLAY_MOUSE_MOVE_TIME)


def crop(image):
    """
        Crop the image to only contain the game view
        Define the game view as a defined rectangle around the center of the screen
        Assume the game is in native resolution
        Confirmed to work in 1080p and 1440p
    """
    global GAME_LEFT
    global GAME_TOP

    width = image.size[0]
    height = image.size[1]
    game_width = GAME_WIDTH
    game_height = GAME_HEIGHT

    GAME_LEFT = (width - game_width)/2.0
    GAME_TOP = (height - game_height)/2.0

    return image.crop((GAME_LEFT, GAME_TOP, width - GAME_LEFT, height - GAME_TOP))


def populate_state(image, state):
    """
        Parse the image and populate the given game state
    """

    sampled_colors = {}

    # Loop through the board and extract color data from card values
    for i in range(STACK_COUNT):
        for j in range(MAX_STACK_SIZE):
            left = BOARD_TOP_LEFT[0] + i * BOARD_HORIZONTAL_DELIMITER + CARD_VALUE_OFFSET[0]
            top = BOARD_TOP_LEFT[1] + j * BOARD_VERTICAL_DELIMITER + CARD_VALUE_OFFSET[1]

            CLICK_STACKS[i][j] = (left, top)

            if j >= INITIAL_STACK_SIZE:
                continue

            right = left + CARD_VALUE_SIZE[0]
            bottom = top + CARD_VALUE_SIZE[1]
            card_value = image.crop((left, top, right, bottom))

            # Get avg from top left corner
            top_left_avg = sample_avg_color(card_value, (2, 2))

            # Get overall color average
            pixels = list(card_value.getdata())
            avg_color = avg_color_list(pixels)

            comb_color = avg_color + top_left_avg

            sampled_colors[(i, j)] = comb_color

    position_lookup = {}

    # Find the card colors and values
    for position in sampled_colors:
        comb_color = sampled_colors[position]

        found = False

        # Go through all color settings and try to find the correct one, that is as close to the given values as possible
        for suit in CARD_LOOKUP:
            if found:
                break
            suit_cards = CARD_LOOKUP[suit]
            for card_index in range(len(suit_cards)):
                comparison_color = suit_cards[card_index]

                # Split the 6-tuples into 3-tuples
                sampled_avg_color = comb_color[:3]
                sampled_check_color = comb_color[3:]

                comparison_avg_color = comparison_color[:3]
                comparison_check_color = comparison_color[3:]

                # Test if the colors are close to each other. Store the card position
                if color_distance(sampled_avg_color, comparison_avg_color) < COLOR_MATCH_THRESHOLD and color_distance(sampled_check_color, comparison_check_color) < COLOR_MATCH_THRESHOLD:
                    position_lookup[position] = (suit, card_index)
                    found = True
                    break

        if not found:
            pass
            # The card that should have been at the given place was probably auto-resolved. The state will update rose + suit counts
            # print("Not found", position, comb_color)

    for position in sorted(position_lookup.keys()):
        stack_index = position[0]
        state.parse_card_into_stack(stack_index, position_lookup[position])

    # Check already resolved colors from suit stacks
    for i in range(3):
        left = SUIT_STACK_LEFT + i * BOARD_HORIZONTAL_DELIMITER + CARD_VALUE_OFFSET[0]
        top = SUIT_STACK_TOP + CARD_VALUE_OFFSET[1]

        right = left + CARD_VALUE_SIZE[0]
        bottom = top + CARD_VALUE_SIZE[1]
        card_value = image.crop((left, top, right, bottom))

        # Get avg from top left corner
        top_left_avg = sample_avg_color(card_value, (2, 2))

        # Get overall color average
        pixels = list(card_value.getdata())
        avg_color = avg_color_list(pixels)

        comb_color = avg_color + top_left_avg

        found = False

        for suit in SUIT_STACKS_LOOKUP:
            if found:
                break
            suit_cards = SUIT_STACKS_LOOKUP[suit]
            for card_index in range(len(suit_cards)):
                comparison_color = suit_cards[card_index]

                # Split the 6-tuples into 3-tuples
                sampled_avg_color = comb_color[:3]
                sampled_check_color = comb_color[3:]

                comparison_avg_color = comparison_color[:3]
                comparison_check_color = comparison_color[3:]

                # Test if the colors are close to each other. Store the card position
                if color_distance(sampled_avg_color, comparison_avg_color) < COLOR_MATCH_THRESHOLD and color_distance(sampled_check_color, comparison_check_color) < COLOR_MATCH_THRESHOLD:
                    print("Autoresolved suit order:", suit)
                    state.suit_insert_order.append(suit)
                    found = True
                    break


def sample_avg_color(image, position):
    """
        Sample an average color from the image at the given position
        Averages a 3x3 kernel around the pixel
    """
    kernel = []
    topleft = (position[0] - 1, position[1] - 1)
    for i in range(3):
        for j in range(3):
            kernel.append(image.getpixel((topleft[0] + j, topleft[1] + i)))
    return avg_color_list(kernel)


def avg_color_list(color_list):
    """
        Returns the average color of the given list of 3-tuples
    """
    colors = tuple(functools.reduce(lambda x, y: tuple(map(lambda a, b: a + b, x, y)), color_list))
    colors = tuple(map(lambda x: x // len(color_list), colors))
    return colors


def color_distance(from_color, to_color):
    """
        Calculate the euclidean distance of two colors in 3D space
    """
    return math.sqrt((from_color[0] - to_color[0]) ** 2 + (from_color[1] - to_color[1]) ** 2 + (from_color[2] - to_color[2]) ** 2)


def game_to_screen(position):
    """
        Converts coordinates from game view into screen coordinates for mouse interaction
    """
    return (GAME_LEFT + position[0], GAME_TOP + position[1])


if __name__ == "__main__":
    main()
