from main.solvers.stairs.stairs import Stairs

solver = Stairs(stability=True)

current_connections = {'wlxd85d4c99ce52': {'SIGNAL': '13', 'SSID': 'TP-LINK_609C', 'BSSID': 'C0:25:E9:61:60:9C'}, 'wlan0': {'SIGNAL': '12', 'SSID': 'STANTION-eva', 'BSSID': '0A:C5:E1:0B:79:3B'}}
connection_map = {'wlxd85d4c99ce52' : 'connected', 'wlan0' : 'connected', 'test' : 'disconnected'}
signal_matrix_update = {'wlxd85d4c99ce52': {'1': '10', '2': '8', '3' : '6'}, 'wlan0': {'1': '8', '2': '8', '3' : '75' }, 'test' : {'1': '8', '2': '8', '3' : '75' }}
update_min_signal = 20
update_max_signal = 40

solver.update(current_connections, connection_map, signal_matrix_update, update_min_signal, update_max_signal)

print(solver.run())