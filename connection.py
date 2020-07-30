import NetworkManager
from settings import single_connection_update_delay
import threading
import time
import uuid
import logging

class Connection(object):

    def __init__(self, device):
        self.device = device
        self.ESSID = None
        self.BSSID = None
        self.password = None
        self.login = None
        self.is_check = True
        self.auto_connector_thread = threading.Thread(target=self.auto_connector)
        self.auto_connector_thread.setDaemon(True)
        self.is_alive = True
        self.delay = single_connection_update_delay
        self.status = "__init__"
        self.auto_connector_thread.start()

    def __del__(self):
        self.is_check = False
        self.is_alive = False
        # del self.auto_connector_thread
        while self.auto_connector_thread.is_alive():
            time.sleep(self.delay / 10.0)
        self.status = "__del__"

    def auto_connector(self):
        while self.is_alive:
            time.sleep(self.delay)
            if (not self.is_check):
                continue
            if (self.status != "__del__"):
                try:
                    self.status = self.check()
                except Exception as e:
                    logging.error(str(e))
                    pass

    def get_status(self):
        return self.status

    def connect(self, BSSID, ESSID, login=None, password=None):
        self.is_check = False
        self.BSSID = BSSID
        self.ESSID = ESSID
        self.password = password
        self.login = login
        self.status = "manual connecting"
        self.is_check = True

    def disconnect(self):
        self.is_check = False
        self.BSSID = None
        self.ESSID = None
        self.password = None
        self.login = None
        self.status = "manual disconnecting"
        self.is_check = True

    def check(self):
        try:
            device = NetworkManager.NetworkManager.GetDeviceByIpIface(self.device)
            if device is None:
                raise Exception
        except:
            return "ERROR wrong device used"
        if (device.ActiveAccessPoint is not None
                and device.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED):
            if (self.BSSID is None or device.ActiveAccessPoint.HwAddress != self.BSSID
            and self.ESSID is None or device.ActiveAccessPoint.Ssid != self.ESSID):
                device.Disconnect()
                return "connected to wrong both bssid and ssid"
            elif self.BSSID is None or device.ActiveAccessPoint.HwAddress != self.BSSID:
                device.Disconnect()
                return "connected to wrong bssid"
            elif self.ESSID is None or device.ActiveAccessPoint.Ssid != self.ESSID:
                device.Disconnect()
                return "connected to wrong ssid"
            elif (device.ActiveAccessPoint.HwAddress == self.BSSID
                and device.ActiveAccessPoint.Ssid == self.ESSID):
                return "connected {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED and self.BSSID is None and self.ESSID is None:
            return "disconnected {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_FAILED: return "AUTH_ERROR failed {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_NEED_AUTH: return "AUTH_ERROR need_auth {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_UNAVAILABLE: return "DEVICE_ERROR unavailable {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_UNKNOWN: return "DEVICE_ERROR unknown {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_UNMANAGED: return "DEVICE_ERROR unmanaged {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_CONFIG: return "config {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_DEACTIVATING: return "deactivating {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_IP_CHECK: return "ip_check {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_IP_CONFIG: return "ip_config {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_PREPARE: return "prepare {}".format(device.StateReason)
        if device.State == NetworkManager.NM_DEVICE_STATE_SECONDARIES: return "secondaries {}".format(device.StateReason)
        if self.login is not None and self.password is not None:
            connection_settings = {
                "802-11-wireless": {"mode": "infrastructure",
                                    "security": "802-11-wireless-security",
                                    "ssid": self.ESSID,
                                    "hidden" : True,
                                    "bssid" : self.BSSID},
                "802-11-wireless-security": {"auth-alg": "open", "key-mgmt": "wpa-eap"},
                "802-1x": {"eap": ["peap"],
                           "identity": self.login,
                           "password": self.password,
                           "phase2-auth": "mschapv2"},
                "connection": {"id": self.BSSID,
                               "type": "802-11-wireless",
                               "uuid": str(uuid.uuid4())},
                "ipv4": {"method": "auto"},
                "ipv6": {"method": "auto"}
            }
        elif self.login is None and self.password is not None:
            connection_settings = {
                "802-11-wireless": {"mode": "infrastructure",
                                    "security": "802-11-wireless-security",
                                    "ssid": self.ESSID,
                                    "hidden": True,
                                    "bssid": self.BSSID},
                "802-11-wireless-security": {"auth-alg": "open", "key-mgmt": "wpa-psk", "psk": self.password},
                "connection": {"id": self.BSSID,
                               "type": "802-11-wireless",
                               "uuid": str(uuid.uuid4())},
                "ipv4": {"method": "auto"},
                "ipv6": {"method": "auto"}
            }
        elif self.login is None and self.password is None:
            # WARNING (из спецификации 802-11)
            # If specified, directs the device to only associate with the given access point.
            # This capability is highly driver dependent and not supported by all devices.
            # Note: this property does not control the BSSID used when creating an Ad-Hoc network
            # and is unlikely to in the future.
            # FIX
            # Исправлено дополнительной ручной проверкой в def check() на соответствие SSID и BSSID
            connection_settings = {
                "802-11-wireless": {"mode": "infrastructure",
                                    "ssid": self.ESSID,
                                    "hidden": True,
                                    "bssid": self.BSSID},
                "connection": {"id": self.BSSID,
                               "type": "802-11-wireless",
                               "uuid": str(uuid.uuid4())},
                "ipv4": {"method": "auto"},
                "ipv6": {"method": "auto"}
            }
        else:
            return "MISTAKE secret incorrect \"You can't use login auth without password yet\""
        conn = NetworkManager.Settings.AddConnectionUnsaved(connection_settings)
        dev = NetworkManager.NetworkManager.GetDeviceByIpIface(self.device)
        NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
        return "attempt to connect"
