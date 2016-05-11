import arcpy
import os
import network_k_calculation
import k_function_helper
import random_odcm_permutations_svc
import global_k_function_svc

from arcpy import env

# ArcMap caching prevention.
network_k_calculation        = reload(network_k_calculation)
k_function_helper            = reload(k_function_helper)
random_odcm_permutations_svc = reload(random_odcm_permutations_svc)
global_k_function_svc        = reload(global_k_function_svc)

from network_k_calculation        import NetworkKCalculation
from k_function_helper            import KFunctionHelper
from random_odcm_permutations_svc import RandomODCMPermutationsSvc
from global_k_function_svc        import GlobalKFunctionSvc

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
    # Input origin features.
    points = arcpy.Parameter(
      displayName="Input Points Feature Dataset",
      name="points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    points.filter.list = ["Point"]

    # Network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Input Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Number of distance increments.
    numBands = arcpy.Parameter(
      displayName="Input Number of Distance Bands",
      name="num_dist_bands",
      datatype="Long",
      parameterType="Optional",
      direction="Input")

    # Beginning distance.
    begDist = arcpy.Parameter(
      displayName="Input Beginning Distance",
      name="beginning_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    begDist.value = 0

    # Distance increment.
    distInc = arcpy.Parameter(
      displayName="Input Distance Increment",
      name="distance_increment",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 1000

    # Snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    snapDist.value = 25

    # Output location.
    outNetKLoc = arcpy.Parameter(
      displayName="Output Location (Database Path)",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outNetKLoc.value = arcpy.env.workspace

    # The raw ODCM data.
    outRawODCMFCName = arcpy.Parameter(
      displayName="Raw ODCM Data Table",
      name = "output_raw_odcm_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outRawODCMFCName.value = "Global_K_Raw_ODCM_Data"

    # The raw data feature class (e.g. observed and random point computations).
    outRawFCName = arcpy.Parameter(
      displayName="Raw Global-K Data Table (Raw Analysis Data)",
      name = "output_raw_analysis_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outRawFCName.value = "Global_K_Raw_Analysis_Data"

    # The analysis feature class.
    outAnlFCName = arcpy.Parameter(
      displayName="Global-K Summary Data (Plottable Data)",
      name = "output_analysis_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outAnlFCName.value = "Global_K_Summary_Data"

    # Confidence envelope (number of permutations).
    numPerms = arcpy.Parameter(
      displayName="Number of Random Point Permutations",
      name = "num_permutations",
      datatype="GPString",
      parameterType="Required",
      direction="Input")
    permKeys             = self.kfHelper.getPermutationSelection().keys()
    numPerms.filter.list = permKeys
    numPerms.value       = permKeys[0]

    # Projected coordinate system.
    outCoordSys = arcpy.Parameter(
      displayName="Output Network Dataset Length Projected Coordinate System",
      name="coordinate_system",
      datatype="GPSpatialReference",
      parameterType="Optional",
      direction="Input")
	  
    # Number of points field.
    numPointsFieldName = arcpy.Parameter(
      displayName="Number of Points Field",
      name = "num_points_field",
      datatype="GPString",
      parameterType="Optional",
      direction="Input")
   
    return [points, networkDataset, numBands, begDist, distInc, snapDist,
      outNetKLoc, outRawODCMFCName, outRawFCName, outAnlFCName, numPerms,
      outCoordSys, numPointsFieldName]

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
    outCoordSys    = parameters[11].value

    # Default the coordinate system.
    if networkDataset is not None and outCoordSys is None:
      ndDesc = arcpy.Describe(networkDataset)
      # If the network dataset's coordinate system is a projected one,
      # use its coordinate system as the defualt.
      if (ndDesc.spatialReference.projectionName != "" and
        ndDesc.spatialReference.linearUnitName == "Meter" and
        ndDesc.spatialReference.factoryCode != 0):
        parameters[11].value = ndDesc.spatialReference.factoryCode

    # Set the source of the fields (the network dataset).
    if networkDataset is not None:
      parameters[12].filter.list = self.kfHelper.getEdgeSourceFieldNames(networkDataset)

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[11].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[11].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      elif outCoordSys.linearUnitName != "Meter":
        parameters[11].setErrorMessage("Output coordinate system must have a linear unit code of 'Meter.'")
      else:
        parameters[11].clearMessage()

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    points             = parameters[0].valueAsText
    networkDataset     = parameters[1].valueAsText
    numBands           = parameters[2].value
    begDist            = parameters[3].value
    distInc            = parameters[4].value
    snapDist           = parameters[5].value
    outNetKLoc         = parameters[6].valueAsText
    outRawODCMFCName   = parameters[7].valueAsText
    outRawFCName       = parameters[8].valueAsText
    outAnlFCName       = parameters[9].valueAsText
    numPermsDesc       = parameters[10].valueAsText
    numPerms           = self.kfHelper.getPermutationSelection()[numPermsDesc]
    outCoordSys        = parameters[11].value
    numPointsFieldName = parameters[12].value
    ndDesc             = arcpy.Describe(networkDataset)
    gkfSvc             = GlobalKFunctionSvc()

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nOrigin points: {0}".format(points))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Number of distance bands: {0}".format(numBands))
    messages.addMessage("Beginning distance: {0}".format(begDist))
    messages.addMessage("Distance increment: {0}".format(distInc))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Output location (database path): {0}".format(outNetKLoc))
    messages.addMessage("Raw ODCM data table: {0}".format(outRawODCMFCName))
    messages.addMessage("Raw global-K data table (raw analysis data): {0}".format(outRawFCName))
    messages.addMessage("Global-K summary data (plottable data): {0}".format(outAnlFCName))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}\n".format(outCoordSys.name))
	messages.addMessage("Number of Points Field Name: {0}\n".format(numPointsFieldName))



    # Calculate the length of the network.
    networkLength = self.kfHelper.calculateLength(networkDataset, outCoordSys)
    messages.addMessage("Total network length: {0}".format(networkLength))

    # Count the number of crashes.
    numPoints = self.kfHelper.countNumberOfFeatures(os.path.join(outNetKLoc, points))

    # Set up a cutoff lenght for the ODCM data if possible.  (Optimization.)
    cutoff = gkfSvc.getCutoff(numBands, distInc, begDist)

    # The results of all the calculations end up here.
    netKCalculations = []

    # Use a mutable container for the number of bands so that the below callback
    # can write to it.  The "nonlocal" keyword not available in Python 2.x.
    numBandsCont = [numBands]

    # Callback function that does the Network K calculation on an OD cost matrix.    
    def doNetKCalc(odDists, iteration):
      # Do the actual network k-function calculation.
      netKCalc = NetworkKCalculation(networkLength, numPoints, odDists, begDist, distInc, numBandsCont[0])
      netKCalculations.append(netKCalc.getDistanceBands())

      # If the user did not specifiy a number of distance bands explicitly,
      # store the number of bands.  It's computed from the observed data.
      if numBandsCont[0] is None:
        numBandsCont[0] = netKCalc.getNumberOfDistanceBands()

    # Generate the ODCM permutations, including the ODCM for the observed data.
    # doNetKCalc is called on each iteration.
    randODCMPermSvc = RandomODCMPermutationsSvc()
    randODCMPermSvc.generateODCMPermutations("Global Analysis",
      points, points, networkDataset, snapDist, cutoff, outNetKLoc,
      outRawODCMFCName, numPerms, outCoordSys, numPointsFieldName,messages, doNetKCalc)

    # Store the raw analysis data.
    messages.addMessage("Writing raw analysis data.")
    gkfSvc.writeRawAnalysisData(outNetKLoc, outRawFCName, netKCalculations)

    # Analyze the data and store the results.
    messages.addMessage("Analyzing data.")
    gkfSvc.writeAnalysisSummaryData(numPerms, netKCalculations, outNetKLoc, outAnlFCName)
