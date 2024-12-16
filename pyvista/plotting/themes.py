"""API description for managing plotting theme parameters in pyvista.

Examples
--------
Apply a built-in theme

>>> import pyvista as pv
>>> pv.set_plot_theme('default')
>>> pv.set_plot_theme('document')
>>> pv.set_plot_theme('dark')
>>> pv.set_plot_theme('paraview')

Load a theme into pyvista

>>> from pyvista.plotting.themes import Theme
>>> theme = Theme.document_theme()
>>> theme.save('my_theme.json')  # doctest:+SKIP
>>> loaded_theme = pv.load_theme('my_theme.json')  # doctest:+SKIP

Create a custom theme from the default theme and load it into
pyvista.

>>> my_theme = Theme.document_theme()
>>> my_theme.font.size = 20
>>> my_theme.font.title_size = 40
>>> my_theme.cmap = 'jet'
>>> pv.global_theme.load_theme(my_theme)
>>> pv.global_theme.font.size
20

"""

from __future__ import annotations

from collections.abc import MutableMapping
from itertools import chain
import json
import os
import pathlib
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
import warnings

import pyvista
from pyvista.core.errors import PyVistaDeprecationWarning
from pyvista.core.utilities.misc import _check_range

from .colors import Color
from .colors import get_cmap_safe
from .colors import get_cycler
from .opts import InterpolationType
from .tools import parse_font_family

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable
    from typing import ClassVar

    from pyvista.core._typing_core import VectorLike
    from pyvista.plotting import Plotter

    from ._typing import ColorLike


def _set_plot_theme_from_env() -> None:
    """Set plot theme from an environment variable."""
    if 'PYVISTA_PLOT_THEME' in os.environ:
        try:
            theme = os.environ['PYVISTA_PLOT_THEME']
            set_plot_theme(theme.lower())
        except ValueError:
            allowed = ', '.join(Theme.defaults())
            warnings.warn(
                f'\n\nInvalid PYVISTA_PLOT_THEME environment variable "{theme}". '
                f'Should be one of the following: {allowed}',
            )


def load_theme(filename):
    """Load a theme from a file.

    Parameters
    ----------
    filename : str
        Theme file. Must be json.

    Returns
    -------
    pyvista.Theme
        The loaded theme.

    Examples
    --------
    >>> import pyvista as pv
    >>> from pyvista.plotting.themes import Theme
    >>> theme = Theme.document_theme()
    >>> theme.save('my_theme.json')  # doctest:+SKIP
    >>> loaded_theme = pv.load_theme('my_theme.json')  # doctest:+SKIP

    """
    with Path(filename).open() as f:
        theme_dict = json.load(f)
    return Theme.from_dict(theme_dict)


def set_plot_theme(theme):
    """Set the plotting parameters to a predefined theme using a string.

    Parameters
    ----------
    theme : str
        Theme name.  Either ``'default'``, ``'document'``, ``'document_pro'``,
        ``'dark'``, ``'paraview'``, ``'vtk'``, or ``'testing'``.

    Examples
    --------
    Set to the default theme.

    >>> import pyvista as pv
    >>> pv.set_plot_theme('default')

    Set to the document theme.

    >>> pv.set_plot_theme('document')

    Set to the dark theme.

    >>> pv.set_plot_theme('dark')

    Set to the ParaView theme.

    >>> pv.set_plot_theme('paraview')

    """
    if isinstance(theme, str):
        theme = theme.lower()
        try:
            new_theme_type = Theme.from_default(theme)
        except KeyError:
            raise ValueError(
                f"Theme '{theme}' not found in PyVista's default themes: {Theme.defaults()}"
            )
        pyvista.global_theme.load_theme(new_theme_type)
    elif isinstance(theme, Theme):
        pyvista.global_theme.load_theme(theme)
    else:
        raise TypeError(
            f'Expected a ``pyvista.plotting.themes.Theme`` or ``str``, not {type(theme).__name__}',
        )


# Mostly from https://stackoverflow.com/questions/56579348/how-can-i-force-subclasses-to-have-slots
class _ForceSlots(type):
    """Metaclass to force classes and subclasses to have __slots__."""

    @classmethod
    def __prepare__(metaclass, name, bases, **kwargs):
        super_prepared = super().__prepare__(metaclass, name, bases, **kwargs)  # type: ignore[arg-type, call-arg, misc]
        super_prepared['__slots__'] = ()
        return super_prepared


class _ThemeConfig(metaclass=_ForceSlots):
    """Provide common methods for theme configuration classes."""

    __slots__: list[str] = []

    _defaults: ClassVar[dict[str, str]] = {}

    def _handle_kwargs(self, **kwargs):
        """Set config values from **kwargs."""
        for key, value in kwargs.items():
            if isinstance(value, MutableMapping):
                self[key].update_from_dict(value)
            else:
                self[key] = value

    @classmethod
    def from_dict(cls, dict_):
        """Create from a dictionary."""
        inst = cls()
        for key, value in dict_.items():
            attr = getattr(inst, key)
            if hasattr(attr, 'from_dict'):
                setattr(inst, key, attr.from_dict(value))
            else:
                setattr(inst, key, value)
        return inst

    def update_from_dict(self, dict_):
        """Update theme in place with dictionary."""
        for key, value in dict_.items():
            attr = getattr(self, key)
            if hasattr(attr, 'update_from_dict'):
                attr.update_from_dict(value)
            else:
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Return theme config parameters as a dictionary.

        Returns
        -------
        dict
            This theme parameter represented as a dictionary.

        """
        # remove the first underscore in each entry
        dict_ = {}
        for key in self._all__slots__():
            value = getattr(self, key)
            key = key[1:]
            if hasattr(value, 'to_dict'):
                dict_[key] = value.to_dict()
            else:
                dict_[key] = value
        return dict_

    def __eq__(self, other) -> bool:
        if not isinstance(other, _ThemeConfig):
            return False

        for attr_name in other.__slots__:
            attr = getattr(self, attr_name)
            other_attr = getattr(other, attr_name)
            if (
                isinstance(attr, (tuple, list))
                and tuple(attr) != tuple(other_attr)
                or not attr == other_attr
            ):
                return False

        return True

    def __getitem__(self, key):
        """Get a value via a key.

        Implemented here for backwards compatibility.
        """
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Set a value via a key.

        Implemented here for backwards compatibility.
        """
        setattr(self, key, value)

    @classmethod
    def _all__slots__(cls):
        """Get all slots including parent classes."""
        mro = cls.mro()
        return tuple(chain.from_iterable(c.__slots__ for c in mro if c is not object))  # type: ignore[attr-defined]

    @classmethod
    def register_default(cls, name, dict_, doc=None):
        """Register a default theme from a dictionary.

        Parameters
        ----------
        name : str
            Name of theme for attribute.
        dict_ : dict
            Theme dictionary
        doc : str, optional
            Docstring to add to attribute.

        Examples
        --------
        Register a default theme for downstream use.

        >>> from pyvista.plotting.themes import Theme
        >>> Theme.register_default("my_theme", {"show_edges": True})
        >>> my_theme = Theme.my_theme()
        >>> my_theme.show_edges
        True

        """

        @classmethod
        def return_theme(cls):
            return cls.from_dict(dict_)

        setattr(cls, name, return_theme)
        attr = getattr(cls, name)
        attr.__func__.__name__ = name
        if doc is not None:
            attr.__func__.__doc__ = doc

        cls._defaults[name] = name

    @classmethod
    def from_default(cls, name):
        """Return a default theme.

        Examples
        --------
        >>> from pyvista.plotting.themes import Theme
        >>> theme = Theme.from_default("vtk")

        See Also
        --------
        Theme.defaults

        """
        theme = getattr(cls, cls._defaults[name])
        return theme()

    @classmethod
    def defaults(self):
        """Return list of default themes.

        Examples
        --------
        >>> from pyvista.plotting.themes import Theme
        >>> theme = Theme.defaults()

        """
        return list(self._defaults.keys())


class _LightingConfig(_ThemeConfig):
    """PyVista lighting configuration.

    This will control the lighting interpolation type, parameters,
    and Physically Based Rendering (PBR) options

    Examples
    --------
    Set global PBR parameters.

    >>> import pyvista as pv
    >>> pv.global_theme.lighting_params.interpolation = 'pbr'
    >>> pv.global_theme.lighting_params.metallic = 0.5
    >>> pv.global_theme.lighting_params.roughness = 0.25

    """

    __slots__ = [
        '_interpolation',
        '_metallic',
        '_roughness',
        '_ambient',
        '_diffuse',
        '_specular',
        '_specular_power',
        '_emissive',
    ]

    def __init__(self, **kwargs):
        self._interpolation = InterpolationType.FLAT.value
        self._metallic = 0.0
        self._roughness = 0.5
        self._ambient = 0.0
        self._diffuse = 1.0
        self._specular = 0.0
        self._specular_power = 100.0
        self._emissive = False

        self._handle_kwargs(**kwargs)

    @property
    def interpolation(self) -> InterpolationType:  # numpydoc ignore=RT01
        """Return or set the default interpolation type.

        See :class:`pyvista.plotting.opts.InterpolationType`.

        Options are:

        * ``'Phong'``
        * ``'Flat'``
        * ``'Physically based rendering'``

        This is stored as an integer value of the ``InterpolationType``
        so that the theme can be JSON-serializable.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.interpolation = 'Phong'
        >>> pv.global_theme.lighting_params.interpolation
        <InterpolationType.PHONG: 2>


        """
        return InterpolationType.from_any(self._interpolation)

    @interpolation.setter
    def interpolation(
        self,
        interpolation: str | int | InterpolationType,
    ):
        self._interpolation = InterpolationType.from_any(interpolation).value

    @property
    def metallic(self) -> float:  # numpydoc ignore=RT01
        """Return or set the metallic value.

        This requires that the interpolation be set to ``'Physically based
        rendering'``. Must be between 0 and 1.

        Examples
        --------
        Set the global metallic value used in physically based rendering to
        ``0.5``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.metallic = 0.5
        >>> pv.global_theme.lighting_params.metallic
        0.5

        """
        return self._metallic

    @metallic.setter
    def metallic(self, metallic: float):
        _check_range(metallic, (0, 1), 'metallic')
        self._metallic = metallic

    @property
    def roughness(self) -> float:  # numpydoc ignore=RT01
        """Return or set the roughness value.

        This value has to be between 0 (glossy) and 1 (rough). A glossy
        material has reflections and a high specular part. This parameter is
        only used by PBR interpolation.

        Examples
        --------
        Set the global roughness value used in physically based rendering to
        ``0.25``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.roughness = 0.25
        >>> pv.global_theme.lighting_params.roughness
        0.25

        """
        return self._roughness

    @roughness.setter
    def roughness(self, roughness: float):
        _check_range(roughness, (0, 1), 'roughness')
        self._roughness = roughness

    @property
    def ambient(self) -> float:  # numpydoc ignore=RT01
        """Return or set the ambient value.

        When lighting is enabled, this is the amount of light in the range of 0
        to 1 that reaches the actor when not directed at the light source
        emitted from the viewer.

        Examples
        --------
        Set the global ambient lighting value to ``0.2``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.ambient = 0.2
        >>> pv.global_theme.lighting_params.ambient
        0.2

        """
        return self._ambient

    @ambient.setter
    def ambient(self, ambient: float):
        _check_range(ambient, (0, 1), 'ambient')
        self._ambient = ambient

    @property
    def diffuse(self) -> float:  # numpydoc ignore=RT01
        """Return or set the diffuse value.

        This is the scattering of light by reflection or
        transmission. Diffuse reflection results when light strikes an
        irregular surface such as a frosted window or the surface of a
        frosted or coated light bulb. Must be between 0 and 1.

        Examples
        --------
        Set the global diffuse lighting value to ``0.5``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.diffuse = 0.5
        >>> pv.global_theme.lighting_params.diffuse
        0.5

        """
        return self._diffuse

    @diffuse.setter
    def diffuse(self, diffuse: float):
        _check_range(diffuse, (0, 1), 'diffuse')
        self._diffuse = diffuse

    @property
    def specular(self) -> float:  # numpydoc ignore=RT01
        """Return or set the specular value.

        Specular lighting simulates the bright spot of a light that appears
        on shiny objects. Must be between 0 and 1.

        Examples
        --------
        Set the global specular value to ``0.1``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.specular = 0.1
        >>> pv.global_theme.lighting_params.specular
        0.1

        """
        return self._specular

    @specular.setter
    def specular(self, specular: float):
        _check_range(specular, (0, 1), 'specular')
        self._specular = specular

    @property
    def specular_power(self) -> float:  # numpydoc ignore=RT01
        """Return or set the specular power value.

        Must be between 0.0 and 128.0.

        Examples
        --------
        Set the global specular power value to ``50``.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.specular_power = 50
        >>> pv.global_theme.lighting_params.specular_power
        50

        """
        return self._specular_power

    @specular_power.setter
    def specular_power(self, specular_power: float):
        _check_range(specular_power, (0, 128), 'specular_power')
        self._specular_power = specular_power

    @property
    def emissive(self) -> bool:  # numpydoc ignore=RT01
        """Return or set if emissive is used with point Gaussian style.

        Examples
        --------
        Globally enable emissive lighting when using the point Gaussian style.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting_params.emissive = True
        >>> pv.global_theme.lighting_params.emissive
        True

        """
        return self._emissive

    @emissive.setter
    def emissive(self, emissive: bool):
        self._emissive = bool(emissive)


