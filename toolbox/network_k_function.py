import arcpy
import os
from arcpy import env

class NetworkKFunction(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Network K Function"
    self.description = "Uses a Network K Function to analyze clustering and dispersion trends in a set of crash points."
    self.canRunInBackground = False

    env.overwriteOutput = True
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter: input origin features.
    originPoints = arcpy.Parameter(
      displayName="Input Origin Feature Dataset",
      name="origin_points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    originPoints.filter.list = ["Point"]

    # Second parameter: input destination features.
    destPoints = arcpy.Parameter(
      displayName="Input Destination Feature Dataset",
      name="dest_points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    destPoints.filter.list = ["Point"]

    # Third parameter: network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Existing Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Fourth parameter: number of distance increments.
    numInc = arcpy.Parameter(
      displayName="Input Number of Distance Increments",
      name="dist_increment",
      datatype="Long",
      parameterType="Required",
      direction="Input")
    numInc.filter.type  = "Range"
    numInc.filter.list  = [1, 100]
    numInc.value        = 10

    # Fifth parameter: beginning distance.
    begDist = arcpy.Parameter(
      displayName="Input Beginning Distance",
      name="beginning_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    begDist.value = 0

    # Sixth parameter: distance increment.
    distInc = arcpy.Parameter(
      displayName="Input Distance Increment",
      name="distance_increment",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 1000

    # Seventh parameter: snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 100
   
    params = [originPoints, destPoints, networkDataset, numInc, begDist, distInc, snapDist]
    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    # Network Analyst tools must be available.
    return arcpy.CheckExtension("Network") == "Available"

  ###
  # Validate each input.
  ###
  def updateParameters(self, parameters):
    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    originPoints   = parameters[0].valueAsText
    destPoints     = parameters[1].valueAsText
    networkDataset = parameters[2].valueAsText
    numInc         = parameters[3].value
    begDist        = parameters[4].value
    distInc        = parameters[5].value
    snapDist       = parameters[6].value

    #if distInc is None:
    #  messages.addMessage("Distance increment is none... need to calculate it.")

    messages.addMessage("Origin points: {0}".format(originPoints))
    messages.addMessage("Destination points: {0}".format(destPoints))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Number of distance increments: {0}".format(numInc))
    messages.addMessage("Beginning distance: {0}".format(begDist))
    messages.addMessage("Distance increment: {0}".format(distInc))
    messages.addMessage("Snap distance: {0}".format(snapDist))

    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    # The name of the ODCM layer.
    odcmName = "ODCM__{0}__{1}__{2}__{3}__{4}-{5}".format(
      arcpy.Describe(originPoints).baseName,
      arcpy.Describe(destPoints).baseName,
      arcpy.Describe(networkDataset).baseName,
      numInc, begDist, distInc)

    # Create the cost matrix.
    costMatResult = arcpy.na.MakeODCostMatrixLayer(networkDataset, odcmName, "Length")
    odcmLayer     = costMatResult.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, originPoints, "", snapDist)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destPoints,   "", snapDist)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show ODCM layer to the user.
    arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    arcpy.RefreshTOC()

    # Get the "Lines" layer, which has the distance between each point.
    #messages.addMessage("Sublayers {0}".format(odcmSublayers))
    odcmLines = odcmSublayers["ODLines"]

    # This array will hold all the meta data about each distance band (the
    # distance band and the number of points within that band).
    distCount = []

    for i in range(0, numInc):
      # This is the distance band.
      distBand = begDist + i * distInc
      messages.addMessage("Iteration: {0} Distance band: {1}".format(i, distBand))

      # Initialize the distance band meta data.
      distCount.append({"distanceBand": distBand, "count": 0})

      # The distance between the points must be less than or equal to the
      # current distance band.
      if originPoints == destPoints:
        # The origin and desination points are the same.
        # The OD Cost Matrix finds lengths on the _combination_ of points.
        # So, if there are two points, the result will have distances from
        # 1 to 1, 1 to 2, 2 to 1, and 2 to 2.  The second part of this condition
        # eliminates distances from a point to itself, and redundancy (e.g. the
        # distance from 1 to 2 is the same as the distance from 2 to 1).
        where = """{0} <= {1} AND {2} < {3}""".format(
          arcpy.AddFieldDelimiters(odcmLines, "Total_Length"),
          distBand,
          arcpy.AddFieldDelimiters(odcmLines, "originID"),
          arcpy.AddFieldDelimiters(odcmLines, "destinationID"))
      else:
        where = """{0} <= {1}""".format(
          arcpy.AddFieldDelimiters(odcmLines, "Total_Length"),
          distBand)

      messages.addMessage("Where: {0}".format(where))

      with arcpy.da.SearchCursor(
        in_table=odcmLines,
        field_names=["Total_Length", "originID", "destinationID"],
        where_clause=where) as cursor:

        for row in cursor:
          messages.addMessage("Total_Length: {0} OriginID: {1} DestinationID: {2}".format(
            row[0], row[1], row[2]))

          # Keep track of the total number of points in the current distance band.
          distCount[i]["count"] += 1

    # distCount now holds the final summation results.
    messages.addMessage("****************************************************")
    messages.addMessage("Distance count: {0}".format(distCount))
    messages.addMessage("****************************************************")

    # The length of the network is needed.  Get the edge source(s).
    ndDesc        = arcpy.Describe(networkDataset)
    edgeSources   = ndDesc.edgeSources
    networkLength = 0

    for edgeSource in edgeSources:
      edgePath = ndDesc.path + "\\" + edgeSource.name
      messages.addMessage("Edge source for network dataset: Name {0} Path: {1}".format(edgeSource.name, edgePath))

      # The edge source must be in a projected coordinate system in order to
      # calculate the length in units of meters, but a feature class that
      # participates in a network dataset cannot be projected.  Created a copy
      # of the edge source.
      edgeCopyPath     = arcpy.env.workspace
      edgeCopyName     = "TEMP_{0}".format(edgeSource.name)
      edgeCopyFullPath = os.path.join(edgeCopyPath, edgeCopyName)
      arcpy.FeatureClassToFeatureClass_conversion(edgePath, edgeCopyPath, edgeCopyName)
      messages.addMessage("Created edge copy: {0}".format(edgeCopyFullPath))
      edgeCopyDesc = arcpy.Describe(edgeCopyFullPath)

      # Make sure that the original coordinate system can be determined.  An
      # initial coordinate system is required for to complete a projection.
      messages.addMessage("Original spatial reference: {0}".format(edgeCopyDesc.spatialReference.name))

      if edgeCopyDesc.spatialReference.name == "Unknown":
        messages.addMessage("Fatal error -- original projection unknown.")
        return

      # Make a projected version of the temporary feature class so that the length
      # can be calculated in meters.
      projEdgeName     = "TEMP_PROJECTED_{0}".format(edgeSource.name)
      projEdgePath     = arcpy.env.workspace
      projEdgeFullPath = os.path.join(projEdgePath, projEdgeName)

      # TODO: Allow user to pick the projected coordinate system.  When updating the spaces
      # might present a problem since the normal name has underscores.  It seems like it is possible
      # to use the ID.
      # http://pro.arcgis.com/en/pro-app/arcpy/classes/spatialreference.htm
      outCordSys   = arcpy.SpatialReference("NAD 1983 UTM Zone 10N")
      arcpy.Project_management(edgeCopyFullPath, projEdgeName, outCordSys)
      messages.addMessage("Created projected version of edge source: {0}".format(projEdgeFullPath))

      # Delete the temporary feature class.
      arcpy.Delete_management(edgeCopyFullPath)

      # Sum up the length of each edge.
      with arcpy.da.SearchCursor(in_table=projEdgeFullPath, field_names=["Shape_Length"]) as cursor:
        for row in cursor:
          messages.addMessage("Length: {0}".format(row[0]))
          networkLength += row[0]

      # Delete the temporary projected feature class.
      arcpy.Delete_management(projEdgeFullPath)

    messages.addMessage("****************************************************")
    messages.addMessage("Total network length: {0}".format(networkLength))
    messages.addMessage("****************************************************")
    return