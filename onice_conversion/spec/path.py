import typing
import sys
from pathlib import Path as plPath
import glob
import re

import parse

from onice_conversion.spec import BaseSpec
from onice_conversion.utils import AmbiguityError, _gather_list_of_dicts, _recursive_dedupe_dicts


class Path(BaseSpec):
    """
    Specify a metadata variable embedded in a path using :mod:`parse`

    See the `parse documentation <https://github.com/r1chardj0n3s/parse>`_
    for more details, but briefly, to specify the metadata variables
    ``subject_id == 'jonny'`` and ``session_id = '001'``
    in a file path ``data/recordings/jonny_spikes_001.spikes``, one would
    use a ``format == 'data/recordings/{subject_id}_spikes_{session_id}.spikes``.
    Additional options like specifying a format for the values, etc. can be
    found in the parse documentation.

    Raises an exception if multiple matching values are found in :meth:`.Path._parse` ,
    this is the singular version, and if there are multiple matches that means it's mis-specified
    To allow multiple matches, try :class:`.Paths`

    .. todo::

        This should be renamed something like MetaInPath or something, and then
        Path and Paths should be things that are basically globs with constraints.
        jonny is just very tired rn
    """

    def __init__(self, format:str,
                 *args, **kwargs):
        super(Path, self).__init__(*args, **kwargs)

        self.format = str(format)
        self.parser = parse.Parser(self.format) # type: typing.Optional[parse.Parser]

        if len(self.parser.named_fields) == 0:
            raise ValueError('format string must use named fields, not anonymous fields like {}')

    @property
    def _specifies(self) -> typing.Tuple[str, ...]:
        return tuple(self.parser.named_fields)

    def _parse_dir(self, base_path:typing.Union[str, plPath]) -> list:
        """
        First part of :meth:`.Path._parse` , given a base directory and parser,
        return a list of dicts of matching keys found.
        """
        # make absolute
        base_path = plPath(base_path).absolute()
        # globify format string to find all matching files
        format_glob = re.sub(r'\{.*?\}', '*', self.format)

        # find matching files relative to the base_path
        matching_files = base_path.glob(format_glob)

        # parse results
        results = []
        for match in matching_files:
            # make relative to base_path to match format
            match = match.relative_to(base_path)
            parsed = self.parser.parse(str(match))
            # parser returns None if no matches
            if parsed is not None:
                results.append(parsed.named)

        if len(results) == 0:
            raise ValueError(f'No matches were found between \n(relative) format:\n{self.format}\nglob string:{format_glob}\nin\n{base_path}')

        return results


    def _parse(self, base_path:typing.Union[str, plPath],
               metadata:typing.Optional[dict]=None) -> dict:
        """
        Parse metadata stored in some path name relative to
         using the parser created by :attr:`.format`.

        If the input path is not absolute, it is made absolute relative to
        :attr:`.base_path` so that it matches :attr:`.format`

        Raises a :class:`~.utils.AmbiguityError` if multiple matches for a single
        key are found, and a ``ValueError`` if zero matches are found.

        Parameters
        ----------
        base_path : :class:`pathlib.Path`
            Path to _parse!!!

        Returns
        -------
        dict of metadata params
        """
        results = self._parse_dir(base_path)

        # check for dupes!!
        try:
            gathered = _gather_list_of_dicts(results)
            results = _recursive_dedupe_dicts(gathered, raise_on_dupes=True)
        except AmbiguityError as e:
            # reraise error with additional informative message about what else to use
            raise type(e)(
                str(e)+'\nIf this was intentional, you might want to try spec.Paths'
            ).with_traceback(sys.exc_info()[2])

        return results

class Paths(Path):
    """
    Like :class:`.spec.Path` but allows multiple values for a single key
    """

    def _parse(self, base_path: typing.Union[str, plPath]) -> dict:
        results = self._parse_dir(base_path)

        gathered = _gather_list_of_dicts(a_list)
        return _recursive_dedupe_dicts(results, raise_on_dupes=False)

class Glob(BaseSpec):
    """
    Sort of the opposite of :class:`.Path` -- specify some path given some metadata values

    Replaces any named format variables in `{brackets}`, and then globs any `'*'`s
    """

    def __init__(self, key:str,format:str, only_dirs:bool=False, *args, **kwargs):
        """
        Args:
            key (str): The key that will define what's returned from Parse
            format (str): A globlike format string to match files within the base directory,
                eg to match ``parentdir_335092/some_file_250269287.bin`` we might use
                ``"parentdir_*/some_file_*.bin"``

                Can also use previously defined metadata, eg to replace some part of the file with ``subject_id``, use
                ``"parentdir_{subject_id}/"`` etc.
            only_dirs (bool): Only match directories, not files (default: False)
            *args ():
            **kwargs ():
        """
        super(Glob, self).__init__(*args, **kwargs)
        self.only_dirs = only_dirs
        self.key = key
        self.format = str(format)

    @property
    def _specifies(self) -> typing.Tuple[str, ...]:
        return (self.key,)

    def _parse(self,
               base_path:typing.Union[str, plPath],
               metadata:typing.Optional[dict]=None) -> dict:
        """
        Find a path by first replacing `{format_strings}` with variables from the passed metadata dict
        and then globbing over any `'*'`

        This class ensures a single path is returned, and raises an :class:`.AmbiguityError` otherwise.
        To return multiple paths, use :class:`.Globs`

        Parameters
        ----------
        base_path :
        metadata :

        Returns
        -------

        """

        # replace format string
        try:
            format_str = self.format.format(**metadata)
        except KeyError as e:
            # reraise error with additional informative message about what else to use
            raise type(e)(
                str(e) + '\nField not found in metadata, did you add it with `add_metadata`?'
            ).with_traceback(sys.exc_info()[2])

        # add to base_path
        full_path = plPath(base_path).absolute() / format_str

        # glob us some matching files if it's got an asterisk
        if '*' in str(full_path):
            paths = glob.glob(str(full_path))
            if self.only_dirs:
                paths = [path for path in paths if plPath(path).is_dir()]


            if len(paths)>1:
                raise AmbiguityError(f'Multiple paths matched glob string: {str(full_path)},\nif this was intentional, use Globs instead!')
            elif len(paths)<0:
                raise FileNotFoundError(f'No file was found matching query string {str(full_path)}')

            path = paths[0]

        else:
            path = str(full_path)

        return {self.key: path}
