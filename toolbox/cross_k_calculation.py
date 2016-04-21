from network_k_calculation import NetworkKCalculation

class CrossKCalculation(NetworkKCalculation):
  # Count the number of points in each distance band.
  def countDistanceBands(self):
    distBands = []
    startDist = self.getBeginningDistance()
    numBands  = self.getNumberOfDistanceBands()
    odDists   = self.getDistances()
    numDists  = len(odDists)
    distNum   = 0
    
    # Go through all the distance bands.
    for bandNum in range(0, numBands):
      distBands.append({"distanceBand": startDist, "count": 0})
      distBand = distBands[-1]

      # Increase the count of points in the current distance band until either
      # the current distance is exceeded or the last point is reached.  Note
      # that the distances are ordered by Total_Length.
      endDist = startDist + self.getDistanceIncrement()

      while distNum < numDists and odDists[distNum]["Total_Length"] < endDist:
        # The user may have specified a start distance, and there may be distances between
        # points that are smaller than the user-defined start dist.  Don't count these.
        # For example, if the user specifies a start distance of 200M, and there is a
        # crash 30M from a bridge then it's not in the first distance band and
        # is not counted.
        if odDists[distNum]["Total_Length"] >= startDist:
          distBand["count"] += 1
        distNum += 1
      startDist += self.getDistanceIncrement()

    return distBands
