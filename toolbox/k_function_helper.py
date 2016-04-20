import arcpy
import os

from collections import OrderedDict

###
# Helper functions that are shared by the various types of K functions.
###
class KFunctionHelper(object):
  ###
  # Initialize the helper class.
  ###
  def __init__(self):
    self.permutations = OrderedDict([
      ("0 Permutations (No Confidence Envelope)", 0),
      ("9 Permutations", 9),
      ("99 Permutations", 99),
      ("999 Permutations", 999)])

    self.analysisTypes = OrderedDict([
      ("Global Analysis", "GLOBAL"),
      ("Cross Analysis",  "CROSS")])

    self.caToolsImported = False

  # Helper function to import the crash analysis toolbox.
  def _importCAToolbox(self):
    if not self.caToolsImported:
      # The Network Dataset Length and Generate Random Points tools are used.
      # Import the toolbox.  It's is in the Crash Analysis Toolbox (this tool's
      # toolbox).
      toolboxPath     = os.path.dirname(os.path.abspath(__file__))
      toolboxName     = "Crash Analysis Toolbox.pyt"
      toolboxFullPath = os.path.join(toolboxPath, toolboxName)
      arcpy.ImportToolbox(toolboxFullPath)

      self.caToolsImported = True

  ###
  # Get a map of selectable permutation numbers.
  ###
  def getPermutationSelection(self):
    return self.permutations

  ###
  # Get a map of analysis types.
  ###
  def getAnalysisTypeSelection(self):
    return self.analysisTypes

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
    self._importCAToolbox()
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
    self._importCAToolbox()
    arcpy.NetworkDatasetRandomPoints_crashAnalysis(network_dataset=networkDataset,
      out_location=wsPath, output_point_feature_class=randPtsFCName, num_points=numPoints)

    return randPtsFullPath

  ###
  # Calculate the number of unique destination points in the OD cost matrix.
  # @param odDists An array of objects containing a DestinationID key.
  ###
  def countNumberOfDestinations(self, odDists):
    pointLookup = {}
    for odDist in odDists:
      pointLookup[odDist["DestinationID"]] = True
    return len(pointLookup.keys())
