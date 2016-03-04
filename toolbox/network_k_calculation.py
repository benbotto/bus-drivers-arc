#Bus Drivers
#Kian Faroughi
#Compute Observed K Function
#Look at excel file K_IH_CMC+Observed_Distances3_FINAL for where calculations are derived

import math

class NetworkKCalculation:
  ###
  # Initialize the calculator.
  # @param netLen The length of the network.
  # @param odDists An array of origins and destinations from an OD cost
  #        matrix.  Each should have keys Total_Length, OriginID, DestinationID.
  # @param begDist The distance to begin calculating (the first distance band).
  # @param distInc The amount to increment each distance band.
  # @param numBands The number of distance bands (optional).
  ###
  def __init__(self, netLen, odDists, begDist, distInc, numBands):
    self._netLen   = netLen
    self._odDists  = sorted(odDists, key=lambda odDist: odDist["Total_Length"])
    self._begDist  = begDist
    self._distInc  = distInc
    self._numBands = numBands

    # If the user doesn't specify the number of distance bands then calculate it.
    maxLen   = self._odDists[-1]["Total_Length"]
    maxBands = math.ceil((maxLen - self._begDist) / self._distInc + 1)

    if self._numBands is None or self._numBands > maxBands:
      self._numBands = maxBands

    # Calculate the total number of points.
    self._numPoints = self.countNumberOfPoints()

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
  def getnumberOfDistanceBands(self):
    return self._numBands

  # Calculate the number of points in the network.
  def countNumberOfPoints(self):
    pointLookup = {}
    for odDist in self.getDistances():
      pointLookup[odDist["OriginID"]] = True
    return len(pointLookup.keys())

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
    bandNum   = 1
    numBands  = self.getnumberOfDistanceBands()

    distBands.append({"distanceBand": curDist, "count": 0})
    distBand = distBands[-1]

    for odDist in self.getDistances():
      if odDist["Total_Length"] <= curDist:
        distBand["count"] += 1
      else:
        curDist += self.getDistanceIncrement()
        bandNum += 1

        # The user can optionally set the number of bands.  If the user-requested
        # number of bands is reached, break out of the loop.
        if numBands is not None and bandNum > numBands:
          break
        else:
          # Move to the next distance band.  The count for each band is cumulative.
          distBands.append({"distanceBand": curDist, "count": distBand["count"]})
          distBand = distBands[-1]

          # The current point may be in the new distance band.
          if odDist["Total_Length"] <= curDist:
            distBand["count"] += 1

    return distBands

  # Get the distance bands array.
  def getDistanceBands(self):
    return self._distBands

  # Calculate the network k function result for each distance band.  The
  # result goes in distBands
  def calculateNetworkK(self):
    for distBand in self.getDistanceBands():
      distBand["KFunction"] = distBand["count"] * self.getPointNetworkDensity()
