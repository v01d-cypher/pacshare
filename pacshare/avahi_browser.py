from gi.repository import GObject

import pacshare.avahi as avahi
from pacshare.dbus import DBus


GObject.threads_init()

class AvahiBrowser(object):
    def __init__(self, **kwargs):
        self.daemon = kwargs.get('daemon', False)
        self.service_type = kwargs.get('service_type', '_workstation._tcp')
        self.show_local = kwargs.get('show_local', False)
        self.services = {}
        self.all_for_now = False
        self.connected = False

        self.bus = DBus('SYSTEM')
        self.mainloop = GObject.MainLoop()

        self.avahi_server = self._get_avahi_server()
        if self.avahi_server:
            self.avahi_browser = self._get_avahi_browser(self.avahi_server)
            self.mainloop.run()

    def _get_avahi_server(self):
        try:
            avahi_server = self.bus.get(avahi.DBUS_NAME,
                                        avahi.DBUS_PATH_SERVER,
                                        avahi.DBUS_INTERFACE_SERVER)
        except:
            print("Can't connect to avahi daemon")
        else:
            self.connected = True
            return avahi_server

    def _get_avahi_browser(self, server):
        avahi_browser = self.bus.get(avahi.DBUS_NAME,
                                     server.ServiceBrowserNew('(iissu)', # D-Bus type signature
                                                              avahi.IF_UNSPEC,
                                                              avahi.PROTO_UNSPEC,
                                                              self.service_type,
                                                              'local',
                                                              0),
                                     avahi.DBUS_INTERFACE_SERVICE_BROWSER)
        avahi_browser.connect('g-signal', self.on_g_signal)
        return avahi_browser

    def on_g_signal(self, proxy, sender, signal, params):
        params = params.unpack()
        #print(signal, params)

        if signal == 'AllForNow':
            if not self.daemon:
                self.all_for_now = True
                self.mainloop.quit()
            else:
                print('All for now')
        elif signal == 'ItemNew':
            (interface, protocol, name, service_type, domain, flags) = params
            local = False
            if flags & avahi.LOOKUP_RESULT_LOCAL:
                local = True
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

        event = service[1]
        if event == avahi.RESOLVER_FOUND and (self.show_local or not local):
            name = service[2]
            self.services[name] = {
                'type': service[3],
                'domain': service[4],
                'host_name': service[5],
                'address': service[7],
                'port': service[8],
                'txt': service[9],
                'flags': service[10],}

if __name__ == '__main__':
    from pprint import pprint
    ab = AvahiBrowser(service_type='_workstation._tcp', show_local=True)
    if ab.connected:
        while not ab.all_for_now:
            pass

        for service, params in ab.services.items():
            print(service)
            pprint(params)


# Can't get this to work yet.
#from gi.repository import Avahi
#sbrowser = Avahi.ServiceBrowser.new_full(-1, # Interface
#                                    Avahi.Protocol.GA_PROTOCOL_UNSPEC,
#                                    TYPE,
#                                    'local',
#                                    Avahi.LookupFlags.GA_LOOKUP_NO_FLAGS)
#sbrowser.connect('new_service', callback)
