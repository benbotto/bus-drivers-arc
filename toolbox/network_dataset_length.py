import arcpy
import os

class NetworkDatasetLength(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Network Dataset Length"
    self.description = "Calculates the total length of a network dataset."
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

    # Second parameter: projected coordinate system.
    outCoordSys = arcpy.Parameter(
      displayName="Output Network Dataset Length Projected Coordinate System",
      name="out_coordinate_system",
      datatype="GPSpatialReference",
      parameterType="Optional",
      direction="Input")

    # Third parameter: output location.
    outLocation = arcpy.Parameter(
      displayName="Location to Output Network Dataset Length Table",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLocation.value = arcpy.env.workspace

    # Fourth parameter: name of the length table.
    outTable = arcpy.Parameter(
      displayName="Output Network Dataset Length Table Name",
      name="out_length_table_name",
      datatype="GPString",
      parameterType="Required",
      direction="Output")

    params = [networkDataset, outCoordSys, outLocation, outTable]
    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    return True

  ###
  # Set the defaults for parameters.
  ###
  def updateParameters(self, parameters):
    networkDataset = parameters[0].value
    outCoordSys    = parameters[1].value
    outTable       = parameters[3].value
    
    if networkDataset is not None:
      ndDesc = arcpy.Describe(networkDataset)
      if outCoordSys is None:
        # If the network dataset's coordinate system is a projected one,
        # use its coordinate system as the defualt.
        if ndDesc.spatialReference.projectionName != "" and ndDesc.spatialReference.factoryCode != 0:
          parameters[1].value = ndDesc.spatialReference.factoryCode

      if outTable is None:
        # Default for the output table name.
        parameters[3].value = ndDesc.name + "_Length"

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[1].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[1].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      else:
        parameters[1].clearMessage()
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    networkDataset = parameters[0].valueAsText
    outCoordSys    = parameters[1].value
    outPath        = parameters[2].value
    outTable       = parameters[3].value
    wsPath         = arcpy.env.workspace
    ndDesc         = arcpy.Describe(networkDataset)

    # The output coordinate system is optional.  Note: this is set as a default
    # in the updateParameters method, but it only works for standard spatial
    # references (those having a factory code).  If a custom projection (.prj
    # file) is used for the network dataset, this sets the output default.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Network dataset length projected coordinate system: {0}".format(outCoordSys.name))
    messages.addMessage("Location to output network dataset length table: {0}".format(outPath))
    messages.addMessage("Network dataset length table name: {0}".format(outTable))

    # The length of the network is needed.  Get the edge source(s).
    edgeSources   = ndDesc.edgeSources
    networkLength = 0

    for edgeSource in edgeSources:
      edgePath = os.path.join(ndDesc.path, edgeSource.name)
      messages.addMessage("Edge source for network dataset: Name {0} Path: {1}".format(edgeSource.name, edgePath))

      # The edge source must be in a projected coordinate system in order to
      # calculate the length in units of meters, but a feature class that
      # participates in a network dataset cannot be projected.  Created a copy
      # of the edge source.
      edgeCopyName     = "TEMP_{0}".format(edgeSource.name)
      edgeCopyFullPath = os.path.join(wsPath, edgeCopyName)
      arcpy.FeatureClassToFeatureClass_conversion(edgePath, wsPath, edgeCopyName)
      messages.addMessage("Created edge copy: {0}".format(edgeCopyFullPath))
      edgeCopyDesc = arcpy.Describe(edgeCopyFullPath)

      # Make sure that the original coordinate system can be determined.  An
      # initial coordinate system is required for to complete a projection.
      messages.addMessage("Original spatial reference: {0}".format(edgeCopyDesc.spatialReference.name))

      if edgeCopyDesc.spatialReference.name == "Unknown":
        messages.addMessage("Fatal error: Original projection unknown.")
        return

      if edgeCopyDesc.spatialReference.name == outCoordSys.name:
        # No reason to project the copy because the coordinate system is not changing.
        messages.addMessage("Same source and destination coordinate system.")
        projEdgeFullPath = edgeCopyFullPath
      else:
        # Make a projected version of the temporary feature class so that the length
        # can be calculated in meters.
        projEdgeName     = "TEMP_PROJECTED_{0}".format(edgeSource.name)
        projEdgeFullPath = os.path.join(wsPath, projEdgeName)
        arcpy.Project_management(edgeCopyFullPath, projEdgeName, outCoordSys)
        messages.addMessage("Created projected version of edge source: {0}".format(projEdgeFullPath))

      # Find the total length.
      with arcpy.da.SearchCursor(in_table=projEdgeFullPath, field_names=["Shape_Length"]) as cursor:
        for row in cursor:
          networkLength += row[0]

      # Delete the temporary feature classes.
      arcpy.Delete_management(edgeCopyFullPath)
      arcpy.Delete_management(projEdgeFullPath)

    messages.addMessage("****************************************************")
    messages.addMessage("Total network length: {0}".format(networkLength))
    messages.addMessage("****************************************************")

    # Create the output table.
    arcpy.CreateTable_management(outPath, outTable)
    arcpy.AddField_management(outTable, "Network_Dataset_Length", "DOUBLE")
    arcpy.AddField_management(outTable, "Network_Dataset_Name",   "TEXT")

    # Insert the length.
    with arcpy.da.InsertCursor(outTable, ["Network_Dataset_Length", "Network_Dataset_Name"]) as cursor:
      cursor.insertRow([networkLength, networkDataset])
    return
