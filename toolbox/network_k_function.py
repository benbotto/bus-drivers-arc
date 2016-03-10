import arcpy
import os
import network_k_calculation
import network_k_analysis

from collections import OrderedDict
from arcpy       import env

# ArcMap caching prevention.
network_k_calculation = reload(network_k_calculation)
network_k_analysis    = reload(network_k_analysis)

from network_k_calculation import NetworkKCalculation
from network_k_analysis    import NetworkKAnalysis

class NetworkKFunction(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label              = "Network K Function"
    self.description        = "Uses a Network K Function to analyze clustering and dispersion trends in a set of crash points."
    self.canRunInBackground = False
    env.overwriteOutput     = True

    self.permutations = OrderedDict([
      ("0 Permutations (No Confidence Envelope)", 0),
      ("9 Permutations", 9),
      ("99 Permutations", 99),
      ("999 Permutations", 999)])
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter: input origin features.
    points = arcpy.Parameter(
      displayName="Input Points Feature Dataset",
      name="points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    points.filter.list = ["Point"]

    # Second parameter: network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Input Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Third parameter: number of distance increments.
    numBands = arcpy.Parameter(
      displayName="Input Number of Distance Bands",
      name="num_dist_bands",
      datatype="Long",
      parameterType="Optional",
      direction="Input")

    # Fourth parameter: beginning distance.
    begDist = arcpy.Parameter(
      displayName="Input Beginning Distance",
      name="beginning_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    begDist.value = 0

    # Fifth parameter: distance increment.
    distInc = arcpy.Parameter(
      displayName="Input Distance Increment",
      name="distance_increment",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 1000

    # Sixth parameter: snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    snapDist.value = 25

    # Seventh parameter: output location.
    outNetKLoc = arcpy.Parameter(
      displayName="Output Location (Database Path)",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outNetKLoc.value = arcpy.env.workspace

    # Eigth parameter: the raw data feature class (e.g. observed and random
    # point computations).
    outRawFCName = arcpy.Parameter(
      displayName="Output Feature Class Name (Raw Network-K Data)",
      name = "output_raw_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outRawFCName.value = "Net_K_Raw_Data"

    # Ninth parameter: the analysis feature class.
    outAnlFCName = arcpy.Parameter(
      displayName="Output Feature Class Name (Network-K Analysis Data)",
      name = "output_analysis_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outAnlFCName.value = "Net_K_Analysis_Data"

    # Tenth parameter: confidence envelope (number of permutations).
    numPerms = arcpy.Parameter(
      displayName="Number of Random Point Permutations",
      name = "num_permutations",
      datatype="GPString",
      parameterType="Required",
      direction="Input")
    permKeys             = self.permutations.keys();
    numPerms.filter.list = permKeys
    numPerms.value       = permKeys[0]

    # Eleventh parameter: projected coordinate system.
    outCoordSys = arcpy.Parameter(
      displayName="Output Network Dataset Length Projected Coordinate System",
      name="coordinate_system",
      datatype="GPSpatialReference",
      parameterType="Optional",
      direction="Input")
   
    return [points, networkDataset, numBands, begDist, distInc, snapDist,
      outNetKLoc, outRawFCName, outAnlFCName, numPerms, outCoordSys]

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    # Network Analyst tools must be available.
    return arcpy.CheckExtension("Network") == "Available"

  ###
  # Set parameter defaults.
  ###
  def updateParameters(self, parameters):
    networkDataset = parameters[1].value
    outCoordSys    = parameters[10].value

    # Default the coordinate system.
    if networkDataset is not None and outCoordSys is None:
      ndDesc = arcpy.Describe(networkDataset)
      # If the network dataset's coordinate system is a projected one,
      # use its coordinate system as the defualt.
      if (ndDesc.spatialReference.projectionName != "" and
        ndDesc.spatialReference.linearUnitName == "Meter" and
        ndDesc.spatialReference.factoryCode != 0):
        parameters[10].value = ndDesc.spatialReference.factoryCode

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[10].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[10].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      elif outCoordSys.linearUnitName != "Meter":
        parameters[10].setErrorMessage("Output coordinate system must have a linear unit code of 'Meter.'")
      else:
        parameters[10].clearMessage()
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    points         = parameters[0].valueAsText
    networkDataset = parameters[1].valueAsText
    numBands       = parameters[2].value
    begDist        = parameters[3].value
    distInc        = parameters[4].value
    snapDist       = parameters[5].value
    outNetKLoc     = parameters[6].valueAsText
    outRawFCName   = parameters[7].valueAsText
    outAnlFCName   = parameters[8].valueAsText
    numPerms       = self.permutations[parameters[9].valueAsText]
    outCoordSys    = parameters[10].value
    ndDesc         = arcpy.Describe(networkDataset)

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("Origin points: {0}".format(points))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Number of distance bands: {0}".format(numBands))
    messages.addMessage("Beginning distance: {0}".format(begDist))
    messages.addMessage("Distance increment: {0}".format(distInc))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Path to output network-K feature class: {0}".format(outNetKLoc))
    messages.addMessage("Output feature class name (raw network-K data): {0}".format(outRawFCName))
    messages.addMessage("Output feature class name (network-K analysis data): {0}".format(outAnlFCName))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}\n".format(outCoordSys.name))

    # The Network Dataset Length and Generate Random Points tools are used.
    # Import the toolbox.  It's is in the Crash Analysis Toolbox (this tool's
    # toolbox).
    toolboxPath     = os.path.dirname(os.path.abspath(__file__))
    toolboxName     = "Crash Analysis Toolbox.pyt"
    toolboxFullPath = os.path.join(toolboxPath, toolboxName)
    arcpy.ImportToolbox(toolboxFullPath)

    # Calculate the length of the network.
    networkLength = self.calculateLength(networkDataset, outCoordSys)
    messages.addMessage("Total network length: {0}".format(networkLength))

    # The results of all the calculations end up here.
    netKCalculations = []

    # Observed distance bands.
    messages.addMessage("Iteration 0 (observed).")

    # Make the ODCM and calculate the distance between each set of points.
    odDists = self.calculateDistances(networkDataset, points, snapDist)

    # Do the actual network k-function calculation and return the result.
    netKCalc  = NetworkKCalculation(networkLength, odDists, begDist, distInc, numBands)
    numPoints = netKCalc.getNumberOfPoints()
    numBands  = netKCalc.getNumberOfDistanceBands()
    netKCalculations.append(netKCalc.getDistanceBands())

    # Generate a set of random points on the network.
    for i in range(1, numPerms + 1):
      messages.addMessage("Iteration {0}.".format(i))

      randPoints = self.generateRandomPoints(networkDataset, outCoordSys, numPoints)
      odDists    = self.calculateDistances(networkDataset, randPoints, snapDist)
      netKCalc   = NetworkKCalculation(networkLength, odDists, begDist, distInc, numBands)
      netKCalculations.append(netKCalc.getDistanceBands())

      # Clean up the random points table.
      arcpy.Delete_management(randPoints)

    # Write the distance bands to a table.  The 0th iteration is the observed
    # data.  Subsequent iterations are the uniform point data.
    messages.addMessage("Writing raw data.")
    outRawFCFullPath = os.path.join(outNetKLoc, outRawFCName)
    arcpy.CreateTable_management(outNetKLoc, outRawFCName)

    arcpy.AddField_management(outRawFCFullPath, "Iteration_Number", "LONG")
    arcpy.AddField_management(outRawFCFullPath, "Distance_Band",    "DOUBLE")
    arcpy.AddField_management(outRawFCFullPath, "Point_Count",      "DOUBLE")
    arcpy.AddField_management(outRawFCFullPath, "K_Function",       "DOUBLE")

    with arcpy.da.InsertCursor(outRawFCFullPath,
      ["Iteration_Number", "Distance_Band", "Point_Count", "K_Function"]) as cursor:
      for netKNum in range(0, len(netKCalculations)):
        for distBand in netKCalculations[netKNum]:
          cursor.insertRow([netKNum, distBand["distanceBand"], distBand["count"], distBand["KFunction"]])

    # Analyze the network k results (generate plottable output).
    # No confidence intervals are computed if there are no random permutations.
    messages.addMessage("Analyzing data.")
    if numPerms != 0:
      netKAn_95 = NetworkKAnalysis(.95, netKCalculations)
      netKAn_90 = NetworkKAnalysis(.90, netKCalculations)

    # Write the analysis data to a table.
    messages.addMessage("Writing analysis data.")
    outAnlFCFullPath = os.path.join(outNetKLoc, outAnlFCName)
    arcpy.CreateTable_management(outNetKLoc, outAnlFCName)
    arcpy.AddField_management(outAnlFCFullPath, "Description",   "TEXT")
    arcpy.AddField_management(outAnlFCFullPath, "Distance_Band", "DOUBLE")
    arcpy.AddField_management(outAnlFCFullPath, "Point_Count",   "DOUBLE")
    arcpy.AddField_management(outAnlFCFullPath, "K_Function",    "DOUBLE")

    with arcpy.da.InsertCursor(outAnlFCFullPath,
      ["Description", "Distance_Band", "Point_Count", "K_Function"]) as cursor:
      self.writeAnalysis(cursor, netKCalculations[0], "Observed")

      if numPerms != 0:
        self.writeAnalysis(cursor, netKAn_95.getLowerConfidenceEnvelope(), "2.5% Lower Bound")
        self.writeAnalysis(cursor, netKAn_95.getUpperConfidenceEnvelope(), "2.5% Upper Bound")
        self.writeAnalysis(cursor, netKAn_90.getLowerConfidenceEnvelope(), "5% Lower Bound")
        self.writeAnalysis(cursor, netKAn_90.getUpperConfidenceEnvelope(), "5% Upper Bound")

  ###
  # Calculate the length of networkDataset and return it.
  # @param networkDataset A network dataset which the points are on.
  # @param outCoordSys The output coordinate system.  Expected to be projected.
  ###
  def calculateLength(self, networkDataset, outCoordSys):
    ndDesc = arcpy.Describe(networkDataset)
    wsPath = arcpy.env.workspace

    # The length will get stored in a temporary table.
    lenTblName     = "TEMP_LENGTH_{0}".format(ndDesc.baseName)
    lenTblFullPath = os.path.join(wsPath, lenTblName)
    arcpy.NetworkDatasetLength_crashAnalysis(networkDataset, outCoordSys, wsPath, lenTblName)

    # Pull the length from the temporary length table.
    networkLength = 0
    with arcpy.da.SearchCursor(in_table=lenTblFullPath, field_names=["Network_Dataset_Length"]) as cursor:
      for row in cursor:
        networkLength += row[0]

    # Delete the temporary network length storage.
    arcpy.Delete_management(lenTblFullPath)

    return networkLength

  ###
  # Add random points to the network dataset and return the points table.
  # @param networkDataset A network dataset which the points are on.
  # @param outCoordSys The output coordinate system.  Expected to be projected.
  # @param numPoints The number of points to add.
  ###
  def generateRandomPoints(self, networkDataset, outCoordSys, numPoints):
    ndDesc = arcpy.Describe(networkDataset)
    wsPath = arcpy.env.workspace

    randPtsFCName   = "TEMP_RANDOM_POINTS_{0}".format(ndDesc.baseName)
    randPtsFullPath = os.path.join(wsPath, randPtsFCName)
    arcpy.NetworkDatasetRandomPoints_crashAnalysis(network_dataset=networkDataset,
      out_location=wsPath, output_point_feature_class=randPtsFCName, num_points=numPoints)

    return randPtsFullPath

  ###
  # Calculate the distances between each set of points using an OD Cost Matrix.
  # The distances are returned as an object.
  # @param networkDataset A network dataset which the points are on.
  # @param points The points to calculate distances between.
  # @param snapDist If a point is not directly on the network, it will be
  #        snapped to the nearset line if it is within this threshold.
  ###
  def calculateDistances(self, networkDataset, points, snapDist):
    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    # Create the cost matrix.
    costMatResult = arcpy.na.MakeODCostMatrixLayer(networkDataset, "TEMP_ODCM_NETWORK_K", "Length")
    odcmLayer     = costMatResult.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, points, "", snapDist)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   points, "", snapDist)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show the ODCM layer (it must be showing to open th ODLines sub layer below).
    #arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    #arcpy.RefreshTOC()

    # Get the "Lines" layer, which has the distance between each point.
    odcmLines = arcpy.mapping.ListLayers(odcmLayer, odcmSublayers["ODLines"])[0]

    # This array will hold all the OD distances.
    odDists = []

    # Get all the data from the distance data from the ODCM where the
    # origin and destination are not the same.
    where = """{0} <> {1}""".format(
      arcpy.AddFieldDelimiters(odcmLines, "originID"),
      arcpy.AddFieldDelimiters(odcmLines, "destinationID"))

    with arcpy.da.SearchCursor(
      in_table=odcmLines,
      field_names=["Total_Length", "originID", "destinationID"],
      where_clause=where) as cursor:

      for row in cursor:
        odDists.append({"Total_Length": row[0], "OriginID": row[1], "DestinationID": row[2]})

    return odDists

  # Write the analysis data in distBands using cursor.
  def writeAnalysis(self, cursor, distBands, description):
    for distBand in distBands:
        cursor.insertRow([description, distBand["distanceBand"], distBand["count"], distBand["KFunction"]])
