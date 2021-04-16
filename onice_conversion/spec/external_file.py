from nwb_conversion_tools.spec.external_file import BaseExternalFileSpec as _BaseExternalFileSpec
from nwb_conversion_tools.spec.external_file import JSON as _JSON
from nwb_conversion_tools.spec.external_file import Mat as _Mat
from nwb_conversion_tools.spec.external_file import YAML as _YAML


class BaseExternalFileSpec(_BaseExternalFileSpec):
    pass

class JSON(_JSON):
    pass

class Mat(_Mat):
    pass

class YAML(_YAML):
    pass