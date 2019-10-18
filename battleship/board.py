from typing import List, Tuple

from battleship.ship import Ship

from itertools import combinations, permutations

from random import randint, choice

OFFSET_UPPER_CASE_CHAR_CONVERSION = 64

class Board(object):
    """
    Class representing the board of the player. Interface between the player and its ships.
    """
    SIZE_X = 10  # length of the rectangular board, along the x axis
    SIZE_Y = 10  # length of the rectangular board, along the y axis

    # dict: length -> number of ships of that length
    DICT_NUMBER_SHIPS_PER_LENGTH = {1: 1,
                                    2: 1,
                                    3: 1,
                                    4: 1,
                                    5: 1}

    def __init__(self,
                 list_ships: List[Ship]):
        """
        :param list_ships: list of ships for the board.
        :raise ValueError if the list of ships is in contradiction with Board.DICT_NUMBER_SHIPS_PER_LENGTH.
        :raise ValueError if there are some ships that are too close from each other
        """

        self.list_ships = list_ships
        self.set_coordinates_previous_shots = set()
        self.ship_lengths = [ship.length() for ship in self.list_ships]

        if not self.lengths_of_ships_correct():
            total_number_of_ships = sum(self.DICT_NUMBER_SHIPS_PER_LENGTH.values())

            error_message = f"There should be {total_number_of_ships} ships in total:\n"

            for length_ship, number_ships in self.DICT_NUMBER_SHIPS_PER_LENGTH.items():
                error_message += f" - {number_ships} of length {length_ship}\n"

            raise ValueError(error_message)

        if self.are_some_ships_too_close_from_each_other():
            raise ValueError("There are some ships that are too close from each other.")

    def has_no_ships_left(self) -> bool:
        """
        :return: True if and only if all the ships on the board have sunk.
        """
        return all(ship.has_sunk() for ship in self.list_ships)

    def is_attacked_at(self, coord_x: int, coord_y: int) -> Tuple[bool, bool]:
        """
        The board receives an attack at the position (coord_x, coord_y).
        - if there is no ship at that position -> nothing happens
        - if there is a ship at that position -> it is damaged at that coordinate

        :param coord_x: integer representing the projection of a coordinate on the x-axis
        :param coord_y: integer representing the projection of a coordinate on the y-axis
        :return: a tuple of bool variables (is_ship_hit, has_ship_sunk) where:
                    - is_ship_hit is True if and only if the attack was performed at a set of coordinates where an
                    opponent's ship is.
                    - has_ship_sunk is True if and only if that attack made the ship sink.
        """

        is_ship_hit = False
        has_ship_sunk = False
        for ship in self.list_ships:
            if ship.is_on_coordinate(coord_x, coord_y):
                ship.gets_damage_at(coord_x, coord_y)
                is_ship_hit = True
                has_ship_sunk = ship.has_sunk()
                return (is_ship_hit, has_ship_sunk)

        return(is_ship_hit, has_ship_sunk)


    def print_board_with_ships_positions(self) -> None:
        array_board = [[' ' for _ in range(self.SIZE_X)] for _ in range(self.SIZE_Y)]

        for x_shot, y_shot in self.set_coordinates_previous_shots:
            array_board[y_shot - 1][x_shot - 1] = 'O'

        for ship in self.list_ships:
            if ship.has_sunk():
                for x_ship, y_ship in ship.set_all_coordinates:
                    array_board[y_ship - 1][x_ship - 1] = '$'
                continue

            for x_ship, y_ship in ship.set_all_coordinates:
                array_board[y_ship - 1][x_ship - 1] = 'S'

            for x_ship, y_ship in ship.set_coordinates_damages:
                array_board[y_ship - 1][x_ship - 1] = 'X'

        board_str = self._get_board_string_from_array_chars(array_board)

        print(board_str)

    def print_board_without_ships_positions(self) -> None:
        array_board = [[' ' for _ in range(self.SIZE_X)] for _ in range(self.SIZE_Y)]

        for x_shot, y_shot in self.set_coordinates_previous_shots:
            array_board[y_shot - 1][x_shot - 1] = 'O'

        for ship in self.list_ships:
            if ship.has_sunk():
                for x_ship, y_ship in ship.set_all_coordinates:
                    array_board[y_ship - 1][x_ship - 1] = '$'
                continue

            for x_ship, y_ship in ship.set_coordinates_damages:
                array_board[y_ship - 1][x_ship - 1] = 'X'

        board_str = self._get_board_string_from_array_chars(array_board)

        print(board_str)

    def _get_board_string_from_array_chars(self, array_board: List[List[str]]) -> str:
        list_lines = []

        array_first_line = [chr(code + OFFSET_UPPER_CASE_CHAR_CONVERSION) for code in range(1, self.SIZE_X + 1)]
        first_line = ' ' * 6 + (' ' * 5).join(array_first_line) + ' \n'

        for index_line, array_line in enumerate(array_board, 1):
            number_spaces_before_line = 2 - len(str(index_line))
            space_before_line = number_spaces_before_line * ' '
            list_lines.append(f'{space_before_line}{index_line} |  ' + '  |  '.join(array_line) + '  |\n')

        line_dashes = '   ' + '-' * 6 * self.SIZE_X + '-\n'

        board_str = first_line + line_dashes + line_dashes.join(list_lines) + line_dashes

        return board_str

    def lengths_of_ships_correct(self) -> bool:
        """
        :return: True if and only if there is the right number of ships of each length, according to
        Board.DICT_NUMBER_SHIPS_PER_LENGTH
        """
        keys = sorted(list(set(self.ship_lengths))) ## set removes duplicates

        dict_number_ships_per_length = {key: self.ship_lengths.count(key) for key in keys}

        return dict_number_ships_per_length == self.DICT_NUMBER_SHIPS_PER_LENGTH

        ##  this method is robust to changes in the number of ships and new ship lengths


    def are_some_ships_too_close_from_each_other(self) -> bool:
        """
        :return: True if and only if there are at least 2 ships on the board that are near each other.
        """
        all_ship_combination_pairs = combinations(self.list_ships, 2)  ## returns a list of tuples of all ship pairs
        return any(ship.is_near_ship(other_ship) for (ship, other_ship) in all_ship_combination_pairs)  ##  checks if any two ships are near eachother

