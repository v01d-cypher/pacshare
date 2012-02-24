# Pacshare
__Pacshare__ is a utility that works with Arch Linux's pacman to enable sharing
of packages on a local network. It does not require a central server, but rather
uses a peer to peer system. It uses Avahi to publish and discover peers.
Pacshare has 2 components: a server, and a client.

## Sharing Server
This is a http server which shares the contents of your pacman CacheDir
directory (default `/var/cache/pacman/pkg`,) and publishes it's self with Avahi.

When installed using the Arch package, you can configure the server by editing
`/etc/conf.d/pacshare.conf`, and start and stop the server using `rc.d
pacshare`. Add `pacshare` to the `DAEMONS` list in `/etc/rc.conf` to start the
server on boot.

For development or testing purposes, you can run the server using the
`pacshare-server` command.

## XferCommand Client
The pacshare client is used as a pacman XferCommand. Enable it by adding the
following to `/etc/pacman.conf`:

    XferCommand = /usr/lib/pacshare-xferclient %u %o

The client will first try download packages from pacshare peers, and if none of
the peers have the package, then it will download the package from the repo.
