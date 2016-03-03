import arcpy

##
# This class generates an OD Cost Matrix for a set of points.  It then finds
# the length between each combination of points, and adds the lengths
# to a dictionary.
##
class ODCMDistanceCalculation:
  ###
  # Calculate the distances.
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
