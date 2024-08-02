"""
All imports from VTK (including GL-dependent).

These are the modules within VTK that must be loaded across pyvista's
plotting API. Here, we attempt to import modules using the ``vtkmodules``
package, which lets us only have to import from select modules and not
the entire library.

"""

# ruff: noqa: F401
from __future__ import annotations

from vtkmodules.vtkChartsCore import vtkAxis
from vtkmodules.vtkChartsCore import vtkChart
from vtkmodules.vtkChartsCore import vtkChartBox
from vtkmodules.vtkChartsCore import vtkChartPie
from vtkmodules.vtkChartsCore import vtkChartXY
from vtkmodules.vtkChartsCore import vtkChartXYZ
from vtkmodules.vtkChartsCore import vtkPlotArea
from vtkmodules.vtkChartsCore import vtkPlotBar
from vtkmodules.vtkChartsCore import vtkPlotBox
from vtkmodules.vtkChartsCore import vtkPlotLine
from vtkmodules.vtkChartsCore import vtkPlotLine3D
from vtkmodules.vtkChartsCore import vtkPlotPie
from vtkmodules.vtkChartsCore import vtkPlotPoints
from vtkmodules.vtkChartsCore import vtkPlotPoints3D
from vtkmodules.vtkChartsCore import vtkPlotStacked
from vtkmodules.vtkChartsCore import vtkPlotSurface
from vtkmodules.vtkCommonColor import vtkColorSeries
from vtkmodules.vtkInteractionWidgets import vtkBoxWidget
from vtkmodules.vtkInteractionWidgets import vtkButtonWidget
from vtkmodules.vtkInteractionWidgets import vtkDistanceRepresentation3D
from vtkmodules.vtkInteractionWidgets import vtkDistanceWidget
from vtkmodules.vtkInteractionWidgets import vtkImplicitPlaneWidget
from vtkmodules.vtkInteractionWidgets import vtkLineWidget
from vtkmodules.vtkInteractionWidgets import vtkLogoRepresentation
from vtkmodules.vtkInteractionWidgets import vtkLogoWidget
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
from vtkmodules.vtkInteractionWidgets import vtkPlaneWidget
from vtkmodules.vtkInteractionWidgets import vtkPointHandleRepresentation3D
from vtkmodules.vtkInteractionWidgets import vtkResliceCursorPicker
from vtkmodules.vtkInteractionWidgets import vtkScalarBarWidget
from vtkmodules.vtkInteractionWidgets import vtkSliderRepresentation2D
from vtkmodules.vtkInteractionWidgets import vtkSliderWidget
from vtkmodules.vtkInteractionWidgets import vtkSphereWidget
from vtkmodules.vtkInteractionWidgets import vtkSplineWidget
from vtkmodules.vtkInteractionWidgets import vtkTexturedButtonRepresentation2D
from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
from vtkmodules.vtkRenderingAnnotation import vtkAxisActor
from vtkmodules.vtkRenderingAnnotation import vtkAxisActor2D
from vtkmodules.vtkRenderingAnnotation import vtkCornerAnnotation
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkRenderingAnnotation import vtkLegendBoxActor
from vtkmodules.vtkRenderingAnnotation import vtkLegendScaleActor
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingContext2D import vtkBlockItem
from vtkmodules.vtkRenderingContext2D import vtkBrush
from vtkmodules.vtkRenderingContext2D import vtkContext2D
from vtkmodules.vtkRenderingContext2D import vtkContextActor
from vtkmodules.vtkRenderingContext2D import vtkContextScene
from vtkmodules.vtkRenderingContext2D import vtkImageItem
from vtkmodules.vtkRenderingContext2D import vtkPen

try:
    from vtkmodules.vtkRenderingCore import vtkHardwarePicker
except ImportError:  # pragma: no cover
    # VTK < 9.2 is missing this class
    vtkHardwarePicker = None
from vtkmodules.vtkRenderingCore import VTK_RESOLVE_OFF
from vtkmodules.vtkRenderingCore import VTK_RESOLVE_POLYGON_OFFSET
from vtkmodules.vtkRenderingCore import VTK_RESOLVE_SHIFT_ZBUFFER
from vtkmodules.vtkRenderingCore import vtkAbstractMapper
from vtkmodules.vtkRenderingCore import vtkActor
from vtkmodules.vtkRenderingCore import vtkActor2D
from vtkmodules.vtkRenderingCore import vtkAreaPicker
from vtkmodules.vtkRenderingCore import vtkCamera
from vtkmodules.vtkRenderingCore import vtkCellPicker
from vtkmodules.vtkRenderingCore import vtkColorTransferFunction
from vtkmodules.vtkRenderingCore import vtkCompositeDataDisplayAttributes
from vtkmodules.vtkRenderingCore import vtkCompositePolyDataMapper
from vtkmodules.vtkRenderingCore import vtkCoordinate
from vtkmodules.vtkRenderingCore import vtkDataSetMapper
from vtkmodules.vtkRenderingCore import vtkImageActor
from vtkmodules.vtkRenderingCore import vtkLight
from vtkmodules.vtkRenderingCore import vtkLightActor
from vtkmodules.vtkRenderingCore import vtkLightKit
from vtkmodules.vtkRenderingCore import vtkMapper
from vtkmodules.vtkRenderingCore import vtkPointGaussianMapper
from vtkmodules.vtkRenderingCore import vtkPointPicker
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper2D
from vtkmodules.vtkRenderingCore import vtkProp3D
from vtkmodules.vtkRenderingCore import vtkPropAssembly
from vtkmodules.vtkRenderingCore import vtkProperty
from vtkmodules.vtkRenderingCore import vtkPropPicker
from vtkmodules.vtkRenderingCore import vtkRenderedAreaPicker
from vtkmodules.vtkRenderingCore import vtkRenderer
from vtkmodules.vtkRenderingCore import vtkRenderWindow
from vtkmodules.vtkRenderingCore import vtkRenderWindowInteractor
from vtkmodules.vtkRenderingCore import vtkScenePicker
from vtkmodules.vtkRenderingCore import vtkSelectVisiblePoints
from vtkmodules.vtkRenderingCore import vtkSkybox
from vtkmodules.vtkRenderingCore import vtkTextActor
from vtkmodules.vtkRenderingCore import vtkTextProperty
from vtkmodules.vtkRenderingCore import vtkTexture
from vtkmodules.vtkRenderingCore import vtkVolume
from vtkmodules.vtkRenderingCore import vtkVolumeProperty
from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
from vtkmodules.vtkRenderingCore import vtkWorldPointPicker
from vtkmodules.vtkRenderingFreeType import vtkMathTextFreeTypeTextRenderer
from vtkmodules.vtkRenderingFreeType import vtkVectorText
from vtkmodules.vtkRenderingLabel import vtkLabelPlacementMapper
from vtkmodules.vtkRenderingLabel import vtkPointSetToLabelHierarchy
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper
from vtkmodules.vtkRenderingVolume import vtkUnstructuredGridVolumeRayCastMapper
from vtkmodules.vtkRenderingVolume import vtkVolumePicker
from vtkmodules.vtkViewsContext2D import vtkContextInteractorStyle

from pyvista.core._vtk_core import *

from ._vtk_gl import *

try:
    from vtkmodules.vtkInteractionWidgets import vtkOrientationRepresentation
    from vtkmodules.vtkInteractionWidgets import vtkOrientationWidget
except ImportError:  # pragma: no cover
    # VTK < 9.3 is missing this class
    pass
