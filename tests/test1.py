from src import RoomNode

# Use a non-square room to catch axis/rotation bugs
room = RoomNode(15, 8, density_percent="active", object_density_percent="cluttered")

# Add a door on each wall
print("North door:", room.add_door(7, 0))
print("South door:", room.add_door(7, 7))
print("West door:", room.add_door(0, 4))
print("East door:", room.add_door(14, 4))

# Corners should all fail
print("Corner (0,0):", room.add_door(0, 0))
print("Corner (14,7):", room.add_door(14, 7))

print()
print("Doors:", room.doors)
print("Objects placed:", len(room.objects))
for obj in room.objects:
    print(f"  {type(obj).__name__} at {obj.pos}, facing {obj.direction}")

print()
print("Enemy count target:", room.enemy_count)
print("Object count target:", room.object_count)

print()
print(room.get_map())
