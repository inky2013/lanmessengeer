from zeroconf import ServiceBrowser, Zeroconf, ServiceInfo
import socket
import logging
import json

logger = logging.getLogger('root')

class Listener:
    def __init__(self, add_cb, del_cb):
        self.add_cb = add_cb
        self.del_cb = del_cb
        super().__init__()

    def remove_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        logger.debug("Removed %s" % name)
        try:
            info = json.loads(info)
        except json.JSONDecodeError:
            return
        self.del_cb(info["ip"])

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if name == "LANMSG._http._tcp.local.":
            logger.debug("Service %s added, service info: %s" % (name, info))
            if not isinstance(info.properties, dict):
                return
            for k in info.properties:
                try:
                    info.properties[k.decode()] = info.properties[k].decode()
                except AttributeError:
                    pass
                else:
                    del info.properties[k]
            self.add_cb(info.properties["name"], info.properties["ip"])


def start_search(add_callback, remove_callback):
    zeroconf = Zeroconf()
    listener = Listener(add_callback, remove_callback)
    browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
    return zeroconf


def register(display_name, addr):
    info = ServiceInfo("_http._tcp.local.",
                       "LANMSG._http._tcp.local.",
                       socket.inet_aton("10.0.1.2"), 80, 0, 0,
                       {"name": display_name, "ip": addr[0]+":"+str(addr[1])}, "ash-2.local.")

    zeroconf = Zeroconf()
    zeroconf.register_service(info)
    return zeroconf

def stop(info, search):
    info.unregister_service(info)
    info.close()
    search.close()