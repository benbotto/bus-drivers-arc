import arcpy
import os.path
from arcpy import env

class CrashNetworkDensity(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Crash Network Density"
    self.description = "Finds the distance between origins and destinations using a network dataset.  The network dataset can optionally be gerated automatically."
    self.canRunInBackground = False

    env.overwriteOutput = True
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter, input origin features.
    origin_points = arcpy.Parameter(
        displayName="Input Origin Feature Dataset",
        name="origin_points",
        datatype="Feature Class",
        parameterType="Required",
        direction="Input")
    origin_points.filter.list = ["Point"]

    # Second parameter, input origin snap distance units.
    origin_snap_units = arcpy.Parameter(
        displayName="Origin Layer Snap Distance Units",
        name="origin_snap_units",
        datatype="String",
        parameterType="Required",
        direction="Input")

    origin_snap_units.filter.type = "ValueList"
    origin_snap_units.filter.list = ["METERS", "FEET", "KILOMETERS", "MILES"]
    origin_snap_units.value = "METERS"
  
    # Third parameter, input origin snap distance magnitude.
    origin_snap = arcpy.Parameter(
        displayName="Origin Layer Snap Distance Magnitude",
        name="origin_snap",
        datatype="Long",
        parameterType="Required",
        direction="Input")
    origin_snap.filter.type = "Range"
    origin_snap.filter.list = [1,500]
    origin_snap.value = 10

    # Fourth parameter, input destination features.
    dest_points = arcpy.Parameter(
        displayName="Input Destination Feature Dataset",
        name="dest_points",
        datatype="Feature Class",
        parameterType="Required",
        direction="Input")
    dest_points.filter.list = ["Point"]

    # Fifth parameter, input destination snap distance units.
    dest_snap_units = arcpy.Parameter(
        displayName="Destination Layer Snap Distance Units",
        name="dest_snap_units",
        datatype="String",
        parameterType="Required",
        direction="Input")

    dest_snap_units.filter.type = "ValueList"
    dest_snap_units.filter.list = ["METERS", "FEET", "KILOMETERS", "MILES"]
    dest_snap_units.value = "METERS"
  
    # Sixth parameter, input destination snap distance magnitude.
    dest_snap = arcpy.Parameter(
        displayName="Destination Layer Snap Distance Magnitude",
        name="dest_snap",
        datatype="Long",
        parameterType="Required",
        direction="Input")
    dest_snap.filter.type = "Range"
    dest_snap.filter.list = [1,500]
    dest_snap.value = 10

    # Seventh parameter, drivetime cutoff.
    drivetime_cutoff_meters = arcpy.Parameter(
        displayName="Enter Drive Distance Cutoff in Meters",
        name = "drivetime_cutoff_meters",
        datatype="Double",
        parameterType="Required",
        direction="Input")
    drivetime_cutoff_meters.value = 1000

    # Eigth parameter, OSM dataset name.
    dataset_name = arcpy.Parameter(
        displayName="Enter Name of OSM Dataset to be Created",
        name = "dataset_name",
        datatype="String",
        parameterType="Optional",
        direction="Input")

    # Ninth parameter, optional network dataset.
    network_dataset = arcpy.Parameter(
        displayName="Existing Network Dataset",
        name = "network_dataset",
        datatype="Network Dataset Layer",
        parameterType="Optional",
        direction="Input")

    params = [origin_points, origin_snap_units, origin_snap, dest_points, dest_snap_units, dest_snap, drivetime_cutoff_meters, dataset_name, network_dataset]

    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    # Network Analyst tools must be available.
    if arcpy.CheckExtension("Network") != "Available":
      return False

    # Make sure the OSM toolbox can be found.
    instInfo    = arcpy.GetInstallInfo()
    osmToolPath = instInfo["InstallDir"] + r"ArcToolbox\Toolboxes\OpenStreetMap Toolbox.tbx"
    return os.path.isfile(osmToolPath)

  ###
  # Validate each input.
  ###
  def updateParameters(self, parameters):
    if parameters[1].value == "METERS":
      parameters[2].filter.list = [1,500]
      if parameters[2].value > 500:
        parameters[2].value = 500
    elif parameters[1].value == "FEET":
      parameters[2].filter.list = [1,1500]
      if parameters[2].value > 1500:
        parameters[2].value = 1500
    elif parameters[1].value == "MILES":
      parameters[2].filter.list = [1,2]
      if parameters[2].value > 2:
        parameters[2].value = 2
    elif parameters[1].value == "KILOMETERS":
      parameters[2].filter.list = [1,3]
      if parameters[2].value > 3:
        parameters[2].value = 3
      
    if parameters[4].value == "METERS":
      parameters[5].filter.list = [1,500]
      if parameters[5].value > 500:
        parameters[5].value = 500
    elif parameters[4].value == "FEET":
      parameters[5].filter.list = [1,1500]
      if parameters[5].value > 1500:
        parameters[5].value = 1500
    elif parameters[4].value == "MILES":
      parameters[5].filter.list = [1,2]
      if parameters[5].value > 2:
        parameters[5].value = 2
    elif parameters[4].value == "KILOMETERS":
      parameters[5].filter.list = [1,3]
      if parameters[5].value > 3:
        parameters[5].value = 3

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    # There must be valid units for the snap distances.
    if parameters[1].hasError():
      parameters[1].setErrorMessage("The input you have entered is invalid. Please select one of the available units from the drop down menu.")

    if parameters[4].hasError():
      parameters[4].setErrorMessage("The input you have entered is invalid. Please select one of the available units from the drop down menu.")

    if parameters[7].valueAsText == None and parameters[8].valueAsText == None:
      parameters[7].setErrorMessage("Either a new dataset name or an existing network dataset is required.")

    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    # Load the OpenStreetMap toolbox.
    instInfo    = arcpy.GetInstallInfo()
    osmToolPath = instInfo["InstallDir"] + r"ArcToolbox\Toolboxes\OpenStreetMap Toolbox.tbx"
    arcpy.ImportToolbox(osmToolPath)
  
    originTableName    = parameters[0].valueAsText
    originSnapDistance = parameters[2].valueAsText + " " + parameters[1].valueAsText

    destinationTableName    = parameters[3].valueAsText
    destinationSnapDistance = parameters[5].valueAsText + " " + parameters[4].valueAsText

    # Drivetime cutoff meters.
    drivetime_cutoff_meters = parameters[6].valueAsText

    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    if parameters[7].valueAsText != None:
      ##
      # User chose to make a new network dataset from OSM.
      ##

      # Note that this has "\\".  10.1 has a hard time finding the directory of the _ND file otherwise.
      dataset_name    = parameters[7].valueAsText
      dataset_name_nd = parameters[7].valueAsText + "\\" + parameters[7].valueAsText +"_ND"

      # The DataFrame object has an "extent" object that has the XMin, XMax, YMin, and YMax.
      extent = dataFrame.extent
      messages.addMessage("Using window extents.  XMin: {0}, XMax: {1}, YMin: {2}, YMax: {3}".format(extent.XMin, extent.XMax, extent.YMin, extent.YMax))

      # Download the data from OSM.
      arcpy.DownloadExtractSymbolizeOSMData2_osmtools(extent, True, dataset_name, "OSMLayer")

      # Convert the OSM data to a network dataset.
      arcpy.OSMGPCreateNetworkDataset_osmtools(dataset_name, "DriveGeneric.xml", "ND")
    else:
      # Use selected dataset.
      dataset_name_nd = parameters[8].valueAsText
      messages.addMessage("Using existing network dataset: {0}".format(dataset_name_nd))

    # Create the OD Cost Matrix layer and get a refrence to the layer.
    result    = arcpy.na.MakeODCostMatrixLayer(dataset_name_nd, "OD Cost Matrix", "Length", drivetime_cutoff_meters)
    odcmLayer = result.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, originTableName, "", originSnapDistance)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destinationTableName, "", destinationSnapDistance)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show ODCM layer to the user.
    arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    
    # Save a cost matrix layer.  In 10.1 there is a bug that prevents layers from
    # being added progranmatically.
    odcmLayer.saveACopy("ODCM_Network_Crash_Density.lyr")
    arcpy.RefreshTOC()
    
    return