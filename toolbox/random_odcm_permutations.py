import arcpy
import os
import k_function_helper

from arcpy import env

# ArcMap caching prevention.
k_function_helper = reload(k_function_helper)

from k_function_helper import KFunctionHelper

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

    # Fifth parameter: output location.
    outLoc = arcpy.Parameter(
      displayName="Output Location (Database Path)",
      name="out_location",
      datatype="DEWorkspace",
      parameterType="Required",
      direction="Input")
    outLoc.value = arcpy.env.workspace

    # Sixth parameter: the raw data feature class.
    outRawFCName = arcpy.Parameter(
      displayName="Output Feature Class Name (Raw ODCM Data)",
      name = "output_raw_feature_class",
      datatype="GPString",
      parameterType="Required",
      direction="Output")
    outRawFCName.value = "ODCM_Raw_Data"

    # Seventh parameter: confidence envelope (number of permutations).
    numPerms = arcpy.Parameter(
      displayName="Number of Random Point Permutations",
      name = "num_permutations",
      datatype="GPString",
      parameterType="Required",
      direction="Input")
    permKeys             = self.kfHelper.getPermutationSelection().keys()
    numPerms.filter.list = permKeys
    numPerms.value       = permKeys[0]

    # Eigth parameter: projected coordinate system.
    outCoordSys = arcpy.Parameter(
      displayName="Output Network Dataset Length Projected Coordinate System",
      name="coordinate_system",
      datatype="GPSpatialReference",
      parameterType="Optional",
      direction="Input")
   
    return [srcPoints, destPoints, networkDataset, snapDist, outLoc,
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
    outCoordSys    = parameters[7].value

    # Default the coordinate system.
    if networkDataset is not None and outCoordSys is None:
      ndDesc = arcpy.Describe(networkDataset)
      # If the network dataset's coordinate system is a projected one,
      # use its coordinate system as the defualt.
      if (ndDesc.spatialReference.projectionName != "" and
        ndDesc.spatialReference.linearUnitName == "Meter" and
        ndDesc.spatialReference.factoryCode != 0):
        parameters[11].value = ndDesc.spatialReference.factoryCode

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    outCoordSys = parameters[7].value

    if outCoordSys is not None:
      if outCoordSys.projectionName == "":
        parameters[7].setErrorMessage("Output coordinate system must be a projected coordinate system.")
      elif outCoordSys.linearUnitName != "Meter":
        parameters[7].setErrorMessage("Output coordinate system must have a linear unit code of 'Meter.'")
      else:
        parameters[7].clearMessage()
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    srcPoints      = parameters[0].valueAsText
    destPoints     = parameters[1].valueAsText
    networkDataset = parameters[2].valueAsText
    snapDist       = parameters[3].value
    outLoc         = parameters[4].valueAsText
    outRawFCName   = parameters[5].valueAsText
    numPerms       = self.kfHelper.getPermutationSelection()[parameters[6].valueAsText]
    outCoordSys    = parameters[7].value
    ndDesc         = arcpy.Describe(networkDataset)

    # Refer to the note in the NetworkDatasetLength tool.
    if outCoordSys is None:
      outCoordSys = ndDesc.spatialReference

    messages.addMessage("\nOrigin points: {0}".format(srcPoints))
    messages.addMessage("Destination points: {0}".format(destPoints))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Snap distance: {0}".format(snapDist))
    messages.addMessage("Path to output feature class: {0}".format(outLoc))
    messages.addMessage("Output feature class name (raw cross-K data): {0}".format(outRawFCName))
    messages.addMessage("Number of random permutations: {0}".format(numPerms))
    messages.addMessage("Network dataset length projected coordinate system: {0}\n".format(outCoordSys.name))
  