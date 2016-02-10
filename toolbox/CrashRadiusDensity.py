import arcpy
from arcpy import env

'''
This class finds the number of points within in a user-defined radius.
'''
class CrashRadiusDensity(object):

  def __init__(self):
    self.label = "Crash Radius Density"
    self.description = "This tool creates a feature that contains the density of crashes around each crash."
    self.canRunInBackground = False

    env.overwriteOutput = True
  
  def getParameterInfo(self):
  
    # First parameter, input features (geodatabase)
    points = arcpy.Parameter(
      displayName="Input Point Feature Dataset",
      name="points",
      datatype="Feature Layer",
      parameterType="Required",
      direction="Input")
    points.filter.list = ["Point"]

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
      
    return [points, radius_units, radius_magnitude]

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
    featureName   = parameters[0].valueAsText
    featureRadius = parameters[2].valueAsText + " " + parameters[1].valueAsText
    featureDesc   = arcpy.Describe(featureName)

    messages.addMessage("Feature Name: {0} Radius: {1}".format(featureName, featureRadius))

    # Add a Count column and default it to 1.
    # Not necessary, but kept here for reference.  The Join_Count field in the
    # "_sum" feature is used for this.
    #messages.addMessage("Adding field 'Count' to feature {0}".format(featureName))
    #arcpy.AddField_management(featureName, "Count", "SHORT")
    #arcpy.CalculateField_management(featureName, "Count", "1", "PYTHON_9.3")

    # Create a buffer around each point.
    bufferFeature = featureDesc.catalogPath + "_buffer"
    messages.addMessage("Adding buffer feature: {0}".format(bufferFeature))
    arcpy.Buffer_analysis(featureName, bufferFeature, featureRadius)
  
    # Join the collision data and the collision buffer.
    sumFeature = featureDesc.catalogPath + "_sum"
    messages.addMessage("Summarizing to {0}".format(sumFeature))
    arcpy.SpatialJoin_analysis(bufferFeature, featureName, sumFeature)

    # Show the feature layer.
    curMapDoc = arcpy.mapping.MapDocument("CURRENT")
    dataFrame = arcpy.mapping.ListDataFrames(curMapDoc, "Layers")[0]
    arcpy.mapping.AddLayer(dataFrame, arcpy.mapping.Layer(sumFeature), "TOP")
    arcpy.RefreshTOC()

    return