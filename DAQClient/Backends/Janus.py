from .Backend import Backend

class Janus(Backend):
    name = "Janus"
    def __init__(self,):
        self.run_id = 0
        self.spill_id = 0
    
    def set_socketio(self, socket):
        self.socketio = socket

    def start_run(self):
        self.run_id += 1
        self.spill_id += 1

    def stop_run(self):
        pass

    def pause_run(self):
        pass

    def resume_run(self):
        pass

    def reset(self):
        self.__init__()

    def get_run_id(self):
        return self.run_id

    def get_spill_id(self):
        return self.spill_id

    def get_event_rate(self):
        pass

    def connect(self):
        pass

    def prepare(self):
        pass