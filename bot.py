from collections import Counter
from functools import partial
from pprint import pprint
from collections import deque
from typing import Dict, List
from game_message import *
from bot_message import *
import random

TAIL_THRESHOLD = 15
TAIL_INCREMENT = 2
OPPONENT_THRESHOLD = 7


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
        self.opponents_spawn = []
        self.opponents = []

    def get_next_move(self, game_message: GameMessage) -> Move:
        try:
            return self._get_next_move(game_message)
        except Exception as e:
            try:
                print(e)
                legal_moves = [Move.FORWARD, Move.TURN_LEFT, Move.TURN_RIGHT]

                next_moves = self.prune_legal_moves(
                    legal_moves, (self.player.position.x, self.player.position.y), self.player.direction
                )
                if len(next_moves) > 0:
                    return random.choice(next_moves[0])
                return Move.TURN_LEFT
            except Exception as e:
                print(e)
                return Move.TURN_LEFT

    def _get_next_move(self, game_message: GameMessage) -> Move:
        global TAIL_THRESHOLD
        self.game = game_message.game
        
        
        # print(self.game.pretty_map)

        if not self.player:
            print("Set player")
            for player in game_message.players:
                if player.id == self.game.player_id:
                    self.player = player
                else:
                    self.opponents.append(player)
                    self.opponents_spawn = [player.spawn_position]
        else:
            self.player = game_message.players[self.player.id]

        for o in self.opponents:
            
            if self.is_adjacent(o.position, self.player.position) and o.position != o.spawn_position:
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

        if self.goal:
            if (self.player.position.x, self.player.position.y) == (
                self.player.spawn_position.x,
                self.player.spawn_position.y,
            ):
                self.goal = None
            if (self.player.position.x, self.player.position.y) == self.goal:
                self.goal = None

        if legal_moves:
            # if the tail of someone is close enough, go for it
            candidate = []
            for o in self.opponents:
                if self.opponent_in_range(o):
                    candidate += [
                        (pos.x, pos.y) for pos in o.tail + [o.position]
                    ]

            if len(candidate) > 0:
                self.goal = self.closest_point_from_player(candidate)

            if self.goal:
                return self.pathfind(
                    (self.player.position.x, self.player.position.y), self.goal
                )

            # if blitzerium on the map, go for it
            if len(self.items["$"]) > 0:
                candidate = list(self.items["$"])
                if self.player.position != self.player.spawn_position:
                    candidate.append(
                        (
                            self.player.spawn_position.x,
                            self.player.spawn_position.y,
                        )
                    )
                self.goal = self.closest_point_from_player(candidate)

                try:
                    self.items["$"].remove(self.goal)
                except:
                    pass

                path = self.pathfind(
                    (self.player.position.x, self.player.position.y), self.goal,
                    sudoku=False
                )
                if path == None:
                    self.goal = None
                else:
                    return path

            owned_cells = self.owned_cells()
            if len(self.player.tail) > TAIL_THRESHOLD:
                destination = self.closest_point_from_player(owned_cells)

                return self.pathfind(
                    (self.player.position.x, self.player.position.y),
                    destination,
                )

            # DO NOT USE THIS, DOES NOT WORK YET
            return self.move_away_from_owned_cells(legal_moves, owned_cells)

        return self.move_from_direction(self.player.direction, Direction.UP)

    def suicide(self):
        candidate = [(pos.x, pos.y) for pos in self.player.tail[:-2]]
        candidate += list(self.items["W"])
        target = self.closest_point_from_player(candidate)

        return self.move_towards(
            self.player.direction,
            (self.player.position.x, self.player.position.y),
            target,
        )

    def opponent_in_range(self, o):
        if (
            manhattan_distance(
                (self.player.position.x, self.player.position.y),
                (o.spawn_position.x, o.spawn_position.y),
            )
            <= OPPONENT_THRESHOLD
        ):
            return False

        for pos in o.tail + [o.position]:
            if (
                manhattan_distance(
                    (self.player.position.x, self.player.position.y),
                    (pos.x, pos.y),
                )
                <= OPPONENT_THRESHOLD
            ):
                return True
        return False

    def move_away_from_owned_cells(self, legal_moves, owned_cells):
        # go over legal_moves and pick move that goes towards direction that has
        # smallest number of owned cells
        position = (self.player.position.x, self.player.position.y)
        moves = []
        for move, position in legal_moves:
            if not self.can_pathfind(
                position, self.closest_point_from_player(owned_cells)
            ):
                continue

            direction = self.player.direction
            if move == Move.TURN_LEFT:
                direction = self.turn_left(direction)
            if move == Move.TURN_RIGHT:
                direction = self.turn_right(direction)
            owned_count = 0
            if direction == Direction.UP:
                owned_count = sum(
                    1
                    for cell in owned_cells
                    if cell[0] == position[0] and cell[1] < position[1]
                )
            if direction == Direction.DOWN:
                owned_count = sum(
                    1
                    for cell in owned_cells
                    if cell[0] == position[0] and cell[1] > position[1]
                )
            if direction == Direction.LEFT:
                owned_count = sum(
                    1
                    for cell in owned_cells
                    if cell[1] == position[1] and cell[0] < position[0]
                )
            if direction == Direction.RIGHT:
                owned_count = sum(
                    1
                    for cell in owned_cells
                    if cell[1] == position[1] and cell[0] > position[0]
                )
            moves.append((move, owned_count))
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

    def pathfind(self, start, destination, sudoku=True):
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
            if sudoku:
                return self.suicide()
            else:
                return None

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
            if (
                position in self.items["W"]
                or position in self.items["!"]
                or self.is_spawn_point(position)
            ):
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

    def can_pathfind(self, start, destination):
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
            return False

        return True

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


def flood_fill(points):
    """
    finds all points within the set of points (assumes the set of points is
    closed)
    """
    visited = set(points)

    candidates = Counter()
    for point in visited:
        x, y = point
        # top left corner
        if (
            (x + 1, y) in visited
            and (x, y + 1) in visited
            and (x + 1, y + 1) not in visited
        ):
            candidates[(x + 1, y + 1)] += 1
        if (
            (x, y + 1) in visited
            and (x + 1, y + 1) in visited
            and (x + 1, y) not in visited
        ):
            candidates[(x + 1, y)] += 1
        if (
            (x + 1, y) in visited
            and (x + 1, y + 1) in visited
            and (x, y + 1) not in visited
        ):
            candidates[(x, y + 1)] += 1
        if (
            (x - 1, y) in visited
            and (x, y - 1) in visited
            and (x - 1, y - 1) not in visited
        ):
            candidates[(x - 1, y - 1)] += 1

    stack = [c for c, count in candidates.items() if count > 1]
    while stack:
        current_point = stack.pop()
        if current_point in visited:
            continue
        visited.add(current_point)
        x, y = current_point
        for neighbor_point in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if neighbor_point not in visited:
                stack.append(neighbor_point)

    return visited
