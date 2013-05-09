import threading
from flask import Flask
from flaskext.xmlrpc import XMLRPCHandler, Fault


class RPCServer(threading.Thread):

    def __init__(self, app, ip='127.0.0.1', port=8080):
        self._app = app
        self._flask = Flask(__name__)
        self._handler = XMLRPCHandler('RPC2')
        self._handler.connect(self._flask, '/RPC2')

        self._handler.register(self.get_active_preset_name)

        threading.Thread.__init__(self)

    def run(self):
        self._flask.run()

    def stop(self):
        pass

    def get_active_preset_name(self):
        return self._app._mixer.get_active_preset_name()