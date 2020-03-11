if __name__ != "__main__":
    raise RuntimeError("This module is experimental and should not be used in production")

import time
import random


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

        def should_do_search(self):
            return random.random() > self.get_search_probability()

        def get_search_probability(self):
            return (self._DEFAULT_THRESHOLD - self.threshold) * 0.02

        def reset_threshold(self):
            self.threshold = self._DEFAULT_THRESHOLD

    def __init__(self, **kwargs):
        self.update(**kwargs)
        self.adapter_info = dict()

    # noinspection PyMethodMayBeStatic
    def update(self, **parameters_to_update):
        for parameter in ("current_connections", "device_set", "signal_matrix_update",
                          "connection_map", "update_min_signal"):
            # noinspection PyStringFormat
            exec (
                '''
{} = parameters_to_update.pop("{}", None)
if {} is not None:
    self.{} = {}
                '''.format(*([parameter] * 5)))
        assert len(parameters_to_update.keys()) == 0, "Unknown parameters: {}".format(*parameters_to_update.viewkeys())

    def run(self, res=None, used_routers=None, window=5):
        if res is None:
            res = dict()
        if used_routers is None:
            used_routers = set()
        for adapter in self.signal_matrix_update.iterkeys():
            curr_adapter_info = self.adapter_info.get(adapter)
            available_connections = self.signal_matrix_update[adapter]
            signal_strength = available_connections.get(curr_adapter_info.router, 0)
            adapter_status = self.connection_map.get(adapter).get_status()
            if adapter_status == "connected":
                pass  # go to step 2
            elif adapter_status == "connecting":  # requires attention!
                if curr_adapter_info is None:
                    curr_adapter_info = self.adapter_info[adapter] = Adapter()
                curr_time = time.time()
                connection_start = curr_adapter_info.stored_time
                if curr_time - connection_start > 30:
                    signal_strength = 0
                    # go to step 2
                else:
                    continue

            # step 2
            if signal_strength < curr_adapter_info.threshold:
                pass  # go to step 3
            else:
                should_do_search_flag = curr_adapter_info.should_do_search()
                if should_do_search_flag:
                    pass  # go to step 3
                else:
                    continue

            # step 3
            if available_connections == used_routers:
                continue
            best_available_connection = max(available_connections.iteritems(),
                                            key=lambda router, signal: (router not in used_routers, signal))
            if best_available_connection["SIGNAL"] - signal_strength > window:
                used_routers.discard(adapter)
                res[adapter] = best_available_connection["BSSID"]
                used_routers.add(best_available_connection["BSSID"])
                curr_adapter_info.reset_threshold()
            else:
                connection_start = curr_adapter_info.stored_time
                curr_time = time.time()
                if curr_time - connection_start > 60:
                    curr_adapter_info.decrease_threshold(step=1)

        return res
