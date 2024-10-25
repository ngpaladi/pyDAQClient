"""
==============
Configuration.py
==============

"""

import yaml
import copy

DEFAULT_CONFIGURATION = {'name': 'DAQ CLient', 'backend': 'Generic Backend Template', 'graph': {'window': 60}, 'enable_spill_count': True, 'wait_for_spill': True, 'display_character_width': 32, 'time_display_format': '%d %b %Y %H:%M:%S', 'debug_mode': True, 'log_depth': 100, 'web': {'host': '127.0.0.1', 'port': 50000, 'configuration_buttons': [{'event': 'configure', 'disable_on_startup': False, 'tooltip': 'Configure', 'icon': 'hdd-network'}, {'event': 'download', 'disable_on_startup': True, 'tooltip': 'Download', 'icon': 'cloud-arrow-down'}, {'event': 'prestart', 'disable_on_startup': True, 'tooltip': 'Prestart', 'icon': 'file-earmark-play'}], 'start': {
    'show': True, 'disable_on_startup': True, 'tooltip': 'Start Run', 'icon': 'play-circle'}, 'pause': {'show': True, 'disable_on_startup': True, 'tooltip': 'Pause Run', 'icon': 'pause-circle'}, 'stop': {'show': True, 'disable_on_startup': True, 'tooltip': 'End Run', 'icon': 'stop-circle'}, 'reset': {'show': True, 'disable_on_startup': False, 'tooltip': 'Reset', 'icon': 'arrow-counterclockwise'}}, 'autopilot': {'enable': True, 'run_types': ['test', 'physics', 'cosmics'], 'default_user': 'user', 'default_run_type': 'physics', 'default_run_notes': '', 'default_autorestart': True, 'default_run_length': 120}}
CONFIGURATION = copy.deepcopy(DEFAULT_CONFIGURATION)


def LoadYamlConfiguration(file):
    """"Load a configuration from a Yaml-compliant file object"""
    global CONFIGURATION
    CONFIGURATION = copy.deepcopy(DEFAULT_CONFIGURATION)
    temporary_config = yaml.safe_load(file)
    for key in temporary_config:
        CONFIGURATION[key] = copy.deepcopy(temporary_config[key])
    return CONFIGURATION
