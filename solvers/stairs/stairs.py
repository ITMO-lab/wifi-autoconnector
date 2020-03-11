class Stairs(object):

    def __init__(self, stability):
        self.current_connections = {}
        self.connection_map = {}
        self.signal_matrix_update = {}
        self.update_min_signal = 20
        self.update_max_signal = 40
        self.stability = stability

    def update(self, current_connections, connection_map, signal_matrix_update, update_min_signal, update_max_signal):
        self.current_connections = current_connections
        self.connection_map = connection_map
        self.signal_matrix_update = signal_matrix_update
        self.update_min_signal = update_min_signal
        self.update_max_signal = update_max_signal

    def run(self):
        signal_matrix = self.signal_matrix_update.copy()
        bssid_used = set()
        for connection in self.connection_map:
            if self.connection_map.get(connection).BSSID is not None:
                bssid_used.add(self.connection_map.get(connection).BSSID)
        result = {}
        for device in signal_matrix.keys():
            if (self.connection_map.get(device).get_status() == 'connected'):
                if (int(self.current_connections.get(device).get('SIGNAL')) < self.update_min_signal):
                    bssid_max = None
                    signal_max = self.update_max_signal
                    for bssid in signal_matrix.get(device):
                        if (int(signal_matrix.get(device).get(bssid)) >= signal_max
                            and bssid not in bssid_used):
                            bssid_max = bssid
                            signal_max = int(signal_matrix.get(device).get(bssid))
                    if bssid_max is not None:
                        bssid_used.add(bssid_max)
                        result[device] = bssid_max
                else:
                    bssid_used.add(self.current_connections.get(device).get('BSSID'))
                signal_matrix.pop(device)
            elif (self.connection_map.get(device).get_status() != 'disconnected'):
                signal_matrix.pop(device)
        order_map = {}
        order = signal_matrix.keys()
        for key in order:
            order_map[key] = 0
        for device in signal_matrix:
            for bssid in signal_matrix.get(device):
                for device_check in signal_matrix:
                    if signal_matrix.get(device_check).get(bssid) is not None:
                        order_map[device] += int(signal_matrix.get(device).get(bssid))**2 - int(signal_matrix.get(device_check).get(bssid))**2
        order.sort(cmp=lambda x, y: 1 if order_map.get(x) < order_map.get(y) else -1)
        if self.stability:
            order.reverse()
        for device in order:
            if result.get(device) is not None:
                continue
            bssid_map = signal_matrix.get(device)
            for signal in bssid_map:
                bssid_map[signal] = int(bssid_map[signal])
            bssid_list = bssid_map.keys()
            bssid_list.sort(cmp=lambda x, y: 1 if bssid_map.get(x) < bssid_map.get(y) else -1)
            for bssid in bssid_list:
                if bssid not in bssid_used:
                    bssid_used.add(bssid)
                    result[device] = bssid
                    break
        return result
