import numpy as np

from .consts import Directions

__all__ = ["GameObject", "Table", "Shelf"]

_ROTATIONS: dict[Directions, int] = {
    Directions.NORTH: 0,
    Directions.EAST: 1,
    Directions.SOUTH: 2,
    Directions.WEST: 3,
}


class GameObject:
    def __init__(
        self,
        x: int,
        y: int,
        direction: Directions,
        los: bool = False,
        movement_restriction: bool = True,
    ) -> None:
        self.pos = (x, y)
        self.size = (0, 0)
        self.direction = direction
        self.los = los
        self.movement_restriction = movement_restriction
        self.object_schematic: np.ndarray = np.array([])

    def get_schematic(self) -> np.ndarray:
        k = _ROTATIONS[self.direction]
        return np.rot90(self.object_schematic, k=k)


class Table(GameObject):
    def __init__(self, x: int, y: int, direction: Directions) -> None:
        super().__init__(x, y, direction, False, True)
        self.size = (1, 2)
        self.object_schematic = np.ones(self.size)


class Shelf(GameObject):
    def __init__(self, x: int, y: int, direction: Directions) -> None:
        super().__init__(x, y, direction, True, True)
        self.size = (1, 1)
        self.object_schematic = np.ones(self.size)
