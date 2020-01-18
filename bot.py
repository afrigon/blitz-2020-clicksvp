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
        self.opponents = []
        self.game = None

    def get_next_move(self, game_message: GameMessage) -> Move:
        self.game = game_message.game
        self.opponents = []

        for player in game_message.players:
            if player.id == self.game.player_id:
                self.player = player
            else:
                self.opponents.append(player)

        for o in self.opponents:
            if self.is_adjacent(o.position, self.player.position):
                if o.position.x < self.player.position.x:
                    return self.move_from_direction(self.player.direction, Direction.LEFT)
                if o.position.x > self.player.position.x:
                    return self.move_from_direction(self.player.direction, Direction.RIGHT)
                if o.position.y > self.player.position.y:
                    return self.move_from_direction(self.player.direction, Direction.DOWN)
                if o.position.y < self.player.position.y:
                    return self.move_from_direction(self.player.direction, Direction.UP)

        players_by_id: Dict[
            int, Player
        ] = game_message.generate_players_by_id_dict()

        legal_moves = self.get_legal_moves_for_current_tick(
            game=game_message.game, players_by_id=players_by_id
        )

        #print("legal_moves: ", legal_moves)
        legal_moves = self.prune_legal_moves(legal_moves)
        #print("pruned legal moves: ", legal_moves)

        if legal_moves:
            #print(self.player.position)
            #print(self.player.direction)
            #print(legal_moves)
            #print(self.game.pretty_map)
            return random.choice(legal_moves)

        return self.move_from_direction(self.player.direction, Direction.UP)

    def move_from_direction(self, player_direction, move_direction):
        if player_direction == Direction.UP:
            if move_direction == Direction.UP:
                return Move.FORWARD
            elif move_direction == Direction.LEFT:
                return Move.TURN_LEFT
            elif move_direction == Direction.RIGHT:
                return Move.TURN_RIGHT
        elif player_direction == Direction.DOWN:
            if move_direction == Direction.DOWN:
                return Move.FORWARD
            elif move_direction == Direction.LEFT:
                return Move.TURN_RIGHT
            elif move_direction == Direction.RIGHT:
                return Move.TURN_LEFT
        elif player_direction == Direction.LEFT:
            if move_direction == Direction.UP:
                return Move.TURN_RIGHT
            if move_direction == Direction.DOWN:
                return Move.TURN_LEFT
            elif move_direction == Direction.LEFT:
                return Move.FORWARD
        elif player_direction == Direction.RIGHT:
            if move_direction == Direction.UP:
                return Move.TURN_LEFT
            if move_direction == Direction.DOWN:
                return Move.TURN_RIGHT
            elif move_direction == Direction.RIGHT:
                return Move.FORWARD

        return None

    def is_adjacent(self, p1, p2):
        print(p1)
        print(p2)
        return (abs(p1.x - p2.x) == 1 and abs(p1.y - p2.y) == 0) or (abs(p1.x - p2.x) == 0 and abs(p1.y - p2.y) == 1)

    def prune_legal_moves(self, legal_moves):
        game_map = self.game.map

        asteroid_locations = {
            (rowi, coli)
            for rowi, row in enumerate(game_map)
            for coli, col in enumerate(row)
            if col == TileType.ASTEROIDS
        }

        moves = self.get_moves()
        print("moves: ", moves)

        rowcount = len(game_map)
        colcount = len(game_map[0])

        tail_locations = self.tail_locations()
        print("tail: ", tail_locations)

        valid_moves = []
        for (move, position) in moves:
            # This code is trash but it works
            if position in asteroid_locations:
                continue
            if position in tail_locations:
                continue
            if move not in legal_moves:
                continue
            if not (0 <= position[0] < rowcount):
                continue
            if not (0 <= position[0] < colcount):
                continue
            valid_moves.append(move)

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
