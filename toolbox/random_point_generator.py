import arcpy
import os

##
# This is a helper class that calculates the length of a network dataset,
# stores it in a temporary variable, and returns the length.
##
class RandomPointGenerator:
  def __init__(self):
    # The Network Dataset Length tool is used to find the length of the
    # network.  Import that tool's toolbox; it's is in the Crash
    # Analysis Toolbox (this tool's toolbox).
    toolboxPath     = os.path.dirname(os.path.abspath(__file__))
    toolboxName     = "Crash Analysis Toolbox.pyt"
    toolboxFullPath = os.path.join(toolboxPath, toolboxName)
    arcpy.ImportToolbox(toolboxFullPath)

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
