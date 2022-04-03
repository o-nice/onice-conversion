# Reese

## Conversion Example

Presented at ONICE meeting 2022-04-01. Sample dataset to be uploaded separately

Demonstrates reading trialwise behavior data for odor concentration experiment, including

* Making an {class}`pynwb.NWBFile` with a {class}`pynwb.file.Subject` description
* Trialwise data using {meth}`pynwb.file.NWBFile.add_trial`
* Spatial data from pose tracking using {class}`pynwb.behavior.Position`
* Generic Timeseries data for analog sniff signal using {class}`pynwb.base.TimeSeries`
* Writing an NWBFile with {class}`pynwb.NWBHDF5IO`

```{literalinclude} ../../../examples/smear/reese.py
:language: python
:linenos:
```

## Opportunities for Reuse

Some opportunities to make this code able to be integrated into this package, and
opportunities to learn a bit of Python!

### Breaking into Functions

Most analysis code in science is written as scripts --- code that is usually
written in the "root" of the document, usually not enclosed within functions or classes
(or in the case of matlab, a single function per file). Scripts can be a very 
direct way of approaching a problem, but they can be difficult to reuse and maintain.

One first step in making code a bit more resuable is to break the code into separate functions.
There are a lot of ways of thinking about what makes a "good" function, but in my opinion a good
function is one that (among other things)

* **Does "one"(ish) thing**, or, has a well-defined purpose. Functions should be
  short -- it's always possible to combine multiple functions in a larger "wrapper"
  function. 
* Allows **alternative behavior** with arguments using optional arguments with **reasonable defaults.**
  A function should encapsulate a particular operation that you might need to do multiple times, 
  so rather than copying code with minor modifications, a function should offer the caller optionoal arguments
  that change its behavior. The function should *require* as few things as it needs to perform the option,
  so optional arguments should have default values that make the function do what one would expect it
  to do (ie. what its documentation says it does)
