from pprint import pprint

from src import MapGenerator

m1 = MapGenerator()
m2 = MapGenerator()

m1.generate_new_map((50, 50))

room1 = m1.rooms
pprint(room1)

m2.generate_new_map((100, 100))

room2 = m2.rooms
pprint(room2)
