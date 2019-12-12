from typing import NamedTuple, NewType


Fips = NewType("Fips", str)
StateFips = NewType("StateFips", str)
CountyFips = NewType("CountyFips", str)
County = NamedTuple("County", [("fips", Fips), ("name", str), ("state", str)])
