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


SERVER_INVALID, SERVER_REGISTERING, SERVER_RUNNING, SERVER_COLLISION, SERVER_FAILURE = range(0, 5)

ENTRY_GROUP_UNCOMMITED, ENTRY_GROUP_REGISTERING, ENTRY_GROUP_ESTABLISHED, ENTRY_GROUP_COLLISION, ENTRY_GROUP_FAILURE = range(0, 5)

DOMAIN_BROWSER_BROWSE, DOMAIN_BROWSER_BROWSE_DEFAULT, DOMAIN_BROWSER_REGISTER, DOMAIN_BROWSER_REGISTER_DEFAULT, DOMAIN_BROWSER_BROWSE_LEGACY = range(0, 5)

PROTO_UNSPEC, PROTO_INET, PROTO_INET6  = -1, 0, 1

IF_UNSPEC = -1

PUBLISH_UNIQUE = 1
PUBLISH_NO_PROBE = 2
PUBLISH_NO_ANNOUNCE = 4
PUBLISH_ALLOW_MULTIPLE = 8
PUBLISH_NO_REVERSE = 16
PUBLISH_NO_COOKIE = 32
PUBLISH_UPDATE = 64
PUBLISH_USE_WIDE_AREA = 128
PUBLISH_USE_MULTICAST = 256

LOOKUP_USE_WIDE_AREA = 1
LOOKUP_USE_MULTICAST = 2
LOOKUP_NO_TXT = 4
LOOKUP_NO_ADDRESS = 8

LOOKUP_RESULT_CACHED = 1
LOOKUP_RESULT_WIDE_AREA = 2
LOOKUP_RESULT_MULTICAST = 4
LOOKUP_RESULT_LOCAL = 8
LOOKUP_RESULT_OUR_OWN = 16
LOOKUP_RESULT_STATIC = 32

RESOLVER_FOUND = 0
RESOLVER_FAILURE = 1

SERVICE_COOKIE = "org.freedesktop.Avahi.cookie"
SERVICE_COOKIE_INVALID = 0

DBUS_NAME = "org.freedesktop.Avahi"
DBUS_INTERFACE_SERVER = DBUS_NAME + ".Server"
DBUS_PATH_SERVER = "/"
DBUS_INTERFACE_ENTRY_GROUP = DBUS_NAME + ".EntryGroup"
DBUS_INTERFACE_DOMAIN_BROWSER = DBUS_NAME + ".DomainBrowser"
DBUS_INTERFACE_SERVICE_TYPE_BROWSER = DBUS_NAME + ".ServiceTypeBrowser"
DBUS_INTERFACE_SERVICE_BROWSER = DBUS_NAME + ".ServiceBrowser"
DBUS_INTERFACE_ADDRESS_RESOLVER = DBUS_NAME + ".AddressResolver"
DBUS_INTERFACE_HOST_NAME_RESOLVER = DBUS_NAME + ".HostNameResolver"
DBUS_INTERFACE_SERVICE_RESOLVER = DBUS_NAME + ".ServiceResolver"
DBUS_INTERFACE_RECORD_BROWSER = DBUS_NAME + ".RecordBrowser"



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



class ZeroconfService(object):
    def __init__(self, name, service_type='', port=8000, domain='', host='', text=None):
        self.name = name
        self.service_type = service_type
        self.port = port
        self.domain = domain
        self.host = host
        self.text = text

        self.connected = False
        self.avahi_server = None
        self.group = None #our entry group
        self.rename_count = 12 # Counter so we only rename after collisions a sensible number of times

        self.bus = DBus('SYSTEM')
        self._get_avahi_server()

    def _get_avahi_server(self):
        try:
            self.avahi_server = self.bus.get(avahi.DBUS_NAME,
                                             avahi.DBUS_PATH_SERVER,
                                             avahi.DBUS_INTERFACE_SERVER)
        except:
            print("Can't connect to avahi daemon")
        else:
            self.connected = True
            self.avahi_server.connect("g_signal", self.server_state_changed)
            self.server_state_changed(self.avahi_server.GetState())

    def add_service(self):
        if self.group is None:
            self.group = self.bus.get(avahi.DBUS_NAME,
                                      self.avahi_server.EntryGroupNew(),
                                      avahi.DBUS_INTERFACE_ENTRY_GROUP)

            self.group.connect('g_signal', self.entry_group_state_changed)

        print("Adding service '{}' of type '{}' ...".format(self.name, self.service_type))

        #self.group.AddService('(iiussssqaay)',
        self.group.AddService('(iiussssqaay)',
                              avahi.IF_UNSPEC,  # Interface
                              avahi.PROTO_UNSPEC,  # Protocol -1 = both, 0 = ipv4, 1 = ipv6
                              0,  # Flags
                              self.name,
                              self.service_type,
                              self.domain,  # Domain, default to .local
                              self.host,  # Host, default to localhost
                              self.port,  # Port
                              self.text,  # TXT record
                             )
        self.group.Commit()

    def remove_service(self):
        if not self.group is None:
            self.group.Reset()

    def server_state_changed(self, state):
        if state == avahi.SERVER_COLLISION:
            print("WARNING: Server name collision")
            self.remove_service()
        elif state == avahi.SERVER_RUNNING:
            self.add_service()

    #def entry_group_state_changed(self, state, error):
    def entry_group_state_changed(self, proxy, sender, signal, params):
        params = params.unpack()
        state, error = params
        print("state change: {}".format(state))

        if state == avahi.ENTRY_GROUP_ESTABLISHED:
            print("Service established.")
        elif state == avahi.ENTRY_GROUP_COLLISION:
            self.rename_count -= 1

            if self.rename_count > 0:
                self.name = self.avahi_server.GetAlternativeServiceName(self.name)
                print("WARNING: Service name collision, changing name to '{}' ...".format(name))
                self.remove_service()
                self.add_service()
            else:
                print("ERROR: No suitable service name found after {} retries, exiting.".format(n_rename))
        elif state == avahi.ENTRY_GROUP_FAILURE:
            print("Error in group state changed", error)
            self.running = False
            return

