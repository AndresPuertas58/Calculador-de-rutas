from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Point:
    lat: float
    lon: float

    @classmethod
    def from_list(cls, coords: List[float]):
        return cls(lat=coords[0], lon=coords[1])

@dataclass
class RouteResponse:
    distance: float  # In meters
    time: int        # In milliseconds
    points: List[Dict[str, float]]
    instructions: List[Dict[str, Any]]

    def to_dict(self):
        return {
            "distance": self.distance,
            "time": self.time,
            "points": self.points,
            "instructions": self.instructions
        }
