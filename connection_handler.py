#!/usr/bin/python3

import json
import time
import random
import logging
import os
from connection import Connection

import NetworkManager

from solvers.stairs.stairs import Stairs
from settings import *

connection_map = {}
device_wifi_set = set()
device_wifi_set_old = set()
ignore = {}
wait_before_connection = {}
secret = {}

def secret_update():
    secret_data = None
    try:
        secret_file = open('/etc/systemd/system/wifi-autoconnector/secret.json')
        secret_str = secret_file.read()
        secret_data = json.loads(secret_str)
    except Exception as e:
        logging.critical('secret in incorrect\n{0}'.format(str(e)))
        pass
    if secret_data is not None:
        for bssid in secret_data:
            secret[str(bssid)] = {"essid" : (secret_data.get(bssid).get("essid") if secret_data.get(bssid).get("essid") is None else str(secret_data.get(bssid).get("essid"))),
                                  "password" : (secret_data.get(bssid).get("password") if secret_data.get(bssid).get("password") is None else str(secret_data.get(bssid).get("password"))),
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
            if wifi[WIFI_SCAN_KEYS.index('HwAddress')] in secret.keys():
                signal_matrix[device][wifi[WIFI_SCAN_KEYS.index('HwAddress')]] = wifi[WIFI_SCAN_KEYS.index('Strength')]
    return signal_matrix

def current_connections_update():
    current_connections = {}
    for active_connection in NetworkManager.NetworkManager.ActiveConnections:
        for device in active_connection.Devices:
            wifi_ap = active_connection.SpecificObject
            wifi_ap_status = ()
            for field in WIFI_SCAN_KEYS:
                wifi_ap_status += (getattr(wifi_ap, field),)
            current_connections[device.Interface] = wifi_ap_status
    return current_connections

# Нужно для периодических обновлений внутри цикла.
global_cycle_time = time.time()
matcher = Stairs(stability=True)

while True:
    try:
        # Проверка, активен ли сервис. Если файл "online" существует, тогда активен. Иначе - нет.
        if not os.path.isfile('/etc/systemd/system/wifi-autoconnector/online'):
            time.sleep(service_working_flag_check_update)
            continue

        # Циклическое обновление списка пользователей.
        if time.time() > global_cycle_time:
            global_cycle_time += secret_update_timeout
            secret = secret_update()
            logging.info('secret users = {0}'.format(list(secret.keys())))

        start_cycle_time = time.time()
        time.sleep(update_delay)

        # Обновляем информацию с списке видимых wifi адаптеров.
        device_wifi_set = device_wifi_set_update()

        # Сканируем сети и смотрим автоматически обновляемую NetworkManager service (стандартный системный сервис)
        # информацию через dbus. После чего записываем её в наши переменные. Работает значительно быстрее,
        # чем работа с nmcli.
        wifi_scan = wifi_scan_update(device_wifi_set)
        signal_matrix = signal_matrix_update(device_wifi_set, wifi_scan)
        current_connections = current_connections_update()

        # Обновление соединений при обновлении списка wifi адаптеров.
        # Старые соединения беопасно уничтожаются, а новые создаются.
        for device in device_wifi_set.difference(device_wifi_set_old):
            time.sleep(update_delay * random.random())
            connection_map[device] = Connection(device)
            connection_map[device].disconnect()
        for device in device_wifi_set_old.difference(device_wifi_set):
            connection_map[device].disconnect()
            connection_map[device].__del__()
            connection_map.pop(device)

        # Отключаем дублированные подключения к сети. Скорости это всё равно для 802-11 не даст, протоколы не умею сами
        # пакеты перераспределять между двумя IP адресами, а у нас это целый адаптер займёт.
        connection_set = set()
        for device in current_connections:
            BSSID = current_connections.get(device)[WIFI_SCAN_KEYS.index('HwAddress')]
            if (BSSID in connection_set):
                connection_map[device].disconnect()
            connection_set.add(BSSID)

        # Отключаем неавторизированные подключения, состояние которые установилось (подключено или не подключено)
        device_wifi_set_old = device_wifi_set
        signal_matrix_new = {}
        bssid_set = set()
        for device in signal_matrix:
            if (connection_map[device].get_status().startswith('connected')
                    or connection_map[device].get_status().startswith('disconnected')):
                signal_matrix_new[device] = signal_matrix[device].copy()
            if (current_connections.get(device) is not None
                    and current_connections.get(device)[WIFI_SCAN_KEYS.index('HwAddress')] not in secret.keys()):
                connection_map[device].disconnect()

        # Создание матрицы сигналов для решателя.
        signal_matrix = signal_matrix_new.copy()
        signal_matrix_new = {}
        for device in signal_matrix:
            bssid_map = {}
            for bssid in signal_matrix[device]:
                if (bssid not in bssid_set
                        and bssid not in ignore.keys()
                        and bssid not in wait_before_connection.keys()):
                    bssid_map[bssid] = signal_matrix[device][bssid]
            signal_matrix_new[device] = bssid_map.copy()


        # Баним сети, к которым не удалось подключиться по причине ошибки аутентификации в сети.
        for connection in connection_map.copy().values():
            if connection.BSSID is None or connection.BSSID not in wait_before_connection.copy().keys():
                continue
            if (connection.get_status().startswith('AUTH_ERROR')):
                ignore[connection.BSSID] = time.time() + ignore_wrong_auth_timeout
                connection.disconnect()

        # Обновление переменных решателя.
        matcher.update(current_connections=current_connections.copy(), connection_map=connection_map,
                       signal_matrix_update=signal_matrix_new.copy(), update_min_signal=update_min_signal,
                       update_max_signal=update_max_signal)

        # Запуск решателя.
        command = matcher.run()
        for device in command:
            if (command.get(device) is None):
                continue
            connection_map[device].connect(BSSID=command.get(device),
                                           ESSID=secret.get(command.get(device)).get("essid"),
                                           login=secret.get(command.get(device)).get("login"),
                                           password=secret.get(command.get(device)).get("password"))
            wait_before_connection[command.get(device)] = wait_configure_before_ignore_timeout


        # Обновляем список временно игнорируемых сетей - смотрим, у какой сети уже пора снять блокировку.
        # Сделано через взятие времени в начале с в конце цикла, чтобы ошибки linux NetworkManager не приводили к
        # Блокировке сетей. Да, я сам не знаю, почему они возникают, возникают они периодически и лишь на время.
        end_cycle_time = time.time()
        for bssid in ignore.keys():
            ignore[bssid] -= end_cycle_time - start_cycle_time
            if ignore[bssid] < 0.0:
                ignore.pop(bssid)

        # Обновление списка активных попыток подключения - смотрим, какие сети слишком долго занимают
        # очередь попытки подключиться. Если время ожидания превысило предел wait_configure_before_ignore_timeout,
        # Мы баним подключения к данной сети на срок ignore_waiting_time_exceeded_timeout.
        for bssid in wait_before_connection.copy().keys():
            if bssid is None:
                wait_before_connection.pop(bssid)
                continue
            if bssid not in wait_before_connection.copy().keys():
                continue
            wait_before_connection[bssid] -= end_cycle_time - start_cycle_time
            if wait_before_connection[bssid] < 0.0:
                if bssid in ignore.keys():
                    ignore[bssid] += ignore_waiting_time_exceeded_timeout
                else:
                    ignore[bssid] = ignore_waiting_time_exceeded_timeout
                wait_before_connection.pop(bssid)

        # Удаляем сети, к которым уже выполнено подключение(отключение) из списка попыток подключения и снимаем бан.
        for connection in connection_map.copy().values():
            if connection.BSSID is None or connection.BSSID not in wait_before_connection.copy().keys():
                continue
            if (connection.get_status().startswith('connected')
                    or connection.get_status().startswith('disconnected')):
                wait_before_connection.pop(connection.BSSID)
            if connection.BSSID in ignore.keys():
                ignore.pop(connection.BSSID)

        # Логгирование ошибок и подключений.
        for key, value in connection_map.items():
            logging.info('interface {0} in status {1}'.format(key, value.get_status()))
        logging.info('ignore = {0}'.format(ignore))
        logging.info('wait_before_connection = {0}'.format(wait_before_connection))
        logging.info('current_connections = {0}'.format(current_connections))
        logging.info('signal_matrix_new = {0}'.format(signal_matrix_new))
        logging.info('command = {0}'.format(command))
    except Exception as e:
        logging.error(str(e))