class AvahiBrowser(object):
    def __init__(self, **kwargs):
        self.service_type = kwargs.get('service_type', '_workstation._tcp')
        self.show_local = kwargs.get('show_local', False)
        self.avahi_server = None
        self.services = {}
        self.connected = False

        self.bus = DBus('SYSTEM')

        self._get_avahi_server()
        if self.avahi_server:
            self._get_avahi_browser(self.avahi_server)

    def _get_avahi_server(self):
        try:
            self.avahi_server = self.bus.get(avahi.DBUS_NAME,
                                             avahi.DBUS_PATH_SERVER,
                                             avahi.DBUS_INTERFACE_SERVER)
        except:
            print("Can't connect to avahi daemon")
        else:
            self.connected = True

    def _get_avahi_browser(self, server):
        self.avahi_browser = self.bus.get(avahi.DBUS_NAME,
                                          server.ServiceBrowserNew('(iissu)', # D-Bus type signature
                                                                   avahi.IF_UNSPEC,
                                                                   avahi.PROTO_UNSPEC,
                                                                   self.service_type,
                                                                   'local',
                                                                   0),
                                          avahi.DBUS_INTERFACE_SERVICE_BROWSER)
        self.avahi_browser.connect('g-signal', self.on_g_signal)

    def on_g_signal(self, proxy, sender, signal, params):
        params = params.unpack()
        #print(signal, params)
        #if signal == 'ItemNew':
        #    (interface, protocol, name, _type, domain, flags) = params
        #    ours = bool(flags & 8)
        #    print(ours)
        #    #(ip, port) = avahi.ResolveService('(iisssiu)',
        #    #    interface, protocol, name, _type, domain, -1, 0
        #    #)[7:9]
        #    all_ = self.avahi_server.ResolveService('(iisssiu)',
        #        interface, protocol, name, _type, domain, -1, 0
        #    )
        #    print(all_)
        #    #print(ip, port)

        if signal == 'AllForNow':
            print('All for now')
        elif signal == 'ItemNew':
            (interface, protocol, name, service_type, domain, flags) = params
            local = flags & avahi.LOOKUP_RESULT_LOCAL
            try:
                service = self.avahi_server.ResolveService('(iisssiu)', # D-Bus type signature
                                                           interface,
                                                           protocol,
                                                           name,
                                                           service_type,
                                                           domain,
                                                           avahi.PROTO_UNSPEC,
                                                           0)
                self.service_resolved(service, local)
            except Exception as e:
                print("Cant resolve service :", e)

    def service_resolved(self, service, local):
        #(3, 0, 'Beast [00:19:db:b6:86:05]', '_workstation._tcp', 'local', 'Beast.local', 0, '10.0.0.2', 9, [], 5)
        #AvahiServiceResolver *r,
        #AvahiResolverEvent event,
        #const char *name,
        #const char *type,
        #const char *domain,
        #const char *host_name,
        #const AvahiAddress *address,
        #uint16_t port,
        #AvahiStringList *txt,
        #AvahiLookupResultFlags flags,

        if self.show_local or not local:
            name = service[2]
            self.services[name] = {
                'type': service[3],
                'domain': service[4],
                'host_name': service[5],
                'address': service[7],
                'port': service[8],
                'txt': service[9],
                'flags': service[10],}
            print(self.services[name])



