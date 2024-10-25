"""
==============
Client.py
==============

"""

import yaml
import math
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit
import json
from .Log import *
from .Exceptions import *
from .Configuration import *
from .Backends import Backend
from .State import State

from threading import Thread
import time


class Client:
    def __init__(self, config_file_path: str = None, log_file_path: str = None):
        self.config = CONFIGURATION
        if config_file_path != None:
            self.config = LoadYamlConfiguration(open(config_file_path))
        self.socketio = SocketIO(debug=bool(
            self.config["debug_mode"]), cors_allowed_origins='*', async_mode='eventlet')
        self.name = str(self.config["name"])
        self.backend = None
        self.state = State.Disconnected
        self.connected = False
        self.autopilot_on = False
        self.autopilot = self.load_autopilot(self.config["autopilot"])
        self.run_id = 0
        self.spill_id = 0
        self.log_file_path = log_file_path
        self.log_entries = []
        self.active_spill = False
        self.prepare_actions = []
        self.debug_mode = bool(self.config["debug_mode"])
        self.events = []
        self.event_handlers = {}
        self.prepare_macro = None
        self.background_thread = None

    def load_backend(self, backend: Backend = None):
        """"""
        self.backend = backend
        self.backend.set_socketio(self.socketio)
        self.setup_events()
        self.log(LogItem("Backend Loaded"))

    def setup_events(self):

        self.set_event_handler(
            "connect_backend", self.connect_backend)
        self.events.append("connect_backend")

        for event in self.backend.get_preparation_events():
            self.set_event_handler(
                event, self.backend.get_preparation_events()[event])
            self.events.append(event)

        for event in ["start", "pause", "stop", "reset", "bos", "spill_start", "eos", "spill_end"]:
            self.set_event_handler(
                event, self.default_event_handler(event))
            self.events.append(event)

        if self.config["autopilot"]["enable"]:
            for event in ["autopilot_enable", "autopilot_disable"]:
                self.set_event_handler(
                    event, self.default_event_handler(event))
                self.events.append(event)

    def get_backend(self):
        return self.backend

    def connect_backend(self):
        self.backend.connect()
        self.connected = True
        self.state = State.Connected
        self.log(LogItem("Connected to Backend"))
        self.start_background_task()

    def start_background_task(self):
        if self.background_thread is None:
            self.log(LogItem("Starting Background Update Thread"))
            self.background_thread = self.socketio.start_background_task(
                target=self.background_task)

    def __str__(self) -> str:
        return_str = '-'*(self.config["display_character_width"]) + "\n"
        half_space = (
            self.config["display_character_width"]-4-len(self.name))/2.
        display_name = self.name
        if half_space < 0:
            display_name = self.name[0:self.config["display_character_width"]-4]
            half_space = 0

        return_str += '| ' + ' '*max(math.floor(half_space), 0) + display_name + \
            ' '*max(math.ceil(half_space), 0) + ' |\n'
        return_str += '-'*(self.config["display_character_width"]) + "\n|" + \
            ' '*(self.config["display_character_width"]-2)+"|\n"
        lines = []
        lines.append("DAQ State: " + self.state.name)
        lines.append("Run ID: " + str(self.run_id))
        if self.config["track_spills"]:
            lines.append("Spill ID: " + str(self.spill_id))

        for line in lines:
            return_str += "| "+line+' ' * \
                max(self.config["display_character_width"] -
                    len(line)-4, 0)+' |\n'

        return_str += '|'+' '*(self.config["display_character_width"]-2) + "|\n" + \
            '-'*(self.config["display_character_width"])+"\n\n\n"

        return return_str

    def status(self):
        self.run_id = self.backend.get_run_id()
        self.spill_id = self.backend.get_spill_id()
        return {"autopilot": self.autopilot, "connected": self.connected,
                "run_id": self.run_id, "spill_id": self.spill_id}

    def start(self):
        if self.state == State.Paused:
            self.backend.resume_run()
        else:
           self.backend.start_run() 
        self.run_id = self.backend.get_run_id()
        self.state = State.Running
        self.log(LogItem("Run %i Started" % self.run_id))

    def stop(self):
        if self.config["wait_for_spill"]:
            self.wait()
        self.backend.stop_run()
        self.state = State.Stopped
        self.log(LogItem("Run %i Stopped" % self.run_id))

    def pause(self):
        if self.config["wait_for_spill"]:
            self.wait()
        self.backend.pause_run()
        self.state = State.Paused
        self.log(LogItem("Run %i Paused" % self.run_id))

    def reset(self):
        if self.config["wait_for_spill"]:
            self.wait()
        self.backend.reset()
        self.state = State.Connected
        self.log(LogItem("Reset"))

    def wait(self):
        while self.active_spill:
            time.sleep(1)
        return

    def spill_start(self):
        self.active_spill = True
        log_item = LogItem("Spill Started")
        if self.config["track_spills"]:
            log_item = LogItem("Spill %d Started" % self.spill_id)
        self.log(log_item)

    def spill_end(self):
        self.active_spill = False
        log_item = LogItem("Spill Ended")
        if self.config["track_spills"]:
            log_item = LogItem("Spill %d Ended" % self.spill_id)
        self.log(log_item)

    def log(self, entry: LogItem):
        self.log_entries.append(entry.as_dict())
        if len(self.log_entries) > self.config["log_depth"]:
            self.log_entries.pop(0)
        if self.log_file_path != None:
            with open(self.log_file_path, "a") as logfile:
                logfile.write(str(entry))
        print(entry)

    def log_completed_process(self, cmd_result):
        log_entries = []
        if cmd_result.returncode > 0:
            log_entries.append(LogItem(cmd_result.stdout, LogType.Output))
            log_entries.append(LogItem(cmd_result.stderr, LogType.Error))
        else:
            log_entries.append(LogItem(cmd_result.stdout, LogType.Output))
            if cmd_result.stderr != "":
                log_entries.append(LogItem(cmd_result.stderr, LogType.Warning))
        for entry in log_entries:
            self.log(entry)
        return log_entries

    def load_autopilot(self, input_dict: dict) -> dict:
        """Set Autopilot to use values from a dictionary"""
        user = str(CONFIGURATION['autopilot']['default_user'])
        run_type = str(CONFIGURATION['autopilot']['default_run_type'])
        run_notes = str(CONFIGURATION['autopilot']['default_run_notes'])
        autorestart = bool(CONFIGURATION['autopilot']['default_autorestart'])
        run_length = int(CONFIGURATION['autopilot']['default_run_length'])
        wait_for_spill = bool(CONFIGURATION['wait_for_spill'])
        return_dict = {}

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

        return_dict['user'] = str(user)
        return_dict['autorestart'] = bool(autorestart)
        return_dict['run_type'] = str(run_type)
        return_dict['run_notes'] = str(run_notes)
        return_dict['run_length'] = int(run_length)
        return_dict['wait_for_spill'] = bool(wait_for_spill)
        self.autopilot = return_dict
        return return_dict

    def bos(self):
        return self.spill_start()

    def eos(self):
        return self.spill_end()

    def background_task(self):
        timer = 0
        while True:
            if self.autopilot_on:
                timer += 1
                if timer > self.autopilot['run_length']*60 and self.autopilot_is_autorestart_enabled():
                    self.autopilot_restart()
                    timer = 0
                elif timer > self.autopilot['run_length']*60 and not self.autopilot_is_autorestart_enabled():
                    self.autopilot_stop()
            self.update()
            self.socketio.sleep(1)

    def get_state(self):
        return self.state

    def respond(self, event: str):
        pass

    def update(self):
        pass

    def do_nothing(self):
        pass

    def set_autopilot_run_length(self, run_length: int):
        """Set autopilot run length"""
        self.autopilot['run_length'] = run_length

    def set_autopilot_run_type(self, run_type: str):
        """Set autopilot run type"""
        self.autopilot['run_type'] = run_type

    def set_autopilot_autorestart(self, autorestart: bool):
        """Enable (True) / disable (False) automatically restarting after the run is over"""
        self.autopilot['autorestart'] = autorestart

    def set_autopilot_user(self, user: str):
        """Set autopilot user"""
        self.autopilot['user'] = user

    def set_autopilot_run_notes(self, run_notes: str):
        """Set run notes"""
        self.autopilot['run_notes'] = run_notes

    def set_autopilot_start_macro(self, macro):
        """Set a custom macro (function with no arguments) to run before the standard autopilot start process"""
        self.autopilot['start_macro'] = macro

    def set_autopilot_stop_macro(self, macro):
        """Set a custom macro (function with no arguments) to run after the standard autopilot stop process"""
        self.autopilot['stop_macro'] = macro

    def set_autopilot_restart_macro(self, macro):
        """Set a custom macro (function with no arguments) to run before the standard autopilot run restart process"""
        self.autopilot['restart_macro'] = macro

    def set_autopilot_client(self, client):
        """Set the default Client to run from the autopilot"""
        self.autopilot_client = client

    def autopilot_log(self) -> LogItem:
        if self.autopilot['autorestart']:
            return LogItem("Starting Autopilot with new runs every %d minutes" % self.autopilot['run_length'])
        else:
            return LogItem("Starting Autopilot with no time limit on runs" % self.autopilot['run_length'])

    def get_autopilot_run_length(self) -> int:
        """Return the current autopilot run length setting"""
        return self.autopilot['run_length']

    def get_autopilot_user(self) -> str:
        """Return the current autopilot user setting"""
        return self.autopilot['user']

    def get_autopilot_run_notes(self) -> str:
        """Return the current autopilot run notes setting"""
        return self.autopilot['run_notes']

    def autopilot_is_autorestart_enabled(self) -> bool:
        """Return the status of the autorestart flag"""
        return self.autopilot['autorestart']

    def autopilot_start(self, client=None):
        """Check the current DAQ state and act appropriately to start the autopilot mode start/continue a run (prepended with a start macro if set)"""
        self.autopilot_on = True
        self.log(self.autopilot_log())
        if 'start_macro' in self.autopilot:
            self.autopilot['start_macro']()
        if not self.get_state() in [State.Ready, State.Paused, State.Stopped, State.Running]:
            if self.prepare_macro == None and client:
                for event in self.events[1:1+len(self.backend.get_preparation_events().keys())]:
                    self.event(event)
                    self.socketio.sleep(1)
            else:
                self.prepare_macro()
        if not self.get_state() == State.Running:
            self.event("start")

    def autopilot_stop(self, client=None):
        """Check the current DAQ state and act appropriately to stop the autopilot mode (appended with a stop macro if set)"""
        if self.config['wait_for_spill']:
            self.wait()

        if self.get_state() in [State.Running, State.Paused]:
            self.stop()

        if 'stop_macro' in self.autopilot:
            self.autopilot['stop_macro']()
        self.autopilot_on = False

    def autopilot_restart(self, client=None):
        """Check the current DAQ state and act appropriately to restart the current run (with a restart macro run between stopping the old run and starting the new one, if set)"""
        if self.config['wait_for_spill']:
            self.wait()
        self.stop()
        if 'restart_macro' in self.autopilot:
            self.autopilot['restart_macro']()
        self.start()

    def default_event_handler(self, event):
        if event == "connect_backend":
            return self.connect_backend
        if event == "start":
            return self.start
        elif event == "stop":
            return self.stop
        elif event == "pause":
            return self.pause
        elif event == "reset":
            return self.reset
        elif event == "autopilot_enable":
            return self.autopilot_start
        elif event == "autopilot_disable":
            return self.autopilot_stop
        elif event == 'bos' or event == 'spill_start':
            return self.bos
        elif event == 'eos' or event == 'spill_end':
            return self.eos
        else:
            return None

    def set_event_handler(self, event: str, event_handler):
        def event_handler_function(*args, **kwargs):
            if event_handler != None:
                event_handler(*args, **kwargs)
            self.respond(event)
        self.event_handlers[event] = event_handler_function
        self.socketio.on_event(event, self.get_event_handler(event))

    def get_event_handler(self, event: str):
        if event in self.event_handlers:
            return self.event_handlers[event]
        else:
            raise UnregisteredEvent(
                "Please register an event handler for event '%s'" % event)
