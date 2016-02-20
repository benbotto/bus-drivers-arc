import arcpy
import os

class NetworkDatasetRandomPoints(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Create Random Points on a Network Dataset"
    self.description = "Create a series of random points on a network dataset."
    self.canRunInBackground = False

    arcpy.env.overwriteOutput = True

  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter: network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Existing Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Second parameter: output location.
    outLocation = arcpy.Parameter(
      displayName="Location to Output Random Point Feature Class",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLocation.value = arcpy.env.workspace

    # Third paramter: the random point feature class to create.
    outPointClass = arcpy.Parameter(
      displayName="Output Random Point Feature Class Name",
      name = "output_point_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")

    numPoints = arcpy.Parameter(
      displayName="Number of Points",
      name = "num_points",
      datatype="GPLong",
      parameterType="Required",
      direction="Input")

    params = [networkDataset, outLocation, outPointClass, numPoints]
    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    return True

  ###
  # Set the parameter defaults.
  ###
  def updateParameters(self, parameters):
    networkDataset = parameters[0].value
    outPointClass  = parameters[2].value
    if networkDataset is not None and outPointClass is None:
      # Default name for the output table.
      ndDesc = arcpy.Describe(networkDataset)
      parameters[2].value = ndDesc.name + "_Random_Points"
    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    numPoints = parameters[3].value

    if numPoints is not None:
      if numPoints <= 0:
        parameters[2].setErrorMessage("The number of points must be greater than 0.")
      else:
        parameters[2].clearMessage()
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    networkDataset    = parameters[0].value
    outPath           = parameters[1].value
    outPointClass     = parameters[2].value
    numPoints         = parameters[3].value

    wsPath            = arcpy.env.workspace
    ndDesc            = arcpy.Describe(networkDataset)

    messages.addMessage("Network Dataset: {0}".format(ndDesc.catalogPath))
    messages.addMessage("Location to Output Random Point Feature Class: {0}".format(outPath))
    messages.addMessage("Output Random Point Feature Class: {0}".format(outPointClass))
    messages.addMessage("Number of Points: {0}".format(numPoints))

    # All the edge sources that make up the network dataset are combined into
    # a single feature class.
    lineClassName     = "TEMP_LINES_{0}".format(ndDesc.name)
    lineClassFullPath = os.path.join(wsPath, lineClassName)
    arcpy.CreateFeatureclass_management(out_path=wsPath, out_name=lineClassName,
      geometry_type="POLYLINE", spatial_reference=ndDesc.spatialReference)
    
    with arcpy.da.InsertCursor(lineClassName, ["SHAPE@"]) as insCursor:
      # Get the edge sources that make up the network.
      edgeSources = ndDesc.edgeSources

      for edgeSource in edgeSources:
        edgePath = os.path.join(ndDesc.path, edgeSource.name)

        with arcpy.da.SearchCursor(edgePath, ["SHAPE@"]) as cursor:
          for row in cursor:
            startpt = row[0].firstPoint
            endpt   = row[0].lastPoint

            messages.addMessage("Point: ({0:.0f}, {1:.0f}) - ({2:.0f}, {3:.0f})"
              .format(startpt.X, startpt.Y, endpt.X, endpt.Y))
            insCursor.insertRow([row[0]])

    # Combine all the line segments into a single line.
    singleLineName     = "TEMP_SINGLE_LINE_{0}".format(ndDesc.name)
    singleLineFullPath = os.path.join(wsPath, singleLineName)
    arcpy.UnsplitLine_management(lineClassFullPath, singleLineFullPath)

    # Create a series of random points on the new line class.
    messages.addMessage("Creating point feature class.  Name: {0} Path: {1}"
      .format(outPointClass, outPath))
    arcpy.CreateRandomPoints_management(out_path=outPath, out_name=outPointClass,
      constraining_feature_class=singleLineFullPath, number_of_points_or_field=numPoints)

    # Clean up the temporary feature class.
    arcpy.Delete_management(lineClassFullPath)
    arcpy.Delete_management(singleLineFullPath)
    return
