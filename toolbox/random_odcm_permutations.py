import arcpy
import os
import k_function_helper
import k_function_timer
import random_odcm_permutations_svc

from arcpy import env

# ArcMap caching prevention.
k_function_helper            = reload(k_function_helper)
k_function_timer             = reload(k_function_timer)
random_odcm_permutations_svc = reload(random_odcm_permutations_svc)

from k_function_helper            import KFunctionHelper
from k_function_timer             import KFunctionTimer
from random_odcm_permutations_svc import RandomODCMPermutationsSvc

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
    # Analysis type.
    analysisType = arcpy.Parameter(
      displayName="Analysis Type",
      name = "analysis_type",
      datatype="GPString",
      parameterType="Required",
      direction="Input")
    atKeys                   = self.kfHelper.getAnalysisTypeSelection().keys()
    analysisType.filter.list = atKeys
    analysisType.value       = atKeys[0]

    # Input origin points features.
    srcPoints = arcpy.Parameter(
      displayName="Input Origin Points Feature Dataset (e.g. bridges)",
      name="srcPoints",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    srcPoints.filter.list = ["Point"]

    # Input destination origin features.
    destPoints = arcpy.Parameter(
      displayName="Input Destination Points Feature Dataset (e.g. crashes)",
      name="destPoints",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    destPoints.filter.list = ["Point"]

    # Network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Input Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    snapDist.value = 25

    # Cutoff distance.
    cutoff = arcpy.Parameter(
      displayName="Input Cutoff Distance",
      name="cutoff_distance",
      datatype="Double",
      parameterType="Optional",
      direction="Input")

    # Output location.
    outLoc = arcpy.Parameter(
      displayName="Output Location (Database Path)",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLoc.value = arcpy.env.workspace

    # Raw data feature class.
    outFC = arcpy.Parameter(
      displayName="Output Feature Class Name (Raw ODCM Data)",
      name = "output_raw_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outFC.value = "ODCM_Raw_Data"

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
   
    return [analysisType, srcPoints, destPoints, networkDataset, snapDist,
      cutoff, outLoc, outFC, numPerms, outCoordSys]

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
    networkDataset = parameters[3].value
    outCoordSys    = parameters[9].value

    # Default the coordinate system.
    if networkDataset is not None and outCoordSys is None:
      ndDesc = arcpy.Describe(networkDataset)
      # If the network dataset's coordinate system is a projected one,
      # use its coordinate system as the defualt.
      if (ndDesc.spatialReference.projectionName != "" and
        ndDesc.spatialReference.linearUnitName == "Meter" and
        ndDesc.spatialReference.factoryCode != 0):
        parameters[9].value = ndDesc.spatialReference.factoryCode

    # Enable/disable the destination points based on the analysis type.  CROSS has
    # sources and destinations; GLOBAL only has one set of points.
    analysisTypes = self.kfHelper.getAnalysisTypeSelection()
    if parameters[0].valueAsText in analysisTypes:
      if analysisTypes[parameters[0].valueAsText] == "CROSS":
        parameters[2].enabled = True
      else:
        parameters[2].enabled = False
        parameters[2].value = parameters[1].valueAsText

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[9].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[9].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      elif outCoordSys.linearUnitName != "Meter":
        parameters[9].setErrorMessage("Output coordinate system must have a linear unit code of 'Meter.'")
      else:
        parameters[9].clearMessage()

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    analysisType   = self.kfHelper.getAnalysisTypeSelection()[parameters[0].valueAsText]
    srcPoints      = parameters[1].valueAsText
    destPoints     = parameters[2].valueAsText
    networkDataset = parameters[3].valueAsText
    snapDist       = parameters[4].value
    cutoff         = parameters[5].value
    outLoc         = parameters[6].valueAsText
    outFC          = parameters[7].valueAsText
    numPerms       = self.kfHelper.getPermutationSelection()[parameters[8].valueAsText]
    outCoordSys    = parameters[9].value
    ndDesc         = arcpy.Describe(networkDataset)

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nAnalysis type: {0}".format(analysisType))
    messages.addMessage("Origin points: {0}".format(srcPoints))
    messages.addMessage("Destination points: {0}".format(destPoints))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Cutoff distance: {0}".format(cutoff))
    messages.addMessage("Path to output feature class: {0}".format(outLoc))
    messages.addMessage("Output feature class name: {0}".format(outFC))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}\n".format(outCoordSys.name))

    # The actual work is done in a reusable service.
    randODCMPermSvc = RandomODCMPermutationsSvc()
    randODCMPermSvc.generateODCMPermutations(analysisType, srcPoints, destPoints,
      networkDataset, snapDist, cutoff, outLoc, outFC, numPerms, outCoordSys, messages)
