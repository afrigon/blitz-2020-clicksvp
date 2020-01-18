from functools import partial
from pprint import pprint
from collections import deque
from typing import Dict, List
from game_message import *
from bot_message import *
import random

TAIL_THRESHOLD = 15


def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


class Bot:
    def __init__(self):
        """
        This method should be use to initialize some variables you will need throughout the game.
        """
        self.player = None
        self.opponents = []
        self.game = None
        self.goal = None

    def get_next_move(self, game_message: GameMessage) -> Move:
        global TAIL_THRESHOLD
        self.game = game_message.game
        self.opponents = []
        self.opponents_spawn = []
        
        for player in game_message.players:
            if player.id == self.game.player_id:
                self.player = player
            else:
                self.opponents.append(player)

        for o in self.opponents:
            self.opponents_spawn = [opp.spawn_position for opp in self.opponents]
            if self.is_adjacent(o.position, self.player.position):
                if o.position.x < self.player.position.x:
                    return self.move(Direction.LEFT)
                if o.position.x > self.player.position.x:
                    return self.move(Direction.RIGHT)
                if o.position.y > self.player.position.y:
                    return self.move(Direction.DOWN)
                if o.position.y < self.player.position.y:
                    return self.move(Direction.UP)

        players_by_id: Dict[
            int, Player
        ] = game_message.generate_players_by_id_dict()

        self.items = {"W": set(), "%": set(), "$": set(), "!": set()}

        for rowi, row in enumerate(self.game.map):
            for coli, col in enumerate(row):
                if col in ["$", "!", "W", "%"]:
                    self.items[col].add((coli, rowi))

        legal_moves = self.get_legal_moves_for_current_tick(
            game=game_message.game, players_by_id=players_by_id
        )

        legal_moves = self.prune_legal_moves(
            legal_moves,
            (self.player.position.x, self.player.position.y),
            self.player.direction,
        )

        if self.player.position == self.player.spawn_position:
            TAIL_THRESHOLD += TAIL_INCREMENT

        if self.goal:
            if (self.player.position.x, self.player.position.y) == self.goal:
                self.goal = None

        if legal_moves:
            if self.goal:
                return self.pathfind(
                    (self.player.position.x, self.player.position.y), self.goal
                )

            # if blitzerium on the map, go for it
            if len(self.items["$"]) > 0:
                self.goal = self.closest_point_from_player(self.items["$"])
                self.items["$"].remove(self.goal)

                return self.pathfind(
                    (self.player.position.x, self.player.position.y), self.goal
                )

            owned_cells = self.owned_cells()
            if len(self.player.tail) > TAIL_THRESHOLD:
                destination = self.closest_point_from_player(owned_cells)
                return self.pathfind(
                    (self.player.position.x, self.player.position.y),
                    destination,
                )

            # DO NOT USE THIS, DOES NOT WORK YET
            # return self.move_away_from_owned_cells(legal_moves, owned_cells)
            return random.choice(legal_moves)[0]

        return self.move_from_direction(self.player.direction, Direction.UP)

    def move_away_from_owned_cells(self, legal_moves, owned_cells):
        moves = []
        for move, position in legal_moves:
            moves.append(
                (
                    move,
                    sum(
                        manhattan_distance(position, oc) for oc in owned_cells
                    ),
                )
            )
        return min(moves, key=lambda x: x[1])[0]

    def owned_cells(self):
        owned = "C-" + str(self.game.player_id)
        owned_planet = "%-" + str(self.game.player_id)
        owned_cells = {
            (coli, rowi)
            for rowi, row in enumerate(self.game.map)
            for coli, col in enumerate(row)
            if col in [owned, owned_planet]
        }
        return owned_cells

    def closest_point_from_player(self, points):
        closest = min(
            points,
            key=partial(
                manhattan_distance,
                (self.player.position.x, self.player.position.y),
            ),
        )
        return closest

    def move(self, direction):
        return self.move_from_direction(self.player.direction, direction)

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
        return (abs(p1.x - p2.x) == 1 and abs(p1.y - p2.y) == 0) or (
            abs(p1.x - p2.x) == 0 and abs(p1.y - p2.y) == 1
        )

    def pathfind(self, start, destination):
        legal_moves = [Move.FORWARD, Move.TURN_LEFT, Move.TURN_RIGHT]
        Q = deque([(start, self.player.direction)])
        parent = {}
        visited = set()

        while Q:
            current_position, current_direction = Q.popleft()
            if current_position in visited:
                continue
            visited.add(current_position)

            if current_position == destination:
                break

            next_moves = self.prune_legal_moves(
                legal_moves, current_position, current_direction
            )
            next_moves = sorted(
                next_moves,
                key=lambda move_position: manhattan_distance(
                    destination, move_position[1]
                ),
            )

            for (move, position) in next_moves:
                if move == Move.FORWARD:
                    Q.append((position, current_direction))
                if move == Move.TURN_LEFT:
                    Q.append((position, self.turn_left(current_direction)))
                if move == Move.TURN_RIGHT:
                    Q.append((position, self.turn_right(current_direction)))
                if position not in parent:
                    parent[position] = current_position

        if destination not in parent:
            return random.choice(legal_moves)[0]

        path = [destination]
        while path[-1] != start:
            position = path[-1]
            path.append(parent[position])

        # TODO: store path instead of recomputing every time

        next_position = list(reversed(path))[1]

        return self.move_towards(self.player.direction, start, next_position)

    def move_towards(self, direction, from_, to_):
        fx, fy = from_
        tx, ty = to_

        if direction == Direction.UP:
            if ty < fy:
                return Move.FORWARD
            if tx < fx:
                return Move.TURN_LEFT
            return Move.TURN_RIGHT
        if direction == Direction.DOWN:
            if ty > fy:
                return Move.FORWARD
            if tx < fx:
                return Move.TURN_RIGHT
            return Move.TURN_LEFT
        if direction == Direction.LEFT:
            if tx < fx:
                return Move.FORWARD
            if ty > fy:
                return Move.TURN_LEFT
            return Move.TURN_RIGHT
        if direction == Direction.RIGHT:
            if tx > fx:
                return Move.FORWARD
            if ty > fy:
                return Move.TURN_RIGHT
            return Move.TURN_LEFT

    def turn_left(self, current_direction):
        return {
            Direction.UP: Direction.LEFT,
            Direction.LEFT: Direction.DOWN,
            Direction.DOWN: Direction.RIGHT,
            Direction.RIGHT: Direction.UP,
        }[current_direction]

    def turn_right(self, current_direction):
        return {
            Direction.UP: Direction.RIGHT,
            Direction.RIGHT: Direction.DOWN,
            Direction.DOWN: Direction.LEFT,
            Direction.LEFT: Direction.UP,
        }[current_direction]

    def prune_legal_moves(
        self, legal_moves, player_position, player_direction
    ):
        game_map = self.game.map

        moves = self.get_moves(player_position, player_direction)

        rowcount = len(game_map)
        colcount = len(game_map[0])

        tail_locations = self.tail_locations()

        valid_moves = []
        for (move, position) in moves:
            # This code is trash but it works
            if position in self.items["W"]or position in self.items["!"] or self.is_spawn_point(position):
                continue
            if position in tail_locations:
                continue
            if move not in legal_moves:
                continue
            if not (0 <= position[1] < rowcount):
                continue
            if not (0 <= position[0] < colcount):
                continue
            valid_moves.append((move, position))

        return list(valid_moves)

    def is_spawn_point(self, position):
        for spawn_point in self.opponents_spawn:
            if position == (spawn_point.x, spawn_point.y):
                return True
        return False

    def tail_locations(self):
        locations = [(p.x, p.y) for p in self.player.tail[1:]]
        return locations

    def get_moves(self, position, direction):
        col, row = position

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
