import arcpy
import os
import k_function_helper
import k_function_timer

from arcpy import env

# ArcMap caching prevention.
k_function_helper = reload(k_function_helper)
k_function_timer  = reload(k_function_timer)

from k_function_helper import KFunctionHelper
from k_function_timer  import KFunctionTimer

class RandomODCMPermutations(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label              = "Random ODCM Permutations"
    self.description        = "Generates OD Cost Matrices with oberved data and a complementrary set of random point permutations."
    self.canRunInBackground = False
    env.overwriteOutput     = True
    self.kfHelper           = KFunctionHelper()
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter: input origin points features.
    srcPoints = arcpy.Parameter(
      displayName="Input Origin Points Feature Dataset (e.g. bridges)",
      name="srcPoints",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    srcPoints.filter.list = ["Point"]

    # Second parameter: input destination origin features.
    destPoints = arcpy.Parameter(
      displayName="Input Destination Points Feature Dataset (e.g. crashes)",
      name="destPoints",
      datatype="Feature Class",
      parameterType="Optional",
      direction="Input")
    destPoints.filter.list = ["Point"]

    # Third parameter: network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Input Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Fourth parameter: snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    snapDist.value = 25

    # Fifth parameter: snap distance.
    cutoff = arcpy.Parameter(
      displayName="Input Cutoff Distance",
      name="cutoff_distance",
      datatype="Double",
      parameterType="Optional",
      direction="Input")

    # Sixth parameter: output location.
    outLoc = arcpy.Parameter(
      displayName="Output Location (Database Path)",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLoc.value = arcpy.env.workspace

    # Seventh parameter: the raw data feature class.
    outRawFCName = arcpy.Parameter(
      displayName="Output Feature Class Name (Raw ODCM Data)",
      name = "output_raw_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outRawFCName.value = "ODCM_Raw_Data"

    # Eigth parameter: confidence envelope (number of permutations).
    numPerms = arcpy.Parameter(
      displayName="Number of Random Point Permutations",
      name = "num_permutations",
      datatype="GPString",
      parameterType="Required",
      direction="Input")
    permKeys             = self.kfHelper.getPermutationSelection().keys()
    numPerms.filter.list = permKeys
    numPerms.value       = permKeys[0]

    # Ninth parameter: projected coordinate system.
    outCoordSys = arcpy.Parameter(
      displayName="Output Network Dataset Length Projected Coordinate System",
      name="coordinate_system",
      datatype="GPSpatialReference",
      parameterType="Optional",
      direction="Input")
   
    return [srcPoints, destPoints, networkDataset, snapDist, cutoff, outLoc,
      outRawFCName, numPerms, outCoordSys]

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
    outCoordSys    = parameters[8].value

    # Default the coordinate system.
    if networkDataset is not None and outCoordSys is None:
      ndDesc = arcpy.Describe(networkDataset)
      # If the network dataset's coordinate system is a projected one,
      # use its coordinate system as the defualt.
      if (ndDesc.spatialReference.projectionName != "" and
        ndDesc.spatialReference.linearUnitName == "Meter" and
        ndDesc.spatialReference.factoryCode != 0):
        parameters[8].value = ndDesc.spatialReference.factoryCode

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[8].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[8].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      elif outCoordSys.linearUnitName != "Meter":
        parameters[8].setErrorMessage("Output coordinate system must have a linear unit code of 'Meter.'")
      else:
        parameters[8].clearMessage()
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    srcPoints      = parameters[0].valueAsText
    destPoints     = parameters[1].valueAsText
    networkDataset = parameters[2].valueAsText
    snapDist       = parameters[3].value
    cutoff         = parameters[4].value
    outLoc         = parameters[5].valueAsText
    outRawFCName   = parameters[6].valueAsText
    numPerms       = self.kfHelper.getPermutationSelection()[parameters[7].valueAsText]
    outCoordSys    = parameters[8].value
    ndDesc         = arcpy.Describe(networkDataset)

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nOrigin points: {0}".format(srcPoints))
    messages.addMessage("Destination points: {0}".format(destPoints))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Cutoff distance: {0}".format(cutoff))
    messages.addMessage("Path to output feature class: {0}".format(outLoc))
    messages.addMessage("Output feature class name: {0}".format(outRawFCName))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}\n".format(outCoordSys.name))

    # This is the full path to the output feature class.
    outFCFullPath = os.path.join(outLoc, outRawFCName)

    # Create the output table.
    arcpy.CreateTable_management(outLoc, outRawFCName)
    arcpy.AddField_management(outFCFullPath, "Iteration_Number", "LONG")
    arcpy.AddField_management(outFCFullPath, "OriginID",         "LONG")
    arcpy.AddField_management(outFCFullPath, "DestinationID",    "LONG")
    arcpy.AddField_management(outFCFullPath, "Total_Length",     "DOUBLE")

    # Observed distance bands.
    # Make the ODCM and calculate the distance between each set of points.
    odDists = self.calculateDistances(networkDataset, srcPoints, destPoints, snapDist, cutoff)
    self.writeODCMData(odDists, 0, outFCFullPath)

    # Count the number of unique destinations in the resulting ODCM.  These are
    # the "crash" points.  During each permutation below, this number of random
    # points will be created on the network.
    numDests = self.kfHelper.countNumberOfDestinations(odDists)

    # Generate the OD Cost matrix permutations.
    kfTimer = KFunctionTimer(numPerms)
    for i in range(0, numPerms):
      randPoints = self.kfHelper.generateRandomPoints(networkDataset, outCoordSys, numDests)
      odDists    = self.calculateDistances(networkDataset, randPoints, randPoints, snapDist, cutoff) # TODO: src/dest global or cross.
      self.writeODCMData(odDists, i, outFCFullPath)
      #netKCalc   = NetworkKCalculation(networkLength, odDists, begDist, distInc, numBands)
      #netKCalculations.append(netKCalc.getDistanceBands()) # TODO: write to table.

      # Clean up the random points table.
      arcpy.Delete_management(randPoints)

      # Show the progress.
      kfTimer.increment()
      messages.addMessage("Iteration {0} complete.  Elapsed time: {1}s.  ETA: {2}s.".format(
        i, kfTimer.getElapsedTime(), kfTimer.getETA()))

  ###
  # Calculate the distances between each set of points using an OD Cost Matrix.
  # @param networkDataset A network dataset which the points are on.
  # @param srcPoints The source points to calculate distances from.
  # @param destPoints The destination points to calculate distances to.
  # @param snapDist If a point is not directly on the network, it will be
  #        snapped to the nearset line if it is within this threshold.
  # @param cutoff The cutoff distance for the ODCM (optional).
  ###
  def calculateDistances(self, networkDataset, srcPoints, destPoints, snapDist, cutoff):
    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    # Create the cost matrix.
    costMatResult = arcpy.na.MakeODCostMatrixLayer(networkDataset, "TEMP_ODCM_NETWORK_K", "Length", cutoff)
    odcmLayer     = costMatResult.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, srcPoints,  "", snapDist)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destPoints, "", snapDist)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show the ODCM layer (it must be showing to open th ODLines sub layer below).
    #arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    #arcpy.RefreshTOC()

    # Get the "Lines" layer, which has the distance between each point.
    odcmLines = arcpy.mapping.ListLayers(odcmLayer, odcmSublayers["ODLines"])[0]

    # This array will hold all the OD distances.
    odDists = []

    if srcPoints == destPoints:
      # If the source points and destination points are the same, exclude the
      # distance from the point to itself.
      where = """{0} <> {1}""".format(
        arcpy.AddFieldDelimiters(odcmLines, "originID"),
        arcpy.AddFieldDelimiters(odcmLines, "destinationID"))
    else:
      where = ""

    with arcpy.da.SearchCursor(
      in_table=odcmLines,
      field_names=["Total_Length", "originID", "destinationID"],
      where_clause=where) as cursor:

      for row in cursor:
        odDists.append({"Total_Length": row[0], "OriginID": row[1], "DestinationID": row[2]})

    return odDists
  
  ###
  # Write the ODCM data to a table.
  # @param odDists The ODCM data.
  # @param iteration The iteration number.
  # @param tablePath The full path to the output table.
  ###
  def writeODCMData(self, odDists, iteration, tablePath):
    with arcpy.da.InsertCursor(tablePath,
      ["Iteration_Number", "OriginID", "DestinationID", "Total_Length"]) as cursor:
      for odDist in odDists:
        cursor.insertRow([iteration, odDist["OriginID"], odDist["DestinationID"], odDist["Total_Length"]])
