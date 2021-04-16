from abc import abstractmethod, ABC
import typing
import importlib
from pathlib import Path

from nwb_conversion_tools.json_schema_utils import dict_deep_update

from onice_conversion.utils import IntrospectionMixin

class BaseSpec(ABC, IntrospectionMixin):
    """
    Base class for specification objects.

    Abstract, should not be instantiated on its own.
    """

    def __init__(self, retype: typing.Optional[typing.Callable] = None, *args, **kwargs):
        """

        Parameters
        ----------
        retype : Callable (optional)

        """
        self._child = None
        self._parse_ref = None
        self._parent = None  # type: typing.Optional[BaseSpec]

        self.retype = retype

        self._init_args = self._get_init_args()

    def parse(self, base_path: Path, metadata: typing.Optional[dict] = None) -> dict:
        """
        Parse all parameters from self and child :meth:`._parse` methods,
        combining into single dictionary

        Parameters
        ----------
        base_path: Path
            The base path we compute the spec'd value from!
        metadata: dict
            other metadata used by the parsing function, usually passed in :meth:`.NWBConverter.run_conversion`

        Returns
        -------

        """
        if metadata is None:
            metadata = {}
        out = self._parse(base_path, metadata)

        if self._child is not None:
            for child in self.children():
                out = dict_deep_update(out, child._parse(base_path, metadata))

        return out

    @abstractmethod
    def _parse(self, base_path=None, metadata: typing.Optional[dict] = None) -> dict:
        """
        All Specs should instantiate a _parse method that returns a dictionary of
        metadata variable keys and values. eg::

            >>> BaseSpec().parse()
            { 'subject_id': 'jonny' }

        The typical use is to be able to specify some metadata values
        that are contained ***somewhere*** relative to a directory of data, so
        the passed argument should typically be that directory.
        """

    @property
    def specifies(self) -> typing.Tuple[str, ...]:
        """
        Which metadata variables are specified by this Spec object and its children

        Returns
        -------
        tuple of strings
        """
        specified = list(self._specifies)

        if self._child is not None:
            for child in self.children():
                specified.extend(list(child._specifies))

        return tuple(specified)

    @property
    @abstractmethod
    def _specifies(self) -> typing.Tuple[str, ...]:
        """
        Which metadata variables are specified by this Spec object

        Returns
        -------
        tuple of strings
        """

    @property
    def parent(self) -> 'BaseSpec':
        return self._parent

    @parent.setter
    def parent(self, parent: 'BaseSpec'):
        if not issubclass(type(parent), BaseSpec):
            raise TypeError('parents must be subclasses of BaseSpec')
        self._parent = parent

    def children(self) -> typing.Iterable['BaseSpec']:
        """
        Generator for iterating over children (added)

        Returns
        -------

        """
        if self._child is None:
            return

        active_child = self._child
        yield active_child

        while active_child._child is not None:
            active_child = active_child._child
            yield active_child

    def __add__(self, other: 'BaseSpec'):
        if not issubclass(type(other), BaseSpec):
            raise TypeError('can only add subclasses of BaseSpec')

        if self._child is None:
            # if we haven't been chained at all yet, claim the child
            self._child = other
            self._child.parent = self

        else:
            # we already have a child,
            # add it to our child instead (potentially recursively)
            self._child = self._child + other

        return self

    def to_dict(self) -> dict:
        """
        Get a dictionary description of this spec object, of the form::

            {
                'module': self.__module__,
                'class': type(self).__name__,
                'kwargs': self._init_args,
                'children': [ ... same structure as top-level without children list ...]
            }

        That allows a spec to be reconstituted with :meth:`.from_dict`

        Returns
        -------
        dict of initialization parameters, as described above
        """

        out_dict = {
            'module': self.__module__,
            'class': type(self).__name__,
            'kwargs': self._init_args,
            'children': []
        }

        if self._child is not None:
            for child in self.children():
                out_dict['children'].append({
                    'module': child.__module__,
                    'class': type(child).__name__,
                    'kwargs': child._init_args
                })

        return out_dict


def from_dict(spec_dict: dict) -> BaseSpec:
    """
    Reconstitute a spec object from a dict created by :meth:`.BaseSpec.to_dict`

    Parameters
    ----------
    spec_dict : dict
        A dictionary created by :meth:`.BaseSpect.to_dict`

    Returns
    -------
    The reconstituted spec object!
    """

    # import and instantiate!
    spec_class = getattr(importlib.import_module(spec_dict['module']), spec_dict['class'])
    spec_obj = spec_class(**spec_dict['kwargs'])

    if len(spec_dict['children']) > 0:
        for child_dict in spec_dict['children']:
            child_class = getattr(importlib.import_module(child_dict['module']), child_dict['class'])
            child_obj = child_class(**child_dict['kwargs'])
            spec_obj += child_obj

    return spec_obj
