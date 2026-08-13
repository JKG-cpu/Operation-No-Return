## Idea
- **Game Name**: Operation No Return
- **Description**: You command a team of *Delta Force* Operators, your decisions are their every move. One wrong step could end it all. Take on different modes like ***Clear House*** or ***Capture the Hostage***. You can unlock different types of Operators to take into battle to assist you.

## Tools
### Create custom map renderer / generator
![[Map Renderer + Generator.canvas]]

Each `RoomNode` takes a `width` and `height` (plus optional `room_type` / `room_objective`, defaulting to `STANDARD` / `NONE`). Construction is **two-phase**: `__init__` immediately builds just the border via `create_border()`, since a room's real type/objective can't be known until the topology pass has run. Later, `set_type(...)` and `set_objective(...)` are called, followed by `build(density_percent, object_density_percent)`, which fills in walls, floor, objects, and enemy positions as a `numpy` array.

Each object will have these attributes:
- Position
- Direction (n, s, e, w)
- Size (per object, so table 2 by 1 tiles, etc)
- LOS affection (bool)
- Movement Restriction

An object's layout can be called via `MyObject(...).get_schematic()` which returns an array.

**Topology is grid-first.** `MapGenerator._generate_topology(room_count)` grows a fully-connected room graph (`dict[RoomNode, set[RoomNode]]`) by attaching each new `RoomNode` to a free grid-adjacent slot of an already-placed room, tracked in an `occupied: dict[tuple[int,int], RoomNode]` dict, with a capped number of retry attempts per room. Because position and connection happen together, direction falls out automatically and room overlap is structurally impossible. `_add_extra_connects` then adds a few more edges, but only between grid-adjacent rooms that aren't already linked — controlled by `extra_ratio`.

To generate a full map, call `MapGenerator().generate_new_map(size: tuple[int, int])`. Internally this:
1. Picks a `room_count` from an estimated range based on `size`
2. Builds topology (`_generate_topology`, `_add_extra_connects`)
3. Picks entries and objective/decoy rooms (`_generate_entries`, `_generate_objectives`)
4. Tags each room with a `RoomType` and calls `finalize_rooms(...)` — running the two-phase `set_type` / `set_objective` / `build()` sequence on every room
5. Sizes `current_loaded_map` from the real placed-room extents, generates doors between connected rooms (`_generate_doors` / `_place_door_pair`, using `_get_direction_between`), and stamps each room's finished array into the map (`_stamp_maps`)

It returns the finished map as a `numpy` array. (Loading a saved/tutorial map instead of generating one is planned but not yet implemented.)

**Planned next:**
- [ ] Route-diversity validation (needed for Capture the Hostage — deliberately deferred until Clear House ships)
- [ ] `MapRenderer` (`curses`-based) — not yet implemented; color later with `curses`
- [ ]  Fog/memory system: additive (`seen |= currently_visible`), tiles "stay lit" once seen, reveal cone originates from door positions

### Create some entity classes


### Create game play / choices
