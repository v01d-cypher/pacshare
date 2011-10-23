#!/usr/bin/python3

from gi.repository import Gio

class DBus(object):
    def __init__(self, bus_type):
        self.conn = None

        g_bus_type = self._get_bus_type(bus_type)
        if g_bus_type:
            self.conn = Gio.bus_get_sync(g_bus_type, None)

    def _get_bus_type(self, bus_type):
        if hasattr(Gio.BusType, bus_type):
            return getattr(Gio.BusType, bus_type)

    def get(self, bus, path, iface=None):
        if iface is None:
            iface = bus
        if self.conn:
            return Gio.DBusProxy.new_sync(self.conn, 0, None, bus, path, iface, None)
        else:
            return 'No connection. Invalid bus type.'

    def get_async(self, callback, bus, path, iface=None):
        if iface is None:
            iface = bus
        if self.conn:
            return Gio.DBusProxy.new(self.conn, 0, None, bus, path, iface, None, callback, None)
        else:
            return 'No connection. Invalid bus type.'
