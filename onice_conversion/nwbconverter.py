import typing
from typing import Optional
import itertools
import shutil
from pathlib import Path

from tqdm import tqdm

from nwb_conversion_tools import NWBConverter as _NWBConverter
from nwb_conversion_tools.interfaces import list_interfaces

from onice_conversion.spec import BaseSpec
from onice_conversion import containers

class NWBConverter(_NWBConverter):
    """
    ONICE extension to :class:`nwb_conversion_tools.NWBConverter`



    """

    def __init__(self, *args, **kwargs):
        super(NWBConverter, self).__init__(*args, **kwargs)
        self._base_nwb_metadata = {}

    def add_container(self,
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
        if container_name is None:
            # just wanting to list the available containers
            return containers.get_container()
        container = containers.get_container(container_name)

        if spec is None and len(kwargs) == 0:
            # want to list schema for this container
            return containers.get_container_schema(container)

    @property
    def base_nwb_metadata(self) -> typing.Dict[str, tuple]:
        """
        Return descriptions for the basic file-level metadata container objects,
        ``'NWBFile', 'Subject'``

        Returns:
            dict of tuples of parameter spec for each container type
        """
        if len(self._base_nwb_metadata) == 0:
            for container_name in ('NWBFile', 'Subject'):
                self._base_nwb_metadata[container_name] = containers.get_container_schema(container_name)

        return self._base_nwb_metadata



    def hail_mary(self, base_dir: Optional[Path] = None,
                  interface_type: Optional[str] = None
                  ):
        """
        Just try every interface on every file and see what instantiates.

        Parameters
        ----------
        base_dir : directory to peruse. if none, then the base_dir provided on init is used.
        interface_type : if provided, only try interfaces of this type

        Returns
        -------
        tuple of::

            (interface object,
            path (relative to base_dir),
            parameter key that was used,
            and the instantiated object itself)
        """
        if base_dir is None:
            if self.base_dir is None:
                raise ValueError("No base_dir passed, and none give on instantiation. Need to know where to go!")
            else:
                base_dir = self.base_dir
        else:
            base_dir = Path(base_dir)

        # --------------------------------------------------
        # monkeypatch the __del__ method of spikeextractors so it doesn't throw a ton of exceptions during hail mary
        _monkeypatch_spikeextractors()
        # --------------------------------------------------

        interfaces = list_interfaces(interface_type)

        # create iterator to go over all files and interfaces...
        all_paths = itertools.chain((base_dir,), base_dir.glob("**/[!\.]*"))
        everything = itertools.product(interfaces, all_paths)

        # ----------------------------------------------------------------------- #
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
        #                                                                         #
        #                             _|_|                          _|    _|      #
        #   _|_|_|    _|_|          _|        _|_|    _|  _|_|          _|_|_|_|  #
        # _|    _|  _|    _|      _|_|_|_|  _|    _|  _|_|          _|    _|      #
        # _|    _|  _|    _|        _|      _|    _|  _|            _|    _|      #
        #   _|_|_|    _|_|          _|        _|_|    _|            _|      _|_|  #
        #       _|                                                                #
        #   _|_|                                                                  #
        #                 w h a t   i f   i t   w o r k s   ? ? ?                 #
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! #
        # ----------------------------------------------------------------------- #
        hits = []
        hit_bar = tqdm(position=1, desc="Hits")
        for interface, path in tqdm(everything, position=0):
            for req_param in interface.get_source_schema().get('required', []):
                try:
                    instance = interface(**{req_param: str(path)})
                    hits.append((interface, path.relative_to(base_dir), req_param, instance))
                    hit_bar.update()
                except:
                    # print(e, interface, req_param, str(path))
                    pass

        emotion = ":)" if len(hits) > 0 else ":("
        hit_string = "\n".join(
            [f"{interf.interface_type}, {interf.device_name}, {req_param}, {path}" for interf, path, req_param, _ in
             hits])

        print(f'Found {len(hits)} hits {emotion}\n\n' + hit_string)
        return hits


def _monkeypatch_spikeextractors():
    """
    To make :meth:`.NWBConverter.hail_mary` work, we have to override some __del__ methods in
    spikeextractors that throw errors on incomplete __init__ calls
    """

    def __base__del__(self):
        # close memmap files (for Windows)
        if hasattr(self, '_memmap_files'):
            for memmap_obj in self._memmap_files:
                self.del_memmap_file(memmap_obj)
            if self._tmp_folder is not None and len(self._memmap_files) > 0:
                try:
                    shutil.rmtree(self._tmp_folder)
                except Exception as e:
                    print('Impossible to delete temp file:', self._tmp_folder, 'Error', e)

    def __hdf5__del__(self):
        if hasattr(self, '_file'):
            self._file.close()

    def __cfnme__del__(self):
        if hasattr(self, '_dataset_file'):
            self._dataset_file.close()

    import spikeextractors.baseextractor
    spikeextractors.baseextractor.BaseExtractor.__del__ = __base__del__

    import roiextractors.extractors.hdf5imagingextractor.hdf5imagingextractor
    roiextractors.extractors.hdf5imagingextractor.hdf5imagingextractor.Hdf5ImagingExtractor.__del__ = __hdf5__del__

    import roiextractors.extractors.schnitzerextractor.cnmfesegmentationextractor
    import roiextractors.extractors.schnitzerextractor.extractsegmentationextractor
    import roiextractors.extractors.caiman.caimansegmentationextractor
    roiextractors.extractors.schnitzerextractor.cnmfesegmentationextractor.CnmfeSegmentationExtractor.__del__ = __cfnme__del__
    roiextractors.extractors.schnitzerextractor.extractsegmentationextractor.ExtractSegmentationExtractor.__del__ = __cfnme__del__
    roiextractors.extractors.caiman.caimansegmentationextractor.CaimanSegmentationExtractor.__del__ = __cfnme__del__