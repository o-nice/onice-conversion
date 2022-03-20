"""
Specify where your metadata is within a directory.

An extension of the spec module I started in the nwb-conversion-tools package, rebuilt here.

In reseracher-specific data formats, metadata is tucked away in a thousand unpredictable places.
The spec module is intended to give you the means of expressing where it is.

If it's embedded within some path name, try :class:`.spec.Path`,

If it's embedded in some .mat file, try :class:`.spec.Mat`

.. todo::

    examples!

"""

from onice_conversion.spec.base_spec import BaseSpec, from_dict
from onice_conversion.spec.path import Path, Paths, Glob
from onice_conversion.spec.external_file import JSON, Mat, YAML


def parse_nested_spec(spec, base_dir):
    out_dict = {}
    for key, value in spec.items():
        if isinstance(value, dict):
            out_dict[key].update(parse_nested_spec(value, base_dir))
        elif issubclass(type(value), BaseSpec):
            out_dict[key] = value._parse(base_dir)
        else:
            out_dict[key] = value

    return out_dict
