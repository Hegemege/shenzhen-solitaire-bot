STACK_COUNT = 8
OPEN_SLOT_COUNT = 3
SUIT_STACK_COUNT = 3

# Each card is represented as a tuple
# There are 3 main suits: red, green and black, and one rose card (rose, 0)
# Number cards are represented as a 2-tuple, (color, value)
# Suit token cards are represented as a 2-tuple, (color, 0)
# Open slots contain the cards, or a 2-tuple (color, -1) if the token stack has been turned over there

class GameState:
    stacks = [] # list of lists of tuples
    open_slots = [] # list of tuples
    suit_stacks = [] # list of lists (2-tuples really) indicating current value per suit

    def __init__(self):
        # Initialize all stacks as empty
        for i in range(STACK_COUNT):
            self.stacks.append([])

        # Set all suit values to 0
        self.suit_stacks.append(["red", 0])
        self.suit_stacks.append(["green", 0])
        self.suit_stacks.append(["black", 0])

    def clone(self):
        clone = GameState()

        for i in range(STACK_COUNT): 
            for j in range(len(self.stacks[i])):
                clone.stacks[i].append(self.stacks[i][j]) # Copy each card from each stack
        
        for i in range(len(self.open_slots)):
            clone.open_slots.append(self.open_slots[i])

        for i in range(SUIT_STACK_COUNT):
            clone.suit_stacks[i][1] = self.suit_stacks[i][1]

        return clone

    # Determine if the current state is the won end state
    def is_won(self):
        for i in range(len(self.open_slots)):
            if self.open_slots[i][1] != -1:
                return False
        
        for i in range(SUIT_STACK_COUNT):
            if self.suit_stacks[i][1] != 9:
                return False
        
        for i in range(STACK_COUNT):
            if len(self.stacks[i]) != 0:
                return False

        return True

    # Automatically resolve state transformations that are "free" e.g. removing the rose card and suit cards such that
    # a card is only moved if all off-suit suit stacks contain at least a value that is 1 less than the card being moved
    # Example: suit stacks 000, can move any 1's and 2's
    # Example: suit stacks 412, can move middle color (-> 422) but not others (-> 512 or 413)
    def auto_resolve(self):
        previous_count = 0
        while previous_count != self.get_total_card_count():
            previous_count = self.get_total_card_count()

            # Get the minimum value of the suit stacks
            # Allow autoresolving a suited card that is only +1 of minimum
            minimum_suit_value = min(map(lambda x: x[1], self.suit_stacks))

            early_continue = False

            # Go through all top cards in stacks
            for i in range(STACK_COUNT):
                top_card = self.query_stack_top(i)
                if top_card is None:
                    continue

                # If the card is the rose, remove it instantly
                if self.suit_index(top_card) is None:
                    self.pull_from_stack(i, 1)
                    continue
                
                current_suit_value = self.suit_stacks[self.suit_index(top_card)][1]

                # If card is (current + 1) and the value is (min + 1), remove it
                # Also remove any 1's and 2's (only of can be placed)
                if top_card[1] == current_suit_value + 1 and (top_card[1] == minimum_suit_value + 1 or top_card[1] == 1 or top_card[1] == 2):
                    self.pull_from_stack(i, 1)
                    self.suit_stacks[self.suit_index(top_card)][1] += 1
                    early_continue = True

            # If a card was autoresolved from the stacks, do not try to autoresolve from the open slots at the same time
            if early_continue:
                continue

            open_slot_card = None
                
            # Also go through all open slot cards. Rose cannot be found here
            for i in range(len(self.open_slots)):
                card = self.open_slots[len(self.open_slots) - 1 - i] # Reverse order
                current_suit_value = self.suit_stacks[self.suit_index(card)][1]

                if card[1] == current_suit_value + 1 and (card[1] == minimum_suit_value + 1 or card[1] == 1 or card[1] == 2):
                    open_slot_card = card
                    break
            
            if open_slot_card is not None:
                self.open_slots.remove(open_slot_card)
                self.suit_stacks[self.suit_index(card)][1] += 1


    # Return the card that is on top of the given stack at index. Returns None if stack is empty
    # Does not remove the card from the stack
    def query_stack_top(self, index):
        stack = self.stacks[index]
        if len(stack) == 0:
            return None
        return stack[len(stack) - 1]

    # Returns the total card count in the stacks
    def get_total_card_count(self):
        return sum([len(x) for x in self.stacks])

    # Return given number of cards from the given stack
    # Removes the said cards from the stack
    def pull_from_stack(self, index, count):
        stack = self.stacks[index]
        start = stack[:len(stack) - count]
        end = stack[-count:]

        # Set the "new" stack and return the extra
        self.stacks[index] = start
        return end

    # Get the index of the given suit. Returns None for the rose card
    def suit_index(self, card):
        if card[0] == "red":
            return 0
        elif card[0] == "green":
            return 1
        elif card[0] == "black":
            return 2
        return None

    def __eq__(self, other):
        for i in range(STACK_COUNT):
            if self.stacks[i] != other.stacks[i]:
                return False
        
        for i in range(OPEN_SLOT_COUNT):
            if self.open_slots[i] != other.open_slots[i]:
                return False

        return True

    def __hash__(self):
        open_slots_hash = "".join(["".join(x) for x in self.open_slots])
        stacks_hash = "".join(["".join("".join(x)) for x in self.stacks])
        return hash(open_slots_hash + "-" + stacks_hash)

    def __str__(self):
        return ("Open slots: " + ", ".join(map(lambda slot: slot[0] + " " + str(slot[1]), self.open_slots)) + "\n" +
            "Suit stacks: " + ", ".join(map(lambda slot: slot[0] + " " + str(slot[1]), self.suit_stacks)) + "\n" +
            "Board:\n" +
            "\n".join([", ".join(map(lambda slot: slot[0] + " " + str(slot[1]), stack)) for stack in self.stacks]))
            