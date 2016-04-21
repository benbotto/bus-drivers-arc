#Bus Drivers
#Kian Faroughi
#Compute Observed K Function
#Look at excel file K_IH_CMC+Observed_Distances3_FINAL for where calculations are derived

import math

class NetworkKCalculation:
  ###
  # Initialize the calculator.
  # @param netLen The length of the network.
  # @param numPoints The total number of points in the observed data.
  # @param odDists An array of origins and destinations from an OD cost
  #        matrix.  Each should have keys Total_Length, OriginID, DestinationID.
  # @param begDist The distance to begin calculating (the first distance band).
  # @param distInc The amount to increment each distance band.
  # @param numBands The number of distance bands (optional).
  ###
  def __init__(self, netLen, numPoints, odDists, begDist, distInc, numBands):
    self._netLen    = netLen
    self._numPoints = numPoints
    self._odDists   = sorted(odDists, key=lambda odDist: odDist["Total_Length"])
    self._begDist   = begDist
    self._distInc   = distInc
    self._numBands  = numBands

    # If the user doesn't specify the number of distance bands then calculate it.
    if self._numBands is None:
      maxLen         = self._odDists[-1]["Total_Length"]
      self._numBands = int(math.ceil((maxLen - self._begDist) / self._distInc + 1))

    # Calculate the overall point-network density.
    self._pnDensity = self.calculatePointNetworkDensity()

    # Count the points in each distance band.
    self._distBands = self.countDistanceBands()

    # Calculate the network k values.
    self.calculateNetworkK()

  # Get the network length.
  def getNetworkLength(self):
    return self._netLen

  # Get the distances list, which is sorted.
  def getDistances(self):
    return self._odDists

  # Get the beginning distance.
  def getBeginningDistance(self):
    return self._begDist

  # Get the distance increment.
  def getDistanceIncrement(self):
    return self._distInc

  # Get the number of increments, or none.
  def getNumberOfDistanceBands(self):
    return self._numBands

  # Get the number of points in the network.
  def getNumberOfPoints(self):
    return self._numPoints

  # Calculate the point-network density.
  def calculatePointNetworkDensity(self):
    numberOfPointsOneDown = self.getNumberOfPoints() - 1
    pointsFraction        = numberOfPointsOneDown * self.getNumberOfPoints()
    density               = self.getNetworkLength() / pointsFraction
    return density

  # Get the point-network density.
  def getPointNetworkDensity(self):
    return self._pnDensity

  # Count the number of points in each distance band.
  def countDistanceBands(self):
    distBands = []
    curDist   = self.getBeginningDistance()
    numBands  = self.getNumberOfDistanceBands()
    odDists   = self.getDistances()
    numDists  = len(odDists)
    distNum   = 0
    bandCount = 0
    
    # Go through all the distance bands.
    for bandNum in range(0, numBands):
      # Points are cumulative.
      distBands.append({"distanceBand": curDist, "count": bandCount})
      distBand = distBands[-1]

      # Increase the count of points in the current distance band until either
      # the current distance is exceeded or the last point is reached.  Note
      # that the distances are ordered by Total_Length.
      while distNum < numDists and odDists[distNum]["Total_Length"] <= curDist:
        distBand["count"] += 1
        bandCount         += 1
        distNum           += 1

      curDist += self.getDistanceIncrement()

    return distBands

  # Get the distance bands array.
  def getDistanceBands(self):
    return self._distBands

  # Calculate the network k function result for each distance band.  The
  # result goes in distBands
  def calculateNetworkK(self):
    for distBand in self.getDistanceBands():
      distBand["KFunction"] = distBand["count"] * self.getPointNetworkDensity()
