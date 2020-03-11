if __name__ != "__main__":
    raise RuntimeError("This module is experimental and should not be used in production")

import time


class Matcher(object):
    class Adapter(object):

        def __init__(self, threshold=20, router=None, time_=None):
            self._DEFAULT_THRESHOLD = threshold
            self.threshold = self._DEFAULT_THRESHOLD
            self.router = router
            self.stored_time = time_ if time_ is not None else time.time()

        def connect(self, router=None, reset_threshold=True):
            if reset_threshold:
                self.threshold = self._DEFAULT_THRESHOLD
            if router is None:
                self.router = router
            return router

        def reconnect(self):
            return self.connect(self.router)

        def timestamp(self):
            self.stored_time = time.time()
            return self.stored_time

        def decrease_threshold(self, step=1):
            self.threshold -= step
            return self.threshold

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.devices_currently_connecting = set()

    def update(self, **parameters_to_update):
        for parameter in ("current_connections", "device_set", "signal_matrix_update",
                          "connection_map", "update_min_signal"):
            exec (
                '''
{} = parameters_to_update.pop("{}", None)
if {} is not None:
    self.{} = {}
                '''.format(*([parameter] * 5)))
        assert len(parameters_to_update.keys()) == 0, "Unknown parameters: {}".format(*parameters_to_update.viewkeys())

    def process_currently_connecting_routers(self, signal_matrix, res):
        used_routers = set()
        interfaces_connected = set()
        interfaces_with_no_available_router_found = set()
        for interface in self.devices_currently_connecting:
            if interface.get_status() == "connected":
                interface.timestamp()
                used_routers.add(interface.router)
                interfaces_connected.add(interface)
            else:
                routers = signal_matrix.get(interface)
                if routers is None:
                    interfaces_with_no_available_router_found.add(interface)
                else:
                    router = routers.get(interface.router)
                    if router is None:
                        # connecting to the router lost
                        self.devices_currently_connecting.remove(interface)
                    else:
                        used_routers.add(interface.router)
                        if time.time() - interface.start_time >= 30:
                            res[interface] = interface.reconnect()
        self.devices_currently_connecting.difference_update(interfaces_connected
                                                            | interfaces_with_no_available_router_found)
        return used_routers, interfaces_with_no_available_router_found

    def run(self, signal_matrix, res=None):
        if res is None:
            res = dict()
        used_routers, interfaces_with_no_available_router_found = self.process_currently_connecting_routers(
            signal_matrix, res)
        interfaces_unmatched = self.device_set.difference(self.devices_currently_connecting
                                                          | interfaces_with_no_available_router_found)
        for interface in interfaces_unmatched:
            connections = signal_matrix.get(interface)
            if connections is not None:
                curr_connection = connections.get(interface.router, -1)
                if curr_connection < interface.threshold:
                    best = max(connections.iteritems(),
                               key=lambda router, signal: (router not in used_routers, signal))
                    if best - curr_connection > 5 or best >= 20:  # an optimization due to the lazy evaluation
                        res[interface] = interface.connect(best, reset_threshold=True)
                        self.devices_currently_connecting.add(interface)
                    elif time.time() - interface.stored_time >= 60:
                        interface.decrease_threshold(step=1)

        return res
