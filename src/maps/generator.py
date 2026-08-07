import numpy as np
import random
from pprint import pprint

from .nodes import RoomNode
from .consts import RoomType


__all__ = ["MapGenerator"]


class MapGenerator:
    def __init__(self) -> None:
        self.current_loaded_map: np.ndarray = np.array([])
        self.room_graph: dict[int, set[int]] = {}

        self.entries: list[int] = []
        self.objective: int | None = None
        self.decoy_objectives: list[int] = []

    # ========== Helpers ==========
    def _is_full_connected(self, graph: dict[int, set[int]]) -> bool:
        """
        Check whether every room in the graph is reachable from every other
        room - i.e. there are no isolated "islands."

        Works by starting at any single room and spreading outward (visiting
        every connected neighbor, then their neighbors, and so on) until
        nothing new is found. If the number of rooms visited this way equals
        the total room count, nothing was left stranded.

        Returns True if the graph is fully connected, False otherwise.
        """
        if not graph:
            return True

        start = next(iter(graph))
        visited = {start}
        to_check = [start]

        while to_check:
            current = to_check.pop()
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    to_check.append(neighbor)

        return len(visited) == len(graph)

    def _get_room_degrees(self, graph: dict[int, set[int]]) -> dict[int, int]:
        """
        Count how many direct connections each room has.

        A room's "degree" is just the size of its connection set - how many
        other rooms it directly connects to. This is used as the basis for
        several downstream decisions: low-degree rooms are good entry point
        candidates (they sit on the "edge" of the layout), degree-1 rooms
        are dead ends, and high-degree rooms (relative to the map's average)
        become junctions.

        Returns a dict mapping each room ID to its degree, e.g. {0: 3, 1: 1, 2: 2}.
        """
        rooms = list(graph.keys())

        return {
            r: len(graph[r]) for r in rooms
        }

    def _is_room_connected_to_entry(self, graph: dict[int, set[int]], room: int) -> bool:
        """
        Check whether a given room is directly connected to any room already
        marked as an entry point.

        Used while picking entries, so newly chosen entries aren't placed
        right next to ones already chosen - keeping them spread out across
        the map instead of clustered together.

        Returns False immediately if no entries have been chosen yet.
        """
        if not self.entries:
            return False

        for entry in self.entries:
            connections = graph[entry]

            if room in connections:
                return True

        return False

    def _get_distance_from_room(self, graph: dict[int, set[int]], start: int) -> dict[int, int]:
        """
        Measure how many "hops" away every other room is from a given starting room.

        Works by spreading outward one ring at a time (breadth-first search):
        first visit every room directly connected to `start` (1 hop away), then
        every room connected to those (2 hops away), and so on, until nothing
        new is found.

        Important: `to_check.pop(0)` (pulling from the front of the list) is
        what makes this explore ring-by-ring, in order of distance, rather than
        diving deep down one path first. That guarantees the *first* time a
        room is reached, it's via the shortest possible path - so the distances
        returned are always minimal, never accidentally inflated by a longer
        route being found first.

        Returns a dict mapping each reachable room ID to its distance from
        `start`, e.g. {start: 0, 4: 1, 7: 2}. `start` itself is always 0.
        """
        distances = {start: 0}
        to_check = [start]

        while to_check:
            current = to_check.pop(0)
            for neighbor in graph[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    to_check.append(neighbor)

        return distances

    def _get_min_distance_from_entries(self, graph: dict[int, set[int]]) -> dict[int, int]:
        """
        Find, for every room, how far it is from the *nearest* entry point -
        not the farthest, and not some average.

        Runs `_get_distance_from_room` once per entry (since each entry has
        its own distance map), then for every room, keeps only the smallest
        distance seen across all of them. This matters because a room could
        be far from one entry but right next to another - what we actually
        care about is "how close can a player realistically get to this room,
        picking whichever entrance is most convenient," which is always the
        minimum, not any single entry's value in isolation.

        This is the basis for objective selection: the room with the LARGEST
        value in the returned dict is the one that's genuinely hard to reach,
        no matter which entrance a player picks.

        Returns a dict mapping each room ID to its distance from the closest
        entry, e.g. {0: 0, 1: 0, 2: 3, 3: 1}. Entry rooms themselves always
        map to 0.
        """
        room_min_distance: dict[int, int] = {}

        for entry in self.entries:
            distances = self._get_distance_from_room(graph, entry)

            for room, dist in distances.items():
                if room not in room_min_distance or dist < room_min_distance[room]:
                    room_min_distance[room] = dist

        return room_min_distance

    def _get_farthest_rooms(self, room_min_distance: dict[int, int]) -> list[int]:
        """
        Find every room tied for the largest "distance from nearest entry"
        value - not just the first one found.

        Capturing every room at the max distance (rather than stopping at
        one) matters because ties are exactly what make good decoy
        candidates: rooms that are equally hard to reach as the true
        objective, so a player can't tell them apart just by how deep
        they are.

        Returns a list of room IDs, e.g. [2] if there's a single farthest
        room, or [2, 5] if rooms 2 and 5 are tied.
        """
        max_distance = max(room_min_distance.values())

        return [
            room for room, dist in room_min_distance.items()
            if dist == max_distance
        ]

    def _get_junction_threshold(self, degrees: dict[int, int]) -> float:
        """
        Calculate how many connections a room needs to count as a "junction,"
        scaled to this specific map rather than a fixed number.

        Uses the graph's average degree (total connections summed across all
        rooms, divided by room count) as a baseline, then requires a room to
        have 1.5x that average to qualify as a junction. This way the
        threshold automatically adjusts to the map's overall density - a
        sparse map and a densely-connected map will each get a sensible,
        proportional junction cutoff instead of sharing one flat number that
        might be meaningless on one map size and too strict on another.

        Returns the minimum degree (as a float) a room needs to be tagged
        JUNCTION.
        """
        total_degree = sum(degrees.values())
        average_degree = total_degree / len(degrees)

        return average_degree * 1.5

    # ========== Generators ==========
    def _generate_entries(self, graph: dict[int, set[int]]) -> None:
        """
        Choose up to `self.max_entries` rooms to act as entry points.

        Favors low-degree rooms (degree <= 2) since these sit on the "edge"
        of the layout, similar to how real entrances tend to be on the
        perimeter of a building rather than in a busy central room. Also
        skips any candidate directly connected to an entry already chosen,
        so entries end up spread across the map instead of clustered next
        to each other.

        Populates `self.entries` in place. Prints a warning if no valid
        entries were found (should be rare, but not yet raised as an
        exception).
        """
        room_degrees = self._get_room_degrees(graph)

        for room, degree_count in room_degrees.items():
            if len(self.entries) == self.max_entries:
                return

            if degree_count <= 2 and not self._is_room_connected_to_entry(graph, room):
                self.entries.append(room)

        if len(self.entries) == 0:
            print("No Entries Generated") # Handle with Exception later

    def _generate_objectives(self, graph: dict[int, set[int]]) -> None:
        """
        Choose the true objective room, plus any decoy rooms.

        The objective is picked from whichever room(s) sit farthest from
        every entry point (see `_get_min_distance_from_entries` /
        `_get_farthest_rooms`). If multiple rooms are tied for farthest,
        one is chosen at random as the real objective and the rest become
        decoys - rooms equally "deep" in the map, so a player can't tell
        which one is real just by how far in it is.

        If only one room is farthest (no tie), there are no decoys for
        this map.

        Sets `self.objective` and `self.decoy_objectives` in place.
        """
        room_min_distance = self._get_min_distance_from_entries(graph)

        farthest_rooms = self._get_farthest_rooms(room_min_distance)

        if len(farthest_rooms) == 1:
            self.objective = farthest_rooms[0]

        else:
            self.objective = random.choice(farthest_rooms)
            farthest_rooms.remove(self.objective)
            self.decoy_objectives = farthest_rooms

    def _tag_rooms(self, graph: dict[int, set[int]]) -> dict[int, RoomType]:
        """
        Assign a `RoomType` to every room in the graph.

        Priority order matters here, since a room can only hold one
        RoomType even though it might qualify for more than one category:
        1. Entry rooms are tagged ENTRY first, regardless of their degree -
           being a spawn point is the more important fact about that room.
        2. Remaining degree-1 rooms are tagged DEADEND.
        3. Remaining rooms at or above the junction threshold (see
           `_get_junction_threshold`) are tagged JUNCTION.
        4. Everything left over is tagged STANDARD.

        Returns a dict mapping each room ID to its assigned RoomType.
        """
        room_degrees = self._get_room_degrees(graph)
        room_types: dict[int, RoomType] = {}
        junction_threshold = self._get_junction_threshold(room_degrees)

        for room, degree in room_degrees.items():
            if room in self.entries:
                room_types[room] = RoomType.ENTRY

            elif degree == 1:
                room_types[room] = RoomType.DEADEND

            elif degree >= junction_threshold:
                room_types[room] = RoomType.JUNCTION

            else:
                room_types[room] = RoomType.STANDARD

        return room_types

    def _add_extra_connects(self, graph: dict[int, set[int]], extra_ratio: float = 0.3) -> None:
        """
        Add extra random connections on top of the base topology, so the
        map has loops (multiple routes between rooms) instead of being a
        single-path tree with no alternate routes.

        `extra_ratio` controls how many bonus connections to add, relative
        to room count - e.g. 0.3 on a 10-room map aims for ~3 extra
        connections. Candidate room pairs that are already connected are
        skipped and retried, up to `max_attempts`, so this doesn't loop
        forever if the graph runs out of valid new pairs to connect
        (more likely on very small or already-dense maps).

        Modifies `graph` in place.
        """
        room_count = len(graph)
        extra_count = max(1, int(room_count * extra_ratio))

        attempts = 0
        added = 0
        max_attempts = extra_count * 10

        while added < extra_count and attempts < max_attempts:
            attempts += 1

            room_a, room_b = random.sample(range(room_count), 2)

            if room_b in graph[room_a]:
                continue

            graph[room_a].add(room_b)
            graph[room_b].add(room_a)
            added += 1

    def _generate_topology(self, room_count: int) -> dict[int, set[int]]:
        """
        Build the base room-connection graph, guaranteeing every room is
        reachable from every other room (no islands).

        Works by growing a "connected" group one room at a time: start with
        room 0 as the only member, then for each remaining room (in random
        order), connect it to a randomly chosen room already in the group.
        Since every new room always attaches to something already
        connected, there's no possibility of a room being left stranded -
        the result is a fully connected but "thin" tree shape (mostly
        single paths, few loops), which `_add_extra_connects` builds on
        top of afterward.

        Returns a fresh room graph as a dict mapping each room ID to the
        set of room IDs it connects to.
        """
        graph: dict[int, set[int]] = {i: set() for i in range(room_count)}

        connected = [0] # Room 0 starts connection
        remaining = list(range(1, room_count))
        random.shuffle(remaining)

        for room in remaining:
            target = random.choice(connected)
            graph[room].add(target)
            graph[target].add(room)
            connected.append(room)

        return graph

    # ========== Callables ==========
    def generate_new_map(self) -> np.ndarray:
        """
        Generate a full map: topology, entry points, objective/decoys, and
        room type tags.

        This currently only builds and prints the abstract room graph -
        actual RoomNode instances (real geometry, doors, objects, enemies)
        aren't created yet; that happens in a later integration step.

        Returns the (currently blank) map array. Room graph and generation
        results are stored on the instance (`self.room_graph`,
        `self.entries`, `self.objective`, `self.decoy_objectives`) for
        inspection.
        """
        self.current_loaded_map = np.zeros((50, 50))

        room_count = 10
        self.max_entries = min(4, max(1, room_count // 4))
        self.room_graph = self._generate_topology(room_count)
        self._add_extra_connects(self.room_graph)
        self._generate_entries(self.room_graph)
        self._generate_objectives(self.room_graph)

        room_types = self._tag_rooms(self.room_graph)
        room_min_distance = self._get_min_distance_from_entries(self.room_graph)

        if not self._is_full_connected(self.room_graph):
            print("Graph not fully connected")

        for room_id, connections in self.room_graph.items():
            print()
            print(f"Room {room_id} connects to: {connections}")
            print(f"Room {room_id} is {room_min_distance[room_id]} steps from the nearest entry")
            if room_id in self.entries:
                print(f"Room {room_id} is also an entry point")

        print()
        print(f"Current room objective: {self.objective}")
        print(f"Decoy Objectives: {self.decoy_objectives if self.decoy_objectives else "None"}")

        print("Room Types:")
        pprint(room_types)

        return self.current_loaded_map


