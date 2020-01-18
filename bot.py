from pprint import pprint
from typing import Dict, List
from game_message import *
from bot_message import *
import random


class Bot:
    def __init__(self):
        """
        This method should be use to initialize some variables you will need throughout the game.
        """
        self.player = None
        self.opponent = None
        self.game = None

    def get_next_move(self, game_message: GameMessage) -> Move:
        """
        Here is where the magic happens, for now the moves are random. I bet you can do better ;)
        """
        players_by_id: Dict[
            int, Player
        ] = game_message.generate_players_by_id_dict()

        legal_moves = self.get_legal_moves_for_current_tick(
            game=game_message.game, players_by_id=players_by_id
        )

        self.player = players_by_id[0]
        self.opponent = players_by_id.get(1, None)
        self.game = game_message.game

        legal_moves = self.prune_legal_moves(legal_moves)

        return random.choice(legal_moves)

    def prune_legal_moves(self, legal_moves):
        game_map = self.game.map
        rowcount = len(game_map)
        colcount = len(game_map[0])

        asteroid_locations = {
            (rowi, coli)
            for rowi, row in enumerate(game_map)
            for coli, col in enumerate(row)
            if col == "W"
        }

        moves = self.get_moves()

        valid_moves = {
            move
            for (move, position) in moves
            if position not in asteroid_locations
            and move in legal_moves
            and 0 <= position[0] < rowcount
            and 0 <= position[1] < colcount
        }

        print(self.game.pretty_map)

        return list(valid_moves)

    def get_moves(self):
        position = self.player.position
        direction = self.player.direction
        row, col = position.x, position.y

        if direction == Direction.UP:
            return [
                (Move.FORWARD, (row - 1, col)),
                (Move.TURN_LEFT, (row, col - 1)),
                (Move.TURN_RIGHT, (row, col + 1)),
            ]
        if direction == Direction.DOWN:
            return [
                (Move.FORWARD, (row + 1, col)),
                (Move.TURN_LEFT, (row, col + 1)),
                (Move.TURN_RIGHT, (row, col - 1)),
            ]
        if direction == Direction.LEFT:
            return [
                (Move.FORWARD, (row, col - 1)),
                (Move.TURN_LEFT, (row - 1, col)),
                (Move.TURN_RIGHT, (row + 1, col)),
            ]
        if direction == Direction.RIGHT:
            return [
                (Move.FORWARD, (row, col + 1)),
                (Move.TURN_LEFT, (row + 1, col)),
                (Move.TURN_RIGHT, (row - 1, col)),
            ]

    def can_stomp_opponent(self, players_by_id):
        pass

    def stomp_opponent(self):
        pass

    def get_legal_moves_for_current_tick(
        self, game: Game, players_by_id: Dict[int, Player]
    ) -> List[Move]:
        """
        You should define here what moves are legal for your current position and direction
        so that your bot does not send a lethal move.

        Your bot moves are relative to its direction, if you are in the DOWN direction.
        A TURN_RIGHT move will make your bot move left in the map visualization (replay or logs)
        """
        me: Player = players_by_id[game.player_id]

        return [move for move in Move]
