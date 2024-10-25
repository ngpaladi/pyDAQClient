from enum import Enum 
class State(Enum):
    Disconnected = 0
    Connected = 1
    Ready = 2
    Running = 3
    Paused = 4
    Stopped = 5
    Crashed = 6
    Unknown = 7