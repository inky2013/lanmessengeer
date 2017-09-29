import jsonpickle
from initializer import initializer
from getpass import getuser
import logging
import rsa
from threading import Thread
import ui
import socket
from uuid import uuid1 as _uuid1
import os


def toast_notify(title, message):
    os.system("toast\\toast.exe -t \"%s\" -m \"%s\"" % (title, message))

def truncate(s, length):
    return s[:length] + ("" if len(s) < length else "...")

uuid1 = lambda: str(_uuid1())

class Serializable:
    _pickler = jsonpickle.pickler.Pickler()
    _unpickler = jsonpickle.unpickler.Unpickler()
    def to_json(self):
        return self._pickler.flatten(self)

    @classmethod
    def from_json(cls, json):
        return cls._unpickler.restore(json)


class User(Serializable):
    @initializer
    def __init__(self, address, uuid, username, display_name, public_key):
        pass


class MessageThread(Serializable):
    def __init__(self):
        self.messages = []


class Message(Serializable):
    @initializer
    def __init__(self, sender, content):
        pass


class InlineObject:
    @initializer
    def __init__(self, **kwargs):
        pass


class Group(Serializable):
    def __init__(self, name, uuid=uuid1()):
        self.name, self.uuid = name, uuid
        self.users = []
        self.messageThread = MessageThread()


class MessageReceiver:
    @initializer
    def __init__(self, ui):
        pass


class MessageSender:
    @initializer
    def __init__(self, ui):
        pass


class BrowserExternal:
    @initializer
    def __init__(self, ui, browser=None):
        pass

    def print(self, jobj):
        self.ui.logger.info(jobj)

    def set_blur(self, val):
        self.ui.logger.debug("Window is %s focus" % ("out of" if val else "in"))
        self.ui.is_blurred = val

    def dom_ready(self):
        self.ui.logger.info("DOM Ready")
        self.ui.browserController.hide_loader()
        self.ui.browserController.append_to_groups(Group("TestGroup"))
        self.ui.browserController.display_message(Message(self.ui.user, "Test Message Please Ignore"), Group("TestGroup"))


class BrowserController:
    @initializer
    def __init__(self, ui, browser=None):
        pass

    def exjsf(self, name, *args, **kwargs):
        return self.browser.ExecuteFunction(name, *args, **kwargs)

    def hide_loader(self, *args):
        self.exjsf("hide_loader", *args)

    def append_to_groups(self, group):
        self.exjsf("append_to_groups", group.uuid, group.name)

    def change_active_groups(self):
        pass

    def display_message(self, msg, group):
        if self.ui.selected_group == group:
            self.exjsf("display_message_received", msg.sender.display_name, msg.content, msg.sender == self.ui.user)
        else:
            if self.ui.is_blurred:
                toast_notify("Message from %s in %s" % (msg.sender.display_name, group.name), truncate(msg.content, 120))
            self.exjsf("notify_message_received", msg.sender.display_name, msg.content, group.uuid, group.name, self.ui.is_blurred)




def read_file(fname):
    with open(fname) as f:
        return f.read()


class UIInfo:
    def __init__(self, display_name, port):
        self.threads = {}
        self.logger = logging.getLogger('root')
        self.logger.info("Initializing Application")
        self.port = port
        self.machine_name = socket.gethostname()
        self.host_name = socket.gethostbyname(self.machine_name)
        self.contacts = {}
        self.groups = {}
        self.is_blurred = True
        self.public_key, self._private_key = rsa.newkeys(512)
        self.selected_group = None
        self.user = User(self.host_name+":"+str(self.port), uuid1(), getuser(), display_name, self.public_key)
        self.receiver = MessageReceiver(self)
        self.sender = MessageSender(self)
        self.browserExternal = BrowserExternal(self)
        self.browserController = BrowserController(self)
        self._browser = ui.get_browser("LAN Messenger", read_file("www/simple.html"), [["external", self.browserExternal]])
        self.browserExternal.browser = self._browser
        self.browserController.browser = self._browser
        self.start_window()

    def start_window(self):
        ui.get_start()()


