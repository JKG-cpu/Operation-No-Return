from src import MapGenerator

CHAR_MAP = {
    0: " ",  # empty
    1: "#",  # border
    2: "D",  # door
    3: "W",  # wall
    4: "E",  # enemy
    5: "O",  # object
}

m1 = MapGenerator()
m1.generate_new_map((50, 50))

for row in m1.current_loaded_map:
    print("".join(CHAR_MAP.get(int(tile), "?") for tile in row))
