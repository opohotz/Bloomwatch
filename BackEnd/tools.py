class LRUCache:

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}

    def get(self, key: str) -> str:
        if key not in self.cache:
            return ""
        val = self.cache[key]
        self.cache.pop(key)
        self.cache[key] = val
        return val

    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            old_val = self.cache.pop(key)
            self.cache[key] = value
            return old_val
        elif len(self.cache) < self.capacity:
            self.cache[key] = value
            return ""
        else:
            for k in self.cache.keys():
                old_val = self.cache.pop(k)
                break
            self.cache[key] = value
            return old_val

class input_parameters:
    """
    The following class compresses the data necessary for inputting into the AppEEARS database into one object.
    Args:
    - latitude (string)   : latitude of the desired coordinate
    - longitude (string)  : longitude of the desired coordinate
    - date_start (string) : Start of the date range for which to extract data: MM-DD-YYYY
    - date_end (string)   : End of the date range for which to extract data: MM-DD-YYYY
    - recurring (bool)    : Makes the data ignore one year and return data for a range of years
    - year_range (int[])  : [-1,-1] if not recurring, [year start, year end] if recurring is true
    """
    def __init__(self, latitude, longitude, date_start, date_end):
        self.lat           = latitude
        self.lon           = longitude
        self.date_start    = date_start 
        self.date_end      = date_end
    