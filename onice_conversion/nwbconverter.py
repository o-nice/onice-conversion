import typing

from nwb_conversion_tools import NWBConverter as _NWBConverter
from nwb_conversion_tools.spec import BaseSpec

class NWBConverter(_NWBConverter):
    """
    ONICE extension to :class:`nwb_conversion_tools.NWBConverter`



    """

    def add_container(self,
                      container_type:typing.Optional[str]=None,
                      container_name:typing.Optional[str]=None,
                      spec:typing.Optional[BaseSpec]=None,
                      **kwargs
                      ):
        """
        Add a

        Args:
            container_type (str):
            container_name (str):
            spec (:class:`~nwb_conversion_tools.spec.BaseSpec`): Spec object declaring
                the metadata for the container
            **kwargs: stored as static metadata and passed to container

        Returns:

        """