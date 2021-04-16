"""
Utility functions used internally across the library
"""

import inspect


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

