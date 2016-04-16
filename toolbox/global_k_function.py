import arcpy
import os
import network_k_calculation
import network_k_analysis
import k_function_helper
import k_function_timer

from arcpy import env

# ArcMap caching prevention.
network_k_calculation = reload(network_k_calculation)
network_k_analysis    = reload(network_k_analysis)
k_function_helper     = reload(k_function_helper)
k_function_timer      = reload(k_function_timer)

from network_k_calculation import NetworkKCalculation
from network_k_analysis    import NetworkKAnalysis
from k_function_helper     import KFunctionHelper
from k_function_timer      import KFunctionTimer

class GlobalKFunction(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label              = "Global K Function"
    self.description        = "Uses a Global Network K Function to analyze clustering and dispersion trends in a set of crash points."
    self.canRunInBackground = False
    env.overwriteOutput     = True
    self.kfHelper           = KFunctionHelper()
  
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
    permKeys             = self.kfHelper.getPermutationSelection().keys()
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
    numPerms       = self.kfHelper.getPermutationSelection()[parameters[9].valueAsText]
    outCoordSys    = parameters[10].value
    ndDesc         = arcpy.Describe(networkDataset)

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nOrigin points: {0}".format(points))
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

    # Calculate the length of the network.
    networkLength = self.kfHelper.calculateLength(networkDataset, outCoordSys)
    messages.addMessage("Total network length: {0}".format(networkLength))

    # The results of all the calculations end up here.
    netKCalculations = []

    # Observed distance bands.
    # Make the ODCM and calculate the distance between each set of points.
    odDists = self.kfHelper.calculateDistances(networkDataset, points, points, snapDist)

    # Do the actual network k-function calculation and return the result.
    netKCalc  = NetworkKCalculation(networkLength, odDists, begDist, distInc, numBands)
    numPoints = netKCalc.getNumberOfPoints()
    numBands  = netKCalc.getNumberOfDistanceBands()
    netKCalculations.append(netKCalc.getDistanceBands())
    messages.addMessage("Iteration 0 (observed) complete.")

    # Generate a set of random points on the network.
    kfTimer = KFunctionTimer(numPerms)
    for i in range(1, numPerms + 1):
      randPoints = self.kfHelper.generateRandomPoints(networkDataset, outCoordSys, numPoints)
      odDists    = self.kfHelper.calculateDistances(networkDataset, randPoints, randPoints, snapDist)
      netKCalc   = NetworkKCalculation(networkLength, odDists, begDist, distInc, numBands)
      netKCalculations.append(netKCalc.getDistanceBands())

      # Clean up the random points table.
      arcpy.Delete_management(randPoints)

      # Show the progress.
      kfTimer.increment()
      messages.addMessage("Iteration {0} complete.  Elapsed time: {1}s.  ETA: {2}s.".format(
        i, kfTimer.getElapsedTime(), kfTimer.getETA()))

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

  # Write the analysis data in distBands using cursor.
  def writeAnalysis(self, cursor, distBands, description):
    for distBand in distBands:
      cursor.insertRow([description, distBand["distanceBand"], distBand["count"], distBand["KFunction"]])
