import numpy as np
import random

from .consts import (
    DirectionError,
    InvalidRoomSizeError,
    Directions,
    RoomType,
    RoomObjective,
    TILES,
    EnemyDensityPercent,
    ObjectDensityPercent,
)
from .game_objects import GameObject, Table, Shelf

__all__ = ["RoomNode"]


class RoomNode:
    def __init__(
        self,
        width: int,
        height: int,
        room_type: RoomType = RoomType.STANDARD,
        room_objective: RoomObjective = RoomObjective.NONE,
    ) -> None:
        self.width = width
        self.height = height
        self.room_type = room_type
        self.room_objective = room_objective

        self.map = np.zeros((self.height, self.width))
        self.doors: list[tuple[int, int, Directions]] = []
        self.objects: list[GameObject] = []
        self.grid_position: tuple[int, int] | None = None

        # Construct Border
        self.create_border()

    # ========== Helper Methods ==========
    def _get_door_direction(self, x: int, y: int) -> Directions:
        if x == 0:
            return Directions.WEST

        if x == self.width - 1:
            return Directions.EAST

        if y == 0:
            return Directions.NORTH

        if y == self.height - 1:
            return Directions.SOUTH

        raise DirectionError()

    def _get_object_count(self, density_percent: ObjectDensityPercent) -> int:
        walkable_tiles = (self.width - 2) * (self.height - 2)
        return max(1, int(walkable_tiles * density_percent.value))

    def _get_enemy_count(self, density_percent: EnemyDensityPercent) -> int:
        walkable_tiles = (self.width - 2) * (self.height - 2)
        return max(1, int(walkable_tiles / 2 * density_percent.value))

    def _check_empty(self) -> bool:
        return bool(np.any(self.map == 0))

    def _get_empty(self) -> np.ndarray:
        inner_map = self.map[1:-1, 1:-1]
        return (
            np.argwhere(inner_map == TILES["empty"]) + 1
        )  # Add 1 to adjust indices back to map coords

    def _place_object(self, obj: GameObject, x: int, y: int) -> bool:
        schematic = obj.get_schematic()
        h, w = schematic.shape

        if y + h > self.map.shape[0] or x + w > self.map.shape[1]:
            return False

        region = self.map[y : y + h, x : x + w]

        if not np.all(region == TILES["empty"]):
            return False

        self.map[y : y + h, x : x + w] = np.where(
            schematic == 1, TILES["object"], region
        )

        return True

    # ========== Setup Map ==========
    def create_border(self) -> None:
        self.map[0, :] = TILES["border"]  # Top Row
        self.map[-1, :] = TILES["border"]  # Bottom Row
        self.map[:, 0] = TILES["border"]  # Left Column
        self.map[:, -1] = TILES["border"]  # Right Column

    def generate_objects(self, empty_spots: np.ndarray) -> None:
        if len(empty_spots) == 0:
            return

        placed = 0
        attempts = 0
        max_attempts = self.object_count * 10

        while placed < self.object_count and attempts < max_attempts:
            attempts += 1

            object_cls = random.choice([Table, Shelf])
            dir = random.choice(list(Directions))

            spot = empty_spots[np.random.randint(len(empty_spots))]
            y, x = spot

            obj = object_cls(x, y, dir)

            if self._place_object(obj, x, y):
                self.objects.append(obj)
                placed += 1

    def generate_enemies(self, empty_spots: np.ndarray) -> None:
        if len(empty_spots) == 0:
            raise InvalidRoomSizeError(
                self.width, self.height, "Not enough room for enemies"
            )

        enemy_count = min(self.enemy_count, len(empty_spots))

        if enemy_count < self.enemy_count:
            raise InvalidRoomSizeError(
                self.width,
                self.height,
                f"Not enough empty tiles for enemies (wanted {self.enemy_count}, had {len(empty_spots)})",
            )

        random_choices = np.random.choice(
            len(empty_spots), size=enemy_count, replace=False
        )
        random_coords = empty_spots[random_choices]

        rows = random_coords[:, 0]
        cols = random_coords[:, 1]
        self.map[rows, cols] = TILES["enemy"]

    # ========== Callables ==========
    def build(
        self,
        density_percent: EnemyDensityPercent,
        object_density_percent: ObjectDensityPercent,
    ) -> None:
        self.enemy_count = self._get_enemy_count(density_percent)
        self.object_count = self._get_object_count(object_density_percent)

        self.generate_objects(self._get_empty())
        self.generate_enemies(self._get_empty())

    def add_door(self, x: int, y: int) -> bool:
        # Check if x, y is out of bounds
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return False

        # Check if x or y is not on the border
        if self.map[y][x] != TILES["border"]:
            return False

        # Check if [x, y] is not a corner
        is_corner = x in (0, self.width - 1) and (y in (0, self.height - 1))
        if is_corner:
            return False

        self.map[y][x] = TILES["door"]
        self.doors.append((x, y, self._get_door_direction(x, y)))

        return True  # Door Created

    def set_objective(self, room_objective: RoomObjective) -> None:
        self.room_objective = room_objective

    def set_type(self, room_type: RoomType) -> None:
        self.room_type = room_type

    def set_grid_position(self, grid_x: int, grid_y: int) -> None:
        self.grid_position = (grid_x, grid_y)

    def get_map(self) -> np.ndarray:
        return self.map

    def get_objective(self) -> RoomObjective:
        return self.room_objective

    def get_type(self) -> RoomType:
        return self.room_type

    def get_grid_position(self) -> tuple[int, int] | None:
        return self.grid_position

    def __repr__(self) -> str:
        return (
            f"RoomNode(room_type={self.room_type},room_objective={self.room_objective})"
        )
