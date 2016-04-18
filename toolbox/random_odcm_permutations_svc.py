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

class RandomODCMPermutationsSvc:
  ###
  # Initialize the service (stateless).
  ###
  def __init__(self):
    self.kfHelper = KFunctionHelper()

  ###
  # Generate the ODCM permutations.
  # @param analysisType Either Global Analysis or Cross Analysis.
  # @param srcPoints The source points.
  # @param destPoints The destination points.  Ignored if analysisType is GLOBAL.
  # @param networkDataset The network dataset to use for the ODCMs.
  # @param snapDist The snap distance for points that are not directly on the network.
  # @param cutoff The cutoff distance.  Ignored if None.
  # @param outLoc The full path to a database.  The ODCM data will be written here.
  # @param outFC The name of the feature class in outLoc where the ODCM data will be written.
  # @param numPerms The number of permutations (string representation).
  # @param outCoordSys The coordinate system to project the points into (optional).
  # @param messages A messages instances with addMessage() implemented (for debug output).
  ###
  def generateODCMPermutations(self, analysisType, srcPoints, destPoints,
    networkDataset, snapDist, cutoff, outLoc, outFC, numPerms, outCoordSys, messages):
    # This is the full path to the output feature class.
    outFCFullPath = os.path.join(outLoc, outFC)

    # Create the output table.
    arcpy.CreateTable_management(outLoc, outFC)
    arcpy.AddField_management(outFCFullPath, "Iteration_Number", "LONG")
    arcpy.AddField_management(outFCFullPath, "OriginID",         "LONG")
    arcpy.AddField_management(outFCFullPath, "DestinationID",    "LONG")
    arcpy.AddField_management(outFCFullPath, "Total_Length",     "DOUBLE")

    # Make the observed ODCM and calculate the distance between each set of
    # points.  If a cross analysis is selected, find the distance between the
    # source and destination points.  Otherwise there is only one set of points
    if analysisType == "CROSS":
      odDists = self.calculateDistances(networkDataset, srcPoints, destPoints, snapDist, cutoff)
    else:
      odDists = self.calculateDistances(networkDataset, srcPoints, srcPoints, snapDist, cutoff)
    self.writeODCMData(odDists, 0, outFCFullPath)

    # Count the number of unique destinations in the resulting ODCM.  These are
    # the "crash" points.  During each permutation below, this number of random
    # points will be created on the network.
    numDests = self.kfHelper.countNumberOfDestinations(odDists)

    # Generate the OD Cost matrix permutations.
    kfTimer = KFunctionTimer(numPerms)
    for i in range(1, numPerms + 1):
      randPoints = self.kfHelper.generateRandomPoints(networkDataset, outCoordSys, numDests)

      # See the note above: Either find the distance from the source points to the random points,
      # or the distance between the random points.
      if analysisType == "CROSS":
        odDists = self.calculateDistances(networkDataset, srcPoints, randPoints, snapDist, cutoff)
      else:
        odDists = self.calculateDistances(networkDataset, randPoints, randPoints, snapDist, cutoff)
      self.writeODCMData(odDists, i, outFCFullPath)

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
