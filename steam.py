import os

os.add_dll_directory(os.getcwd())

from steamworks import STEAMWORKS
from steamworks.exceptions import SteamNotRunningException

sw = STEAMWORKS()

try:
    sw.initialize()

except SteamNotRunningException:
    exit(-2)

except OSError:
    exit(-1)

