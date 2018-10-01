STACK_COUNT = 8
INITIAL_STACK_SIZE = 5
OPEN_SLOT_COUNT = 3
SUIT_STACK_COUNT = 3

# Each card is represented as a tuple
# There are 3 main suits: red, green and black, and one rose card (rose, 0)
# Number cards are represented as a 2-tuple, (color, value)
# Suit token cards are represented as a 2-tuple, (color, 0)
# Open slots contain the cards, or a 2-tuple (color, -1) if the token stack has been turned over there


class GameState:
    def __init__(self):
        # List of lists of tuples
        self.stacks = []

        # List of tuples
        self.open_slots = []

        # List of lists (2-tuples really) indicating current value per suit
        self.suit_stacks = []

        # Initialize all stacks as empty
        for i in range(STACK_COUNT):
            self.stacks.append([])

        # Set all suit values to 0
        self.suit_stacks.append(["red", 0])
        self.suit_stacks.append(["green", 0])
        self.suit_stacks.append(["black", 0])

    def clone(self):
        """
            Clones the given GameState object
        """
        clone = GameState()

        for i in range(STACK_COUNT):
            for j in range(len(self.stacks[i])):
                # Copy each card from each stack
                clone.stacks[i].append(self.stacks[i][j])

        for i in range(len(self.open_slots)):
            clone.open_slots.append(self.open_slots[i])

        for i in range(SUIT_STACK_COUNT):
            clone.suit_stacks[i][1] = self.suit_stacks[i][1]

        return clone

    def is_won(self):
        """
            Determine if the current state is the won end state
        """
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

    def auto_resolve(self):
        """
            Automatically resolve state transformations that are "free" e.g. removing the rose card and suit cards such that
            a card is only moved if all off-suit suit stacks contain at least a value that is 1 less than the card being moved
            Example: suit stacks 000, can move any 1's and 2's
            Example: suit stacks 412, can move middle color (-> 422) but not others (-> 512 or 413)
        """
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
                # Also remove any 1's and 2's (only of can be pl    aced)
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
                card = self.open_slots[i]
                current_suit_value = self.suit_stacks[self.suit_index(card)][1]

                if card[1] == current_suit_value + 1 and (card[1] == minimum_suit_value + 1 or card[1] == 1 or card[1] == 2):
                    open_slot_card = card
                    break

            if open_slot_card is not None:
                self.open_slots.remove(open_slot_card)
                self.suit_stacks[self.suit_index(card)][1] += 1

    def query_stack_top(self, index):
        """
            Return the card that is on top of the given stack at index. Returns None if stack is empty
            Does not remove the card from the stack
        """
        stack = self.stacks[index]
        if len(stack) == 0:
            return None
        return stack[-1]

    def get_total_card_count(self):
        """
            Returns the total card count in the stacks
        """
        return sum([len(x) for x in self.stacks])

    def pull_from_stack(self, index, count):
        """
            Return given number of cards from the given stack
            Removes the said cards from the stack
        """
        stack = self.stacks[index]
        start = stack[:-count]
        end = stack[-count:]

        # Set the "new" stack and return the extra
        self.stacks[index] = start
        return end

    def pull_from_open_slot(self, index):
        """
            Removes the card at the given index from the open slot
        """
        card = self.open_slots[index]

        slots = self.open_slots
        start = slots[:index]
        end = slots[index + 1:]

        self.open_slots = start + end

        return card

    def parse_card_into_stack(self, index, card):
        """
            Puts the given card at the top of the stack, used in the image parsing
        """
        self.stacks[index].append(card)

    def validate_state(self):
        """
            Tells the state that the parsing has concluded. The state needs to check how many cards it is missing in
            each color and update the suit_stacks counts accordingly.
        """
        suit_check = [[0, 0, 0] + [x for x in range(10)] for i in range(3)]

        for stack_index in range(STACK_COUNT):
            stack = self.stacks[stack_index]
            for card_index in range(len(stack)):
                card = stack[card_index]
                suit_index = self.suit_index(card)

                if suit_index is None:
                    continue

                try:
                    suit_check[suit_index].remove(card[1])
                except:
                    print("Parsing image into game state failed. Duplicate card found: " + str(card))
                    exit(1)

        # If there are cards remaining, they were already autoresolved. Figure out which cards and suits, and increment the suit stacks accordingly
        # No need to care about the rose card
        for suit_index in range(len(suit_check)):
            for card_value in suit_check[suit_index]:
                # Check for errors
                if card_value == 0:
                    print("Parsing image into game state failed. Not all suit token cards were found. Suit: " +
                          self.suit_name(suit_index))
                    exit(1)

                # If the card in the given suit is not an expected value, some cards were not detected correctly
                expected_value = self.suit_stacks[suit_index][1] + 1
                if card_value != expected_value:
                    print("Parsing image into game state failed. Unexpected card not found: " + str(card))
                    exit(1)

                # Increment the suit stack for the given suit
                self.suit_stacks[suit_index][1] += 1

    def get_legal_actions(self):
        """
            Returns all legal actions as a 2-tuple of 2-tuples:
                (from, to)

            "from" is a 2-tuple
                (stack_index, card_index)
            with stack_index = -1 meaning the open slots, and card_index meaning the index of the card in the given stack

            "to" is a 2-tuple
                (destination, index)
            with destination being "suit", "open", "stack" or "token", with a number indicating the target stack index
            "token" means the player wants to bundle up all 4 available token cards into a discard pile into an empty open slot
                In this case the index is the suit index

            Any single stack card can be placed into open cards if there is space.
            Any single stack card that is not a suit token can be placed onto the suit stack if the value is (suit value + 1)
        """
        actions = []

        # Loop through all stacks, and list out all legal actions
        for stack_index in range(STACK_COUNT):
            stack = self.stacks[stack_index]
            for card_index in range(len(stack)):
                card = stack[card_index]
                can_move, stack_depth = self.can_move(stack_index, card_index)
                if not can_move:
                    continue

                # No actions for the rose card
                if self.suit_index(card) is None:
                    continue

                # Check if the card can be placed upon any other stack
                for target_stack_index in range(STACK_COUNT):
                    # Can not move onto the same stack
                    if stack_index == target_stack_index:
                        continue

                    if self.can_place(card, target_stack_index):
                        actions.append((
                            (stack_index, card_index), ("stack", target_stack_index)
                        ))

                # Check if the card can be placed into the open slots. The card must be moved alone
                if len(self.open_slots) < OPEN_SLOT_COUNT and stack_depth == 1:
                    actions.append((
                        (stack_index, card_index), ("open", None)
                    ))

                # Check if the card can be moved into suit stack. The card must be moved alone
                suit_index = self.suit_index(card)
                if card[1] == self.suit_stacks[suit_index][1] + 1 and stack_depth == 1:
                    actions.append((
                        (stack_index, card_index), ("suit", None)
                    ))

        # Loop through all open slots, add legal actions
        for card_index in range(len(self.open_slots)):
            card = self.open_slots[card_index]

            if card[1] == -1:
                continue

            # Check if the card can be placed upon any other stack
            for target_stack_index in range(STACK_COUNT):
                if self.can_place(card, target_stack_index):
                    actions.append((
                        (-1, card_index), ("stack", target_stack_index)
                    ))

            # There is no point moving a card from one open slot to another

            # Check if the card can be moved into suit stack
            suit_index = self.suit_index(card)
            if suit_index is not None and card[1] == self.suit_stacks[suit_index][1] + 1:
                actions.append((
                    (-1, card_index), ("suit", None)
                ))

        # Check if 4 of the same token card are visible for the discarding action
        # Also check if a given suit card is already in the open slots
        suit_token_count = {"red": 0, "green": 0, "black": 0}
        suit_token_in_open_slot = {"red": False, "green": False, "black": False}

        # Search from stacks...
        for stack_index in range(STACK_COUNT):
            card = self.query_stack_top(stack_index)
            if card is not None:
                suit_index = self.suit_index(card)
                if suit_index is not None and card[1] == 0:
                    suit_token_count[card[0]] += 1

        # ... and open slots
        for card_index in range(len(self.open_slots)):
            card = self.open_slots[card_index]
            if card[1] == 0:
                suit_token_count[card[0]] += 1
                suit_token_in_open_slot[card[0]] = True

        for suit in suit_token_count:
            count = suit_token_count[suit]
            if count == 4 and (suit_token_in_open_slot[suit] == True or len(self.open_slots) < OPEN_SLOT_COUNT):
                actions.append((
                    (None, None), ("token", suit)
                ))

        return actions

    def apply_action(self, action):
        """
            Applies the given action to this state. Assumes that the action is valid.
        """
        action_from = action[0]
        action_to = action[1]

        # Moving one card into the open slots (appended to the end)
        if action_to[0] == "open":
            from_stack_index = action_from[0]
            cards = self.pull_from_stack(from_stack_index, 1)
            self.open_slots += cards

        # Moving a card or stack onto another stack
        elif action_to[0] == "stack":
            from_stack_index = action_from[0]
            from_card_index = action_from[1]

            to_stack_index = action_to[1]

            # If pulling from open slots
            if from_stack_index == -1:
                card = self.pull_from_open_slot(from_card_index)
                self.stacks[to_stack_index] += [card]

            # If pulling from stack
            else:
                cards_to_pull = len(self.stacks[from_stack_index]) - from_card_index
                cards = self.pull_from_stack(from_stack_index, cards_to_pull)
                self.stacks[to_stack_index] += cards

        # Moving one card from the stacks or open slots into its suit stack
        elif action_to[0] == "suit":
            from_stack_index = action_from[0]
            from_card_index = action_from[1]

            # If pulling from open slots
            if from_stack_index == -1:
                card = self.pull_from_open_slot(from_card_index)
                suit_index = self.suit_index(card)
                self.suit_stacks[suit_index][1] += 1

            # If pulling from stack
            else:
                card = self.pull_from_stack(from_stack_index, 1)[0]
                suit_index = self.suit_index(card)
                self.suit_stacks[suit_index][1] += 1

        # Discarding all 4 token cards of a given suit into a free open slot
        elif action_to[0] == "token":
            token_suit = action_to[1]

            # Find all token cards with the given suit and remove them
            for stack_index in range(STACK_COUNT):
                stack_top = self.query_stack_top(stack_index)
                if stack_top is not None and stack_top[0] == token_suit and stack_top[1] == 0:
                    self.pull_from_stack(stack_index, 1)

            self.open_slots = list(filter(lambda card: not (card[0] == token_suit and card[1] == 0), self.open_slots))

            # Add the discarded pile into the open slots
            self.open_slots.append((token_suit, -1))

    def can_move(self, stack_index, card_index):
        """
            Returns a 2-tuple with first value True if the card can be moved from the current stack
            The second value is the depth of the stack underneath the card
        """
        card = self.stacks[stack_index][card_index]
        current_card = card
        stack_depth = 1
        next_card_index = card_index + 1
        while next_card_index < len(self.stacks[stack_index]):
            next_card = self.stacks[stack_index][next_card_index]

            if next_card[1] == 0 or current_card[1] == 0:
                return (False, 0)

            if (next_card[0] == current_card[0] or next_card[1] != current_card[1] - 1):
                return (False, 0)

            current_card = next_card
            next_card_index += 1
            stack_depth += 1

        return (True, stack_depth)

    def can_place(self, card, stack_index):
        """
            Returns true if the given card can be placed onto the given stack
        """
        # Can always place on empty stack
        if len(self.stacks[stack_index]) == 0:
            return True

        target_card = self.stacks[stack_index][-1]

        # Cannot place onto suit token
        # Cannot place suit token onto anything other than empty stack
        if target_card[1] == 0 or card[1] == 0:
            return False

        # Target card must be different suit and +1 in value
        if target_card[0] == card[0] or target_card[1] != card[1] + 1:
            return False

        return True

    def suit_index(self, card):
        """
            Get the index of the given suit. Returns None for the rose card
        """
        if card[0] == "red":
            return 0
        elif card[0] == "green":
            return 1
        elif card[0] == "black":
            return 2
        return None

    def suit_name(self, index):
        """
            Convert a suit index to the suit name
        """
        if index == 0:
            return "red"
        elif index == 1:
            return "green"
        elif index == 2:
            return "black"
        return "rose"

    def __eq__(self, other):
        for i in range(STACK_COUNT):
            if self.stacks[i] != other.stacks[i]:
                return False

        for i in range(OPEN_SLOT_COUNT):
            if self.open_slots[i] != other.open_slots[i]:
                return False

        return True

    def __hash__(self):
        open_slots_hash = "".join([str(x) for x in self.open_slots])
        stacks_hash = "".join(["".join([str(y) for y in x]) for x in self.stacks])
        return hash(open_slots_hash + "-" + stacks_hash)

    def __str__(self):
        return ("Open slots: " + ", ".join(map(lambda slot: str(slot[0]) + " " + str(slot[1]), self.open_slots)) + "\n" +
                "Suit stacks: " + ", ".join(map(lambda slot: str(slot[0]) + " " + str(slot[1]), self.suit_stacks)) + "\n" +
                "Board:\n" +
                "\n".join([", ".join(map(lambda slot: str(slot[0]) + " " + str(slot[1]), stack)) for stack in self.stacks]))