class _DepthPeelingConfig(_ThemeConfig):
    """PyVista depth peeling configuration.

    Examples
    --------
    Set global depth peeling parameters.

    >>> import pyvista as pv
    >>> pv.global_theme.depth_peeling.number_of_peels = 1
    >>> pv.global_theme.depth_peeling.occlusion_ratio = 0.0
    >>> pv.global_theme.depth_peeling.enabled = True

    """

    __slots__ = ['_number_of_peels', '_occlusion_ratio', '_enabled']

    def __init__(self, **kwargs):
        self._number_of_peels = 4
        self._occlusion_ratio = 0.0
        self._enabled = False

        self._handle_kwargs(**kwargs)

    @property
    def number_of_peels(self) -> int:  # numpydoc ignore=RT01
        """Return or set the number of peels in depth peeling.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.depth_peeling.number_of_peels = 1

        """
        return self._number_of_peels

    @number_of_peels.setter
    def number_of_peels(self, number_of_peels: int):
        self._number_of_peels = int(number_of_peels)

    @property
    def occlusion_ratio(self) -> float:  # numpydoc ignore=RT01
        """Return or set the occlusion ratio in depth peeling.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.depth_peeling.occlusion_ratio = 0.0

        """
        return self._occlusion_ratio

    @occlusion_ratio.setter
    def occlusion_ratio(self, occlusion_ratio: float):
        self._occlusion_ratio = float(occlusion_ratio)

    @property
    def enabled(self) -> bool:  # numpydoc ignore=RT01
        """Return or set if depth peeling is enabled.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.depth_peeling.enabled = True

        """
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        self._enabled = bool(enabled)

    def __repr__(self):
        txt = ['']
        parm = {
            'Number': 'number_of_peels',
            'Occlusion ratio': 'occlusion_ratio',
            'Enabled': 'enabled',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'    {name:<21}: {setting}')
        return '\n'.join(txt)


class _SilhouetteConfig(_ThemeConfig):
    """PyVista silhouette configuration.

    Examples
    --------
    Set global silhouette parameters.

    >>> import pyvista as pv
    >>> pv.global_theme.silhouette.enabled = True
    >>> pv.global_theme.silhouette.color = 'grey'
    >>> pv.global_theme.silhouette.line_width = 2
    >>> pv.global_theme.silhouette.feature_angle = 20

    """

    __slots__ = ['_color', '_line_width', '_opacity', '_feature_angle', '_decimate', '_enabled']

    def __init__(self, **kwargs):
        self._color = Color('black')
        self._line_width = 2
        self._opacity = 1.0
        self._feature_angle = None
        self._decimate = None
        self._enabled = False

        self._handle_kwargs(**kwargs)

    @property
    def enabled(self) -> bool:  # numpydoc ignore=RT01
        """Return or set whether silhouette is on or off."""
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        self._enabled = bool(enabled)

    @property
    def color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the silhouette color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.color = 'red'

        """
        return self._color

    @color.setter
    def color(self, color: ColorLike):
        self._color = Color(color)

    @property
    def line_width(self) -> float:  # numpydoc ignore=RT01
        """Return or set the silhouette line width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.line_width = 2.0

        """
        return self._line_width

    @line_width.setter
    def line_width(self, line_width: float):
        self._line_width = float(line_width)  # type: ignore[assignment]

    @property
    def opacity(self) -> float:  # numpydoc ignore=RT01
        """Return or set the silhouette opacity.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.opacity = 1.0

        """
        return self._opacity

    @opacity.setter
    def opacity(self, opacity: float):
        _check_range(opacity, (0, 1), 'opacity')
        self._opacity = float(opacity)

    @property
    def feature_angle(self) -> float | None:  # numpydoc ignore=RT01
        """Return or set the silhouette feature angle.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.feature_angle = 20.0

        """
        return self._feature_angle

    @feature_angle.setter
    def feature_angle(self, feature_angle: float | None):
        self._feature_angle = feature_angle

    @property
    def decimate(self) -> float:  # numpydoc ignore=RT01
        """Return or set the amount to decimate the silhouette.

        Parameter must be between 0 and 1.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.decimate = 0.9

        """
        return self._decimate  # type: ignore[return-value]

    @decimate.setter
    def decimate(self, decimate: float):
        if decimate is None:
            self._decimate = None
        else:
            _check_range(decimate, (0, 1), 'decimate')
            self._decimate = float(decimate)

    def __repr__(self):
        txt = ['']
        parm = {
            'Color': 'color',
            'Line width': 'line_width',
            'Opacity': 'opacity',
            'Feature angle': 'feature_angle',
            'Decimate': 'decimate',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'    {name:<21}: {setting}')
        return '\n'.join(txt)


class _ColorbarConfig(_ThemeConfig):
    """PyVista colorbar configuration.

    Examples
    --------
    Set the colorbar width.

    >>> import pyvista as pv
    >>> pv.global_theme.colorbar_horizontal.width = 0.2

    """

    __slots__ = ['_width', '_height', '_position_x', '_position_y']

    def __init__(self, **kwargs):
        self._width = None
        self._height = None
        self._position_x = None
        self._position_y = None

        self._handle_kwargs(**kwargs)

    @property
    def width(self) -> float:  # numpydoc ignore=RT01
        """Return or set colorbar width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_horizontal.width = 0.2

        """
        return self._width  # type: ignore[return-value]

    @width.setter
    def width(self, width: float):
        self._width = float(width)

    @property
    def height(self) -> float:  # numpydoc ignore=RT01
        """Return or set colorbar height.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_horizontal.height = 0.2

        """
        return self._height  # type: ignore[return-value]

    @height.setter
    def height(self, height: float):
        self._height = float(height)

    @property
    def position_x(self) -> float:  # numpydoc ignore=RT01
        """Return or set colorbar x position.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_horizontal.position_x = 0.2

        """
        return self._position_x  # type: ignore[return-value]

    @position_x.setter
    def position_x(self, position_x: float):
        self._position_x = float(position_x)

    @property
    def position_y(self) -> float:  # numpydoc ignore=RT01
        """Return or set colorbar y position.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_horizontal.position_y = 0.2

        """
        return self._position_y  # type: ignore[return-value]

    @position_y.setter
    def position_y(self, position_y: float):
        self._position_y = float(position_y)

    def __repr__(self):
        txt = ['']
        parm = {
            'Width': 'width',
            'Height': 'height',
            'X Position': 'position_x',
            'Y Position': 'position_y',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'    {name:<21}: {setting}')

        return '\n'.join(txt)


class _AxesConfig(_ThemeConfig):
    """PyVista axes configuration.

    Examples
    --------
    Show the default axes configuration values.

    >>> import pyvista as pv
    >>> pv.global_theme.axes.x_color
    Color(name='tomato', hex='#ff6347ff', opacity=255)

    >>> pv.global_theme.axes.y_color
    Color(name='seagreen', hex='#2e8b57ff', opacity=255)

    >>> pv.global_theme.axes.z_color
    Color(name='blue', hex='#0000ffff', opacity=255)

    >>> pv.global_theme.axes.box
    False

    >>> pv.global_theme.axes.show
    True

    Set the x-axis color to black.

    >>> pv.global_theme.axes.x_color = 'black'

    Show the axes orientation widget by default.

    >>> pv.global_theme.axes.show = True

    Use the :func:`axes orientation box <pyvista.create_axes_orientation_box>` as the orientation widget.

    >>> pv.global_theme.axes.box = True

    """

    __slots__ = ['_x_color', '_y_color', '_z_color', '_box', '_show']

    def __init__(self, **kwargs):
        self._x_color = Color('tomato')
        self._y_color = Color('seagreen')
        self._z_color = Color('mediumblue')
        self._box = False
        self._show = True

        self._handle_kwargs(**kwargs)

    def __repr__(self):
        txt = ['Axes configuration']
        parm = {
            'X Color': 'x_color',
            'Y Color': 'y_color',
            'Z Color': 'z_color',
            'Use Box': 'box',
            'Show': 'show',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'    {name:<21}: {setting}')

        return '\n'.join(txt)

    @property
    def x_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set x-axis color.

        Examples
        --------
        Get the default x-axis color

        >>> import pyvista as pv
        >>> pv.global_theme.axes.x_color
        Color(name='tomato', hex='#ff6347ff', opacity=255)

        Change the default color.

        >>> pv.global_theme.axes.x_color = 'red'

        """
        return self._x_color

    @x_color.setter
    def x_color(self, color: ColorLike):
        self._x_color = Color(color)

    @property
    def y_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set y-axis color.

        Examples
        --------
        Get the default y-axis color

        >>> import pyvista as pv
        >>> pv.global_theme.axes.y_color
        Color(name='seagreen', hex='#2e8b57ff', opacity=255)

        Change the default color.

        >>> pv.global_theme.axes.y_color = 'green'

        """
        return self._y_color

    @y_color.setter
    def y_color(self, color: ColorLike):
        self._y_color = Color(color)

    @property
    def z_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set z-axis color.

        Examples
        --------
        Get the default z-axis color

        >>> import pyvista as pv
        >>> pv.global_theme.axes.z_color
        Color(name='blue', hex='#0000ffff', opacity=255)

        Change the default color.

        >>> pv.global_theme.axes.z_color = 'purple'

        """
        return self._z_color

    @z_color.setter
    def z_color(self, color: ColorLike):
        self._z_color = Color(color)

    @property
    def box(self) -> bool:  # numpydoc ignore=RT01
        """Use a box axes orientation widget.

        If ``True``, Use the :func:`axes orientation box <pyvista.create_axes_orientation_box>`
        instead of the :class:`pyvista.AxesActor` as the orientation widget for plots.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.axes.box = True

        """
        return self._box

    @box.setter
    def box(self, box: bool):
        self._box = bool(box)

    @property
    def show(self) -> bool:  # numpydoc ignore=RT01
        """Show or hide the axes actor.

        Examples
        --------
        Hide the axes by default.

        >>> import pyvista as pv
        >>> pv.global_theme.axes.show = False

        """
        return self._show

    @show.setter
    def show(self, show: bool):
        self._show = bool(show)


