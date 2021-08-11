'''
Formattors or helper functions to format/deformat information
'''

from datetime import datetime

TIMESTAMPT_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
PID_TIMESTAMPT = '%Y-%m-%d_%H:%M:%S'

def timestamp_serialise(timestamp):
    return timestamp.strftime(TIMESTAMPT_FORMAT)

def timestamp_deserialise(timestamp_str):
    return datetime.strptime(timestamp_str, TIMESTAMPT_FORMAT)

def pid_timestamp_serialise(timestamp):
    return timestamp.strftime(PID_TIMESTAMPT)

def pid_timestamp_deserialise(timestamp_str):
    return datetime.strptime(timestamp_str, PID_TIMESTAMPT)
