from enum import Enum
from datetime import datetime
from .Configuration import CONFIGURATION


class LogType(Enum):
    Information = 0
    Output = 1
    Warning = 2
    Error = 3


class LogItem:
    def __init__(self, message: str, type: LogType = LogType.Information, timestamp: datetime = datetime.now()):
        self.type = type
        self.message = message
        self.timestamp = timestamp

    def as_dict(self):
        return {"type": str(self.type.name), "message": str(self.message),
                "timestamp": str(self.timestamp.strftime(CONFIGURATION["time_display_format"]))}

    def __str__(self):
        return "%s\t%s\t%s" % (self.timestamp.strftime(CONFIGURATION["time_display_format"]), str(self.type.name), 
                               self.message)
