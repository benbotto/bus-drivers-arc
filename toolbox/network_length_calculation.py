import arcpy
import os

##
# This is a helper class that calculates the length of a network dataset,
# stores it in a temporary variable, and returns the length.
##
class NetworkLengthCalculation:
  def __init__(self):
    # The Network Dataset Length tool is used to find the length of the
    # network.  Import that tool's toolbox; it's is in the Crash
    # Analysis Toolbox (this tool's toolbox).
    toolboxPath     = os.path.dirname(os.path.abspath(__file__))
    toolboxName     = "Crash Analysis Toolbox.pyt"
    toolboxFullPath = os.path.join(toolboxPath, toolboxName)
    arcpy.ImportToolbox(toolboxFullPath)

  ###
  # Calculate the length and return it.
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
