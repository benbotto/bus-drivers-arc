import arcpy
import os.path
from arcpy import env

class Toolbox(object):
  def __init__(self):
    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"
    
    # Allows tool to be run multiple times, and overwrites any generated feature classes.
    env.overwriteOutput = True

    # List of tool classes associated with this toolbox
    self.tools = [CrashRadiusDensity, CrashNetworkDensity, NetworkKFunction]


class CrashRadiusDensity(object):

  def __init__(self):
    self.label = "Crash Radius Density"
    self.description = "This tool creates a feature that contains the density of crashes around each crash."
    self.canRunInBackground = False
  
  def getParameterInfo(self):
  
    # First parameter, input features (geodatabase)
    in_features = arcpy.Parameter(
      displayName="Input Features",
      name="in_features",
      datatype="Feature Layer",
      parameterType="Required",
      direction="Input")

    # Second parameter, input radius units
    radius_units = arcpy.Parameter(
      displayName="Radius Units",
      name="radius_units",
      datatype="String",
      parameterType="Required",
      direction="Input")

    radius_units.filter.type = "ValueList"
    radius_units.filter.list = ["METERS", "FEET", "KILOMETERS", "MILES"]
    radius_units.value = "METERS"
  
    # Third parameter, input radius magnitude
    radius_magnitude = arcpy.Parameter(
      displayName="Radius Magnitude",
      name="radius_magnitude",
      datatype="Long",
      parameterType="Required",
      direction="Input")
    radius_magnitude.filter.type = "Range"
    radius_magnitude.filter.list = [1,2000]
    radius_magnitude.value = 1000

    # Fourth parameter, _sum location
    sum_location = arcpy.Parameter(
      displayName="_Sum Name",
      name = "_Sum Location",
      datatype="String",
      parameterType="Required",
      direction="Input")
      
    #put the parameters in an array, for future use
    params = [in_features,radius_units,radius_magnitude,sum_location]

    return params

  def isLicensed(self):
    """Set whether tool is licensed to execute."""
    return True

  def updateParameters(self, parameters):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parameter
    has been changed."""

    if parameters[1].value == "METERS":
      parameters[2].filter.list = [1,2000]
      if parameters[2].value > 2000:
        parameters[2].value = 1000
    elif parameters[1].value == "FEET":
      parameters[2].filter.list = [1,6000]
      if parameters[2].value > 6000:
        parameters[2].value = 3000
    elif parameters[1].value == "MILES":
      parameters[2].filter.list = [1,50]
      if parameters[2].value > 50:
        parameters[2].value = 25
    elif parameters[1].value == "KILOMETERS":
      parameters[2].filter.list = [1,100]
      if parameters[2].value > 100:
        parameters[2].value = 50
    return

  def updateMessages(self, parameters):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    if parameters[1].hasError():
      parameters[1].setErrorMessage("The input you have entered is invalid. Please select one of the available units from the drop down menu.")
    return

  def execute(self, parameters, messages):
    # This is the feature (table) name that we're working with.
    featureName = parameters[0].valueAsText#the gdb file
    featureRadius = parameters[2].valueAsText + " " + parameters[1].valueAsText#the radius, with magnitude and units
    featureloc = parameters[3].valueAsText
    featureDesc = arcpy.Describe(featureName)
    messages.addMessage("Adding field 'Count' to feature {0}".format(featureName))

    # Add a Count column and default it to 1.
    # Not necessary, but kept here for reference.  The Join_Count field in the
    # "_sum" feature is used for this.
    #arcpy.AddField_management(featureName, "Count", "SHORT")
    #arcpy.CalculateField_management(featureName, "Count", "1", "PYTHON_9.3")

    # Create a buffer around each point.
    bufferFeature = featureDesc.catalogPath + "_buffer"
    messages.addMessage("Adding buffer to {0}".format(bufferFeature))
  
    arcpy.Buffer_analysis(featureName, bufferFeature, featureRadius)
  
    # Join the collision data and the collision buffer.
    #Here is where we would change the _sum file names.
    sumFeature = featureloc + "_sum"
    #sumFeature = featureDesc.catalogPath + "_sum"
    messages.addMessage("Summarizing to {0}".format(sumFeature))
    arcpy.SpatialJoin_analysis(bufferFeature, featureName, sumFeature)

    # Show the feature layer.
    '''
    sumLayer  = featureDesc.catalogPath + "_layer"
    mxd       = arcpy.mapping.MapDocument("CURRENT")
    dataFrame = arcpy.mapping.ListDataFrames(mxd, "*")[0]
    newLayer  = arcpy.mapping.Layer(sumFeature)
    arcpy.mapping.AddLayer(dataFrame, newLayer, "AUTO_ARRANGE")
    #arcpy.MakeFeatureLayer_management(featureName, "TEST")
    arcpy.RefreshActiveView()
    arcpy.RefreshTOC()
    '''
    return




class CrashNetworkDensity(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Crash Network Density"
    self.description = "Finds the distance between origins and destinations using a network dataset.  The network dataset can optionally be gerated automatically."
    self.canRunInBackground = False
  
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
    # Origins and destinations must be point feature classes.
    originDesc = arcpy.Describe(parameters[0].valueAsText)
    if originDesc.shapeType != "Point":
      parameters[0].setErrorMessage("The origin points are not of type 'Point'")
    
    destDesc = arcpy.Describe(parameters[3].valueAsText)
    if destDesc.shapeType != "Point":
      parameters[3].setErrorMessage("The destination points are not of type 'Point'")

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

class NetworkKFunction(object):
  ###
  # Initialize the tool.
  ###
  def __init__(self):
    self.label = "Network K Function"
    self.description = "Uses a Network K Function to analyze clustering and dispersion trends in a set of crash points."
    self.canRunInBackground = False
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
    # First parameter: input origin features.
    originPoints = arcpy.Parameter(
      displayName="Input Origin Feature Dataset",
      name="origin_points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    originPoints.filter.list = ["Point"]

    # Second parameter: input destination features.
    destPoints = arcpy.Parameter(
      displayName="Input Destination Feature Dataset",
      name="dest_points",
      datatype="Feature Class",
      parameterType="Required",
      direction="Input")
    destPoints.filter.list = ["Point"]

    # Third parameter: network dataset.
    networkDataset = arcpy.Parameter(
      displayName="Existing Network Dataset",
      name = "network_dataset",
      datatype="Network Dataset Layer",
      parameterType="Required",
      direction="Input")

    # Fourth parameter: number of distance increments.
    numInc = arcpy.Parameter(
      displayName="Input Number of Distance Increments",
      name="dist_increment",
      datatype="Long",
      parameterType="Required",
      direction="Input")
    numInc.filter.type  = "Range"
    numInc.filter.list  = [1, 100]
    numInc.value        = 10

    # Fifth parameter: beginning distance.
    begDist = arcpy.Parameter(
      displayName="Input Beginning Distance",
      name="beginning_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    begDist.value = 0

    # Sixth parameter: distance increment.
    distInc = arcpy.Parameter(
      displayName="Input Distance Increment",
      name="distance_increment",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 1000

    # Seventh parameter: snap distance.
    snapDist = arcpy.Parameter(
      displayName="Input Snap Distance",
      name="snap_distance",
      datatype="Double",
      parameterType="Required",
      direction="Input")
    distInc.value = 100
   
    params = [originPoints, destPoints, networkDataset, numInc, begDist, distInc, snapDist]
    return params

  ###
  # Check if the tool is available for use.
  ###
  def isLicensed(self):
    # Network Analyst tools must be available.
    if arcpy.CheckExtension("Network") != "Available":
      return False

  ###
  # Validate each input.
  ###
  def updateParameters(self, parameters):
    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):
    return

  ###
  # Execute the tool.
  ###
  def execute(self, parameters, messages):
    originPoints   = parameters[0].valueAsText
    destPoints     = parameters[1].valueAsText
    networkDataset = parameters[2].valueAsText
    numInc         = parameters[3].value
    begDist        = parameters[4].value
    distInc        = parameters[5].value
    snapDist       = parameters[6].value

    #if distInc is None:
    #  messages.addMessage("Distance increment is none... need to calculate it.")

    messages.addMessage("Origin points: {0}".format(originPoints))
    messages.addMessage("Destination points: {0}".format(destPoints))
    messages.addMessage("Network dataset: {0}".format(networkDataset))
    messages.addMessage("Number of distance increments: {0}".format(numInc))
    messages.addMessage("Beginning distance: {0}".format(begDist))
    messages.addMessage("Distance increment: {0}".format(distInc))
    messages.addMessage("Snap distance: {0}".format(snapDist))

    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]

    # Create the cost matrix.
    costMatResult = arcpy.na.MakeODCostMatrixLayer(networkDataset,
      "ODCM_{0}_{1}_{2}".format(networkDataset, originPoints, destPoints), "Length")
    odcmLayer     = costMatResult.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins and destinations to the ODCM.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, originPoints, "", snapDist)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destPoints,   "", snapDist)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show ODCM layer to the user.
    arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    arcpy.RefreshTOC()

    # Get the "Lines" layer, which has the distance between each point.
    #odcmSublayers = arcpy.na.GetNAClassNames(odcmLayer)
    #messages.addMessage("Sublayers {0}".format(odcmSublayers))
    odcmLines     = odcmSublayers["ODLines"]

    for i in range(0, numInc):
      # This is the OD Cost Matrix cutoff.
      cutoff = begDist + i * distInc
      messages.addMessage("Iteration: {0} Cutoff: {1}".format(i, cutoff))

      

    return
