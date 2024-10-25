"""
==============
WebClient.py
==============

"""

from .Client import *
from .Configuration import *
from .Log import *
from .Exceptions import *
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import webbrowser
from .State import State


class Button:
    def __init__(self, event: str, disable_on_startup: bool = False, tooltip: str = "",  bootstrap_icon: str = "", disable_on_reset: bool = None):
        self.event = event
        self.disable_on_startup = disable_on_startup
        self.disabled = disable_on_startup
        self.icon = bootstrap_icon
        self.tooltip = tooltip
        if len(tooltip) == 0:
            self.tooltip = event
        
        self.disable_on_reset = disable_on_reset
        if disable_on_reset == None:
            self.disable_on_reset = self.disable_on_startup

    def action(self, function) -> bool:
        try:
            function(event=self.event)
            return True
        except:
            return False

    def status(self) -> dict:
        return {"event": self.event, "disabled": self.disabled}

    def enable(self):
        self.disabled = False

    def disable(self):
        self.disabled = True

    def reset(self):
        self.disabled = self.disable_on_reset

    @classmethod
    def from_dict(cls, input_dict: dict):
        event = ""
        disable_on_startup = False
        tooltip = ""
        bootstrap_icon = ""
        disable_on_reset = False 

        if 'event' in input_dict:
            event = input_dict['event']
        else:
            raise KeyError

        if 'disable_on_startup' in input_dict:
            disable_on_startup = input_dict['disable_on_startup']

        if 'tooltip' in input_dict:
            tooltip = input_dict['tooltip']

        if 'bootstrap_icon' in input_dict:
            bootstrap_icon = input_dict['bootstrap_icon']

        if 'disable_on_reset' in input_dict:
            disable_on_reset = input_dict['disable_on_reset']
        elif 'disable_on_startup' in input_dict:
            disable_on_reset = input_dict['disable_on_startup']


        return cls(event, disable_on_startup, tooltip, bootstrap_icon, disable_on_reset)


