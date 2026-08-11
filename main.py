from src import MapGenerator

m1 = MapGenerator()
m1.generate_new_map((50, 50))

for room in m1.room_graph:
    print(f"{room} at grid {room.get_grid_position()}")

m2 = MapGenerator()
m2.generate_new_map((100, 100))

for room in m2.room_graph:
    print(f"{room} at grid {room.get_grid_position()}")

positions = [room.get_grid_position() for room in m1.room_graph]
unique_positions = set(positions)

if len(positions) != len(unique_positions):
    print(f"OVERLAP DETECTED: {len(positions)} rooms, only {len(unique_positions)} unique positions")
else:
    print(f"No overlaps: {len(positions)} rooms, all unique positions")
