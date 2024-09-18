"""Axes actor module."""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
import warnings

import pyvista
from pyvista.core.errors import PyVistaDeprecationWarning

from . import _vtk
from .actor_properties import ActorProperties


class AxesActor(_vtk.vtkAxesActor):
    """Axes actor wrapper for vtkAxesActor.

    Hybrid 2D/3D actor used to represent 3D axes in a scene. The user
    can define the geometry to use for the shaft or the tip, and the
    user can set the text for the three axes. To see full customization
    options, refer to `vtkAxesActor Details
    <https://vtk.org/doc/nightly/html/classvtkAxesActor.html#details>`_.

    Examples
    --------
    Customize the axis shaft color and shape.

    >>> import pyvista as pv

    >>> axes = pv.Axes()
    >>> axes.axes_actor.z_axis_shaft_properties.color = (0.0, 1.0, 1.0)
    >>> axes.axes_actor.shaft_type = axes.axes_actor.ShaftType.CYLINDER
    >>> pl = pv.Plotter()
    >>> _ = pl.add_actor(axes.axes_actor)
    >>> _ = pl.add_mesh(pv.Sphere())
    >>> pl.show()

    Or you can use this as a custom orientation widget with
    :func:`add_orientation_widget() <pyvista.Renderer.add_orientation_widget>`:

    >>> import pyvista as pv

    >>> axes = pv.Axes()
    >>> axes_actor = axes.axes_actor
    >>> axes.axes_actor.shaft_type = 0

    >>> axes_actor.x_axis_shaft_properties.color = (1.0, 1.0, 1.0)
    >>> axes_actor.y_axis_shaft_properties.color = (1.0, 1.0, 1.0)
    >>> axes_actor.z_axis_shaft_properties.color = (1.0, 1.0, 1.0)

    >>> axes_actor.x_label = 'U'
    >>> axes_actor.y_label = 'V'
    >>> axes_actor.z_label = 'W'

    >>> pl = pv.Plotter()
    >>> _ = pl.add_mesh(pv.Cone())
    >>> _ = pl.add_orientation_widget(
    ...     axes_actor,
    ...     viewport=(0, 0, 0.5, 0.5),
    ... )
    >>> pl.show()

    """

    class ShaftType(Enum):
        """Types of shaft shapes available."""

        CYLINDER = 0
        LINE = 1

    class TipType(Enum):
        """Types of tip shapes available."""

        CONE = 0
        SPHERE = 1

    def __init__(self):
        """Initialize actor."""
        super().__init__()

        self.x_axis_shaft_properties.color = pyvista.global_theme.axes.x_color.float_rgb
        self.x_axis_tip_properties.color = pyvista.global_theme.axes.x_color.float_rgb
        self.x_axis_shaft_properties.opacity = pyvista.global_theme.axes.x_color.float_rgba[3]
        self.x_axis_tip_properties.opacity = pyvista.global_theme.axes.x_color.float_rgba[3]
        self.x_axis_shaft_properties.lighting = pyvista.global_theme.lighting

        self.y_axis_shaft_properties.color = pyvista.global_theme.axes.y_color.float_rgb
        self.y_axis_tip_properties.color = pyvista.global_theme.axes.y_color.float_rgb
        self.y_axis_shaft_properties.opacity = pyvista.global_theme.axes.y_color.float_rgba[3]
        self.y_axis_tip_properties.opacity = pyvista.global_theme.axes.y_color.float_rgba[3]
        self.y_axis_shaft_properties.lighting = pyvista.global_theme.lighting

        self.z_axis_shaft_properties.color = pyvista.global_theme.axes.z_color.float_rgb
        self.z_axis_tip_properties.color = pyvista.global_theme.axes.z_color.float_rgb
        self.z_axis_shaft_properties.opacity = pyvista.global_theme.axes.z_color.float_rgba[3]
        self.z_axis_tip_properties.opacity = pyvista.global_theme.axes.z_color.float_rgba[3]
        self.z_axis_shaft_properties.lighting = pyvista.global_theme.lighting

    @property
    def visibility(self) -> bool:  # numpydoc ignore=RT01
        """Return or set AxesActor visibility.

        Examples
        --------
        Create an Axes object and then access the
        visibility attribute of its AxesActor.

        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.visibility
        True

        """
        return bool(self.GetVisibility())

    @visibility.setter
    def visibility(self, value: bool):  # numpydoc ignore=GL08
        self.SetVisibility(value)

    @property
    def total_length(self) -> tuple[float, float, float]:  # numpydoc ignore=RT01
        """Return or set the length of all axes.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.total_length
        (1.0, 1.0, 1.0)
        >>> axes.axes_actor.total_length = 1.2
        >>> axes.axes_actor.total_length
        (1.2, 1.2, 1.2)
        >>> axes.axes_actor.total_length = (1.0, 0.9, 0.5)
        >>> axes.axes_actor.total_length
        (1.0, 0.9, 0.5)

        """
        return self.GetTotalLength()

    @total_length.setter
    def total_length(self, length):  # numpydoc ignore=GL08
        if isinstance(length, Iterable):
            self.SetTotalLength(length[0], length[1], length[2])
        else:
            self.SetTotalLength(length, length, length)

    @property
    def shaft_length(self) -> tuple[float, float, float]:  # numpydoc ignore=RT01
        """Return or set the length of the axes shaft.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.shaft_length
        (0.8, 0.8, 0.8)
        >>> axes.axes_actor.shaft_length = 0.7
        >>> axes.axes_actor.shaft_length
        (0.7, 0.7, 0.7)
        >>> axes.axes_actor.shaft_length = (1.0, 0.9, 0.5)
        >>> axes.axes_actor.shaft_length
        (1.0, 0.9, 0.5)

        """
        return self.GetNormalizedShaftLength()

    @shaft_length.setter
    def shaft_length(self, length):  # numpydoc ignore=GL08
        if isinstance(length, Iterable):
            self.SetNormalizedShaftLength(length[0], length[1], length[2])
        else:
            self.SetNormalizedShaftLength(length, length, length)

    @property
    def tip_length(self) -> tuple[float, float, float]:  # numpydoc ignore=RT01
        """Return or set the length of the tip.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.tip_length
        (0.2, 0.2, 0.2)
        >>> axes.axes_actor.tip_length = 0.3
        >>> axes.axes_actor.tip_length
        (0.3, 0.3, 0.3)
        >>> axes.axes_actor.tip_length = (0.1, 0.4, 0.2)
        >>> axes.axes_actor.tip_length
        (0.1, 0.4, 0.2)

        """
        return self.GetNormalizedTipLength()

    @tip_length.setter
    def tip_length(self, length):  # numpydoc ignore=GL08
        if isinstance(length, Iterable):
            self.SetNormalizedTipLength(length[0], length[1], length[2])
        else:
            self.SetNormalizedTipLength(length, length, length)

    @property
    def label_position(self) -> tuple[float, float, float]:  # numpydoc ignore=RT01
        """Position of the label along the axes.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.label_position
        (1.0, 1.0, 1.0)
        >>> axes.axes_actor.label_position = 0.3
        >>> axes.axes_actor.label_position
        (0.3, 0.3, 0.3)
        >>> axes.axes_actor.label_position = (0.1, 0.4, 0.2)
        >>> axes.axes_actor.label_position
        (0.1, 0.4, 0.2)

        """
        return self.GetNormalizedLabelPosition()

    @label_position.setter
    def label_position(self, length):  # numpydoc ignore=GL08
        if isinstance(length, Iterable):
            self.SetNormalizedLabelPosition(length[0], length[1], length[2])
        else:
            self.SetNormalizedLabelPosition(length, length, length)

    @property
    def cone_resolution(self) -> int:  # numpydoc ignore=RT01
        """Return or set the resolution of the cone tip.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.cone_resolution
        16
        >>> axes.axes_actor.cone_resolution = 24
        >>> axes.axes_actor.cone_resolution
        24

        """
        return self.GetConeResolution()

    @cone_resolution.setter
    def cone_resolution(self, res: int):  # numpydoc ignore=GL08
        self.SetConeResolution(res)

    @property
    def sphere_resolution(self) -> int:  # numpydoc ignore=RT01
        """Return or set the resolution of the spherical tip.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.sphere_resolution
        16
        >>> axes.axes_actor.sphere_resolution = 24
        >>> axes.axes_actor.sphere_resolution
        24

        """
        return self.GetSphereResolution()

    @sphere_resolution.setter
    def sphere_resolution(self, res: int):  # numpydoc ignore=GL08
        self.SetSphereResolution(res)

    @property
    def cylinder_resolution(self) -> int:  # numpydoc ignore=RT01
        """Return or set the resolution of the shaft cylinder.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.cylinder_resolution
        16
        >>> axes.axes_actor.cylinder_resolution = 24
        >>> axes.axes_actor.cylinder_resolution
        24

        """
        return self.GetCylinderResolution()

    @cylinder_resolution.setter
    def cylinder_resolution(self, res: int):  # numpydoc ignore=GL08
        self.SetCylinderResolution(res)

    @property
    def cone_radius(self) -> float:  # numpydoc ignore=RT01
        """Return or set the radius of the cone tip.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.cone_radius
        0.4
        >>> axes.axes_actor.cone_radius = 0.8
        >>> axes.axes_actor.cone_radius
        0.8

        """
        return self.GetConeRadius()

    @cone_radius.setter
    def cone_radius(self, rad: float):  # numpydoc ignore=GL08
        self.SetConeRadius(rad)

    @property
    def sphere_radius(self) -> float:  # numpydoc ignore=RT01
        """Return or set the radius of the spherical tip.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.sphere_radius
        0.4
        >>> axes.axes_actor.sphere_radius = 0.8
        >>> axes.axes_actor.sphere_radius
        0.8

        """
        return self.GetSphereRadius()

    @sphere_radius.setter
    def sphere_radius(self, rad: float):  # numpydoc ignore=GL08
        self.SetSphereRadius(rad)

    @property
    def cylinder_radius(self) -> float:  # numpydoc ignore=RT01
        """Return or set the radius of the shaft cylinder.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.cylinder_radius
        0.05
        >>> axes.axes_actor.cylinder_radius = 0.03
        >>> axes.axes_actor.cylinder_radius
        0.03

        """
        return self.GetCylinderRadius()

    @cylinder_radius.setter
    def cylinder_radius(self, rad: float):  # numpydoc ignore=GL08
        self.SetCylinderRadius(rad)

    @property
    def shaft_type(self) -> ShaftType:  # numpydoc ignore=RT01
        """Return or set the shaft type.

        Can be either a cylinder(0) or a line(1).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.shaft_type = axes.axes_actor.ShaftType.LINE
        >>> axes.axes_actor.shaft_type
        <ShaftType.LINE: 1>

        """
        return AxesActor.ShaftType(self.GetShaftType())

    @shaft_type.setter
    def shaft_type(self, shaft_type: ShaftType | int):  # numpydoc ignore=GL08
        shaft_type = AxesActor.ShaftType(shaft_type)
        if shaft_type == AxesActor.ShaftType.CYLINDER:
            self.SetShaftTypeToCylinder()
        elif shaft_type == AxesActor.ShaftType.LINE:
            self.SetShaftTypeToLine()

    @property
    def tip_type(self) -> TipType:  # numpydoc ignore=RT01
        """Return or set the shaft type.

        Can be either a cone(0) or a sphere(1).

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.tip_type = axes.axes_actor.TipType.SPHERE
        >>> axes.axes_actor.tip_type
        <TipType.SPHERE: 1>

        """
        return AxesActor.TipType(self.GetTipType())

    @tip_type.setter
    def tip_type(self, tip_type: TipType | int):  # numpydoc ignore=GL08
        tip_type = AxesActor.TipType(tip_type)
        if tip_type == AxesActor.TipType.CONE:
            self.SetTipTypeToCone()
        elif tip_type == AxesActor.TipType.SPHERE:
            self.SetTipTypeToSphere()

    @property
    def labels(self) -> tuple[str, str, str]:  # numpydoc ignore=RT01
        """Return or set the axes labels.

        This property may be used as an alternative to using :attr:`~x_axis_label`,
        :attr:`~y_axis_label`, and :attr:`~z_axis_label` separately.

        .. versionadded:: 0.44.0

        Examples
        --------
        >>> import pyvista as pv
        >>> axes_actor = pv.AxesActor()
        >>> axes_actor.labels = ['X Axis', 'Y Axis', 'Z Axis']
        >>> axes_actor.labels
        ('X Axis', 'Y Axis', 'Z Axis')

        """
        return self.x_label, self.y_label, self.z_label

    @labels.setter
    def labels(self, labels: list[str] | tuple[str]):  # numpydoc ignore=GL08
        if not (isinstance(labels, (list, tuple)) and len(labels) == 3):
            raise ValueError(
                f'Labels must be a list or tuple with three items. Got {labels} instead.',
            )
        self.x_label = labels[0]
        self.y_label = labels[1]
        self.z_label = labels[2]

    @property
    def x_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the x-axis.

        .. deprecated:: 0.44.0

            This parameter is deprecated. Use :attr:`x_label` instead.

        """
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `x_axis_label` is deprecated. Use `x_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        return self.GetXAxisLabelText()  # pragma: no cover

    @x_axis_label.setter
    def x_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `x_axis_label` is deprecated. Use `x_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        self.SetXAxisLabelText(label)  # pragma: no cover

    @property
    def x_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the x-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.x_label = 'This axis'
        >>> axes.axes_actor.x_label
        'This axis'

        """
        return self.GetXAxisLabelText()

    @x_label.setter
    def x_label(self, label: str):  # numpydoc ignore=GL08
        self.SetXAxisLabelText(label)

    @property
    def y_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the y-axis.

        .. deprecated:: 0.44.0

            This parameter is deprecated. Use :attr:`y_label` instead.

        """
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `y_axis_label` is deprecated. Use `y_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        return self.GetYAxisLabelText()  # pragma: no cover

    @y_axis_label.setter
    def y_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `y_axis_label` is deprecated. Use `y_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        self.SetYAxisLabelText(label)  # pragma: no cover

    @property
    def y_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the y-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.y_label = 'This axis'
        >>> axes.axes_actor.y_label
        'This axis'

        """
        return self.GetYAxisLabelText()

    @y_label.setter
    def y_label(self, label: str):  # numpydoc ignore=GL08
        self.SetYAxisLabelText(label)

    @property
    def z_axis_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the z-axis.

        .. deprecated:: 0.44.0

            This parameter is deprecated. Use :attr:`z_label` instead.

        """
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `z_axis_label` is deprecated. Use `z_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        return self.GetZAxisLabelText()  # pragma: no cover

    @z_axis_label.setter
    def z_axis_label(self, label: str):  # numpydoc ignore=GL08
        # deprecated 0.44.0, convert to error in 0.46.0, remove 0.47.0
        warnings.warn(
            'Use of `z_axis_label` is deprecated. Use `z_label` instead.',
            PyVistaDeprecationWarning,
        )
        if pyvista._version.version_info >= (0, 47):  # pragma: no cover
            raise RuntimeError('Remove this deprecated property')
        self.SetZAxisLabelText(label)  # pragma: no cover

    @property
    def z_label(self) -> str:  # numpydoc ignore=RT01
        """Return or set the label for the z-axis.

        Examples
        --------
        >>> import pyvista as pv
        >>> axes = pv.Axes()
        >>> axes.axes_actor.z_label = 'This axis'
        >>> axes.axes_actor.z_label
        'This axis'

        """
        return self.GetZAxisLabelText()

    @z_label.setter
    def z_label(self, label: str):  # numpydoc ignore=GL08
        self.SetZAxisLabelText(label)

    @property
    def x_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the x-axis shaft."""
        return ActorProperties(self.GetXAxisShaftProperty())

    @property
    def y_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the y-axis shaft."""
        return ActorProperties(self.GetYAxisShaftProperty())

    @property
    def z_axis_shaft_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the z-axis shaft."""
        return ActorProperties(self.GetZAxisShaftProperty())

    @property
    def x_axis_tip_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the x-axis tip."""
        return ActorProperties(self.GetXAxisTipProperty())

    @x_axis_tip_properties.setter
    def x_axis_tip_properties(self, properties: ActorProperties):  # numpydoc ignore=GL08
        self.x_axis_tip_properties = properties

    @property
    def y_axis_tip_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the y-axis tip."""
        return ActorProperties(self.GetYAxisTipProperty())

    @y_axis_tip_properties.setter
    def y_axis_tip_properties(self, properties: ActorProperties):  # numpydoc ignore=GL08
        self.y_axis_tip_properties = properties

    @property
    def z_axis_tip_properties(self):  # numpydoc ignore=RT01
        """Return or set the properties of the z-axis tip."""
        return ActorProperties(self.GetZAxisTipProperty())

    @z_axis_tip_properties.setter
    def z_axis_tip_properties(self, properties: ActorProperties):  # numpydoc ignore=GL08
        self.z_axis_tip_properties = properties