class _Font(_ThemeConfig):
    """PyVista plotter font configuration.

    Examples
    --------
    Set the default font family to 'arial'.  Must be either
    'arial', 'courier', or 'times'.

    >>> import pyvista as pv
    >>> pv.global_theme.font.family = 'arial'

    Set the default font size to 20.

    >>> pv.global_theme.font.size = 20

    Set the default title size to 40

    >>> pv.global_theme.font.title_size = 40

    Set the default label size to 10

    >>> pv.global_theme.font.label_size = 10

    Set the default text color to 'grey'

    >>> pv.global_theme.font.color = 'grey'

    Set the string formatter used to format numerical data to '%.6e'

    >>> pv.global_theme.font.fmt = '%.6e'

    """

    __slots__ = ['_family', '_size', '_title_size', '_label_size', '_color', '_fmt']

    def __init__(self, **kwargs):
        self._family = 'arial'
        self._size = 12
        self._title_size = None
        self._label_size = None
        self._color = Color('white')
        self._fmt = None

        self._handle_kwargs(**kwargs)

    def __repr__(self):
        txt = ['']
        parm = {
            'Family': 'family',
            'Size': 'size',
            'Title size': 'title_size',
            'Label size': 'label_size',
            'Color': 'color',
            'Float format': 'fmt',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'    {name:<21}: {setting}')

        return '\n'.join(txt)

    @property
    def family(self) -> str:  # numpydoc ignore=RT01
        """Return or set the font family.

        Must be one of the following:

        * ``"arial"``
        * ``"courier"``
        * ``"times"``

        Examples
        --------
        Set the default global font family to 'courier'.

        >>> import pyvista as pv
        >>> pv.global_theme.font.family = 'courier'

        """
        return self._family

    @family.setter
    def family(self, family: str):
        parse_font_family(family)  # check valid font
        self._family = family

    @property
    def size(self) -> int:  # numpydoc ignore=RT01
        """Return or set the font size.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.font.size = 20

        """
        return self._size

    @size.setter
    def size(self, size: int):
        self._size = int(size)

    @property
    def title_size(self) -> int:  # numpydoc ignore=RT01
        """Return or set the title size.

        If ``None``, then VTK uses ``UnconstrainedFontSizeOn`` for titles.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.font.title_size = 20

        """
        return self._title_size  # type: ignore[return-value]

    @title_size.setter
    def title_size(self, title_size: int):
        if title_size is None:
            self._title_size = None
        else:
            self._title_size = int(title_size)

    @property
    def label_size(self) -> int:  # numpydoc ignore=RT01
        """Return or set the label size.

        If ``None``, then VTK uses ``UnconstrainedFontSizeOn`` for labels.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.font.label_size = 20

        """
        return self._label_size  # type: ignore[return-value]

    @label_size.setter
    def label_size(self, label_size: int):
        if label_size is None:
            self._label_size = None
        else:
            self._label_size = int(label_size)

    @property
    def color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the font color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.font.color = 'black'

        """
        return self._color

    @color.setter
    def color(self, color: ColorLike):
        self._color = Color(color)

    @property
    def fmt(self) -> str:  # numpydoc ignore=RT01
        """Return or set the string formatter used to format numerical data.

        Examples
        --------
        Set the string formatter used to format numerical data to '%.6e'.

        >>> import pyvista as pv
        >>> pv.global_theme.font.fmt = '%.6e'

        """
        return self._fmt  # type: ignore[return-value]

    @fmt.setter
    def fmt(self, fmt: str):
        self._fmt = fmt


class _SliderStyleConfig(_ThemeConfig):
    """PyVista configuration for a single slider style."""

    __slots__ = [
        '_name',
        '_slider_length',
        '_slider_width',
        '_slider_color',
        '_tube_width',
        '_tube_color',
        '_cap_opacity',
        '_cap_length',
        '_cap_width',
    ]

    _defaults: ClassVar[dict[str, str]] = {
        'default': 'default_theme',
        'classic': 'classic_theme',
        'modern': 'modern_theme',
    }

    def __init__(self, **kwargs):
        """Initialize the slider style configuration."""
        self._name = None
        self.slider_length = 0.05
        self.slider_width = 0.05
        self.slider_color = (0, 0, 0)
        self.tube_width = 0.04
        self.tube_color = (0, 0, 0)
        self.cap_opacity = 1.0
        self.cap_length = 0.01
        self.cap_width = 0.05

        self._handle_kwargs(**kwargs)

    @property
    def name(self) -> str:  # numpydoc ignore=RT01
        """Return the name of the slider style configuration."""
        return self._name  # type: ignore[return-value]

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def cap_width(self) -> float:  # numpydoc ignore=RT01
        """Return or set the cap width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.cap_width = 0.02

        """
        return self._cap_width  # type: ignore[return-value]

    @cap_width.setter
    def cap_width(self, cap_width: float):
        self._cap_width = float(cap_width)

    @property
    def cap_length(self) -> float:  # numpydoc ignore=RT01
        """Return or set the cap length.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.cap_length = 0.01

        """
        return self._cap_length  # type: ignore[return-value]

    @cap_length.setter
    def cap_length(self, cap_length: float):
        self._cap_length = float(cap_length)

    @property
    def cap_opacity(self) -> float:  # numpydoc ignore=RT01
        """Return or set the cap opacity.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.cap_opacity = 1.0

        """
        return self._cap_opacity  # type: ignore[return-value]

    @cap_opacity.setter
    def cap_opacity(self, cap_opacity: float):
        _check_range(cap_opacity, (0, 1), 'cap_opacity')
        self._cap_opacity = float(cap_opacity)

    @property
    def tube_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the tube color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.tube_color = 'black'

        """
        return self._tube_color  # type: ignore[return-value]

    @tube_color.setter
    def tube_color(self, tube_color: ColorLike):
        self._tube_color = Color(tube_color)

    @property
    def tube_width(self) -> float:  # numpydoc ignore=RT01
        """Return or set the tube_width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.tube_width = 0.005

        """
        return self._tube_width  # type: ignore[return-value]

    @tube_width.setter
    def tube_width(self, tube_width: float):
        self._tube_width = float(tube_width)

    @property
    def slider_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the slider color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.slider_color = 'grey'

        """
        return self._slider_color  # type: ignore[return-value]

    @slider_color.setter
    def slider_color(self, slider_color: ColorLike):
        self._slider_color = Color(slider_color)

    @property
    def slider_width(self) -> float:  # numpydoc ignore=RT01
        """Return or set the slider width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.slider_width = 0.04

        """
        return self._slider_width  # type: ignore[return-value]

    @slider_width.setter
    def slider_width(self, slider_width: float):
        self._slider_width = float(slider_width)

    @property
    def slider_length(self) -> float:  # numpydoc ignore=RT01
        """Return or set the slider_length.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.slider_length = 0.02

        """
        return self._slider_length  # type: ignore[return-value]

    @slider_length.setter
    def slider_length(self, slider_length: float):
        self._slider_length = float(slider_length)

    def __repr__(self):
        txt = ['']
        parm = {
            'Slider length': 'slider_length',
            'Slider width': 'slider_width',
            'Slider color': 'slider_color',
            'Tube width': 'tube_width',
            'Tube color': 'tube_color',
            'Cap opacity': 'cap_opacity',
            'Cap length': 'cap_length',
            'Cap width': 'cap_width',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'        {name:<17}: {setting}')
        return '\n'.join(txt)

    @classmethod
    def default_theme(cls):
        """Return the default slider theme.

        Examples
        --------
        The default slider configuration.

        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.default_theme()
        <BLANKLINE>
                Slider length    : 0.05
                Slider width     : 0.05
                Slider color     : Color(name='black', hex='#000000ff', opacity=255)
                Tube width       : 0.04
                Tube color       : Color(name='black', hex='#000000ff', opacity=255)
                Cap opacity      : 1.0
                Cap length       : 0.01
                Cap width        : 0.05

        """
        return cls()

    @classmethod
    def classic_theme(cls):
        """Return a classic slider theme.

        Examples
        --------
        The classic slider configuration.

        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.classic_theme()
        <BLANKLINE>
                Slider length    : 0.02
                Slider width     : 0.04
                Slider color     : Color(name='gray', hex='#808080ff', opacity=255)
                Tube width       : 0.005
                Tube color       : Color(name='white', hex='#ffffffff', opacity=255)
                Cap opacity      : 1.0
                Cap length       : 0.01
                Cap width        : 0.02

        """
        return cls.from_dict(
            {
                'slider_length': 0.02,
                'slider_width': 0.04,
                'slider_color': 'gray',
                'tube_width': 0.005,
                'tube_color': 'white',
                'cap_opacity': 1,
                'cap_length': 0.01,
                'cap_width': 0.02,
            }
        )

    @classmethod
    def modern_theme(cls):
        """Return a modern slider theme.

        Examples
        --------
        The modern slider configuration.

        >>> import pyvista as pv
        >>> pv.global_theme.slider_style.modern_theme()
        <BLANKLINE>
                Slider length    : 0.02
                Slider width     : 0.04
                Slider color     : Color(hex='#6e7175ff', opacity=255)
                Tube width       : 0.04
                Tube color       : Color(hex='#b2b3b5ff', opacity=255)
                Cap opacity      : 0.0
                Cap length       : 0.01
                Cap width        : 0.02

        """
        return cls.from_dict(
            {
                'slider_length': 0.02,
                'slider_width': 0.04,
                'slider_color': (110, 113, 117),
                'tube_width': 0.04,
                'tube_color': (178, 179, 181),
                'cap_opacity': 0,
                'cap_length': 0.01,
                'cap_width': 0.02,
            }
        )


class _TrameConfig(_ThemeConfig):
    """PyVista Trame configuration.

    Examples
    --------
    Set global trame view parameters.

    >>> import pyvista as pv
    >>> pv.global_theme.trame.interactive_ratio = 2
    >>> pv.global_theme.trame.still_ratio = 2

    """

    __slots__ = [
        '_interactive_ratio',
        '_still_ratio',
        '_jupyter_server_name',
        '_jupyter_server_port',
        '_server_proxy_enabled',
        '_server_proxy_prefix',
        '_default_mode',
        '_jupyter_extension_available',
        '_jupyter_extension_enabled',
    ]

    def __init__(self, **kwargs):
        self._interactive_ratio = 1
        self._still_ratio = 1
        self._jupyter_server_name = 'pyvista-jupyter'
        self._jupyter_server_port = 0
        self._server_proxy_enabled = 'PYVISTA_TRAME_SERVER_PROXY_PREFIX' in os.environ
        # default for ``jupyter-server-proxy``
        service = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '')
        prefix = os.environ.get('PYVISTA_TRAME_SERVER_PROXY_PREFIX', '/proxy/')
        if service and not prefix.startswith('http'):  # pragma: no cover
            self._server_proxy_prefix = os.path.join(service, prefix.lstrip('/'))  # noqa: PTH118
            self._server_proxy_enabled = True
        else:
            self._server_proxy_prefix = prefix
        self._jupyter_extension_available = 'TRAME_JUPYTER_WWW' in os.environ
        self._jupyter_extension_enabled = (
            self._jupyter_extension_available and not self._server_proxy_enabled
        )
        # if set, jupyter_mode overwrites defaults
        jupyter_mode = os.environ.get('PYVISTA_TRAME_JUPYTER_MODE')
        if jupyter_mode == 'extension' and self._jupyter_extension_available:  # pragma: no cover
            self._server_proxy_enabled = False
            self._jupyter_extension_enabled = True
        elif jupyter_mode == 'proxy' and self._server_proxy_enabled:  # pragma: no cover
            self._jupyter_extension_enabled = False
        elif jupyter_mode == 'native':  # pragma: no cover
            self._jupyter_extension_enabled = False
            self._server_proxy_enabled = False
        self._default_mode = 'trame'

        self._handle_kwargs(**kwargs)

    @property
    def interactive_ratio(self) -> float:  # numpydoc ignore=RT01
        """Return or set the interactive ratio for PyVista Trame views.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.trame.interactive_ratio = 2

        """
        return self._interactive_ratio

    @interactive_ratio.setter
    def interactive_ratio(self, interactive_ratio: float):
        self._interactive_ratio = interactive_ratio  # type: ignore[assignment]

    @property
    def still_ratio(self) -> float:  # numpydoc ignore=RT01
        """Return or set the still ratio for PyVista Trame views.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.trame.still_ratio = 2

        """
        return self._still_ratio

    @still_ratio.setter
    def still_ratio(self, still_ratio: float):
        self._still_ratio = still_ratio  # type: ignore[assignment]

    @property
    def jupyter_server_name(self):  # numpydoc ignore=RT01
        """Return or set the trame server name PyVista uses in Jupyter.

        This defaults to ``'pyvista-jupyter'``.

        This must be set before running :func:`pyvista.set_jupyter_backend`
        to ensure a server of this name is launched.

        Most users should not need to modify this.

        """
        return self._jupyter_server_name

    @jupyter_server_name.setter
    def jupyter_server_name(self, name: str):
        self._jupyter_server_name = name

    @property
    def jupyter_server_port(self) -> int:  # numpydoc ignore=RT01
        """Return or set the port for the Trame Jupyter server."""
        return self._jupyter_server_port

    @jupyter_server_port.setter
    def jupyter_server_port(self, port: int):
        self._jupyter_server_port = port

    @property
    def server_proxy_enabled(self) -> bool:  # numpydoc ignore=RT01
        """Return or set if use of relative URLs is enabled for the Jupyter interface."""
        return self._server_proxy_enabled

    @server_proxy_enabled.setter
    def server_proxy_enabled(self, enabled: bool):
        if enabled and self.jupyter_extension_enabled:
            warnings.warn('Enabling server_proxy will disable jupyter_extension')
            self._jupyter_extension_enabled = False

        self._server_proxy_enabled = bool(enabled)

    @property
    def server_proxy_prefix(self):  # numpydoc ignore=RT01
        """Return or set URL prefix when using relative URLs with the Jupyter interface."""
        return self._server_proxy_prefix

    @server_proxy_prefix.setter
    def server_proxy_prefix(self, prefix: str):
        self._server_proxy_prefix = prefix

    @property
    def jupyter_extension_available(self) -> bool:  # numpydoc ignore=RT01
        """Return whether the trame_jupyter_extension is detected."""
        return self._jupyter_extension_available

    @jupyter_extension_available.setter
    def jupyter_extension_available(self, _available: bool):
        warnings.warn(
            'The jupyter_extension_available flag is read only and is automatically detected.',
        )

    @property
    def jupyter_extension_enabled(self) -> bool:  # numpydoc ignore=RT01
        """Return or set whether to use the trame_jupyter_extension to communicate with clients."""
        return self._jupyter_extension_enabled

    @jupyter_extension_enabled.setter
    def jupyter_extension_enabled(self, enabled: bool):
        if enabled and not self.jupyter_extension_available:
            raise ValueError('The trame_jupyter_extension is not available')

        if enabled and self.server_proxy_enabled:
            warnings.warn('Enabling jupyter_extension will disable server_proxy')
            self._server_proxy_enabled = False

        self._jupyter_extension_enabled = bool(enabled)

    @property
    def default_mode(self):  # numpydoc ignore=RT01
        """Return or set the default mode of the Trame backend.

        * ``'trame'``: Uses a view that can switch between client and server
          rendering modes.
        * ``'server'``: Uses a view that is purely server rendering.
        * ``'client'``: Uses a view that is purely client rendering (generally
          safe without a virtual frame buffer)

        """
        return self._default_mode

    @default_mode.setter
    def default_mode(self, mode: str):
        self._default_mode = mode


class _CameraConfig(_ThemeConfig):
    """PyVista camera configuration.

    Examples
    --------
    Set global camera parameters.

    >>> import pyvista as pv
    >>> pv.global_theme.camera.position = [1.0, 1.0, 1.0]
    >>> pv.global_theme.camera.viewup = [0.0, 0.0, 1.0]

    """

    __slots__ = [
        '_position',
        '_viewup',
        '_parallel_projection',
        '_parallel_scale',
    ]

    def __init__(self):
        self._position = [1.0, 1.0, 1.0]
        self._viewup = [0.0, 0.0, 1.0]
        self._parallel_projection = False
        self._parallel_scale = 1.0

    @property
    def position(self) -> VectorLike[float]:  # numpydoc ignore=RT01
        """Return or set the camera position.

        Examples
        --------
        Set camera position.

        >>> import pyvista as pv
        >>> pv.global_theme.camera.position = [1.0, 1.0, 1.0]

        """
        return self._position

    @position.setter
    def position(self, position: VectorLike[float]):
        self._position = position  # type: ignore[assignment]

    @property
    def viewup(self) -> VectorLike[float]:  # numpydoc ignore=RT01
        """Return or set the camera viewup.

        Examples
        --------
        Set camera viewup.

        >>> import pyvista as pv
        >>> pv.global_theme.camera.viewup = [0.0, 0.0, 1.0]

        """
        return self._viewup

    @viewup.setter
    def viewup(self, viewup: VectorLike[float]):
        self._viewup = viewup  # type: ignore[assignment]

    @property
    def parallel_projection(self) -> bool:  # numpydoc ignore=RT01
        """Return or set parallel projection mode.

        Examples
        --------
        Enable parallel projection.

        >>> import pyvista as pv
        >>> pv.global_theme.camera.parallel_projection = True

        """
        return self._parallel_projection

    @parallel_projection.setter
    def parallel_projection(self, value: bool) -> None:
        self._parallel_projection = value

    @property
    def parallel_scale(self) -> bool:  # numpydoc ignore=RT01
        """Return or set parallel scale.

        Examples
        --------
        Set parallel scale.

        >>> import pyvista as pv
        >>> pv.global_theme.camera.parallel_scale = 2.0

        """
        return self._parallel_scale  # type: ignore[return-value]

    @parallel_scale.setter
    def parallel_scale(self, value: bool) -> None:
        self._parallel_scale = value


class Theme(_ThemeConfig):
    """Base VTK theme.

    Parameters
    ----------
    **kwargs : keyword args
        Keyword args that set attributes.

    Examples
    --------
    Change the global default background color to white.

    >>> import pyvista as pv
    >>> pv.global_theme.color = 'white'

    Show edges by default.

    >>> pv.global_theme.show_edges = True

    Create a new theme from the default theme and apply it globally.

    >>> from pyvista.plotting.themes import Theme
    >>> my_theme = Theme.document_theme()
    >>> my_theme.color = 'red'
    >>> my_theme.background = 'white'
    >>> pv.global_theme.load_theme(my_theme)

    Create a Theme through keyword args.

    >>> from pyvista.plotting.themes import Theme
    >>> my_theme = Theme(show_edges=True)
    >>> pv.global_theme.load_theme(my_theme)

    """

    __slots__ = [
        '_name',
        '_background',
        '_jupyter_backend',
        '_trame',
        '_full_screen',
        '_window_size',
        '_image_scale',
        '_camera',
        '_notebook',
        '_font',
        '_auto_close',
        '_cmap',
        '_color',
        '_color_cycler',
        '_above_range_color',
        '_below_range_color',
        '_nan_color',
        '_edge_color',
        '_line_width',
        '_point_size',
        '_outline_color',
        '_floor_color',
        '_colorbar_orientation',
        '_colorbar_horizontal',
        '_colorbar_vertical',
        '_show_scalar_bar',
        '_show_edges',
        '_show_vertices',
        '_lighting',
        '_interactive',
        '_render_points_as_spheres',
        '_render_lines_as_tubes',
        '_transparent_background',
        '_title',
        '_axes',
        '_multi_samples',
        '_multi_rendering_splitting_position',
        '_volume_mapper',
        '_smooth_shading',
        '_depth_peeling',
        '_silhouette',
        '_slider_style',
        '_return_cpos',
        '_hidden_line_removal',
        '_anti_aliasing',
        '_enable_camera_orientation_widget',
        '_split_sharp_edges',
        '_sharp_edges_feature_angle',
        '_before_close_callback',
        '_allow_empty_mesh',
        '_lighting_params',
        '_interpolate_before_map',
        '_opacity',
        '_before_close_callback',
        '_logo_file',
        '_edge_opacity',
    ]

    _defaults: ClassVar[dict[str, str]] = {
        'dark': 'dark_theme',
        'default': 'document_theme',
        'document': 'document_theme',
        'document_pro': 'document_pro_theme',
        'paraview': 'paraview_theme',
        'testing': 'testing_theme',
        'vtk': 'vtk_theme',
    }

    def __init__(self, **kwargs):
        """Initialize the theme."""
        self._name = 'default'
        self._background = Color([0.3, 0.3, 0.3])
        self._full_screen = False
        self._camera = _CameraConfig()

        self._notebook = None
        self._window_size = [1024, 768]
        self._image_scale = 1
        self._font = _Font()
        self._cmap = 'viridis'
        self._color = Color('white')
        self._color_cycler = None
        self._nan_color = Color('darkgray')
        self._above_range_color = Color('grey')
        self._below_range_color = Color('grey')
        self._edge_color = Color('black')
        self._line_width = 1.0
        self._point_size = 5.0
        self._outline_color = Color('white')
        self._floor_color = Color('gray')
        self._colorbar_orientation = 'horizontal'

        self._colorbar_horizontal = _ColorbarConfig()
        self._colorbar_horizontal.width = 0.6
        self._colorbar_horizontal.height = 0.08
        self._colorbar_horizontal.position_x = 0.35
        self._colorbar_horizontal.position_y = 0.05

        self._colorbar_vertical = _ColorbarConfig()
        self._colorbar_vertical.width = 0.08
        self._colorbar_vertical.height = 0.45
        self._colorbar_vertical.position_x = 0.9
        self._colorbar_vertical.position_y = 0.02

        self._show_scalar_bar = True
        self._show_edges = False
        self._show_vertices = False
        self._lighting = True
        self._interactive = False
        self._render_points_as_spheres = False
        self._render_lines_as_tubes = False
        self._transparent_background = False
        self._title = 'PyVista'
        self._axes = _AxesConfig()
        self._split_sharp_edges = False
        self._sharp_edges_feature_angle = 30.0
        self._before_close_callback = None
        self._allow_empty_mesh = False

        # Grab system flag for anti-aliasing
        # Use a default value of 8 multi-samples as this is default for VTK
        try:
            self._multi_samples = int(os.environ.get('PYVISTA_MULTI_SAMPLES', 8))
        except ValueError:  # pragma: no cover
            self._multi_samples = 8

        # Grab system flag for auto-closing
        self._auto_close = os.environ.get('PYVISTA_AUTO_CLOSE', '').lower() != 'false'

        self._jupyter_backend = os.environ.get('PYVISTA_JUPYTER_BACKEND', 'trame')
        self._trame = _TrameConfig()

        self._multi_rendering_splitting_position = None
        self._volume_mapper = 'fixed_point' if os.name == 'nt' else 'smart'
        self._smooth_shading = False
        self._depth_peeling = _DepthPeelingConfig()
        self._silhouette = _SilhouetteConfig()
        self._slider_style = _SliderStyleConfig()
        self._return_cpos = True
        self._hidden_line_removal = False
        self._anti_aliasing = 'msaa'
        self._enable_camera_orientation_widget = False

        self._lighting_params = _LightingConfig()
        self._interpolate_before_map = True
        self._opacity = 1.0
        self._edge_opacity = 1.0

        self._logo_file = None

        self._handle_kwargs(**kwargs)

    @classmethod
    def dark_theme(cls):
        """Dark mode theme.

        Black background, "viridis" colormap, tan meshes, white (hidden) edges.

        Returns
        -------
        Theme
            Dark theme.

        Examples
        --------
        Make the dark theme the global default.

        >>> import pyvista as pv
        >>> from pyvista import themes
        >>> pv.set_plot_theme(themes.Theme.dark_theme())

        Alternatively, set via a string.

        >>> pv.set_plot_theme('dark')

        """
        return cls.from_dict(
            {
                'name': 'dark',
                'background': 'black',
                'cmap': 'viridis',
                'font': {'color': 'white'},
                'show_edges': False,
                'color': 'lightblue',
                'outline_color': 'white',
                'edge_color': 'white',
                'axes': {
                    'x_color': 'tomato',
                    'y_color': 'seagreen',
                    'z_color': 'blue',
                },
            }
        )

    @classmethod
    def paraview_theme(cls):
        """ParaView-like theme.

        Returns
        -------
        Theme
            ParaView-like theme.

        Examples
        --------
        Make the paraview-like theme the global default.

        >>> import pyvista as pv
        >>> from pyvista import themes
        >>> pv.set_plot_theme(themes.Theme.paraview_theme())

        Alternatively, set via a string.

        >>> pv.set_plot_theme('paraview')

        """
        return cls.from_dict(
            {
                'name': 'paraview',
                'background': 'paraview',
                'cmap': 'coolwarm',
                'font': {
                    'family': 'arial',
                    'label_size': 16,
                    'color': 'white',
                },
                'show_edges': False,
                'color': 'white',
                'outline_color': 'white',
                'edge_color': 'black',
                'axes': {
                    'x_color': 'tomato',
                    'y_color': 'gold',
                    'z_color': 'green',
                },
            }
        )

    @classmethod
    def document_theme(cls):
        """Document theme well suited for papers and presentations.

        This theme uses:

        * A white background
        * Black fonts
        * The "viridis" colormap
        * disables edges for surface plots
        * Hidden edge removal

        Best used for presentations, papers, etc.

        Returns
        -------
        Theme
            Document theme.

        Examples
        --------
        Make the document theme the global default.

        >>> import pyvista as pv
        >>> from pyvista import themes
        >>> pv.set_plot_theme(themes.Theme.document_theme())

        Alternatively, set via a string.

        >>> pv.set_plot_theme('document')

        """
        return cls.from_dict(
            {
                'name': 'document',
                'background': 'white',
                'cmap': 'viridis',
                'font': {
                    'size': 18,
                    'title_size': 18,
                    'label_size': 18,
                    'color': 'black',
                },
                'show_edges': False,
                'color': 'lightblue',
                'outline_color': 'black',
                'edge_color': 'black',
                'axes': {
                    'x_color': 'tomato',
                    'y_color': 'seagreen',
                    'z_color': 'blue',
                },
            }
        )

    @classmethod
    def document_pro_theme(cls):
        """More professional document theme.

        This theme extends :func:`Theme.document_theme` with:

        * Default color cycling
        * Rendering points as spheres
        * MSAA anti aliassing
        * Depth peeling

        Returns
        -------
        Theme
            Document pro theme.

        """
        theme = cls.document_theme()
        theme.update_from_dict(
            {
                'anti_aliasing': 'ssaa',
                'color_cycler': get_cycler('default'),
                'render_points_as_spheres': True,
                'multi_samples': 8,
                'depth_peeling': {
                    'number_of_peels': 4,
                    'occlusion_ratio': 0.0,
                    'enabled': True,
                },
            }
        )
        return theme

    @classmethod
    def testing_theme(cls):
        """Low resolution testing theme, e.g. for ``pytest``.

        Necessary for image regression.  Xvfb doesn't support
        multi-sampling, it's disabled for consistency between desktops and
        remote testing.

        Also disables ``return_cpos`` to make it easier for us to write
        examples without returning camera positions.

        Returns
        -------
        Theme
            Testing theme.

        """
        return cls.from_dict(
            {
                'name': 'testing',
                'multi_samples': 1,
                'window_size': [400, 400],
                'axes': {'show': False},
                'return_cpos': False,
            }
        )

    @classmethod
    def vtk_theme(cls):
        """Theme with :class:`Theme` defaults similar to VTK.

        Same as ``Theme()``.

        Returns
        -------
        Theme
            VTK theme.

        """
        return cls()

    @property
    def hidden_line_removal(self) -> bool:  # numpydoc ignore=RT01
        """Return or set hidden line removal.

        Wireframe geometry will be drawn using hidden line removal if
        the rendering engine supports it.

        See Also
        --------
        pyvista.Plotter.enable_hidden_line_removal

        Examples
        --------
        Enable hidden line removal.

        >>> import pyvista as pv
        >>> pv.global_theme.hidden_line_removal = True
        >>> pv.global_theme.hidden_line_removal
        True

        """
        return self._hidden_line_removal

    @hidden_line_removal.setter
    def hidden_line_removal(self, value: bool):
        self._hidden_line_removal = value

    @property
    def interpolate_before_map(self) -> bool:  # numpydoc ignore=RT01
        """Return or set whether to interpolate colors before mapping.

        If the ``interpolate_before_map`` is turned off, the color
        mapping occurs at polygon points and colors are interpolated,
        which is generally less accurate whereas if the
        ``interpolate_before_map`` is on (the default), then the scalars
        will be interpolated across the topology of the dataset which is
        more accurate.

        See also :ref:`interpolate_before_mapping_example`.

        Examples
        --------
        Enable hidden line removal.

        >>> import pyvista as pv

        Load a cylinder which has cells with a wide spread

        >>> cyl = pv.Cylinder(direction=(0, 0, 1), height=2).elevation()

        Common display argument to make sure all else is constant

        >>> dargs = dict(
        ...     scalars='Elevation', cmap='rainbow', show_edges=True
        ... )

        >>> p = pv.Plotter(shape=(1, 2))
        >>> _ = p.add_mesh(
        ...     cyl,
        ...     interpolate_before_map=False,
        ...     scalar_bar_args={'title': 'Elevation - interpolated'},
        ...     **dargs
        ... )
        >>> p.subplot(0, 1)
        >>> _ = p.add_mesh(
        ...     cyl,
        ...     interpolate_before_map=True,
        ...     scalar_bar_args={'title': 'Elevation - interpolated'},
        ...     **dargs
        ... )
        >>> p.link_views()
        >>> p.camera_position = [
        ...     (-1.67, -5.10, 2.06),
        ...     (0.0, 0.0, 0.0),
        ...     (0.00, 0.37, 0.93),
        ... ]
        >>> p.show()  # doctest: +SKIP

        """
        return self._interpolate_before_map

    @interpolate_before_map.setter
    def interpolate_before_map(self, value: bool):
        self._interpolate_before_map = value

    @property
    def opacity(self) -> float:  # numpydoc ignore=RT01
        """Return or set the opacity.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.opacity = 0.5

        """
        return self._opacity

    @opacity.setter
    def opacity(self, opacity: float):
        _check_range(opacity, (0, 1), 'opacity')
        self._opacity = float(opacity)

    @property
    def edge_opacity(self) -> float:  # numpydoc ignore=RT01
        """Return or set the edges opacity.

        .. note::
            `edge_opacity` uses ``SetEdgeOpacity`` as the underlying method which
            requires VTK version 9.3 or higher. If ``SetEdgeOpacity`` is not
            available, `edge_opacity` is set to 1.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.edge_opacity = 0.5

        """
        return self._edge_opacity

    @edge_opacity.setter
    def edge_opacity(self, edge_opacity: float):
        _check_range(edge_opacity, (0, 1), 'edge_opacity')
        self._edge_opacity = float(edge_opacity)

    @property
    def above_range_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default above range color.

        Examples
        --------
        Set the above range color to red.

        >>> import pyvista as pv
        >>> pv.global_theme.above_range_color = 'r'
        >>> pv.global_theme.above_range_color
        Color(name='red', hex='#ff0000ff', opacity=255)

        """
        return self._above_range_color

    @above_range_color.setter
    def above_range_color(self, value: ColorLike):
        self._above_range_color = Color(value)

    @property
    def below_range_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default below range color.

        Examples
        --------
        Set the below range color to blue.

        >>> import pyvista as pv
        >>> pv.global_theme.below_range_color = 'b'
        >>> pv.global_theme.below_range_color
        Color(name='blue', hex='#0000ffff', opacity=255)

        """
        return self._below_range_color

    @below_range_color.setter
    def below_range_color(self, value: ColorLike):
        self._below_range_color = Color(value)

    @property
    def return_cpos(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default behavior of returning the camera position.

        Examples
        --------
        Disable returning camera position by ``show`` and ``plot`` methods.

        >>> import pyvista as pv
        >>> pv.global_theme.return_cpos = False

        """
        return self._return_cpos

    @return_cpos.setter
    def return_cpos(self, value: bool):
        self._return_cpos = value

    @property
    def background(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default background color of pyvista plots.

        Examples
        --------
        Set the default global background of all plots to white.

        >>> import pyvista as pv
        >>> pv.global_theme.background = 'white'

        """
        return self._background

    @background.setter
    def background(self, new_background: ColorLike) -> None:
        self._background = Color(new_background)

    @property
    def jupyter_backend(self) -> str:  # numpydoc ignore=RT01
        """Return or set the jupyter notebook plotting backend.

        Jupyter backend to use when plotting.  Must be one of the
        following:

        * ``'static'`` : Display a single static image within the
          Jupyterlab environment.  Still requires that a virtual
          framebuffer be set up when displaying on a headless server,
          but does not require any additional modules to be installed.

        * ``'client'`` : Export/serialize the scene graph to be rendered
          with VTK.js client-side through ``trame``. Requires ``trame``
          and ``jupyter-server-proxy`` to be installed.

        * ``'server'``: Render remotely and stream the resulting VTK
          images back to the client using ``trame``. This replaces the
          ``'ipyvtklink'`` backend with better performance.
          Supports the most VTK features, but suffers from minor lag due
          to remote rendering. Requires that a virtual framebuffer be set
          up when displaying on a headless server. Must have at least ``trame``
          and ``jupyter-server-proxy`` installed for cloud/remote Jupyter
          instances. This mode is also aliased by ``'trame'``.

        * ``'trame'``: The full Trame-based backend that combines both
          ``'server'`` and ``'client'`` into one backend. This requires a
          virtual frame buffer.

        * ``'html'``: The ``'client'`` backend, but able to be embedded.

        * ``'none'`` : Do not display any plots within jupyterlab,
          instead display using dedicated VTK render windows.  This
          will generate nothing on headless servers even with a
          virtual framebuffer.

        Examples
        --------
        Just show static images.

        >>> pv.set_jupyter_backend('static')  # doctest:+SKIP

        Disable all plotting within JupyterLab and display using a
        standard desktop VTK render window.

        >>> pv.set_jupyter_backend(None)  # doctest:+SKIP

        """
        return self._jupyter_backend

    @jupyter_backend.setter
    def jupyter_backend(self, backend: str):
        from pyvista.jupyter import _validate_jupyter_backend

        self._jupyter_backend = _validate_jupyter_backend(backend)

    @property
    def trame(self) -> _TrameConfig:  # numpydoc ignore=RT01
        """Return or set the default trame parameters."""
        return self._trame

    @trame.setter
    def trame(self, config: _TrameConfig):
        if not isinstance(config, _TrameConfig):
            raise TypeError('Configuration type must be `_TrameConfig`.')
        self._trame = config

    @property
    def auto_close(self) -> bool:  # numpydoc ignore=RT01
        """Automatically close the figures when finished plotting.

        .. DANGER::
           Set to ``False`` with extreme caution.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.auto_close = False

        """
        return self._auto_close

    @auto_close.setter
    def auto_close(self, value: bool):
        self._auto_close = value

    @property
    def full_screen(self) -> bool:  # numpydoc ignore=RT01
        """Return if figures are shown in full screen.

        Examples
        --------
        Set windows to be full screen by default.

        >>> import pyvista as pv
        >>> pv.global_theme.full_screen = True

        """
        return self._full_screen

    @full_screen.setter
    def full_screen(self, value: bool):
        self._full_screen = value

    @property
    def enable_camera_orientation_widget(self) -> bool:  # numpydoc ignore=RT01
        """Enable the camera orientation widget in all plotters.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.enable_camera_orientation_widget = True
        >>> pv.global_theme.enable_camera_orientation_widget
        True

        """
        return self._enable_camera_orientation_widget

    @enable_camera_orientation_widget.setter
    def enable_camera_orientation_widget(self, value: bool):
        self._enable_camera_orientation_widget = value

    @property
    def camera(self):  # numpydoc ignore=RT01
        """Return or set the default camera position.

        Examples
        --------
        Set both the position and viewup of the camera.

        >>> import pyvista as pv
        >>> pv.global_theme.camera.position = [1.0, 1.0, 1.0]
        >>> pv.global_theme.camera.viewup = [0.0, 0.0, 1.0]

        """
        return self._camera

    @camera.setter
    def camera(self, camera):
        if isinstance(camera, dict):
            self._camera = _CameraConfig.from_dict(camera)
        elif isinstance(camera, _CameraConfig):
            self._camera = camera
        else:
            raise TypeError(
                f'camera value must either be a `dict` or a `_CameraConfig`, got {type(camera)}',
            )

    @property
    def notebook(self) -> bool | None:  # numpydoc ignore=RT01
        """Return or set the state of notebook plotting.

        Setting this to ``True`` always enables notebook plotting,
        while setting it to ``False`` disables plotting even when
        plotting within a jupyter notebook and plots externally.

        Examples
        --------
        Disable all jupyter notebook plotting.

        >>> import pyvista as pv
        >>> pv.global_theme.notebook = False

        """
        return self._notebook

    @notebook.setter
    def notebook(self, value: bool | None):
        self._notebook = value

    @property
    def window_size(self) -> list[int]:  # numpydoc ignore=RT01
        """Return or set the default render window size.

        Examples
        --------
        Set window size to ``[400, 400]``.

        >>> import pyvista as pv
        >>> pv.global_theme.window_size = [400, 400]

        """
        return self._window_size

    @window_size.setter
    def window_size(self, window_size: list[int]):
        if len(window_size) != 2:
            raise ValueError('Expected a length 2 iterable for ``window_size``.')

        # ensure positive size
        if window_size[0] < 0 or window_size[1] < 0:
            raise ValueError('Window size must be a positive value.')

        self._window_size = window_size

    @property
    def image_scale(self) -> int:  # numpydoc ignore=RT01
        """Return or set the default image scale factor."""
        return self._image_scale

    @image_scale.setter
    def image_scale(self, value: int):
        value = int(value)
        if value < 1:
            raise ValueError('Scale factor must be a positive integer.')
        self._image_scale = int(value)

    @property
    def font(self) -> _Font:  # numpydoc ignore=RT01
        """Return or set the default font size, family, and/or color.

        Examples
        --------
        Set the default font family to 'arial'.  Must be either
        'arial', 'courier', or 'times'.

        >>> import pyvista as pv
        >>> pv.global_theme.font.family = 'arial'

        Set the default font size to 20.

        >>> pv.global_theme.font.size = 20

        Set the default title size to 40.

        >>> pv.global_theme.font.title_size = 40

        Set the default label size to 10.

        >>> pv.global_theme.font.label_size = 10

        Set the default text color to 'grey'.

        >>> pv.global_theme.font.color = 'grey'

        String formatter used to format numerical data to '%.6e'.

        >>> pv.global_theme.font.fmt = '%.6e'

        """
        return self._font

    @font.setter
    def font(self, config: _Font):
        if not isinstance(config, _Font):
            raise TypeError('Configuration type must be `_Font`.')
        self._font = config

    @property
    def cmap(self):  # numpydoc ignore=RT01
        """Return or set the default colormap of pyvista.

        See available Matplotlib colormaps.  Only applicable for when
        displaying ``scalars``.  If ``colorcet`` or ``cmocean`` are
        installed, their colormaps can be specified by name.

        You can also specify a list of colors to override an existing
        colormap with a custom one.  For example, to create a three
        color colormap you might specify ``['green', 'red', 'blue']``

        Examples
        --------
        Set the default global colormap to 'jet'.

        >>> import pyvista as pv
        >>> pv.global_theme.cmap = 'jet'

        """
        return self._cmap

    @cmap.setter
    def cmap(self, cmap):
        out = get_cmap_safe(cmap)  # for validation
        if out is None:
            raise ValueError(f'Invalid color map {cmap}')
        self._cmap = cmap

    @property
    def color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default color of meshes in pyvista.

        Used for meshes without ``scalars``.

        When setting, the value must be either a string, rgb list,
        or hex color string.  For example:

        * ``color='white'``
        * ``color='w'``
        * ``color=[1.0, 1.0, 1.0]``
        * ``color='#FFFFFF'``

        Examples
        --------
        Set the default mesh color to 'red'.

        >>> import pyvista as pv
        >>> pv.global_theme.color = 'red'

        """
        return self._color

    @color.setter
    def color(self, color: ColorLike):
        self._color = Color(color)

    @property
    def color_cycler(self):  # numpydoc ignore=RT01
        """Return or set the default color cycler used to color meshes.

        This color cycler is iterated over by each renderer to sequentially
        color datasets when displaying them through ``add_mesh``.

        When setting, the value must be either a list of color-like objects,
        or a cycler of color-like objects. If the value passed is a single
        string, it must be one of:

            * ``'default'`` - Use the default color cycler (matches matplotlib's default)
            * ``'matplotlib`` - Dynamically get matplotlib's current theme's color cycler.
            * ``'all'`` - Cycle through all of the available colors in ``pyvista.plotting.colors.hexcolors``

        Setting to ``None`` will disable the use of the color cycler.

        Examples
        --------
        Set the default color cycler to iterate through red, green, and blue.

        >>> import pyvista as pv
        >>> pv.global_theme.color_cycler = ['red', 'green', 'blue']

        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(pv.Cone(center=(0, 0, 0)))  # red
        >>> _ = pl.add_mesh(pv.Cube(center=(1, 0, 0)))  # green
        >>> _ = pl.add_mesh(pv.Sphere(center=(1, 1, 0)))  # blue
        >>> _ = pl.add_mesh(pv.Cylinder(center=(0, 1, 0)))  # red again
        >>> pl.show()  # doctest: +SKIP

        """
        return self._color_cycler

    @color_cycler.setter
    def color_cycler(self, color_cycler):
        self._color_cycler = get_cycler(color_cycler)

    @property
    def nan_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default NaN color.

        This color is used to plot all NaN values.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.nan_color = 'darkgray'

        """
        return self._nan_color

    @nan_color.setter
    def nan_color(self, nan_color: ColorLike):
        self._nan_color = Color(nan_color)

    @property
    def edge_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default edge color.

        Examples
        --------
        Set the global edge color to 'blue'.

        >>> import pyvista as pv
        >>> pv.global_theme.edge_color = 'blue'

        """
        return self._edge_color

    @edge_color.setter
    def edge_color(self, edge_color: ColorLike):
        self._edge_color = Color(edge_color)

    @property
    def line_width(self) -> float:  # numpydoc ignore=RT01
        """Return or set the default line width.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.line_width = 2.0

        """
        return self._line_width

    @line_width.setter
    def line_width(self, line_width: float):
        self._line_width = float(line_width)

    @property
    def point_size(self) -> float:  # numpydoc ignore=RT01
        """Return or set the default point size.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.line_width = 10.0

        """
        return self._point_size

    @point_size.setter
    def point_size(self, point_size: float):
        self._point_size = float(point_size)

    @property
    def outline_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default outline color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.outline_color = 'white'

        """
        return self._outline_color

    @outline_color.setter
    def outline_color(self, outline_color: ColorLike):
        self._outline_color = Color(outline_color)

    @property
    def floor_color(self) -> Color:  # numpydoc ignore=RT01
        """Return or set the default floor color.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.floor_color = 'black'

        """
        return self._floor_color

    @floor_color.setter
    def floor_color(self, floor_color: ColorLike):
        self._floor_color = Color(floor_color)

    @property
    def colorbar_orientation(self) -> str:  # numpydoc ignore=RT01
        """Return or set the default colorbar orientation.

        Must be either ``'vertical'`` or ``'horizontal'``.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_orientation = 'horizontal'

        """
        return self._colorbar_orientation

    @colorbar_orientation.setter
    def colorbar_orientation(self, colorbar_orientation: str):
        if colorbar_orientation not in ['vertical', 'horizontal']:
            raise ValueError('Colorbar orientation must be either "vertical" or "horizontal"')
        self._colorbar_orientation = colorbar_orientation

    @property
    def colorbar_horizontal(self) -> _ColorbarConfig:  # numpydoc ignore=RT01
        """Return or set the default parameters of a horizontal colorbar.

        Examples
        --------
        Set the default horizontal colorbar width to 0.6.

        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_horizontal.width = 0.6

        Set the default horizontal colorbar height to 0.2.

        >>> pv.global_theme.colorbar_horizontal.height = 0.2

        """
        return self._colorbar_horizontal

    @colorbar_horizontal.setter
    def colorbar_horizontal(self, config: _ColorbarConfig):
        if not isinstance(config, _ColorbarConfig):
            raise TypeError('Configuration type must be `_ColorbarConfig`.')
        self._colorbar_horizontal = config

    @property
    def colorbar_vertical(self) -> _ColorbarConfig:  # numpydoc ignore=RT01
        """Return or set the default parameters of a vertical colorbar.

        Examples
        --------
        Set the default colorbar width to 0.45.

        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_vertical.width = 0.45

        Set the default colorbar height to 0.8.

        >>> import pyvista as pv
        >>> pv.global_theme.colorbar_vertical.height = 0.8

        """
        return self._colorbar_vertical

    @colorbar_vertical.setter
    def colorbar_vertical(self, config: _ColorbarConfig):
        if not isinstance(config, _ColorbarConfig):
            raise TypeError('Configuration type must be `_ColorbarConfig`.')
        self._colorbar_vertical = config

    @property
    def show_scalar_bar(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default color bar visibility.

        Examples
        --------
        Show the scalar bar by default when scalars are available.

        >>> import pyvista as pv
        >>> pv.global_theme.show_scalar_bar = True

        """
        return self._show_scalar_bar

    @show_scalar_bar.setter
    def show_scalar_bar(self, show_scalar_bar: bool):
        self._show_scalar_bar = bool(show_scalar_bar)

    @property
    def show_edges(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default edge visibility.

        Examples
        --------
        Show edges globally by default.

        >>> import pyvista as pv
        >>> pv.global_theme.show_edges = True

        """
        return self._show_edges

    @show_edges.setter
    def show_edges(self, show_edges: bool):
        self._show_edges = bool(show_edges)

    @property
    def show_vertices(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default vertex visibility.

        Examples
        --------
        Show vertices globally by default.

        >>> import pyvista as pv
        >>> pv.global_theme.show_vertices = True

        """
        return self._show_vertices

    @show_vertices.setter
    def show_vertices(self, show_vertices: bool):
        self._show_vertices = bool(show_vertices)

    @property
    def lighting(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``lighting``.

        Examples
        --------
        Disable lighting globally.

        >>> import pyvista as pv
        >>> pv.global_theme.lighting = False

        """
        return self._lighting

    @lighting.setter
    def lighting(self, lighting: bool):
        self._lighting = lighting

    @property
    def interactive(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``interactive`` parameter.

        Examples
        --------
        Make all plots non-interactive globally.

        >>> import pyvista as pv
        >>> pv.global_theme.interactive = False

        """
        return self._interactive

    @interactive.setter
    def interactive(self, interactive: bool):
        self._interactive = bool(interactive)

    @property
    def render_points_as_spheres(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``render_points_as_spheres`` parameter.

        Examples
        --------
        Render points as spheres by default globally.

        >>> import pyvista as pv
        >>> pv.global_theme.render_points_as_spheres = True

        """
        return self._render_points_as_spheres

    @render_points_as_spheres.setter
    def render_points_as_spheres(self, render_points_as_spheres: bool):
        self._render_points_as_spheres = bool(render_points_as_spheres)

    @property
    def render_lines_as_tubes(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``render_lines_as_tubes`` parameter.

        Examples
        --------
        Render points as spheres by default globally.

        >>> import pyvista as pv
        >>> pv.global_theme.render_lines_as_tubes = True

        """
        return self._render_lines_as_tubes

    @render_lines_as_tubes.setter
    def render_lines_as_tubes(self, render_lines_as_tubes: bool):
        self._render_lines_as_tubes = bool(render_lines_as_tubes)

    @property
    def transparent_background(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``transparent_background`` parameter.

        Examples
        --------
        Set transparent_background globally to ``True``.

        >>> import pyvista as pv
        >>> pv.global_theme.transparent_background = True

        """
        return self._transparent_background

    @transparent_background.setter
    def transparent_background(self, transparent_background: bool):
        self._transparent_background = transparent_background

    @property
    def title(self) -> str:  # numpydoc ignore=RT01
        """Return or set the default ``title`` parameter.

        This is the VTK render window title.

        Examples
        --------
        Set title globally to 'plot'.

        >>> import pyvista as pv
        >>> pv.global_theme.title = 'plot'

        """
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title

    @property
    def anti_aliasing(self) -> str | None:  # numpydoc ignore=RT01
        """Enable or disable anti-aliasing.

        Should be either ``"ssaa"``, ``"msaa"``, ``"fxaa"``, or ``None``.

        Examples
        --------
        Use super-sampling anti-aliasing in the global theme.

        >>> import pyvista as pv
        >>> pv.global_theme.anti_aliasing = 'ssaa'
        >>> pv.global_theme.anti_aliasing
        'ssaa'

        Disable anti-aliasing in the global theme.

        >>> import pyvista as pv
        >>> pv.global_theme.anti_aliasing = None

        See :ref:`anti_aliasing_example` for more information regarding
        anti-aliasing.

        """
        return self._anti_aliasing

    @anti_aliasing.setter
    def anti_aliasing(self, anti_aliasing: str | None):
        if isinstance(anti_aliasing, str):
            if anti_aliasing not in ['ssaa', 'msaa', 'fxaa']:
                raise ValueError('anti_aliasing must be either "ssaa", "msaa", or "fxaa"')
        elif anti_aliasing is not None:
            raise TypeError('anti_aliasing must be either "ssaa", "msaa", "fxaa", or None')

        self._anti_aliasing = anti_aliasing  # type: ignore[assignment]

    @property
    def multi_samples(self) -> int:  # numpydoc ignore=RT01
        """Return or set the default ``multi_samples`` parameter.

        Set the number of multisamples to used with hardware anti_aliasing. This
        is only used when :attr:`anti_aliasing <Theme.anti_aliasing>` is
        set to ``"msaa"``.

        Examples
        --------
        Set the default number of multisamples to 2 and enable ``"msaa"``

        >>> import pyvista as pv
        >>> pv.global_theme.anti_aliasing = 'msaa'
        >>> pv.global_theme.multi_samples = 2

        """
        return self._multi_samples

    @multi_samples.setter
    def multi_samples(self, multi_samples: int):
        self._multi_samples = int(multi_samples)

    @property
    def multi_rendering_splitting_position(self) -> float:  # numpydoc ignore=RT01
        """Return or set the default ``multi_rendering_splitting_position`` parameter.

        Examples
        --------
        Set multi_rendering_splitting_position globally to 0.5 (the
        middle of the window).

        >>> import pyvista as pv
        >>> pv.global_theme.multi_rendering_splitting_position = 0.5

        """
        return self._multi_rendering_splitting_position  # type: ignore[return-value]

    @multi_rendering_splitting_position.setter
    def multi_rendering_splitting_position(
        self,
        multi_rendering_splitting_position: float,
    ):
        self._multi_rendering_splitting_position = multi_rendering_splitting_position

    @property
    def volume_mapper(self) -> str:  # numpydoc ignore=RT01
        """Return or set the default ``volume_mapper`` parameter.

        Must be one of the following strings, which are mapped to the
        following VTK volume mappers.

        * ``'fixed_point'`` : ``vtk.vtkFixedPointVolumeRayCastMapper``
        * ``'gpu'`` : ``vtk.vtkGPUVolumeRayCastMapper``
        * ``'open_gl'`` : ``vtk.vtkOpenGLGPUVolumeRayCastMapper``
        * ``'smart'`` : ``vtk.vtkSmartVolumeMapper``

        Examples
        --------
        Set default volume mapper globally to 'gpu'.

        >>> import pyvista as pv
        >>> pv.global_theme.volume_mapper = 'gpu'

        """
        return self._volume_mapper

    @volume_mapper.setter
    def volume_mapper(self, mapper: str):
        mappers = ['fixed_point', 'gpu', 'open_gl', 'smart']
        if mapper not in mappers:
            raise ValueError(
                f"Mapper ({mapper}) unknown. Available volume mappers "
                f"include:\n {', '.join(mappers)}",
            )

        self._volume_mapper = mapper

    @property
    def smooth_shading(self) -> bool:  # numpydoc ignore=RT01
        """Return or set the default ``smooth_shading`` parameter.

        Examples
        --------
        Set the global smooth_shading parameter default to ``True``.

        >>> import pyvista as pv
        >>> pv.global_theme.smooth_shading = True

        """
        return self._smooth_shading

    @smooth_shading.setter
    def smooth_shading(self, smooth_shading: bool):
        self._smooth_shading = bool(smooth_shading)

    @property
    def depth_peeling(self) -> _DepthPeelingConfig:  # numpydoc ignore=RT01
        """Return or set the default depth peeling parameters.

        Examples
        --------
        Set the global depth_peeling parameter default to be enabled
        with 8 peels.

        >>> import pyvista as pv
        >>> pv.global_theme.depth_peeling.number_of_peels = 8
        >>> pv.global_theme.depth_peeling.occlusion_ratio = 0.0
        >>> pv.global_theme.depth_peeling.enabled = True

        """
        return self._depth_peeling

    @depth_peeling.setter
    def depth_peeling(self, config: _DepthPeelingConfig):
        if not isinstance(config, _DepthPeelingConfig):
            raise TypeError('Configuration type must be `_DepthPeelingConfig`.')
        self._depth_peeling = config

    @property
    def silhouette(self) -> _SilhouetteConfig:  # numpydoc ignore=RT01
        """Return or set the default ``silhouette`` configuration.

        Examples
        --------
        Set parameters of the silhouette.

        >>> import pyvista as pv
        >>> pv.global_theme.silhouette.color = 'grey'
        >>> pv.global_theme.silhouette.line_width = 2.0
        >>> pv.global_theme.silhouette.feature_angle = 20

        """
        return self._silhouette

    @silhouette.setter
    def silhouette(self, config: _SilhouetteConfig):
        if not isinstance(config, _SilhouetteConfig):
            raise TypeError('Configuration type must be `_SilhouetteConfig`')
        self._silhouette = config

    @property
    def slider_style(self) -> _SliderStyleConfig:  # numpydoc ignore=RT01
        """Return the default slider style configurations."""
        return self._slider_style

    @slider_style.setter
    def slider_style(self, config: _SliderStyleConfig):
        if not isinstance(config, _SliderStyleConfig):
            raise TypeError('Configuration type must be `_SliderStyleConfig`.')
        self._slider_style = config

    @property
    def axes(self) -> _AxesConfig:  # numpydoc ignore=RT01
        """Return or set the default ``axes`` configuration.

        Examples
        --------
        Set the x-axis color to black.

        >>> import pyvista as pv
        >>> pv.global_theme.axes.x_color = 'black'

        Show the axes orientation widget by default.

        >>> pv.global_theme.axes.show = True

        Use the :func:`axes orientation box <pyvista.create_axes_orientation_box>` as the orientation widget.

        >>> pv.global_theme.axes.box = True

        """
        return self._axes

    @axes.setter
    def axes(self, config: _AxesConfig):
        if not isinstance(config, _AxesConfig):
            raise TypeError('Configuration type must be `_AxesConfig`.')
        self._axes = config

    @property
    def before_close_callback(self) -> Callable[[Plotter], None]:  # numpydoc ignore=RT01
        """Return the default before_close_callback function for Plotter."""
        return self._before_close_callback  # type: ignore[return-value]

    @before_close_callback.setter
    def before_close_callback(
        self,
        value: Callable[[Plotter], None],
    ):
        self._before_close_callback = value

    @property
    def allow_empty_mesh(self) -> bool:  # numpydoc ignore=RT01
        """Return or set whether to allow plotting empty meshes.

        Examples
        --------
        Enable plotting of empty meshes.

        >>> import pyvista as pv
        >>> pv.global_theme.allow_empty_mesh = True

        Now add an empty mesh to a plotter

        >>> pl = pv.Plotter()
        >>> _ = pl.add_mesh(pv.PolyData())
        >>> pl.show()  # doctest: +SKIP

        """
        return self._allow_empty_mesh

    @allow_empty_mesh.setter
    def allow_empty_mesh(self, allow_empty_mesh: bool):
        self._allow_empty_mesh = bool(allow_empty_mesh)

    def restore_defaults(self):
        """Restore the theme to PyVista default theme.

        Examples
        --------
        >>> import pyvista as pv
        >>> pv.global_theme.restore_defaults()

        """
        self.load_theme(self.from_default('default'))

    def __repr__(self):
        """User friendly representation of the current theme."""
        txt = [f'{self.name.capitalize()} Theme']
        txt.append('-' * len(txt[0]))
        parm = {
            'Background': 'background',
            'Jupyter backend': 'jupyter_backend',
            'Full screen': 'full_screen',
            'Window size': 'window_size',
            'Camera': 'camera',
            'Notebook': 'notebook',
            'Font': 'font',
            'Auto close': 'auto_close',
            'Colormap': 'cmap',
            'Color': 'color',
            'Color Cycler': 'color_cycler',
            'NaN color': 'nan_color',
            'Edge color': 'edge_color',
            'Outline color': 'outline_color',
            'Floor color': 'floor_color',
            'Colorbar orientation': 'colorbar_orientation',
            'Colorbar - horizontal': 'colorbar_horizontal',
            'Colorbar - vertical': 'colorbar_vertical',
            'Show scalar bar': 'show_scalar_bar',
            'Show edges': 'show_edges',
            'Lighting': 'lighting',
            'Interactive': 'interactive',
            'Render points as spheres': 'render_points_as_spheres',
            'Transparent Background': 'transparent_background',
            'Title': 'title',
            'Axes': 'axes',
            'Multi-samples': 'multi_samples',
            'Multi-renderer Split Pos': 'multi_rendering_splitting_position',
            'Volume mapper': 'volume_mapper',
            'Smooth shading': 'smooth_shading',
            'Depth peeling': 'depth_peeling',
            'Silhouette': 'silhouette',
            'Slider Style': 'slider_style',
            'Return Camera Position': 'return_cpos',
            'Hidden Line Removal': 'hidden_line_removal',
            'Anti-Aliasing': '_anti_aliasing',
            'Split sharp edges': '_split_sharp_edges',
            'Sharp edges feat. angle': '_sharp_edges_feature_angle',
            'Before close callback': '_before_close_callback',
        }
        for name, attr in parm.items():
            setting = getattr(self, attr)
            txt.append(f'{name:<25}: {setting}')

        return '\n'.join(txt)

    @property
    def name(self) -> str:  # numpydoc ignore=RT01
        """Return or set the name of the theme."""
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    def load_theme(self, theme: str | Theme) -> None:
        """Overwrite the current theme with a theme.

        Parameters
        ----------
        theme : pyvista.plotting.themes.Theme
            Theme to use to overwrite this theme.

        Examples
        --------
        Create a custom theme from the default theme and load it into
        the global theme of pyvista.

        >>> import pyvista as pv
        >>> from pyvista.plotting.themes import Theme
        >>> my_theme = Theme.document_theme()
        >>> my_theme.font.size = 20
        >>> my_theme.font.title_size = 40
        >>> my_theme.cmap = 'jet'
        >>> pv.global_theme.load_theme(my_theme)
        >>> pv.global_theme.font.size
        20

        Create a custom theme from the dark theme and load it into
        pyvista.

        >>> my_theme = Theme.dark_theme()
        >>> my_theme.show_edges = True
        >>> pv.global_theme.load_theme(my_theme)
        >>> pv.global_theme.show_edges
        True

        """
        if isinstance(theme, str):
            theme = load_theme(theme)

        if not isinstance(theme, Theme):
            raise TypeError(
                '``theme`` must be a pyvista theme like ``pyvista.plotting.themes.Theme``.',
            )

        for attr_name in Theme.__slots__:
            setattr(self, attr_name, getattr(theme, attr_name))

    def save(self, filename: str) -> None:
        """Serialize this theme to a json file.

        ``before_close_callback`` is non-serializable and is omitted.

        Parameters
        ----------
        filename : str
            Path to save the theme to.  Should end in ``'.json'``.

        Examples
        --------
        Export and then load back in a theme.

        >>> import pyvista as pv
        >>> theme = pv.themes.Theme.document_theme()
        >>> theme.background = 'white'
        >>> theme.save('my_theme.json')  # doctest:+SKIP
        >>> loaded_theme = pv.load_theme('my_theme.json')  # doctest:+SKIP

        """
        data = self.to_dict()
        # functions are not serializable
        del data['before_close_callback']
        with Path(filename).open('w') as f:
            json.dump(data, f)

    @property
    def split_sharp_edges(self) -> bool:  # numpydoc ignore=RT01
        """Set or return splitting sharp edges.

        See :ref:`shading_example` for an example showing split sharp edges.

        Examples
        --------
        Enable the splitting of sharp edges globally.

        >>> import pyvista as pv
        >>> pv.global_theme.split_sharp_edges = True
        >>> pv.global_theme.split_sharp_edges
        True

        Disable the splitting of sharp edges globally.

        >>> import pyvista as pv
        >>> pv.global_theme.split_sharp_edges = False
        >>> pv.global_theme.split_sharp_edges
        False

        """
        return self._split_sharp_edges

    @split_sharp_edges.setter
    def split_sharp_edges(self, value: bool):
        self._split_sharp_edges = value

    @property
    def sharp_edges_feature_angle(self) -> float:  # numpydoc ignore=RT01
        """Set or return the angle of the sharp edges feature angle.

        See :ref:`shading_example` for an example showing split sharp edges.

        Examples
        --------
        Change the sharp edges feature angle to 45 degrees.

        >>> import pyvista as pv
        >>> pv.global_theme.sharp_edges_feature_angle = 45.0
        >>> pv.global_theme.sharp_edges_feature_angle
        45.0

        """
        return self._sharp_edges_feature_angle

    @sharp_edges_feature_angle.setter
    def sharp_edges_feature_angle(self, value: float):
        self._sharp_edges_feature_angle = float(value)

    @property
    def lighting_params(self) -> _LightingConfig:  # numpydoc ignore=RT01
        """Return or set the default lighting configuration."""
        return self._lighting_params

    @lighting_params.setter
    def lighting_params(self, config: _LightingConfig):
        if not isinstance(config, _LightingConfig):
            raise TypeError('Configuration type must be `_LightingConfig`.')
        self._lighting_params = config

    @property
    def logo_file(self) -> str | None:  # numpydoc ignore=RT01
        """Return or set the logo file.

        .. note::

            :func:`pyvista.Plotter.add_logo_widget` will default to
            PyVista's logo if this is unset.

        Examples
        --------
        Set the logo file to a custom logo.

        >>> import pyvista as pv
        >>> from pyvista import examples
        >>> logo_file = examples.download_file('vtk.png')
        >>> pv.global_theme.logo_file = logo_file

        Now the logo will be used by default for :func:`pyvista.Plotter.add_logo_widget`.

        >>> pl = pv.Plotter()
        >>> _ = pl.add_logo_widget()
        >>> _ = pl.add_mesh(pv.Sphere(), show_edges=True)
        >>> pl.show()

        """
        return self._logo_file

    @logo_file.setter
    def logo_file(self, logo_file: str | pathlib.Path | None):
        if logo_file is None:
            path = None
        else:
            if not pathlib.Path(logo_file).exists():
                raise FileNotFoundError(f'Logo file ({logo_file}) not found.')
            path = str(logo_file)
        self._logo_file = path


# deprecated v0.44.0, make error in v0.48.0, remove in v0.49.0
def _deprecated_subtheme_msg(class_name, obj_name):
    return f"""{class_name} is deprecated.
    Use Theme.{obj_name}() instead of {class_name}()
    """


class DarkTheme(Theme):
    """Dark mode theme.

    Black background, "viridis" colormap, tan meshes, white (hidden) edges.

    Examples
    --------
    Make the dark theme the global default.

    >>> import pyvista as pv
    >>> from pyvista import themes
    >>> pv.set_plot_theme(themes.DarkTheme())  # doctest:+SKIP

    Alternatively, set via a string.

    >>> pv.set_plot_theme('dark')

    """

    def __init__(self):
        """Initialize the theme."""
        super().__init__()
        warnings.warn(
            _deprecated_subtheme_msg('DarkTheme', 'dark_theme'), PyVistaDeprecationWarning
        )
        self.name = 'dark'
        self.background = 'black'  # type: ignore[assignment]
        self.cmap = 'viridis'
        self.font.color = 'white'  # type: ignore[assignment]
        self.show_edges = False
        self.color = 'lightblue'  # type: ignore[assignment]
        self.outline_color = 'white'  # type: ignore[assignment]
        self.edge_color = 'white'  # type: ignore[assignment]
        self.axes.x_color = 'tomato'  # type: ignore[assignment]
        self.axes.y_color = 'seagreen'  # type: ignore[assignment]
        self.axes.z_color = 'blue'  # type: ignore[assignment]


class ParaViewTheme(Theme):
    """A paraview-like theme.

    Examples
    --------
    Make the paraview-like theme the global default.

    >>> import pyvista as pv
    >>> from pyvista import themes
    >>> pv.set_plot_theme(themes.ParaViewTheme())  # doctest:+SKIP

    Alternatively, set via a string.

    >>> pv.set_plot_theme('paraview')

    """

    def __init__(self):
        """Initialize theme."""
        super().__init__()
        warnings.warn(
            _deprecated_subtheme_msg('ParaViewTheme', 'paraview_theme'), PyVistaDeprecationWarning
        )
        self.name = 'paraview'
        self.background = 'paraview'  # type: ignore[assignment]
        self.cmap = 'coolwarm'
        self.font.family = 'arial'
        self.font.label_size = 16
        self.font.color = 'white'  # type: ignore[assignment]
        self.show_edges = False
        self.color = 'white'  # type: ignore[assignment]
        self.outline_color = 'white'  # type: ignore[assignment]
        self.edge_color = 'black'  # type: ignore[assignment]
        self.axes.x_color = 'tomato'  # type: ignore[assignment]
        self.axes.y_color = 'gold'  # type: ignore[assignment]
        self.axes.z_color = 'green'  # type: ignore[assignment]


class DocumentTheme(Theme):
    """A document theme well suited for papers and presentations.

    This theme uses:

    * A white background
    * Black fonts
    * The "viridis" colormap
    * disables edges for surface plots
    * Hidden edge removal

    Best used for presentations, papers, etc.

    Examples
    --------
    Make the document theme the global default.

    >>> import pyvista as pv
    >>> from pyvista import themes
    >>> pv.set_plot_theme(themes.DocumentTheme())  # doctest:+SKIP

    Alternatively, set via a string.

    >>> pv.set_plot_theme('document')

    """

    def __init__(self):
        """Initialize the theme."""
        super().__init__()
        warnings.warn(
            _deprecated_subtheme_msg('DocumentTheme', 'document_theme'), PyVistaDeprecationWarning
        )
        self.name = 'document'
        self.background = 'white'  # type: ignore[assignment]
        self.cmap = 'viridis'
        self.font.size = 18
        self.font.title_size = 18
        self.font.label_size = 18
        self.font.color = 'black'  # type: ignore[assignment]
        self.show_edges = False
        self.color = 'lightblue'  # type: ignore[assignment]
        self.outline_color = 'black'  # type: ignore[assignment]
        self.edge_color = 'black'  # type: ignore[assignment]
        self.axes.x_color = 'tomato'  # type: ignore[assignment]
        self.axes.y_color = 'seagreen'  # type: ignore[assignment]
        self.axes.z_color = 'blue'  # type: ignore[assignment]


class DocumentProTheme(DocumentTheme):
    """A more professional document theme.

    This theme extends the base document theme with:

    * Default color cycling
    * Rendering points as spheres
    * MSAA anti aliassing
    * Depth peeling

    """

    def __init__(self):
        """Initialize the theme."""
        # This Theme subclasses from DocumentTheme, only give one warning
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore', 'DocumentTheme is deprecated.', PyVistaDeprecationWarning
            )
            super().__init__()

        warnings.warn(
            _deprecated_subtheme_msg('DocumentProTheme', 'document_pro_theme'),
            PyVistaDeprecationWarning,
        )
        self.anti_aliasing = 'ssaa'
        self.color_cycler = get_cycler('default')
        self.render_points_as_spheres = True
        self.multi_samples = 8
        self.depth_peeling.number_of_peels = 4
        self.depth_peeling.occlusion_ratio = 0.0
        self.depth_peeling.enabled = True


class _TestingTheme(Theme):
    """Low resolution testing theme for ``pytest``.

    Necessary for image regression.  Xvfb doesn't support
    multi-sampling, it's disabled for consistency between desktops and
    remote testing.

    Also disables ``return_cpos`` to make it easier for us to write
    examples without returning camera positions.

    """

    def __init__(self):
        super().__init__()
        warnings.warn(
            _deprecated_subtheme_msg('_TestingTheme', 'testing_theme'), PyVistaDeprecationWarning
        )
        self.name = 'testing'
        self.multi_samples = 1
        self.window_size = [400, 400]
        self.axes.show = False
        self.return_cpos = False
