from enum import Enum, auto

__all__ = ["DirectionError", "InvalidRoomSizeError", "RoomType", "RoomObjective", "Directions", "TILES", "EnemyDensityPercent", "ObjectDensityPercent", "AVERAGE_ROOM_AREA"]


class DirectionError(Exception):
    """Exception raised for when a coordinate provided cannot have a proper direction resolved"""

    def __init__(
        self, message: str = "Cannot resolve a direction for the current coordinates"
    ) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidRoomSizeError(Exception):
    """Exception raised for when `RoomNode` dimensions are to small"""

    def __init__(self, width: int, height: int, message: str | None = None) -> None:
        self.message = (
            f"Dimensions ({width}x{height}) are to small for a RoomNode. Increase them?"
        )

        if message:
            self.message = message + "\n" + self.message

        super().__init__(self.message)


class RoomType(Enum):
    ENTRY = auto()
    JUNCTION = auto() # Alot of rooms attached
    DEADEND = auto() # Only one connection / decoy
    STANDARD = auto() # Normal room, maybe 1-2 rooms attached


class RoomObjective(Enum):
    NONE = auto()
    DECOY = auto()
    OBJECTIVE = auto()


class Directions(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()


class EnemyDensityPercent(Enum):
    LOW = 0.05
    ACTIVE = 0.07
    HIGH = 0.1
    AMBUSH = 0.15


class ObjectDensityPercent(Enum):
    SPARSE = 0.03
    NORMAL = 0.06
    CLUTTERED = 0.1
    FORTIFIED = 0.15


TILES: dict[str, int] = {
    "empty": 0,
    "border": 1,
    "door": 2,
    "wall": 3,
    "enemy": 4,
    "object": 5,
}

AVERAGE_ROOM_AREA = 12 * 10
