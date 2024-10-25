"""
==============
Autopilot.py
==============

"""

from .Log import *
from .Configuration import *
from .Exceptions import *
from .State import State



class Autopilot:
    """
    The :class:`Autopilot` class performs automatic run start, stop, and restart operations for a self.
    """

    def autopilot___init__(self, user: str = CONFIGURATION['autopilot']['default_user'],
                 run_type: str = CONFIGURATION['autopilot']['default_run_type'],
                 run_notes: str = CONFIGURATION['autopilot']['default_run_notes'],
                 autorestart: bool = CONFIGURATION['autopilot']['default_autorestart'],
                 run_length: int = CONFIGURATION['autopilot']['default_run_length'],
                 wait_for_spill: bool = CONFIGURATION['wait_for_spill']):
        self.autopilot_user = str(user)
        self.autopilot_autorestart = bool(autorestart)
        self.autopilot_run_type = str(run_type)
        self.autopilot_run_notes = str(run_notes)
        self.autopilot_run_length = int(run_length)
        self.autopilot_wait_for_spill = bool(wait_for_spill)
        self.autopilot_start_macro = None
        self.autopilot_stop_macro = None
        self.autopilot_restart_macro = None
        self.autopilot_client = None

    
    def autopilot_load_dict(self, input_dict: dict):
        """Set Autopilot instance to use values from a dictionary"""
        user = str(CONFIGURATION['autopilot']['default_user'])
        run_type = str(CONFIGURATION['autopilot']['default_run_type'])
        run_notes = str(CONFIGURATION['autopilot']['default_run_notes'])
        autorestart = bool(CONFIGURATION['autopilot']['default_autorestart'])
        run_length = int(CONFIGURATION['autopilot']['default_run_length'])
        wait_for_spill = bool(CONFIGURATION['wait_for_spill'])

        for key in ["user", "run_type", "run_notes", "autorestart", "run_length", "wait_for_spill"]:
            if ("default_%s" % key) in input_dict and not key in input_dict:
                input_dict[key] = input_dict["default_%s" % key]

        if "user" in input_dict:
            user = str(input_dict["user"])
        if "run_type" in input_dict:
            run_type = str(input_dict["run_type"])
        if "run_notes" in input_dict:
            run_notes = str(input_dict["run_notes"])
        if "autorestart" in input_dict:
            autorestart = bool(input_dict["autorestart"])
        if "run_length" in input_dict:
            run_length = int(input_dict["run_length"])
        if "wait_for_spill" in input_dict:
            wait_for_spill = bool(input_dict["wait_for_spill"])

        self.autopilot_user = str(user)
        self.autopilot_autorestart = bool(autorestart)
        self.autopilot_run_type = str(run_type)
        self.autopilot_run_notes = str(run_notes)
        self.autopilot_run_length = int(run_length)
        self.autopilot_wait_for_spill = bool(wait_for_spill)

        return self

    @classmethod
    def autopilot_from_dict(cls, input_dict: dict):
        """Generate Autopilot instance from a dictionary"""
        return Autopilot().load_dict(input_dict)

    def autopilot_as_dict(self):
        """Export Autopilot instance as a dictionary"""
        return {"user": self.autopilot_user, "run_type": self.autopilot_run_type, "run_notes": self.autopilot_run_notes, "autorestart": self.autopilot_autorestart, "run_length": self.autopilot_run_length}

    def autopilot___str__(self):
        """Export Autopilot instance as a string for saving to a file"""
        if self.autopilot_autorestart:
            return "User: %s\nRun Type: %s\nRun Length: %s\nNotes:\n%s\n" % (self.autopilot_user, self.autopilot_run_type, self.autopilot_run_length, self.autopilot_run_notes)
        else:
            return "User: %s\nRun Type: %s\nNotes:\n%s\n" % (self.autopilot_user, self.autopilot_run_type, self.autopilot_run_notes)
