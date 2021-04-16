"""
Tools for making an abstract interface to work with pynwb Containers
"""

import typing
from pynwb import get_type_map, NWBContainer

def get_container(container_name:typing.Optional[str]=None
                  ) -> typing.Union[typing.List[NWBContainer], NWBContainer]:
    """
    Get and list pyNWB containers by name.

    If called with no arguments, returns all container objects. Otherwise
    return the container named ``'container_name'``.

    Eg. get ``pynwb.file.NWBFile`` by calling with ``'NWBFile'``

    Args:
        container_name (str, None): if None, return all containers. Otherwise
            return container by name

    Returns:
        list of Containers, or Container itself.
    """
    if container_name is None:
        # return all containers
        return get_type_map().get_container_classes()
    else:
        return get_type_map().get_container_cls('core', container_name)

def get_container_schema(container:typing.Union[NWBContainer, str]) -> typing.Tuple[dict]:
    """
    Get argument schema for a pyNWB container.

    Args:
        container (:class:`pynwb.NWBContainer`, str): Either the container itself, or
            a string to call :func:`.get_container` with

    Returns:
        tuple of dicts that describe each parameter
    """
    if isinstance(container, str):
        container = get_container(container)

    return container.get_fields_conf()
