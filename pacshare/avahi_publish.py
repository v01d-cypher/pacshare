from gi.repository import GObject

import pacshare.avahi as avahi
from pacshare.dbus import DBus


GObject.threads_init()


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

if __name__ == '__main__':
    mainloop = GObject.MainLoop()

    service = ZeroconfService("Demo Service", '_pacshare._tcp', 1234)
    if service.connected:
        mainloop.run()
    
    if not service.group is None:
        service.group.Free()
