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

        print("legal_moves: ", legal_moves)
        legal_moves = self.prune_legal_moves(legal_moves)
        print("pruned legal moves: ", legal_moves)

        if legal_moves:
            print(self.player.position)
            print(self.player.direction)
            print(legal_moves)
            print(self.game.pretty_map)
            return random.choice(legal_moves)

        return Direction.FORWARD

    def prune_legal_moves(self, legal_moves):
        game_map = self.game.map

        asteroid_locations = {
            (rowi, coli)
            for rowi, row in enumerate(game_map)
            for coli, col in enumerate(row)
            if col == "W"
        }

        moves = self.get_moves()
        print("moves: ", moves)

        rowcount = len(game_map)
        colcount = len(game_map[0])

        tail_locations = self.tail_locations()
        print("tail: ", tail_locations)

        valid_moves = []
        for (move, position) in moves:
            print(move, position)
            if position in asteroid_locations:
                print("asteroid")
                continue
            if position in tail_locations:
                print("tail")
                continue
            if move not in legal_moves:
                print("not legal")
                continue
            if not (0 <= position[0] < rowcount):
                print("row wrong")
                continue
            if not (0 <= position[0] < colcount):
                print("col wrong")
                continue
            valid_moves.append(move)

        # valid_moves = {
        #     move
        #     for (move, position) in moves
        #     if position not in asteroid_locations
        #     and position not in tail_locations
        #     and move in legal_moves
        #     and 0 <= position[0] < rowcount
        #     and 0 <= position[1] < colcount
        # }

        return list(valid_moves)

    def tail_locations(self):
        locations = [(p.x, p.y) for p in self.player.tail]
        return locations

    def get_moves(self):
        position = self.player.position
        direction = self.player.direction
        col, row = position.x, position.y

        if direction == Direction.UP:
            return [
                (Move.FORWARD, (col, row - 1)),
                (Move.TURN_LEFT, (col - 1, row)),
                (Move.TURN_RIGHT, (col + 1, row)),
            ]
        if direction == Direction.DOWN:
            return [
                (Move.FORWARD, (col, row + 1)),
                (Move.TURN_LEFT, (col + 1, row)),
                (Move.TURN_RIGHT, (col - 1, row)),
            ]
        if direction == Direction.LEFT:
            return [
                (Move.FORWARD, (col - 1, row)),
                (Move.TURN_LEFT, (col, row + 1)),
                (Move.TURN_RIGHT, (col, row - 1)),
            ]
        if direction == Direction.RIGHT:
            return [
                (Move.FORWARD, (col + 1, row)),
                (Move.TURN_LEFT, (col, row - 1)),
                (Move.TURN_RIGHT, (col, row + 1)),
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
