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

    # Second paramter: the random point feature class to create.
    outPointClass = arcpy.Parameter(
      displayName="Output Random Point Feature Class",
      name = "output_point_feature_class",
      datatype="DEFeatureClass",
      parameterType="Required",
      direction="Output")

    numPoints = arcpy.Parameter(
      displayName="Number of Points",
      name = "num_points",
      datatype="GPLong",
      parameterType="Required",
      direction="Input")

    params = [networkDataset, outPointClass, numPoints]
    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    return True

  ###
  # Validate each input.
  ###
  def updateParameters(self, parameters):
    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    numPoints = parameters[2].value

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
    outPointClass     = parameters[1].value
    numPoints         = parameters[2].value

    wsPath            = arcpy.env.workspace
    ndDesc            = arcpy.Describe(networkDataset)
    outPointClassDesc = arcpy.Describe(outPointClass)

    messages.addMessage("Network Dataset: {0}".format(ndDesc.catalogPath))
    messages.addMessage("Output Random Point Feature Class: {0}".format(outPointClassDesc.catalogPath))
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
    randPointName     = outPointClassDesc.name
    randPointPath     = outPointClassDesc.path
    randPointFullPath = outPointClassDesc.catalogPath

    messages.addMessage("Creating point feature class.  Name: {0} Path: {1} Full path: {2}"
      .format(randPointName, randPointPath, randPointFullPath))
    arcpy.CreateRandomPoints_management(out_path=randPointPath, out_name=randPointName,
      constraining_feature_class=singleLineFullPath, number_of_points_or_field=numPoints)

    # Clean up the temporary feature class.
    arcpy.Delete_management(lineClassFullPath)
    arcpy.Delete_management(singleLineFullPath)
    return
