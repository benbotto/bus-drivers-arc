import arcpy
import os
import k_function_helper

# ArcMap caching prevention.
k_function_helper = reload(k_function_helper)
from k_function_helper import KFunctionHelper

class NetworkDatasetRandomPoints(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Create Random Points on a Network Dataset"
    self.description = "Create a series of random points on a network dataset."
    self.canRunInBackground = False

    arcpy.env.overwriteOutput = True
    self.kfHelper = KFunctionHelper()

  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # Network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Existing Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Output location.
    outLocation = arcpy.Parameter(
      displayName="Path to Output Random Point Feature Class",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLocation.value = arcpy.env.workspace

    # The random point feature class to create.
    outPointClass = arcpy.Parameter(
      displayName="Output Random Point Feature Class Name",
      name = "output_point_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")

    # Num points or long.
    useField = arcpy.Parameter(
      displayName="Use a Data Field for Point Generation",
      name = "use_field",
      datatype="GPBoolean",
      parameterType="Optional",
      direction="Input")

    # Number of random points to generate.
    numPoints = arcpy.Parameter(
      displayName="Number of Points",
      name = "num_points",
      datatype="GPLong",
      parameterType="Optional",
      direction="Input")

    # Number of points field.
    numPointsFieldName = arcpy.Parameter(
      displayName="Number of Points Field",
      name = "num_points_field",
      datatype="GPString",
      parameterType="Optional",
      direction="Input")

    return [networkDataset, outLocation, outPointClass, useField, numPoints, numPointsFieldName]

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
    useField       = parameters[3].value
    
    if networkDataset is not None and outPointClass is None:
      # Default name for the output table.
      ndDesc = arcpy.Describe(networkDataset)
      parameters[2].value = ndDesc.name + "_Random_Points"

    # Num points/num points field is based on the useField checkbox.
    parameters[4].enabled = not useField
    parameters[5].enabled = useField

    # Set the source of the fields (the network dataset).
    if useField == True and networkDataset is not None:
      parameters[5].filter.list = self.kfHelper.getEdgeSourceFieldNames(networkDataset)

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    networkDataset     = parameters[0].value
    useField           = parameters[3].value
    numPoints          = parameters[4].value
    numPointsFieldName = parameters[5].value

    if numPoints is not None:
      if numPoints <= 0:
        parameters[2].setErrorMessage("The number of points must be greater than 0.")
      else:
        parameters[2].clearMessage()

    if useField:
      if numPointsFieldName is None:
        parameters[5].setErrorMessage("Number of points field is required.")
      else:
        parameters[5].clearMessage()

      # Check that there is a single edge source if a field is used.
      if networkDataset is not None:
        if self.kfHelper.getNumEdgeSources(networkDataset) != 1:
          parameters[5].setErrorMessage("If using a field, only a single edge source is supported.")
        else:
          parameters[5].clearMessage()
    else:
      if numPoints is None:
        parameters[4].setErrorMessage("Number of points is required.")
      else:
        parameters[4].clearMessage()

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    networkDataset     = parameters[0].value
    outPath            = parameters[1].value
    outPointClass      = parameters[2].value
    useField           = parameters[3].value
    numPoints          = parameters[4].value
    numPointsFieldName = parameters[5].value

    wsPath            = arcpy.env.workspace
    ndDesc            = arcpy.Describe(networkDataset)

    messages.addMessage("Network Dataset: {0}".format(ndDesc.catalogPath))
    messages.addMessage("Location to Output Random Point Feature Class: {0}".format(outPath))
    messages.addMessage("Output Random Point Feature Class: {0}".format(outPointClass))
    messages.addMessage("Use a Data Field for Point Generation: {0}".format(useField))
    messages.addMessage("Number of Points: {0}".format(numPoints))
    messages.addMessage("Number of Points Field: {0}".format(numPointsFieldName))

    if useField:
      # Use the single edge source for the constraining feature.
      esFullPath = self.kfHelper.getEdgeSourcePath(networkDataset)

      # Create a series of random points on the new line class.
      messages.addMessage("Creating point feature class.  Name: {0} Path: {1}"
        .format(outPointClass, outPath))

      # Use the field name for the number of points (e.g. AADT).
      arcpy.CreateRandomPoints_management(out_path=outPath, out_name=outPointClass,
        constraining_feature_class=esFullPath, number_of_points_or_field=numPointsFieldName)
    else:
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
              insCursor.insertRow([row[0]])

      # Combine all the line segments into a single line.
      singleLineName     = "TEMP_SINGLE_LINE_{0}".format(ndDesc.name)
      singleLineFullPath = os.path.join(wsPath, singleLineName)
      arcpy.Dissolve_management(lineClassFullPath, singleLineFullPath)

      # Create a series of random points on the new line class.
      messages.addMessage("Creating point feature class.  Name: {0} Path: {1}"
        .format(outPointClass, outPath))
      arcpy.CreateRandomPoints_management(out_path=outPath, out_name=outPointClass,
        constraining_feature_class=singleLineFullPath, number_of_points_or_field=numPoints)

      # Clean up the temporary feature class.
      arcpy.Delete_management(lineClassFullPath)
      arcpy.Delete_management(singleLineFullPath)