class WebClient(Client):
    def __init__(self, config_file_path: str = None, log_file_path: str = None):
        self.button_keys = {}
        self.graph = {}
        self.graph["labels"] = []
        self.graph["datasets"] = [{"label": "Event Rate", "data": []}]
        super().__init__(config_file_path, log_file_path)
        self.config['web']['configuration_buttons'] = []
        self.flask_app = Flask(self.name)
        self.socketio.init_app(self.flask_app)

        for i in range(self.config["graph"]["window"]):
            self.graph["labels"].append(
                (datetime.now()-timedelta(seconds=i)).strftime(self.config['time_display_format']))
            self.graph["datasets"][0]["data"].append(0)

        @self.flask_app.route('/')
        def main():
            return render_template('monitor.html', async_mode=self.socketio.async_mode,
                                   config=self.config)
        self.buttons = []
        

    def handshake(self):
        print("New Web Client")
        if self.background_task is None:
            print('Starting Background Thread')
            self.background_task = self.start_background_task(
                target=self.background_task)
            
    def setup_events(self):
        super().setup_events()
        idx = 0
        event = "connect_backend"
        button = self.config["web"]["buttons"][event]
        button['event'] = event
        button['disable_on_startup'] = False
        button['disable_on_reset'] = True
        self.buttons.append(Button.from_dict(button))
        self.config["web"]["buttons"][event] = button
        self.button_keys[event] = idx
        self.events.append(event)
        self.config['web']['configuration_buttons'].append(button)
        idx += 1
        for event in self.backend.preparation_events:
            if event in self.config["web"]["buttons"]:
                button = self.config["web"]["buttons"][event]
                button['event'] = event
                button['disable_on_startup'] = True
                if idx == 1:
                    button['disable_on_reset'] = False
                self.buttons.append(Button.from_dict(button))
                self.button_keys[event] = idx
                self.events.append(event)
                self.config['web']['configuration_buttons'].append(button)
                idx += 1

        for event in ["start", "pause", "stop", "reset"]:
            button = self.config["web"]["buttons"][event]
            button['event'] = event
            button['disable_on_startup'] = True
            if (event == 'start' and len(self.config['web']['configuration_buttons']) == 1) or event=='reset':
                button['disable_on_reset'] = False
            self.buttons.append(Button.from_dict(button))
            self.config["web"]["buttons"][event] = button
            self.button_keys[event] = idx
            idx += 1

        for button in self.buttons[1:]:
            button.disable()
        
        self.log(LogItem("Loaded %d event types, of which %d are configuration events" % (len(self.events),len(self.config['web']['configuration_buttons']))))

        

    def get_button_status(self):
        return_dict = {}
        for button in self.buttons:
            return_dict[button.event] = button.status()
        return return_dict

    def update_button_status(self, event:str):
        if event == "reset":
            for button in self.buttons:
                button.reset()
            return self.get_button_status()

        if event == "autopilot_enable" or self.autopilot_on:
            for button in self.buttons:
                button.disable()
            return self.get_button_status()

        if event == "autopilot_disable":
            if "start" in self.button_keys:
                self.buttons[self.button_keys["start"]].enable()
            return self.get_button_status()

        if event in self.button_keys:
            for button in self.buttons:
                button.disable()
            self.buttons[self.button_keys["reset"]].enable()
            if event in self.backend.get_preparation_events() or event == "connect_backend":
                self.buttons[self.button_keys[event]+1].enable()
            elif event == "start":
                if "pause" in self.button_keys:
                    self.buttons[self.button_keys["pause"]].enable()
                if "stop" in self.button_keys:
                    self.buttons[self.button_keys["stop"]].enable()
            elif event == "pause":
                if "start" in self.button_keys:
                    self.buttons[self.button_keys["start"]].enable()
                if "stop" in self.button_keys:
                    self.buttons[self.button_keys["stop"]].enable()
            elif event == "stop":
                if "start" in self.button_keys:
                    self.buttons[self.button_keys["start"]].enable()

        return self.get_button_status()

    def status(self):
        return_dict = {"buttons": self.get_button_status(),
                       "autopilot": self.autopilot_on, "autopilot_settings": dict(self.autopilot), "connected": self.connected,
                       "run_id": self.run_id, "spill_id": self.spill_id,
                       "logs": self.log_entries, "graph": self.graph}
        print(return_dict)
        return return_dict

    def event(self, event):
        if event in self.event_handlers:
            return self.event_handlers[event]()
        else:
            raise UnregisteredEvent()

    def respond(self, event: str):
        self.update_button_status(event)
        self.socketio.emit('response', {"event": event,
                                        "status": self.status()})

    def update(self):
        if self.backend.get_event_rate() != None:
            self.add_to_graph(self.backend.get_event_rate(), datetime.now())
        self.socketio.emit('update', {"status": self.status()})

    def add_to_graph(self, value, timestamp=datetime.now()):
        self.graph["labels"].append(timestamp.strftime('%d %b %Y %H:%M:%S'))
        self.graph["datasets"][0]["data"].append(value)
        self.graph["datasets"][0]["data"].pop(0)
        self.graph["labels"].pop(0)

    def add_button(self, button: Button, position: int = None):
        if self.state in [State.Disconnected, State.Crashed, State.Unknown]:
            if position == None:
                self.buttons.append(button)
                return self.buttons[-1]
            else:
                self.buttons.insert(position, button)
                return self.buttons[position]
        else:
            raise WebClientAlreadyRunning("Web Client is Already Running")

    def start_web_server(self):
        webbrowser.open_new(
            "http://%s:%d" % (self.config['web']["host"], self.config['web']["port"]))
        self.socketio.run(self.flask_app, debug=bool(self.config["debug_mode"]),
                          host=self.config['web']["host"], port=self.config['web']["port"])
