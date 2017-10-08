import jsonpickle
from initializer import initializer
from getpass import getuser
import logging
import rsa
import client_finder
import communication
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

    def __str__(self):
        return "User(address=%s, display_name=%s, uuid=%s)" % (self.address, self.display_name, self.uuid)


class MessageThread(Serializable):
    def __init__(self):
        self.messages = []


class Message(Serializable):
    @initializer
    def __init__(self, sender, content):
        pass

    def __str__(self):
        return "Message(%s)" % (self.content[:75] + '..') if len(self.content) > 75 else self.content


class InlineObject:
    @initializer
    def __init__(self, **kwargs):
        pass


class Group(Serializable):
    def __init__(self, name, uuid=uuid1()):
        self.name, self.uuid = name, uuid
        self.users = []
        self.messageThread = MessageThread()

    def __str__(self):
        return "Group(name=%s)" % self.name


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

    def switch_groups(self, uuid):
        self.ui.selected_group = self.ui.groups.get(uuid, None)
        if self.ui.selected_group is not None:
            self.ui.logger.debug("Selected group: %s" % self.ui.selected_group)
            for msg in self.ui.selected_group.messageThread.messages[-25:]:
                self.ui.browserController.display_message(msg, self.ui.selected_group)

    def dom_ready(self):
        self.ui.logger.info("DOM Ready")
        self.ui.browserController.hide_loader()
        self.ui.browserController.show_address(self.ui.user.address[0]+":"+str(self.ui.user.address[1]))
        # self.ui.browserController.append_to_groups(Group("TestGroup"))
        # self.ui.browserController.display_message(Message(self.ui.user, "Test Message Please Ignore"), Group("TestGroup"))
        # self.ui.browserController.start_background_task("test_progress", "Test Task", "I am a test plz ignore", "menu", "50", True);
        # self.ui.browserController.update_background_task("test_progress", None, "updated", None, False)

    def connect_to_user(self, address):
        address = tuple(address.split(":"))
        self.ui.communicator.send_details(address, self.ui.user, True)

    def send_message(self, message_text):
        group = self.ui.selected_group
        if group is None: return
        msg = Message(self.ui.user, message_text)
        self.ui.communicator.send_message(group, msg)
        group.messageThread.messages.append(msg)
        self.ui.browserController.display_message(msg, group)


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

    def show_address(self, s):
        self.exjsf("show_address", s)

    def toast(self, s, t=100000):
        self.exjsf("toast", s, t)

    def display_message(self, msg, group):
        if self.ui.selected_group == group:
            self.ui.logger.debug("Sending message: %s to %s" % (msg, group))
            self.exjsf("display_message_received", msg.sender.display_name, msg.content, msg.sender == self.ui.user)
        else:
            if self.ui.is_blurred:
                toast_notify("Message from %s in %s" % (msg.sender.display_name, group.name), truncate(msg.content, 120))
            self.exjsf("notify_message_received", msg.sender.display_name, msg.content, group.uuid, group.name, self.ui.is_blurred)

    def start_background_task(self, uuid, title, message, icon, progress_percent, indeterminate):
        self.exjsf("start_background_task", uuid, title, message, icon, progress_percent, indeterminate)

    def update_background_task(self, uuid, title, message, progress_percent, indeterminate):
        self.exjsf("update_background_task", uuid, title, message, progress_percent, indeterminate)

    def add_discovered_user(self, name, ip):
        self.exjsf("add_discovered_user", name, ip)

    def remove_discovered_user(self, ip):
        self.exjsf("remove_discovered_user", ip)




def read_file(fname):
    with open(fname) as f:
        return f.read()


class CBDict(dict):
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.callback(value)
        super().__setitem__(key, value)


class UIInfo:
    def __init__(self, display_name, port, window_name, dev_tools, rsa_c_len, encrypt_messages):
        self.logger = logging.getLogger('root')
        self.logger.info("Initializing Application")
        self.RSA_CHUNK_LENGTH = rsa_c_len
        self.port = port
        self.machine_name = socket.gethostname()
        self.host_name = socket.gethostbyname(self.machine_name)
        self.contacts = {}
        self.groups = CBDict(self.group_updated)
        self.is_blurred = True
        if encrypt_messages:
            self.public_key, self._private_key = rsa.newkeys(512)
        else:
            self.public_key, self._private_key = None, None
        self.selected_group = None
        self.user = User((self.host_name, self.port), uuid1(), getuser(), display_name, self.public_key)
        self.receiver = MessageReceiver(self)
        self.sender = MessageSender(self)
        self.browserExternal = BrowserExternal(self)
        self.browserController = BrowserController(self)
        self.communicator = communication.Communicator(self)
        self._browser = ui.get_browser(window_name, read_file("www/simple.html"), [["external", self.browserExternal]])
        self.browserExternal.browser = self._browser
        self.browserController.browser = self._browser

        self.searcher = client_finder.start_search(self.browserController.add_discovered_user, self.browserController.remove_discovered_user)
        self.register = client_finder.register(self.user.display_name, self.user.address)

        if dev_tools:
            self._browser.ShowDevTools()
        self.server = communication.SocketServer(self, self.user.address, self._private_key)
        self.server.start_server()
        self.start_window()

    def group_updated(self, group):
        self.logger.debug("Adding %s to groups list in browser" % group)
        self.browserController.append_to_groups(group)

    def start_window(self):
        ui.get_start()()


