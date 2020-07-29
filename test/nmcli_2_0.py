import NetworkManager
import uuid
from time import sleep

example_connection = {
     '802-11-wireless': {'mode': 'infrastructure',
                         'security': '802-11-wireless-security',
                         'ssid': 'STANTION_Uranus'},
     '802-11-wireless-security': {'auth-alg': 'open', 'key-mgmt': 'wpa-eap'},
     '802-1x': {'eap': ['peap'],
                'identity': 'DRONE-Gagarin',
                'password': 'm44keM3f3lIamAlive',
                'phase2-auth': 'mschapv2'},
     'connection': {'id': 'STANTION_Uranus',
                    'type': '802-11-wireless',
                    'uuid': str(uuid.uuid4())},
     'ipv4': {'method': 'auto'},
     'ipv6': {'method': 'auto'}
}

#device = 'wlan0'
device = 'wlxd85d4c99ce52'

conn = NetworkManager.Settings.AddConnectionUnsaved(example_connection)
dev = NetworkManager.NetworkManager.GetDeviceByIpIface(device)

NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")

sleep(5)

print(dir(NetworkManager.NetworkManager))
print(NetworkManager.NetworkManager.ActiveConnections)


a = NetworkManager.NetworkManager.GetDeviceByIpIface(device)

sleep(5)
a.Disconnect()
print(NetworkManager.NetworkManager.ActiveConnections)
