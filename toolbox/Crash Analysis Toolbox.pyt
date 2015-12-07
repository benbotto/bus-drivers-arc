import arcpy
import os.path
from arcpy import env

class Toolbox(object):
  def __init__(self):
    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"
    arcpy.env.overwriteOutput = True #allows tool to be ran again if user decides to. will need to assess for recursive tools

    # List of tool classes associated with this toolbox
    self.tools = [CrashRadiusDensity, CrashNetworkDensity]


class CrashRadiusDensity(object):

  def __init__(self):
    self.label = "CrashRadiusDensity"
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
    self.label = "CrashNetworkDensity"
    self.description = "Finds the density of crashes using an auto-generated network dataset."
    self.canRunInBackground = False
  
  ###
  # Get input from the users.
  ###
  def getParameterInfo(self):
  
    # First parameter, input origin features.
    in_table1 = arcpy.Parameter(
        displayName="Input Origin Feature Dataset",
        name="in_table1",
        datatype="Feature Class",
        parameterType="Required",
        direction="Input")

    # Second parameter, input origin snap distance units.
    radius_units1 = arcpy.Parameter(
        displayName="Origin Layer Snap Distance Units",
        name="radius_units1",
        datatype="String",
        parameterType="Required",
        direction="Input")

    radius_units1.filter.type = "ValueList"
    radius_units1.filter.list = ["METERS", "FEET", "KILOMETERS", "MILES"]
    radius_units1.value = "METERS"
  
    # Third parameter, input origin snap distance magnitude.
    radius_magnitude1 = arcpy.Parameter(
        displayName="Origin Layer Snap Distance Magnitude",
        name="radius_magnitude1",
        datatype="Long",
        parameterType="Required",
        direction="Input")
    radius_magnitude1.filter.type = "Range"
    radius_magnitude1.filter.list = [1,2000]
    radius_magnitude1.value = 1000

    # Fourth parameter, input destination features.
    in_table2 = arcpy.Parameter(
        displayName="Input Destination Feature Dataset",
        name="in_table2",
        datatype="Feature Class",
        parameterType="Required",
        direction="Input")

    # Fifth parameter, input destination snap distance units.
    radius_units2 = arcpy.Parameter(
        displayName="Destination Layer Snap Distance Units",
        name="radius_units2",
        datatype="String",
        parameterType="Required",
        direction="Input")

    radius_units2.filter.type = "ValueList"
    radius_units2.filter.list = ["METERS", "FEET", "KILOMETERS", "MILES"]
    radius_units2.value = "METERS"
  
    # Sixth parameter, input destination snap distance magnitude.
    radius_magnitude2 = arcpy.Parameter(
        displayName="Destination Layer Snap Distance Magnitude",
        name="radius_magnitude2",
        datatype="Long",
        parameterType="Required",
        direction="Input")
    radius_magnitude2.filter.type = "Range"
    radius_magnitude2.filter.list = [1,2000]
    radius_magnitude2.value = 1000

    # Seventh parameter, OSM dataset name.
    dataset_name = arcpy.Parameter(
        displayName="Enter Name of OSM Dataset to be Created",
        name = "dataset_name",
        datatype="String",
        parameterType="Required",
        direction="Input")

    # Eighth parameter, drivetime cutoff.
    # TODO: Needs units.
    drivetime_cutoff_meters = arcpy.Parameter(
        displayName="Enter Drivetime Cutoff in Meters",
        name = "drivetime_cutoff_meters",
        datatype="Double",
        parameterType="Required",
        direction="Input")
   
    params = [in_table1, radius_units1, radius_magnitude1,in_table2, radius_units2, radius_magnitude2, dataset_name, drivetime_cutoff_meters]
    
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
      
    if parameters[4].value == "METERS":
      parameters[5].filter.list = [1,2000]
      if parameters[5].value > 2000:
        parameters[5].value = 1000
    elif parameters[4].value == "FEET":
      parameters[5].filter.list = [1,6000]
      if parameters[5].value > 6000:
        parameters[5].value = 3000
    elif parameters[4].value == "MILES":
      parameters[5].filter.list = [1,50]
      if parameters[5].value > 50:
        parameters[5].value = 25
    elif parameters[4].value == "KILOMETERS":
      parameters[5].filter.list = [1,100]
      if parameters[5].value > 100:
        parameters[5].value = 50

    return

  ###
  # If any fields are invalid, show an appropriate error message.
  ###
  def updateMessages(self, parameters):  
    if parameters[1].hasError():
      parameters[1].setErrorMessage("The input you have entered is invalid. Please select one of the available units from the drop down menu.")

    if parameters[4].hasError():
      parameters[4].setErrorMessage("The input you have entered is invalid. Please select one of the available units from the drop down menu.")

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

    dataset_name    = parameters[6].valueAsText
    # Note that this has "\\".  10.1 has a hard time finding the directory of the _ND file otherwise.
    dataset_name_nd = parameters[6].valueAsText + "\\" + parameters[6].valueAsText +"_ND"

    # Drivetime cutoff minutes.
    drivetime_cutoff_meters = parameters[7].valueAsText

    # This is the current map, which should be an OSM base map.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")

    # Get the data from from the map (see the DataFrame object of arcpy).
    # The DataFrame object has an "extent" object that has the XMin, XMax, YMin, and YMax.
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]
    extent    = dataFrame.extent

    messages.addMessage("Using window extents.")
    messages.addMessage("XMin: {0}, XMax: {1}, YMin: {2}, YMax: {3}".format(extent.XMin, extent.XMax, extent.YMin, extent.YMax))

    # Download the data from OSM.
    # TODO: Use should be able to select a dataset.
    arcpy.DownloadExtractSymbolizeOSMData2_osmtools(extent, True, dataset_name, "OSMLayer")
    
    # Convert the OSM data to a network dataset.
    arcpy.OSMGPCreateNetworkDataset_osmtools(dataset_name, "DriveGeneric.xml", "ND")

    # Create the OD Cost Matrix layer and get a refrence to the layer.
    result    = arcpy.na.MakeODCostMatrixLayer(dataset_name_nd, "OD Cost Matrix", "Length", drivetime_cutoff_meters)
    odcmLayer = result.getOutput(0)

    # The OD Cost Matrix layer will have Origins and Destinations layers.  Get
    # a reference to each of these.
    odcmSublayers   = arcpy.na.GetNAClassNames(odcmLayer)
    odcmOriginLayer = odcmSublayers["Origins"]
    odcmDestLayer   = odcmSublayers["Destinations"]

    # Add the origins.
    # originTableName, ex. "Collisions" should be selected by the user.
    # Snapdistance, ex. 300 Meters should be selected by the user.
    arcpy.na.AddLocations(odcmLayer, odcmOriginLayer, originTableName, "", originSnapDistance)
    arcpy.na.AddLocations(odcmLayer, odcmDestLayer,   destinationTableName, "", destinationSnapDistance)

    # Solve the matrix.
    arcpy.na.Solve(odcmLayer)

    # Show ODCM layer to the user.
    arcpy.mapping.AddLayer(dataFrame, odcmLayer, "TOP")
    #Save the layers, as for some reason in 10.1, the ODCM layer disappears from the layers right after finishing.
    #TODO - find a workaround against this.  Don't want to save needless stuff.
    odcmLayer.saveACopy(dataset_name + ".lyr")
    arcpy.RefreshTOC()
    
    return
