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

import collections
import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

def _dbus_get(bus, bus_name):
    def _dbus_get_inner(path, interface):
        return dbus.Interface(bus.get_object(bus_name, path),
                              dbus_interface=interface)
    return _dbus_get_inner

system_bus = dbus.SystemBus()
avahi_bus_get = _dbus_get(system_bus, DBUS_NAME)
server = avahi_bus_get('/', DBUS_INTERFACE_SERVER)

def entry_group_add_service(name, type,
                            domain='', host='', port=0, txt=(),
                            interface=Interface.UNSPEC,
                            protocol=Protocol.UNSPEC,
                            flags=0):
    entry_group = avahi_bus_get(server.EntryGroupNew(),
                                DBUS_INTERFACE_ENTRY_GROUP)
    entry_group.AddService(interface,  protocol, flags, name, type,
                           domain, host, port, txt)
    entry_group.Commit()


Service = collections.namedtuple(
    'Service', ('interface', 'protocol', 'name', 'type', 'domain', 'flags'))

def service_browser_get_cache(type, domain='local',
                              interface=Interface.UNSPEC,
                              protocol=Protocol.UNSPEC,
                              flags=0):
    """Does a service browse, and returns all items as a list once all items from the cache are returned."""
    import gobject
    mainloop = gobject.MainLoop()
    
    services = []
    
    def item_new(*args):
        services.append(Service(*args))
        
    browser = avahi_bus_get(server.ServiceBrowserNew(interface, protocol, type,
                                                     domain, flags),
                            DBUS_INTERFACE_SERVICE_BROWSER)
    browser.connect_to_signal("ItemNew", item_new)
    browser.connect_to_signal("AllForNow", mainloop.quit)
    
    mainloop.run()
    return services

ResolvedService = collections.namedtuple(
    'ResolvedService', ('interface', 'protocol', 'name', 'type', 'domain',
                        'host_name', 'unknown1', 'address', 'port', 'txt',
                        'flags'))

def resolve_service(name, _type, domain,
                    interface=Interface.UNSPEC,
                    protocol=Protocol.UNSPEC,
                    address_protocol=Protocol.UNSPEC,
                    flags=0):
    return ResolvedService(
        *server.ResolveService(interface, protocol, name, _type, domain,
                               address_protocol, flags))