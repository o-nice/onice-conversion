"""
Tools for making an abstract interface to work with pynwb Containers
"""

import typing
from pynwb import get_type_map, NWBContainer

def get_container(container_type:typing.Optional[str]=None,
                  container_name:typing.Optional[str]=None
                  ) -> typing.Union[typing.List[NWBContainer], NWBContainer]:
    pass

def get_container_schema(container:NWBContainer):
    pass
    # pynwb.get_typemap()
    # typemap.namespace_catalog.get_spec('core', 'ClassName')
