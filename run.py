
import subprocess
import yaml
import copy
import DAQClient
from datetime import datetime
# import coda_utils





daq = DAQClient.WebClient("config.yaml")
daq.load_backend(DAQClient.Backends.Backend())


def event_handler(event: str):
    def event_handler_func():
        daq.socketio.emit('button_press', {"event": event})
        cmd = "simple-gtk-prompt %s" % event
        if (daq.config["backend"] == "coda"):
            cmd = "simple-gtk-prompt 'coda %s'" % event
        elif (daq.config["backend"] == "soda"):
            cmd = "simple-gtk-prompt 'soda %s'" % event
        cmd_result = subprocess.run(
            cmd, stdout=subprocess.PIPE, text=True, shell=True)
        daq.log(DAQClient.Log.LogItem(event))

    return event_handler_func

def get_event_rate():
    if daq.get_state() == DAQClient.State.Running:
        return 8000
    else:
        return 0
daq.backend.get_event_rate = get_event_rate

for event in daq.backend.get_preparation_events():
    daq.set_event_handler(event, event_handler(event))


if __name__ == '__main__':
    daq.start_web_server()