from cx_Freeze import setup, Executable

setup(
    name='pacshare',
    version='0',
    description="Share pacman repositories on LAN",
    executables=[
        Executable("pacshare-xferclient"),
        Executable("pacshare-server"),
    ],
)