class PolarAxesActor(_vtk.vtkPolarAxesActor):
    """PolarAxesActor wrapper for vtkPolarAxesActor.

    This actor is used to represent polar axes in a scene. The user can
    define the geometry to use for the shaft or the tip, and the user
    can set the text for the radial and azimuthal axes. To see full
    customization options, refer to `vtkPolarAxesActor Details
    <https://vtk.org/doc/nightly/html/classvtkPolarAxesActor.html#details>`_.

    Examples
    --------
    Customize the polar axes.

    >>> import pyvista as pv

    Load the teapot geometry using PyVista's built-in methods

    >>> pv.set_jupyter_backend('static')
    >>> filename = pv.examples.download_teapot(
    ...     load=False
    ... )  # Download only, do not load
    >>> mesh = pv.read(filename)

    Apply normals to the geometry

    >>> normals = mesh.compute_normals()

    Create a PyVista plotter

    >>> plotter = pv.Plotter()

    Add the geometry actor (teapot) to the plotter

    >>> actor = plotter.add_mesh(
    ...     normals, color=(0.5, 0.8, 0.3), show_edges=True
    ... )

    Create an outline filter using VTK and add it to the plotter

    >>> _ = plotter.add_mesh(pv.outline_algorithm(normals), color="white")

    Set up the camera.

    >>> camera = pv.Camera()
    >>> camera.clipping_range = (1.0, 100.0)
    >>> camera.focal_point = (0.0, 0.5, 0.0)
    >>> camera.position = (5.0, 6.0, 14.0)

    Set up the light.

    >>> light = pv.Light()
    >>> light.focal_point = (0.21406, 1.5, 0.0)
    >>> light.position = (7.0, 7.0, 4.0)

    Set up the polar axes using VTK and add it to the plotter

    >>> polaxes = pv.PolarAxesActor()
    >>> polaxes.SetBounds(normals.bounds)
    >>> polaxes.pole = (0.5, 1.0, 3.0)
    >>> polaxes.maximum_radius = 3.0
    >>> polaxes.minimum_angle = -60.0
    >>> polaxes.maximum_angle = 210.0
    >>> polaxes.number_of_radial_axes = 10
    >>> polaxes.camera = camera
    >>> polaxes.SetPolarLabelFormat("%6.1f")
    >>> polaxes.GetLastRadialAxisProperty().SetColor(0.0, 1.0, 0.0)
    >>> polaxes.GetSecondaryRadialAxesProperty().SetColor(0.0, 0.0, 1.0)
    >>> polaxes.GetPolarArcsProperty().SetColor(1.0, 0.0, 0.0)
    >>> polaxes.GetSecondaryPolarArcsProperty().SetColor(1.0, 0.0, 1.0)
    >>> polaxes.GetPolarAxisProperty().SetColor(1.0, 0.5, 0.0)
    >>> polaxes.GetPolarAxisTitleTextProperty().SetColor(0.0, 0.0, 0.0)
    >>> polaxes.GetPolarAxisLabelTextProperty().SetColor(1.0, 1.0, 0.0)
    >>> polaxes.GetLastRadialAxisTextProperty().SetColor(0.0, 0.5, 0.0)
    >>> polaxes.GetSecondaryRadialAxesTextProperty().SetColor(
    ...     0.0, 1.0, 1.0
    ... )
    >>> polaxes.screen_size = 9.0

    Add the polar axes to the plotter

    >>> _ = plotter.add_actor(polaxes)

    Set background color

    >>> plotter.set_background((0.8, 0.8, 0.8))

    Set the camera and light

    >>> plotter.camera = camera
    >>> _ = plotter.add_light(light)

    Show the result

    >>> plotter.show()

    """

    @property
    def pole(self) -> tuple[float, float, float]:  # numpydoc ignore=RT01
        """Return or set the pole position.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.pole
        (0.0, 0.0, 0.0)
        >>> polaxes.pole = (0.5, 1.0, 3.0)
        >>> polaxes.pole
        (0.5, 1.0, 3.0)

        """
        return self.GetPole()

    @pole.setter
    def pole(self, pole: tuple[float, float, float]):  # numpydoc ignore=GL08
        self.SetPole(pole[0], pole[1], pole[2])

    @property
    def camera(self) -> pyvista.Camera:  # numpydoc ignore=RT01
        """Return or set the camera.

        the camera to perform scaling and translation of the polar axes.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.camera = pv.Camera()

        """
        return pyvista.Camera(self.GetCamera())

    @camera.setter
    def camera(self, camera: pyvista.Camera):  # numpydoc ignore=GL08
        self.SetCamera(camera)

    @property
    def screen_size(self) -> float:  # numpydoc ignore=RT01
        """Return or set the screen size.

        explicitly specify the screen size of title and label text.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.screen_size
        10.0
        >>> polaxes.screen_size = 20.0
        >>> polaxes.screen_size
        20.0

        """
        return self.GetScreenSize()

    @screen_size.setter
    def screen_size(self, screen_size: float):  # numpydoc ignore=GL08
        self.SetScreenSize(screen_size)

    @property
    def maximum_radius(self) -> float:  # numpydoc ignore=RT01
        """Return or set the maximum radius.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.maximum_radius
        1.0
        >>> polaxes.maximum_radius = 2.0
        >>> polaxes.maximum_radius
        2.0

        """
        return self.GetMaximumRadius()

    @maximum_radius.setter
    def maximum_radius(self, maximum_radius: float):  # numpydoc ignore=GL08
        self.SetMaximumRadius(maximum_radius)

    @property
    def minimum_radius(self) -> float:  # numpydoc ignore=RT01
        """Return or set the minimum radius.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.minimum_radius
        0.0
        >>> polaxes.minimum_radius = 0.5
        >>> polaxes.minimum_radius
        0.5

        """
        return self.GetMinimumRadius()

    @minimum_radius.setter
    def minimum_radius(self, minimum_radius: float):  # numpydoc ignore=GL08
        self.SetMinimumRadius(minimum_radius)

    @property
    def minimum_angle(self) -> float:  # numpydoc ignore=RT01
        """Return or set the minimum angle.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.minimum_angle
        0.0
        >>> polaxes.minimum_angle = -60.0
        >>> polaxes.minimum_angle
        -60.0

        """
        return self.GetMinimumAngle()

    @minimum_angle.setter
    def minimum_angle(self, minimum_angle: float):  # numpydoc ignore=GL08
        self.SetMinimumAngle(minimum_angle)

    @property
    def maximum_angle(self) -> float:  # numpydoc ignore=RT01
        """Return or set the maximum angle.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.maximum_angle
        90.0
        >>> polaxes.maximum_angle = 45.0
        >>> polaxes.maximum_angle
        45.0

        """
        return self.GetMaximumAngle()

    @maximum_angle.setter
    def maximum_angle(self, maximum_angle: float):  # numpydoc ignore=GL08
        self.SetMaximumAngle(maximum_angle)

    @property
    def number_of_radial_axes(self) -> int:  # numpydoc ignore=RT01
        """Return or set the number of radial axes.

        Examples
        --------
        >>> import pyvista as pv
        >>> polaxes = pv.PolarAxesActor()
        >>> polaxes.number_of_radial_axes
        5
        >>> polaxes.number_of_radial_axes = 10
        >>> polaxes.number_of_radial_axes
        10

        """
        return self.GetNumberOfRadialAxes()

    @number_of_radial_axes.setter
    def number_of_radial_axes(self, number_of_radial_axes: int):  # numpydoc ignore=GL08
        self.SetRequestedNumberOfRadialAxes(number_of_radial_axes)
