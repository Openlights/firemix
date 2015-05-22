# This file is part of Firemix.
#
# Copyright 2013-2015 Jonathan Evans <jon@craftyjon.com>
#
# Firemix is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Firemix is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Firemix.  If not, see <http://www.gnu.org/licenses/>.


# Disabled for now

# import threading
# from flask import Flask
# from flaskext.xmlrpc import XMLRPCHandler, Fault
#
#
# class RPCServer(threading.Thread):
#
#     def __init__(self, app, ip='127.0.0.1', port=8080):
#         self._app = app
#         self._flask = Flask(__name__)
#         self._handler = XMLRPCHandler('RPC2')
#         self._handler.connect(self._flask, '/RPC2')
#
#         self._handler.register(self.get_active_preset_name)
#
#         threading.Thread.__init__(self)
#
#     def run(self):
#         self._flask.run()
#
#     def stop(self):
#         pass
#
#     def get_active_preset_name(self):
#         return self._app._mixer.get_active_preset_name()