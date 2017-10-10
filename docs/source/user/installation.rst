.. _installation:

Installing Vaayu
================

Vaayu is a scientific software library written in the Python programming
language that makes extensive use of the rich scientific computing libraries
available for Python. The following are the bare minimum dependencies for using
Vaayu on any system:

  #. Python v2.7 or 3.x
  #. Numerical Python (NumPy) - Provides efficient array data type and
     associated operations, linear algebra routines etc.
  #. Scientific Python (SciPy)
  #. PyYAML - YAML library for interfacing with configuration and input files

In addition, to the aforementioned libraries the following packages are highly
recommended to gain maximum benefit from Vaayu.

  #. Pandas - Data Analysis library
  #. Matplotlib - Plotting and data visualization package
  #. IPython - Interactive python console with enhanced capabilities

Using Anaconda Python Distribution
----------------------------------

In addition to Python, these core scientific libraries also depend on additional
non-Python packages, e.g., BLAS/LAPACK, NetCDF, VTK, etc., that are not
available by default on many systems. Installation, upgrade, and maintenance of
these dependencies manually can be a cumbersome process. The entire process is
greatly simplified with the `Anaconda Python Distribution
<http://docs.continuum.io/anaconda/index>`_. This distribution provides the
comprehensive set of python packages that can be installed into different
*environments* for managing dependencies on all major operating systems. This
guide recommends that users install the Anaconda distribution and use Vaayu from
within a custom *conda environment* to get up and running quickly.

.. note::

   The default installation instructions are provided for Python v2.7. This is
   because the VTK python module is currently only available for Python 2.x
   series. If you are not interested in using VTK-related functionality within
   Vaayu, you can use safely use Vaayu with Python 3.x by selecting the python
   version during Anaconda install (or environment creation phase).

Installing the Anaconda Python distribution requires the following steps:

#. `Download the Anaconda installer
   <https://www.continuum.io/downloads>`_ for your operating system.

#. Execute the downloaded file and follow the installation
   instructions. It is recommended that you install the default
   packages.

#. Update the anaconda environment according to `installation
   instructions
   <http://conda.pydata.org/docs/install/full.html#install-instructions>`_


.. note::

   Make sure that you answer ``yes`` when the installer asks to add the
   installation location to your default PATH locations. Or else the following
   commands will not work. It might be necessary to open a new shell for the
   environment to be updated.

Install Vaayu from Git
----------------------

#. Obtain the Vaayu source from the public git repository

   .. code-block:: bash

      # Switch to directory where you develop code
      git clone https://github.com/sayerhs/vaayu.git
      cd vaayu

#. Create a custom conda environment and install all Vaayu dependencies. A
   :file:`environment.yml` is provided in the main directory to ease this step.

   .. code-block:: bash

      # Activate Anaconda if you haven't added it to default path
      conda env create -f environment.yml

   .. note::

      #. Users interested in using Vaayu with Python 3.x series should use the
         :file:`etc/vaayu-py3k.yml` instead of the default
         :file:`environment.yml`.

      #. The default environment does not install packages that are necessary
         during the development of Vaayu. Developers wishing to extend Vaayu in
         Python 2.7 environment should use :file:`etc/devenv.yaml` instead.

#. Activate the custom environment and install Vaayu within this environment.

   .. code-block:: bash

      source activate vaayu-env
      pip install .

   .. note::

      #. On windows machines use, ``activate vaayu-env`` without the ``source``.

      #. Developers should install Vaayu in *editable* mode by using the ``-e``
         option of pip.

Building documentation locally
------------------------------

A local version of this documentation can be built using Sphinx. Note that this
requires the user to have installed one of the development *conda* environments.

.. code-block:: bash

   # Change to directory where Vaayu was installed
   cd docs/

   # Build HTML documentation
   make html
   # View documentation in browser
   open build/html/index.html

   # Build PDF documentation (requires LaTeX installed)
   make latexpdf
   open build/latex/Vaayu.pdf

Running tests in development environment
----------------------------------------

Vaayu provides several unit tests to test the behavior of the library. These
tests are written using `py.test <https://docs.pytest.org/en/latest>`_. To run
the tests execute the following command :command:`py.test` from the top level
Vaayu directory.
