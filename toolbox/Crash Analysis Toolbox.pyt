
import arcpy

class Toolbox(object):
  def __init__(self):
    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"
    arcpy.env.overwriteOutput = True #allows tool to be ran again if user decides to. will need to assess for recursive tools

    # List of tool classes associated with this toolbox
    self.tools = [CrashRadiusDensity]


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
	
    # Second parameter, input radius magnitude
    radius_magnitude = arcpy.Parameter(
        displayName="Radius Magnitude",
        name="radius_magnitude",
        datatype="String",
        parameterType="Required",
        direction="Input")

    # Third parameter, input radius units
    radius_units = arcpy.Parameter(
        displayName="Radius Units",
        name="radius_units",
        datatype="String",
        parameterType="Required",
        direction="Input")

    # Fourth parameter, _sum location
    sum_location = arcpy.Parameter(
        displayName="_Sum Name",
        name = "_Sum Location",
        datatype="String",
        parameterType="Required",
        direction="Input")
    #put the parameters in an array, for future use
    params = [in_features,radius_magnitude,radius_units,sum_location]
    return params

  def isLicensed(self):
    """Set whether tool is licensed to execute."""
    return True

  def updateParameters(self, parameters):
    """Modify the values and properties of parameters before internal
    validation is performed.  This method is called whenever a parameter
    has been changed."""
    return

  def updateMessages(self, parameters):
    """Modify the messages created by internal validation for each tool
    parameter.  This method is called after internal validation."""
    return

  def execute(self, parameters, messages):
    # This is the feature (table) name that we're working with.
    featureName = parameters[0].valueAsText#the gdb file
    featureRadius = parameters[1].valueAsText + " " + parameters[2].valueAsText#the radius, with magnitude and units
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
