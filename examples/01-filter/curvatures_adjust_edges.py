"""
.. _curvatures_adjust_edges:

curvatures Adjust Edges
~~~~~~~~~~~~~~~~~~~~~~~
"""

import pyvista as pv

source = (
    pv.ParametricRandomHills(
        random_seed=1, number_of_hills=30, u_res=51, v_res=51, texture_coordinates=True
    )
    .translate((0.0, 5.0, 15.0))
    .rotate_x(-90.0)
)

source['Gauss_Curvature'] = source.curvature("gaussian", adjust_edges=True)
source['Mean_Curvature'] = source.curvature("mean", adjust_edges=True)

# Let's visualise what we have done.

window_width = 1024
window_height = 512

plotter = pv.Plotter(shape=(1, 2), window_size=(window_width, window_height))

# Create a common text property.
text_property = pv.TextProperty()
text_property.font_size = 24
text_property.justification_horizontal = "center"
text_property.color = "white"

lut = pv.LookupTable('coolwarm', n_values=256)

# Define viewport ranges
xmins = [0, 0.5]
xmaxs = [0.5, 1]
ymins = [0, 0]
ymaxs = [1.0, 1.0]

curvature_name = 'Gauss_Curvature'
plotter.subplot(0, 0)
curvature_title = curvature_name.replace('_', '\n')

source.GetPointData().SetActiveScalars(curvature_name)
scalar_range = source.GetPointData().GetScalars(curvature_name).GetRange()

mapper = pv.DataSetMapper()
mapper.SetInputData(source)
mapper.SetScalarModeToUsePointFieldData()
mapper.SelectColorArray(curvature_name)
mapper.SetScalarRange(scalar_range)
mapper.SetLookupTable(lut)

actor = pv.Actor(mapper=mapper)

text_actor = pv.Text(text=curvature_title)
text_actor.prop = text_property
text_actor.position = (250, 16)

plotter.add_actor(actor)
plotter.set_background([82, 87, 110])
plotter.add_actor(text_actor)
plotter.add_scalar_bar(
    title=curvature_title,
    unconstrained_font_size=True,
    mapper=mapper,
    n_labels=5,
    position_x=0.85,
    position_y=0.1,
    vertical=True,
    color='white',
)
renderer = plotter.renderers[0]

camera = renderer.camera
camera.elevation = 60
renderer.SetViewport(xmins[0], ymins[0], xmaxs[0], ymaxs[0])
renderer.reset_camera()

curvature_name = 'Mean_Curvature'
plotter.subplot(0, 1)
curvature_title = curvature_name.replace('_', '\n')

source.GetPointData().SetActiveScalars(curvature_name)
scalar_range = source.GetPointData().GetScalars(curvature_name).GetRange()

mapper = pv.DataSetMapper()
mapper.SetInputData(source)
mapper.SetScalarModeToUsePointFieldData()
mapper.SelectColorArray(curvature_name)
mapper.SetScalarRange(scalar_range)
mapper.SetLookupTable(lut)

actor = pv.Actor(mapper=mapper)

text_actor = pv.Text(text=curvature_title)
text_actor.prop = text_property
text_actor.position = (250, 16)

plotter.add_actor(actor)
plotter.set_background([82, 87, 110])
plotter.add_actor(text_actor)
plotter.add_scalar_bar(
    title=curvature_title,
    unconstrained_font_size=True,
    mapper=mapper,
    n_labels=5,
    position_x=0.85,
    position_y=0.1,
    vertical=True,
    color='white',
)
renderer = plotter.renderers[1]


renderer.camera = camera
renderer.SetViewport(xmins[1], ymins[1], xmaxs[1], ymaxs[1])
renderer.reset_camera()

plotter.add_camera_orientation_widget()
plotter.show()