class BoardAutomatic(Board):
    def __init__(self):
        super().__init__(list_ships=self.generate_ships_automatically())

    def generate_ships_automatically(self) -> List[Ship]:
        """
        :return: A list of automatically (randomly) generated ships for the board
        """
        free_coords = set(permutations(range(1,11), 2))  ## all the coords in a 10x10 board
        list_ships = []
        first_ship = True
        for length in list(self.DICT_NUMBER_SHIPS_PER_LENGTH.keys())[::-1]:  ## reverse slice to create big ships first
            for number_of_ships_of_length in range(self.DICT_NUMBER_SHIPS_PER_LENGTH[length]):
                ship_created_successfully = False
                while not ship_created_successfully:
                    start_coord = choice(tuple(free_coords))  ## random start coord
                    end_coord = choice([(start_coord[0] + (length - 1), start_coord[1]), (start_coord[0], start_coord[1] + (length - 1)), (start_coord[0] - (length - 1), start_coord[1]),  (start_coord[0], start_coord[1] - (length - 1))])  ## randomly chooses between vertical or horizontal via choice of end_coord
                    new_ship = Ship(coord_start = start_coord, coord_end = end_coord)  ##  create the new ship
                    if not new_ship.get_all_coordinates().issubset(free_coords): ## if any of the ship coords are not valid
                        continue
                    elif first_ship:
                        list_ships.append(new_ship)
                        first_ship = False
                        free_coords.difference_update(new_ship.get_all_coordinates())  ##  remove all taken coords
                        ship_created_successfully = True
                    elif not any(new_ship.is_near_ship(other_ship) for other_ship in list_ships):  ##  checks if new ship is near any other ships
                        list_ships.append(new_ship)
                        free_coords.difference_update(new_ship.get_all_coordinates())
                        ship_created_successfully = True
        return list_ships



if __name__ == '__main__':
    # SANDBOX for you to play and test your functions
    '''list_ships = [
        Ship(coord_start=(1, 1), coord_end=(1, 1)),
        Ship(coord_start=(3, 3), coord_end=(3, 4)),
        Ship(coord_start=(5, 3), coord_end=(5, 5)),
        Ship(coord_start=(7, 1), coord_end=(7, 4)),
        Ship(coord_start=(9, 3), coord_end=(9, 7)),
    ]
'''


    ##board = Board(list_ships)

    board = BoardAutomatic()
    board.generate_ships_automatically()

   # for ship in list_ships:
    #    print(ship.get_all_coordinates())
     #   print(ship.is_on_coordinate(1,1))


    print(f' lengths of ships correct? {board.lengths_of_ships_correct()}')
    print(f'are any ships too close?  {board.are_some_ships_too_close_from_each_other()}')
    board.print_board_with_ships_positions()
    board.print_board_without_ships_positions()

    print(f'is attacked at (1, 1)?  {board.is_attacked_at(1, 1)}')
    print(f'is attacked at (3, 3)?  {board.is_attacked_at(3, 3)}')
    print(f'is attacked at (5, 4)?  {board.is_attacked_at(5, 4)}')
    print(f'is attacked at (10, 9)?  {board.is_attacked_at(10, 9)}')
    print(board.set_coordinates_previous_shots)
    print(board.lengths_of_ships_correct())