* Has no **side effects,** and conversely doesn't rely on anything outside of the function. A function should never
  change its surrounding environment (unless that's specifically what it is for): it shouldn't change
  the working directory, implicitly make or load files, etc. It also shouldn't rely on other variables/objects in the surrounding environment
  that aren't explicitly passed in as arguments. Functions with side effects are very brittle, as they need to be
  carefully orchestrated with other functions, making their functionality linked and thus harder to maintain because any change
  in one function affects the others. Instead, functions should require what they need with arguments, and return
  their result. Instead of saving a file at the end of a long analysis script, return the result of the analysis and
  then use a separate saving function that takes the data and a path to save it.

Among many other considerations...

To start breaking into functions, it's always a good idea to make a brief outline
of what we need our code to do! In this case, we

* Analyze data from multiple `subjects`, which have biographical data contained in {class}`pynwb.file.Subject` object.
* Each of which has multiple `experiments`
* Which in turn have multiple `sessions` -- each of which has its own nwb file.
* Each session can contain
    * `notes.txt`, which contained the date of the experiment
    * `trial_params.txt`, which describes the metadata for each of the sniff trials.
    * `sniff.bin`, a binary file containing analog sniffing data
* After loading, the data is then saved using one of several objects or methods described at the top of this page. 

That's a reasonable place to start breaking up the code! We can start by breaking up the 
nested for loops by putting them in separate functions that look like this...

```python
import os

def convert_session(experiment_dir:str, session:str):
    # ... code to conver session
    pass

def convert_experiment(subject_dir:str, experiment:str):
    experiment_dir = subject_dir + experiment + "/"
    sessions = os.listdir(experiment_dir)
    for session in sessions:
        convert_session(experiment_dir, session)
  
def convert_subject(data_dir: str, subject:str):
    subject_dir = data_dir + subject + "/"
    subject_number = subject[-4:]
    experiments = os.listdir(subject_dir)
    for experiment in experiments:
        if experiment == 'ARHMM':
            continue
        
        convert_experiment(subject_dir, experiment)
```

but even those are likely to be too "large" --- the `convert_session` function would effectively
have the rest of the code in the script! It's also a good idea for both readability and reusability
to encapsulate other separable operations in functions. 

So we can also break up each of the three different types of data we have into their own functions.
For example, the position data could look like this:

```python
from typing import List, Tuple
import numpy as np
from dataclasses import dataclass

from pynwb.behavior import Position
from pynwb import NWBFile, ProcessingModule

@dataclass
class Frame_Data:
    name: str
    """
    What to call this spatial series
    """
    position: np.ndarray
    """
    Value of the position in (unit)
    """
    timestamps: np.ndarray
    """
    Array of timestamps (ms) for each position
    """
    
    def add_series(self, position:Position, reference_frame:str='session_start') -> Position:
        """
        Method to add this data series to a pynwb Position object.
        """
        position.create_spatial_series(
          name=self.name,
          data=self.position,
          timestamps=self.timestamps,
          reference_frame=reference_frame
        )
        return position

def load_frame_data(data_path:str, delimiter:str = ',', skip_header:int=0) -> List[Frame_Data]:
    """
    Load an individual session's frame data from a file into a list of Frame_Data containers
    """  
    frame_params = np.genfromtxt(
        data_path,
        delimiter = delimiter,
        skip_header=skip_header)
    
    names = ['nose_x', 'nose_y', 'head_x', 'head_y', 'body_x', 'body_y']
    position_series = []
    for i, name in enumerate(names):
        position_series.append(
          Frame_Data(name, frame_params[:,i], frame_params[:,7]))
    
    return position_series

def add_frame_data(nwbfile: NWBFile, frame_data:List[Frame_Data],
                   module_name:str="position", description:str='') -> Tuple[Position, ProcessingModule]:
    """
    Load the data from a given frame data file and add it to an NWB IO file.
    
    Creates a :class:`~pynwb.base.ProcessingModule` 
    
    Args:
        nwbfile: File to add to!
        frame_data (List[:class:`.Frame_Data`]): see :func:`.load_frame_data`
        module_name (str): Name to give to the created ProcessingModule
        description (str): Description to give to the created ProcessingModule
        
    References:
        https://pynwb.readthedocs.io/en/stable/tutorials/general/file.html?highlight=Position#spatial-series-and-position
    """
    position = Position()
    for data_series in frame_data:
        position = data_series.add_series(position)
    
    position_module = nwbfile.create_processing_module(
      name=module_name, description=description
    )

    position_module.add(position)
    
    return position, position_module
                 
```

Which we would use like::
    
    >>> frame_data = load_frame_data(data_path)
    >>> position, position_module = add_frame_data(nwbfile, frame_data)


This is really nice because we have made a relatively general `Frame_Data` class and `add_frame_data` that doesn't
depend on the particularity of the data at hand -- only the `load_frame_data` has information that's 
unique to us! (names and how to load and index the data frame). So someone else could then extend our functions
by adding their own loading function without needing to rewrite the rest!

By writing docstrings as we go (and using types and type hints, which we'll cover another time!!), 
we help keep track of what everything does, so this function would have its documentation rendered like:

```{eval-rst}
.. py:function:: onice_conversion.add_frame_data(nwbfile: NWBFile, frame_data:Frame_Data, module_name:str, description:str)
    
    Load the data from a given frame data file and add it to an NWB IO file.
    
    Creates a :class:`~pynwb.base.ProcessingModule` 
    
    Args:
        nwbfile (NWBFile) : File to add to!
        frame_data (List[:class:`.Frame_Data`]) : see :func:`.load_frame_data`
        module_name (str) : Name to give to the created ProcessingModule
        description (str) : Description to give to the created ProcessingModule
        
    References:
        https://pynwb.readthedocs.io/en/stable/tutorials/general/file.html?highlight=Position#spatial-series-and-position

```


The next thing we would start doing is structuring our code into separate modules: i/o operations, 
processing operations, and so on, but that's for another time!

### Warnings

```{admonition} todo
(warn about using default values)
```

```python
import os
from datetime import datetime
import warnings

dateinfo = "2021-01-01, 01:00:00"
session_date_info = datetime.strptime(dateinfo, "%Y-%m-%d,%H:%M:%S")
if os.path.exists(session_dir + "notes.txt") == True:
    # get date from file
    pass
else:
    warnings.warn(f'Couldnt get data from notes.txt, using default date {dateinfo}')
```

### `pathlib`!

```{admonition} todo
show use of pathlib vs os.path
```

```python
from pathlib import Path

# for example
data_dir = Path().home() / 'my_data'
text_files = data_dir.glob('**/*.txt')
data_dir.exists()
my_file = data_dir / 'myfile.txt'
my_file2 = my_file.with_stem(my_file.stem + "_two")
# myfile_two.txt
```



