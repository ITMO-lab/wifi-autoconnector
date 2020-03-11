#!/usr/bin/python
import pynmcli
import time
import random
import json
from connection import Connection
from solvers.stairs.stairs import Stairs
import os

connection_map = {}
update_delay = 10  # seconds
update_min_signal = 20 # from 0 to 100
update_max_signal = 40 # from 0 to 100
device_wifi_set = set()
device_wifi_set_old = set()

secret = {}
secret_data = None
try:
    secret_file = open('/etc/systemd/system/wifi-autoconnector/secret.json')
    secret_str = secret_file.read()
    secret_data = json.loads(secret_str)
except:
    pass
if secret_data is not None:
    for bssid in secret_data:
        secret[str(bssid)] = {"password" : (secret_data.get(bssid).get("password") if secret_data.get(bssid).get("password") is None else str(secret_data.get(bssid).get("password"))),
                              "login" : (secret_data.get(bssid).get("login") if secret_data.get(bssid).get("login") is None else str(secret_data.get(bssid).get("login")))}

ignore = {}
ignore_wrong_bssid_timeout = 0.0
ignore_wrong_auth_timeout = 30.0
ignore_unexpected_error_timeout = 60.0

matcher = Stairs(stability=True)

while True:
    try:
        time.sleep(update_delay)
        for bssid in ignore.keys():
            if time.time() > ignore.get(bssid):
                ignore.pop(bssid)
        device_list = pynmcli.get_data(pynmcli.NetworkManager.Device().execute())
        device_wifi_set = set()
        for device in device_list:
            if (device['TYPE'] == 'wifi'):
                device_wifi_set.add(device['DEVICE'])
        signal_matrix = {}
        current_connections = {}
        for device in device_wifi_set:
            signal_matrix[device] = {}
            wifi_list_raw = os.popen("nmcli -f in-use,ssid,bssid,signal device wifi list ifname " + device).read()
            wifi_list = pynmcli.get_data(wifi_list_raw)
            for wifi in wifi_list:
                if wifi['BSSID'] in secret.keys():
                    signal_matrix[device][wifi['BSSID']] = wifi['SIGNAL']
            wifi_list_raw_connected = ""
            for line in wifi_list_raw.splitlines():
                if line.startswith('*'):
                    wifi_list_raw_connected += line + "\n"
            wifi_list_connected = pynmcli.get_data(wifi_list_raw_connected)
            for wifi in wifi_list_connected:
                current_connections[device] = wifi
        for device in device_wifi_set.difference(device_wifi_set_old):
            time.sleep(update_delay * random.random())
            connection_map[device] = Connection(device)
            connection_map[device].disconnect()
        for device in device_wifi_set_old.difference(device_wifi_set):
            connection_map[device].disconnect()
            connection_map[device].__del__()
            connection_map.pop(device)
        connection_set = set()
        for device in current_connections:
            BSSID = current_connections.get(device).get('BSSID')
            if (BSSID in connection_set):
                connection_map[device].disconnect()
            connection_set.add(BSSID)
        device_wifi_set_old = device_wifi_set
        signal_matrix_update = {}
        bssid_set = set()
        for device in signal_matrix:
            if (connection_map[device].get_status() == 'connected'
                    or connection_map[device].get_status() == 'disconnected'):
                signal_matrix_update[device] = signal_matrix[device].copy()
            if (current_connections.get(device) is not None
                    and current_connections.get(device).get('BSSID') not in secret.keys()):
                connection_map[device].disconnect()
        signal_matrix = signal_matrix_update.copy()
        signal_matrix_update = {}
        for device in signal_matrix:
            bssid_map = {}
            for bssid in signal_matrix[device]:
                if (bssid not in bssid_set
                        and bssid not in ignore.keys()):
                    bssid_map[bssid] = signal_matrix[device][bssid]
            signal_matrix_update[device] = bssid_map.copy()
        for connection in connection_map.keys():
            BSSID = connection_map[connection].BSSID
            if (connection_map[connection].get_status().find("wrong bssid") != -1):
                ignore[BSSID] = time.time() + ignore_wrong_bssid_timeout
                connection_map[connection].disconnect()
            elif (connection_map[connection].get_status().find("wrong login or password") != -1
                or connection_map[connection].get_status().find("wrong password") != -1):
                ignore[BSSID] = time.time() + ignore_wrong_auth_timeout
                connection_map[connection].disconnect()
            elif (connection_map[connection].get_status().find("Unexpected error, contact your administrator") != -1):
                ignore[BSSID] = time.time() + ignore_unexpected_error_timeout
                connection_map[connection].disconnect()
        matcher.update(current_connections=current_connections.copy(), connection_map=connection_map, signal_matrix_update=signal_matrix_update.copy(), update_min_signal=update_min_signal, update_max_signal=update_max_signal)
        command = {}
        try:
            command = matcher.run()
        except:
            pass
        for device in command:
            if (command.get(device) is None):
                continue
            connection_map[device].connect(BSSID=command.get(device),
                                           login=secret.get(command.get(device)).get("login"),
                                           password=secret.get(command.get(device)).get("password"))
        
        for connection in connection_map:
            print(connection, connection_map[connection].get_status())
        print(ignore)
        print('current_connections = ' + str(current_connections))
        print('signal_matrix_update = ' + str(signal_matrix_update))
        print(command)
        
    except Exception as e:
        print(e.message)
