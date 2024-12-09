"""PyVista package for 3D plotting and mesh analysis."""

# ruff: noqa: F401
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
from typing import Literal
from typing import cast
import warnings

from pyvista._plot import plot
from pyvista._version import __version__
from pyvista._version import version_info
from pyvista.core import *
from pyvista.core import _validation
from pyvista.core._vtk_core import vtk_version_info
from pyvista.core.cell import _get_vtk_id_type
from pyvista.core.utilities.observers import send_errors_to_logging
from pyvista.core.wrappers import _wrappers
from pyvista.jupyter import set_jupyter_backend
from pyvista.report import GPUInfo
from pyvista.report import Report
from pyvista.report import get_gpu_info

# get the int type from vtk
ID_TYPE = cast(int, _get_vtk_id_type())

# determine if using at least vtk 9.0.0
if vtk_version_info.major < 9:  # pragma: no cover
    from pyvista.core.errors import VTKVersionError

    raise VTKVersionError('VTK version must be 9.0.0 or greater.')

# catch annoying numpy/vtk future warning:
warnings.simplefilter(action='ignore', category=FutureWarning)

# A simple flag to set when generating the documentation
OFF_SCREEN = os.environ.get('PYVISTA_OFF_SCREEN', 'false').lower() == 'true'

# flag for when building the sphinx_gallery
BUILDING_GALLERY = os.environ.get('PYVISTA_BUILDING_GALLERY', 'false').lower() == 'true'

# A threshold for the max cells to compute a volume for when repr-ing
REPR_VOLUME_MAX_CELLS = 1e6

# Set where figures are saved
FIGURE_PATH = os.environ.get('PYVISTA_FIGURE_PATH', None)

ON_SCREENSHOT = os.environ.get('PYVISTA_ON_SCREENSHOT', 'false').lower() == 'true'

# Send VTK messages to the logging module:
send_errors_to_logging()

# theme to use by default for the plot directive
PLOT_DIRECTIVE_THEME = None

# Set a parameter to control default print format for floats outside
# of the plotter
FLOAT_FORMAT = '{:.3e}'

# Serialization format to be used when pickling `DataObject`
PICKLE_FORMAT: Literal['vtk', 'xml', 'legacy'] = 'vtk' if vtk_version_info >= (9, 3) else 'xml'

# Name used for unnamed scalars
DEFAULT_SCALARS_NAME = 'Data'

MAX_N_COLOR_BARS = 10


# Import all modules for type checkers and linters
if TYPE_CHECKING:  # pragma: no cover
    from pyvista import demos
    from pyvista import examples
    from pyvista import ext
    from pyvista import trame
    from pyvista import utilities
    from pyvista.plotting import *


# Lazily import/access the plotting module
def __getattr__(name):
    """Fetch an attribute ``name`` from ``globals()`` or the ``pyvista.plotting`` module.

    This override is implemented to prevent importing all of the plotting module
    and GL-dependent VTK modules when importing PyVista.

    Raises
    ------
    AttributeError
        If the attribute is not found.

    """
    import importlib
    import inspect

    allow = {
        'demos',
        'examples',
        'ext',
        'trame',
        'utilities',
    }
    if name in allow:
        return importlib.import_module(f'pyvista.{name}')

    # avoid recursive import
    if 'pyvista.plotting' not in sys.modules:
        import pyvista.plotting

    try:
        feature = inspect.getattr_static(sys.modules['pyvista.plotting'], name)
    except AttributeError:
        raise AttributeError(f"module 'pyvista' has no attribute '{name}'") from None

    return feature
