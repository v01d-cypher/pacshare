# This file is part of avahi.
#
# avahi is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# avahi is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with avahi; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA.

# Some definitions matching those in avahi-common/defs.h

class ServerState:
    (INVALID, REGISTERING, RUNNING, COLLISION, FAILURE) = range(5)
    
class EntryGroupState:
    (UNCOMMITED, REGISTERING, ESTABLISHED, COLLISION, FAILURE ) = range(5)

class PublishFlags: 
    UNIQUE = 1
    NO_PROBE = 2
    NO_ANNOUNCE = 4
    ALLOW_MULTIPLE = 8
    NO_REVERSE = 16
    NO_COOKIE = 32
    UPDATE = 64
    USE_WIDE_AREA = 128
    USE_MULTICAST = 256

class LookupFlags:
    USE_WIDE_AREA = 1
    USE_MULTICAST = 2
    NO_TXT = 4
    NO_ADDRESS = 8        

class LookupResultFlags:
    CACHED = 1
    WIDE_AREA = 2
    MULTICAST = 4
    LOCAL = 8
    OUR_OWN = 16
    STATIC = 32         

class BrowserEvent:
    NEW, REMOVE, CACHE_EXHAUSTED, ALL_FOR_NOW, FAILURE = range(5)

class ResolverEvent:
    FOUND, FAILURE = range(2)

class DomainBrowserType:
    BROWSE, BROWSE_DEFAULT, REGISTER, REGISTER_DEFAULT, BROWSE_LEGACY, MAX = range(6)

class DNSType:
    A = 0x01
    NS = 0x02
    CNAME = 0x05
    SOA = 0x06
    PTR = 0x0C
    HINFO = 0x0D
    MX = 0x0F
    TXT = 0x10
    AAAA = 0x1C
    SRV = 0x21

class DNSClass:
    IN = 0x01

class Protocol:
    UNSPEC, INET, INET6 = -1, 0, 1

class Interface: 
    UNSPEC = -1

DBUS_NAME = "org.freedesktop.Avahi"
DBUS_INTERFACE_SERVER = DBUS_NAME + ".Server"
DBUS_INTERFACE_ENTRY_GROUP = DBUS_NAME + ".EntryGroup"
DBUS_INTERFACE_DOMAIN_BROWSER = DBUS_NAME + ".DomainBrowser"
DBUS_INTERFACE_SERVICE_TYPE_BROWSER = DBUS_NAME + ".ServiceTypeBrowser"
DBUS_INTERFACE_SERVICE_BROWSER = DBUS_NAME + ".ServiceBrowser"
DBUS_INTERFACE_ADDRESS_RESOLVER = DBUS_NAME + ".AddressResolver"
DBUS_INTERFACE_HOST_NAME_RESOLVER = DBUS_NAME + ".HostNameResolver"
DBUS_INTERFACE_SERVICE_RESOLVER = DBUS_NAME + ".ServiceResolver"
DBUS_INTERFACE_RECORD_BROWSER = DBUS_NAME + ".RecordBrowser"

from gi.repository import Gio, GObject

GObject.threads_init()

class DBus:
    def __init__(self, conn):
        self.conn = conn

    def get(self, bus, path, iface=None):
        if iface is None:
            iface = bus
        return Gio.DBusProxy.new_sync(
            self.conn, 0, None, bus, path, iface, None
        )

    def get_async(self, callback, bus, path, iface=None):
        if iface is None:
            iface = bus
        Gio.DBusProxy.new(
            self.conn, 0, None, bus, path, iface, None, callback, None
        )


system = DBus(Gio.bus_get_sync(Gio.BusType.SYSTEM, None))
server = system.get(DBUS_NAME, '/', DBUS_INTERFACE_SERVER)
entry_group = system.get(DBUS_NAME, server.EntryGroupNew(),
                         DBUS_INTERFACE_ENTRY_GROUP)

def entry_group_add_service(name, type,
                            domain='', host='', port=0, txt=None,
                            interface=Interface.UNSPEC,
                            protocol=Protocol.UNSPEC,
                            flags=0):
    entry_group.AddService('(iiussssqaay)',
                           interface,  protocol, flags, name, type,
                           domain, host, port, txt)
    entry_group.Commit()
