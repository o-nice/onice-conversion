"""
Specify metadata that's in a separate, external file from the standard format files
"""
import typing
from pathlib import Path
from abc import abstractmethod
import json
import numpy as np
from glob import glob

from scipy.io import loadmat
from scipy.io.matlab.mio5_params import mat_struct
import yaml

from onice_conversion.spec import BaseSpec
from onice_conversion.utils import AmbiguityError


class BaseExternalFileSpec(BaseSpec):

    loaded_files = {}

    def __init__(self, path:Path,
                 key: str,
                 field:typing.Union[str, typing.Tuple[str, ...]],
                 cache:bool = True,
                 *args, **kwargs):
        """

        Parameters
        ----------
        self :
        path : path relative to base_dir that is passed in :meth:`._parse`
        key :
        field :
        cache : bool
            if True, store loaded file in :attr:`.loaded_files` dictionary to prevent
            re-load if another spec needs it.
        kwargs :

        Returns
        -------

        """
        super(BaseExternalFileSpec, self).__init__(*args, **kwargs)

        self._loaded_file = None
        self.path = Path(path)
        self.key = key
        self.field = field
        self.cache = cache

    @abstractmethod
    def _load_file(self, path:Path) -> dict:
        """
        Load the file and return it as a nested dictionary of dictionaries or tuples

        such that it can be indexed by successively slicing with :attr:`.field`

        Parameters
        ----------
        self :
        key : str
            name of the property that will be returned
        path :

        Returns
        -------

        """

        pass

    @property
    def _specifies(self):
        return tuple(self.key)

    def _sub_select(self, loaded_file:dict) -> typing.Any:
        """
        Use :attr:`.field` to select from the loaded_file

        Parameters
        ----------
        loaded_file :

        Returns
        -------

        """
        # slice the loaded file to get the value of interest
        sub_select = {}
        if isinstance(self.field, (tuple, list)):
            # to avoid copying what could potentially be a large dict,
            # but also avoid modifying the cached one, do this sorta awkward shit
            for i, item in enumerate(self.field):
                if i == 0:
                    try:
                        sub_select = loaded_file[item]
                    except (KeyError, IndexError):
                        sub_select = getattr(loaded_file, item)
                else:
                    try:
                        sub_select = sub_select[item]
                    except (KeyError, IndexError):
                        sub_select = getattr(sub_select, item)
        else:
            # if we just got a string or an int or something give it a shot
            try:
                sub_select = loaded_file[self.field]
            except (KeyError, IndexError):
                sub_select = getattr(loaded_file, self.field)

        return sub_select

    def _parse(self, base_path:Path, metadata:typing.Optional[dict]=None) -> dict:
        # get abs path
        base_path = Path(base_path).absolute()
        if '*' in str(self.path):
            # glob it bby!
            paths = list(base_path.glob(str(self.path)))

            if len(paths) == 1:
                file_path = paths[0]
            elif isinstance(paths, Path):
                file_path = paths
            else:
                raise AmbiguityError(f'Got multiple paths that matched your glob string: {paths}')
        else:
            file_path = (base_path / self.path).absolute()

        # if cache is on, try to retrieve from cache
        if self.cache and file_path in self.loaded_files.keys():
            loaded_file = self.loaded_files[file_path]
        else:
            # otherwise load file
            loaded_file = self._load_file(file_path)
            if self.cache:
                self.loaded_files[file_path] = loaded_file

        return {self.key:self._sub_select(loaded_file)}

class JSON(BaseExternalFileSpec):

    def __init__(self, hook:typing.Optional[typing.Callable]=None,
                 *args, **kwargs):
        """
        Load a field from a .json file. see base class for docs

        Parameters
        ----------
        hook : Optionally, include some callable function to use as the fallback
            object loader hook (see ``object_hook`` argument in ``json.load`` for more information)
        args : passed to :class:`.BaseExternalFileSpec`
        kwargs :
        """
        self.hook = hook
        super(JSON, self).__init__(*args, **kwargs)

    def _load_file(self, path:Path) -> dict:
        with open(path, 'r') as p:
            loaded = json.load(p, object_hook=self.hook)
        return loaded

class Mat(BaseExternalFileSpec):

    def __init__(self, simplified:bool=True, *args, **kwargs):
        """

        Args:
            simplified (bool): Whether we attempt to simplify the matlab struct into lists
                and dicts, or just take the base output from :func:`scipy.io.loadmat`
            *args (): Passed to superclass
            **kwargs (): Passed to superclass
        """
        super(Mat, self).__init__(*args, **kwargs)
        self.simplified = simplified

    def _sub_select(self, loaded_file:dict) -> typing.Any:
        """
        Calls :meth:`.BaseExternalFileSpec._sub_select`, but then
        unstacks all `len == 1` numpy arrays so that the
        `field` arg can be like `('sessionInfo', 'session')`
        rather than `('sessionInfo', 'session', 0, 0, 0, 0, 0, 0)`

        Parameters
        ----------
        loaded_file :

        Returns
        -------

        """
        sub_select = super(Mat, self)._sub_select(loaded_file)
        while isinstance(sub_select, np.ndarray) and np.max(sub_select.shape) == 1:
            sub_select = sub_select[0]

        return sub_select

    def _load_file(self, path:Path) -> dict:
        if self.simplified:
            return load_clean_mat(str(path))
        else:
            return loadmat(file_name=str(path))


class YAML(BaseExternalFileSpec):
    def _load_file(self, path:Path) -> dict:
        with open(path, 'r') as yfile:
            return yaml.load(yfile)


# --------------------------------------------------
# --------------------------------------------------
# Utility functions for converting matlab files to nice dicts
# from https://stackoverflow.com/a/29126361/13113166
# --------------------------------------------------

def load_clean_mat(filename:str) -> dict:
    '''
    Load a matlab `.mat` file as python lists, dictionaries, and
    numpy arrays rather than the sort-of hard to work with numpy record arrays.

    Credit to https://stackoverflow.com/a/29126361/13113166

    Args:
        filename (str): filename of .mat to load

    Returns:
        dict
    '''
    def _check_keys(d):
        '''
        checks if entries in dictionary are mat-objects. If yes
        todict is called to change them to nested dictionaries
        '''
        for key in d:
            if isinstance(d[key], mat_struct):
                d[key] = _todict(d[key])
            elif _has_struct(d[key]):
                d[key] = _tolist(d[key])
        return d

    def _has_struct(elem):
        """Determine if elem is an array and if any array item is a struct"""
        return isinstance(elem, np.ndarray) and any(isinstance(
                    e, mat_struct) for e in elem)

    def _todict(matobj):
        '''
        A recursive function which constructs from matobjects nested dictionaries
        '''
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, mat_struct):
                d[strg] = _todict(elem)
            elif _has_struct(elem):
                d[strg] = _tolist(elem)
            else:
                d[strg] = elem
        return d

    def _tolist(ndarray):
        '''
        A recursive function which constructs lists from cellarrays
        (which are loaded as numpy ndarrays), recursing into the elements
        if they contain matobjects.
        '''
        elem_list = []
        for sub_elem in ndarray:
            if isinstance(sub_elem, mat_struct):
                elem_list.append(_todict(sub_elem))
            elif _has_struct(sub_elem):
                elem_list.append(_tolist(sub_elem))
            else:
                elem_list.append(sub_elem)
        return elem_list
    data = loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_keys(data)