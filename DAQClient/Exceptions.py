"""
==============
Exceptions.py
==============

"""

class UnregisteredEvent(Exception):
    """Exception raised when an event is received from the Web Client and no handler is registered"""
    pass

class MacroOnlyEvent(Exception):
    """Exception raised when an attempt is made to register a handler for a standard event (start, stop, pause, reset) instead of a macro"""
    pass

class MacroNotSet(Exception):
    """Exception raised when no macro is registered for a standard event (start, stop, pause, reset)"""
    pass

class WebClientAlreadyRunning(Exception):
    """Exception raised when a button is added while the Web Client is running"""
    pass

class ClientNotFound(Exception):
    """Exception raised by the Autopilot if no client is attached"""
    pass