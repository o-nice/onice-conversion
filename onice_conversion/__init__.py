from importlib.metadata import version


try:
    __version__ = version(__name__)
except:
    pass

from onice_conversion.nwbconverter import NWBConverter