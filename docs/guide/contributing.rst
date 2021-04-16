Contributing
============


Adding an Example Notebook
---------------------------

Sphinx doesn't allow references to files that are outside the source directory ('/docs' in our case),
so we have to use the `nbsphinx_link <https://github.com/vidartf/nbsphinx-link>`_ package to include them
in our documentation.

Say we have some example notebook located at ``/examples/wehr/wehr-nick.ipynb`` , and we
want to refer to it from the .rst file located at ``/docs/examples/wehr/wehr.rst`` .
We would create an ``.nblink`` file at ``/docs/examples/wehr/wehr-nick.ipynb`` like:

.. code-block:: json

   {
       "path": "../../../examples/wehr/wehr-nick.ipynb"
   }

that references the ``.ipynb`` file relative to the directory that the ``.nblink`` file is in.

In ``/docs/examples/wehr/wehr.rst`` , we would then include the notebook using a ``toctree`` directive like::

    .. toctree:

       wehr-nick

