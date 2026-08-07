## Idea
- **Game Name**: Operation No Return
- **Description**: You command a team of *Delta Force* Operators, your decisions are their every move. One wrong step could end it all. Take on different modes like ***Clear House*** or ***Capture the Hostage***. You can unlock different types of Operators to take into battle to assist you.

## Tools
### Create custom map renderer / generator
![[Map Renderer + Generator.canvas]]

Each `RoomNode` takes in a `width` and `height`. It then generates an array (with `numpy`) that fills in walls, the floor, objects, enemy positions, etc. 

Each object will have these attributes:
- Position
- Direction (n, s, e, w)
- Size (per object, so table 2 by 1 tiles, etc)
- LOS affection (bool)
- Movement Restriction

And object's layout can be called via `MyObject(...).get_schematic()` which returns an array.

Whenever a map is generated, you would just use `MapGenerator().load_map_from_data(...)` or `MapGenerator().generate_new_map()`. When the map generator is creating a new map, you specify the size.

Args:
- `room_count: int`: The amount of rooms in a map
- `extra_ratio: float = 0.3`: Roughly the amount of connects per room (1 - 2), *increase for more connections between rooms*

After generation is complete, `RoomNode(x, y).get_map()` will return an array with numbers corresponding to tile types. The `MapRenderer` takes in that array (either with `MapRenderer().new_map(map)` or just initialize a new map) and can display that array with `curses` (`MapRenderer().show()`).

### Create some entity classes

### Create game play / choices