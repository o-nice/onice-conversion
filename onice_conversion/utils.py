"""
Utility functions used internally across the library
"""

import inspect
import typing

class AmbiguityError(Exception):
    """Exception type for when :mod:`onice_conversion.spec` modules give ambiguous results"""
    pass

class IntrospectionMixin(object):
    """
    Mixin to allow objects to become aware of all the arguments they were called with on initialization

    Call :meth:`._get_init_args` in the __init__ method of any object that inherits from this mixin :)
    """

    @property
    def _full_sig_names(self):
        """
        Introspect child objects and parents to get all argument names in signature

        Returns
        -------
        list of all argument names
        """
        parents = inspect.getmro(type(self))
        # get signatures for each
        # go in reverse order so top classes options come first
        # list to keep track of parameter names to remove duplicates
        param_names = []
        for cls in reversed(parents):
            sig = inspect.signature(cls)
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'kwargs', 'args'):
                    continue
                if param_name not in param_names:
                    # check if we already have a parameter with this name,
                    # if we don't add it.
                    param_names.append(param_name)

        return param_names

    def _get_init_args(self):
        """
        introspect object and get all arguments passed on __init__

        depends on introspecting up frames so should only be called *during* the top-level __init__
        of the base class :)

        Returns
        -------
        dict of argument names and params
        """

        param_names = self._full_sig_names

        # iterate from back to front (top frame to low frame) getting args
        #
        params = {}
        for frame_info in reversed(inspect.stack()):
            frame = frame_info.frame
            frame_locals = inspect.getargvalues(frame).locals
            frame_params = {k:v for k, v in frame_locals.items() if k in param_names}
            params.update(frame_params)

        return params

    def _full_name(self):
        """
        Returns the full module and class name of an object, eg.
        ``nwb_conversion_tools.spec.external_file.JSON``

        Returns
        -------
        str
        """
        return '.'.join((self.__module__, type(self).__name__))



def _recurse_subclasses(cls, leaves_only=True) -> list:
    """
    Given some class, find its subclasses recursively

    See: https://stackoverflow.com/a/17246726/13113166

    Args:
        leave_only (bool): If True, only include classes that have no further subclasses,
        if False, return all subclasses.

    Returns:
        list of subclasses
    """

    all_subclasses = []

    for subclass in cls.__subclasses__():
        if leaves_only:
            if len(subclass.__subclasses__()) == 0:
                all_subclasses.append(subclass)
        else:
            all_subclasses.append(subclass)
        all_subclasses.extend(_recurse_subclasses(subclass))

    return all_subclasses

def _recursive_import(module_name:str) -> typing.List[str]:
    """
    Given some path in a python package, import all modules beneath it

    Args:
        module_name (str): name of module to recursively import

    Returns:
        list of all modules that were imported
    """

    # iterate through modules, importing
    # see https://codereview.stackexchange.com/a/70282


    # import module (shouldnt hurt if it has already)
    base_mod = importlib.import_module(module_name)

    pkg_dir = Path(inspect.getsourcefile(base_mod)).resolve().parent

    loaded_modules = []
    for (module_loader, name, ispkg) in pkgutil.walk_packages([pkg_dir], base_mod.__package__+'.'):
        if not ispkg:
            importlib.import_module(name)
            loaded_modules.append(name)

    return loaded_modules

def _gather_list_of_dicts(a_list:list) -> typing.Dict[str, list]:
    """
    Gather a list of dictionaries like::

        [{'key1':'val1'}, {'key1':'val2'}, {'key1':'val3'}]

    to a dict of lists like:

        {'key1': ['val1', 'val2', 'val3']}
    """
    if len(a_list) == 1:
        # if there's only one dict in here just return it lmao
        return a_list[0]

    out_dict = {}
    for inner_dict in a_list:
        for inner_key, inner_value in inner_dict.items():
            if inner_key not in out_dict.keys():
                out_dict[inner_key] = [inner_value]
            else:
                out_dict[inner_key].append(inner_value)

    return out_dict

def _recursive_dedupe_dicts(a_dict, raise_on_dupes=True):
    """
    Deduplicate a list of dicts.

    Optionally raise an exception if duplicates are found, otherwise
    call ``set`` and unwrap singletons and return

    .. todo::

        TEST ME!!!!

    Parameters
    ----------
    a_dict : of dicts

    Returns
    -------
    dict: deduplicated dictionary

    """
    gathered = {}

    dupes = {}
    for k, v in a_dict.items():
        if isinstance(v, dict):
            gathered[k] = _recursive_dedupe_dicts(v)
        elif isinstance(v, (tuple, list)):
            v = tuple(set(v))
            if len(v)>1:
                dupes[k] = v
                gathered[k] = v
            else:
                gathered[k] = v[0]
        else:
            gathered[k] = v

    if raise_on_dupes and len(dupes)>0:
        dup_str = '\n'.join([f"{k}: {v}" for k, v in dupes.items()])
        raise Exception('Duplicates detected for keys, with values:'+dup_str)

    return gathered

