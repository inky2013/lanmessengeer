import socket
import socketserver
import json
import base
import logging
import copy
from binascii import Error as BinasciiError
from threading import Thread
import base64
import rsa

logger = logging.getLogger('root')

def split_len(seq, length):
    return [seq[i:i+length] for i in range(0, len(seq), length)]

class Communicator:
    def __init__(self, ui):
        self.incrementer = 1
        self.ui = ui

    def _encode(self, data, public_key=None):
        data = base64.b64encode(json.dumps(data).encode("utf-8"))
        if public_key is None:
            return data
        while len(data) % 128 != 0:
            data += b'\00'
        data_chunks = split_len(data, self.ui.RSA_CHUNK_LENGTH)
        print(data_chunks)
        d = b''
        for chunk in data_chunks:
            d += rsa.encrypt(chunk, public_key)
        return d

    def _send(self, addr, data):
        Thread(target=self._send_threadsafe, args=(addr, data), name="ClientThread_%s" % str(self.incrementer).zfill(2)).start()
        self.incrementer += 1 if self.incrementer < 100 else -99

    def _send_threadsafe(self, addr, data):
        try:
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cs.connect((str(addr[0]), int(addr[1])))
            cs.send(data)
            cs.close()
            logger.debug("Sent data to %s successfully" % addr[0]+":"+str(addr[1]))
        except ConnectionRefusedError:
            logger.error("The target machine actively refused the request.")
            logger.error("The program may not be running correctly on the target machine.")
            return
        except IndexError:
            logger.error("The supplied address is invalid. Cannot connect to target machine.")
            return
        except TimeoutError:
            logger.error("The connection to the target machine timed out.")
            return

    def send_details(self, addr, user, require_reply):
        logger.debug("Sending details to %s: %s" % (addr, user))
        self._send(addr, self._encode({"type": "user_connect", "requires_reply": require_reply, "user": user.to_json()}))

    def send_message(self, group, message):
        for u in group.users:
            logger.debug("Sending %s to %s" % (message, u))
            self._send(u.address, self._encode({"type": "message", "group": group.uuid, "message": message.to_json()}, u.public_key))

    def invite_user_to_group(self, group, user):
        group = copy.deepcopy(group)  # It breaks without creating a deep copy of the group for no apparent reason
        group.users.append(self.ui.user)
        self._send(user.address, self._encode({"type": "group_invite", "group": group.to_json()}, user.public_key))


def get_socket_handler(private_key, callback, RSA_CHUNK_LENGTH):
        class SocketTCPHandler(socketserver.BaseRequestHandler):
            def __init__(self, *args, **kwargs):
                self.private_key = private_key
                super().__init__(*args, **kwargs)
            def handle(self):
                print("handle call")
                self.data = b''
                for _ in range(128):
                    d = self.request.recv(1024).strip()
                    if d in [b'', None]:
                        break
                    self.data += d

                try:
                    data = json.loads(base64.b64decode(self.data).decode())
                except (json.JSONDecodeError, BinasciiError, UnicodeDecodeError):
                    logger.debug("Could not interpret data before decryption")
                    try:
                        if private_key is None:
                            logger.debug("No private key has been generated. Unable to read data")
                            return

                        data = b''
                        data_chunks = split_len(data, RSA_CHUNK_LENGTH)
                        for chunk in data_chunks:
                            data += rsa.decrypt(chunk, self.private_key)
                        _ndata = b''
                        for c in data:
                            if c != b"\00":
                                _ndata += c
                        data = _ndata
                        data = json.loads(base64.b64decode(data))
                    except (rsa.DecryptionError, json.JSONDecodeError, BinasciiError, UnicodeDecodeError):
                        logger.error("Invalid data received from %s" % self.client_address)
                        return None


                callback(data)

        return SocketTCPHandler


class SocketServer:
    def __init__(self, ui, address, private_key):
        self.ui = ui
        self.handler = get_socket_handler(private_key, self.data_handler, ui.RSA_CHUNK_LENGTH)
        self.address = address
        self._thread = Thread(target=self._server_start, name="ServerThread")

    def data_handler(self, jobj):
        type = jobj.get("type", None)
        if type is None:
            logger.warning("Got some random request but it was invalid.")
            return
        logger.debug(jobj)
        if type == "user_connect":
            user = base.User.from_json(jobj.get("user"))
            if jobj.get("requires_reply", False):
                self.ui.communicator.send_details(user.address, self.ui.user, False)
            self.ui.contacts[user.uuid] = user
            if jobj.get("requires_reply", False):
                g = base.Group(user.display_name)
                self.ui.groups[g.uuid] = g
                g.users.append(user)
                self.ui.communicator.invite_user_to_group(g, user)
            logger.info("Added %s" % user)
            self.ui.browserController.toast("Connected to <strong>%s</strong>" % user.display_name)

        if type == "message":
            logger.debug("Received message boi")
            group = self.ui.groups.get(jobj.get("group", ""), None)
            if group is None:
                logger.error("Invalid group specified for message")
                return
            message = jobj.get("message", None)
            if message is None:
                logger.error("No message was supplied with the request")
                return
            try:
                message = base.Message.from_json(message)
            except json.JSONDecodeError:
                logger.error("Invalid serialized message")
                return
            logger.debug("Message received and decoded.")
            self.ui.browserController.display_message(message, group)

        if type == "group_invite":
            group = jobj.get("group", None)
            if group is None: return
            try:
                group = base.Group.from_json(group)
            except json.JSONDecodeError:
                logger.error("Invalid serialized group data")
                return
            group.users = [i for i in group.users if i.uuid != self.ui.user.uuid]
            self.ui.groups[group.uuid] = group




    def start_server(self):
        self._thread.start()

    def _server_start(self):
        with socketserver.TCPServer(self.address, self.handler) as server:
            logger.debug("Starting server on %s:%s" % self.address)
            server.serve_forever()




