import pynmcli
import NetworkManager
import threading
import time

class Connection(object):

    def __init__(self, device):
        self.device = device
        self.BSSID = None
        self.password = None
        self.login = None
        self.is_check = True
        self.auto_connector_thread = threading.Thread(target=self.auto_connector)
        self.auto_connector_thread.setDaemon(True)
        self.is_alive = True
        self.delay = 1 # seconds
        self.status = "__init__"
        self.auto_connector_thread.start()

    def __del__(self):
        self.is_check = False
        self.is_alive = False
        # del self.auto_connector_thread
        while self.auto_connector_thread.is_alive():
            time.sleep(self.delay * 1.0 / 10)
        self.status = "__del__"

    def auto_connector(self):
        while self.is_alive:
            time.sleep(self.delay)
            if (not self.is_check):
                continue
            if (self.status != "__del__"):
                try:
                    self.status = self.check()
                except:
                    pass


    def get_status(self):
        return self.status

    def connect(self, BSSID, login=None, password=None):
        self.is_check = False
        self.BSSID = BSSID
        self.password = password
        self.login = login
        self.status = "manual connecting"
        self.is_check = True

    def disconnect(self):
        self.is_check = False
        self.BSSID = None
        self.password = None
        self.login = None
        self.status = "manual disconnecting"
        self.is_check = True

    def check(self):
        device_list = pynmcli.get_data(pynmcli.NetworkManager.Device().execute())
        for line in device_list:
            if (line['DEVICE'] == self.device):
                if ((self.BSSID is None or
                        line['CONNECTION'][:len(self.BSSID):] != self.BSSID)
                        and line['STATE'] == 'connected'):
                    NetworkManager.NetworkManager.GetDeviceByIpIface(self.device).Disconnect()
                    return "connected to wrong bssid"
                elif (line['STATE'] == 'disconnected'
                        and self.BSSID is None):
                    return "disconnected"
                elif (line['CONNECTION'][:len(self.BSSID):] == self.BSSID
                        and line['STATE'] == 'connected'
                        and line['TYPE'] == 'wifi'):
                    return "connected"
                elif (line['STATE'].find('unmanaged') != -1
                        or line['STATE'].find('connecting') != -1):
                    return line['STATE']
                else:
                    if (self.login is not None):
                        pynmcli.NetworkManager.Connection().delete(self.BSSID).execute()
                        pynmcli.NetworkManager.Connection().add("type wifi ifname " + self.device + " con-name " + self.BSSID + " ssid " + self.BSSID).execute()
                        pynmcli.NetworkManager.Connection().modify("id " + self.BSSID + " ipv4.method auto 802-1x.eap peap 802-1x.phase2-auth mschapv2 802-1x.identity " + self.login + " 802-1x.password " + self.password + " wifi-sec.key-mgmt wpa-eap").execute()
                        wifi_connect = pynmcli.NetworkManager.Connection().up(self.BSSID + " ifname " + self.device)
                        if (wifi_connect.find("Connection successfully activated") != -1):
                            return "reconnecting"
                        elif (wifi_connect.find("Connection activation failed") != -1):
                            return "wrong bssid"
                        elif (wifi_connect.find("Passwords or encryption keys are required to access the wireless network") != -1):
                            return "wrong login or password"
                        else:
                            return "Unexpected error, contact your administrator\nnmcli output:\n" + wifi_connect
                    else:
                        wifi_connect = pynmcli.NetworkManager.Device().wifi().connect(self.BSSID + (self.password is None if "" else " password " + self.password) + " ifname " + self.device + " name " + self.BSSID).execute()
                        if (wifi_connect.find("successfully activated with") != -1):
                            return "reconnecting"
                        elif (wifi_connect.find("No access point with BSSID") != -1):
                            return "wrong bssid"
                        elif (wifi_connect.find("Secrets were required, but not provided") != -1):
                            return "wrong password"
                        else:
                            return "Unexpected error, contact your administrator\nnmcli output:\n" + wifi_connect
        return "wrong device"
