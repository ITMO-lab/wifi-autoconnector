#!/usr/bin/python3
import json
import os
import time

import NetworkManager
import pynmcli

from solvers.stairs.stairs import Stairs

update_delay = 1 # 10  # seconds
update_min_signal = 20 # from 0 to 100
update_max_signal = 40 # from 0 to 100
ignore_wrong_bssid_timeout = 0.0
ignore_wrong_auth_timeout = 30.0
ignore_unexpected_error_timeout = 60.0

connection_map = {}
device_wifi_set = set()
device_wifi_set_old = set()
WIFI_SCAN_KEYS = ('Ssid', 'HwAddress', 'Frequency', 'Strength')

ignore = {}
secret = {}

def ignore_update():
    ignore = {}
    for bssid in ignore.keys():
        if time.time() > ignore.get(bssid):
            ignore.pop(bssid)
    return ignore

def secret_update():
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
    return secret

def device_wifi_set_update():
    device_wifi_set = set()
    device_list = NetworkManager.NetworkManager.GetAllDevices()
    for device in device_list:
        if (device.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI):
            device_wifi_set.add(device.Interface)
    return device_wifi_set

def wifi_scan_update(device_wifi_set):
    wifi_scan = {}
    for device in device_wifi_set:
        scan = NetworkManager.NetworkManager.GetDeviceByIpIface(device).GetAllAccessPoints()
        wifi_scan[device] = set()
        for wifi in scan:
            scan_result = ()
            for field in WIFI_SCAN_KEYS:
                scan_result += (getattr(wifi, field), )
            wifi_scan[device].add(scan_result)
    return wifi_scan

def signal_matrix_update(device_wifi_set, wifi_scan):
    signal_matrix = {}
    for device in device_wifi_set:
        signal_matrix[device] = {}
        for wifi in wifi_scan[device]:

            # TODO Удалить тестовый коммент

            #if wifi[WIFI_SCAN_KEYS.index('HwAddress')] in secret.keys():
            signal_matrix[device][wifi[WIFI_SCAN_KEYS.index('HwAddress')]] = wifi[WIFI_SCAN_KEYS.index('Strength')]
    return signal_matrix

def current_connections_update(device_wifi_set, wifi_scan):
    current_connections = {}
    mehtods = ['Connection', 'Devices', 'Id', 'Master', 'SpecificObject']

    # TODO Проверить содержание NetworkManager.NetworkManager.ActiveConnections при подключении двух адаптеров в одной сети

    for active_connection in NetworkManager.NetworkManager.ActiveConnections:
        for device in active_connection.Devices:
            device.Interface
            wifi_ap = active_connection.SpecificObject
        res = {}
        for mehtod in mehtods:
            res[mehtod] = getattr(active_connection, mehtod)
        print(res)
        print(active_connection.Devices[0].Interface)


        print(specificObject)
        scan_result = ()
        for field in WIFI_SCAN_KEYS:
            scan_result += (getattr(specificObject, field),)
        print(scan_result)

    #print(dir(NetworkManager.NetworkManager.ActiveConnections))
    for device in device_wifi_set:
        #print(dir(NetworkManager.NetworkManager.GetDeviceByIpIface(device).GetAppliedConnection(0)))

        wifi_list_raw = os.popen("nmcli -f in-use,ssid,bssid,signal device wifi list ifname " + device).read()
        wifi_list_raw_connected = ""
        for line in wifi_list_raw.splitlines():
            if line.startswith('*'):
                wifi_list_raw_connected += line + "\n"
        wifi_list_connected = pynmcli.get_data(wifi_list_raw_connected)
        for wifi in wifi_list_connected:
            current_connections[device] = wifi
    return current_connections


secret = secret_update()
matcher = Stairs(stability=True)

while True:
    try:
        time.sleep(update_delay)
        ignore = ignore_update()
        device_wifi_set = device_wifi_set_update()
        # NetworkManager.NetworkManager.GetDeviceByIpIface(str)
        wifi_scan = wifi_scan_update(device_wifi_set)
        signal_matrix = signal_matrix_update(device_wifi_set, wifi_scan)
        current_connections = current_connections_update(device_wifi_set, wifi_scan)
        print('wifi_scan ', wifi_scan)

        """
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
        signal_matrix_new = {}
        bssid_set = set()
        for device in signal_matrix:
            if (connection_map[device].get_status() == 'connected'
                    or connection_map[device].get_status() == 'disconnected'):
                signal_matrix_new[device] = signal_matrix[device].copy()
            if (current_connections.get(device) is not None
                    and current_connections.get(device).get('BSSID') not in secret.keys()):
                connection_map[device].disconnect()

        signal_matrix = signal_matrix_new.copy()
        signal_matrix_new = {}
        for device in signal_matrix:
            bssid_map = {}
            for bssid in signal_matrix[device]:
                if (bssid not in bssid_set
                        and bssid not in ignore.keys()):
                    bssid_map[bssid] = signal_matrix[device][bssid]
            signal_matrix_new[device] = bssid_map.copy()

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

        matcher.update(current_connections=current_connections.copy(), connection_map=connection_map, signal_matrix_new=signal_matrix_new.copy(), update_min_signal=update_min_signal, update_max_signal=update_max_signal)

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
        """
        #for connection in connection_map:
        #    print(connection, connection_map[connection].get_status())
        print(ignore)
        print('current_connections = ' + str(current_connections))
        # print('signal_matrix_new = ' + str(signal_matrix_new))
        # print(command)
        
    except Exception as e:
        print(e.message)
