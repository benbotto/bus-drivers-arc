import unittest

from network_k_calculation import NetworkKCalculation

class NetworkKCalculationSuite(unittest.TestCase):
  # Trivial network.
  def test_trivial_network(self):
    netLen  = 14
    odDists = [
      {'Total_Length': 2, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 3, 'DestinationID': 1, 'OriginID': 3},
      {'Total_Length': 2, 'DestinationID': 2, 'OriginID': 1},
      {'Total_Length': 0, 'DestinationID': 2, 'OriginID': 3},
      {'Total_Length': 3, 'DestinationID': 3, 'OriginID': 1},
      {'Total_Length': 0, 'DestinationID': 3, 'OriginID': 2}]
    begDist = 1
    distInc = 1

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, None)
    self.assertEqual(nkc.getNetworkLength(), 14)

    # The OD distances should be sorted by Total_Length.
    self.assertEqual(nkc.getDistances()[0]["Total_Length"], 0)
    self.assertEqual(nkc.getDistances()[1]["Total_Length"], 0)
    self.assertEqual(nkc.getDistances()[2]["Total_Length"], 2)
    self.assertEqual(nkc.getDistances()[3]["Total_Length"], 2)
    self.assertEqual(nkc.getDistances()[4]["Total_Length"], 3)
    self.assertEqual(nkc.getDistances()[5]["Total_Length"], 3)

    self.assertEqual(nkc.getBeginningDistance(), 1)
    self.assertEqual(nkc.getDistanceIncrement(), 1)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 3)
    self.assertEqual(nkc.getPointNetworkDensity(), 14 / (3 * 2))

    # Each distance band length.
    self.assertEqual(nkc.getDistanceBands()[0]["distanceBand"], 1)
    self.assertEqual(nkc.getDistanceBands()[1]["distanceBand"], 2)
    self.assertEqual(nkc.getDistanceBands()[2]["distanceBand"], 3)

    # The count on each distance band.
    self.assertEqual(nkc.getDistanceBands()[0]["count"], 2) # 2 points are 0 meters apart.
    self.assertEqual(nkc.getDistanceBands()[1]["count"], 4) # 2 + 2 points at 2 meters apart.
    self.assertEqual(nkc.getDistanceBands()[2]["count"], 6) # 2 + 2 + 2 points at 3 meters apart.

    # Check the network k value on each distance band.
    self.assertEqual(nkc.getDistanceBands()[0]["KFunction"], 2 * nkc.getPointNetworkDensity())
    self.assertEqual(nkc.getDistanceBands()[1]["KFunction"], 4 * nkc.getPointNetworkDensity())
    self.assertEqual(nkc.getDistanceBands()[2]["KFunction"], 6 * nkc.getPointNetworkDensity())

  # Trivial network with explicit number of distance bands.
  def test_trivial_network_explicit_bands(self):
    netLen  = 14
    odDists = [
      {'Total_Length': 2, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 3, 'DestinationID': 1, 'OriginID': 3},
      {'Total_Length': 2, 'DestinationID': 2, 'OriginID': 1},
      {'Total_Length': 0, 'DestinationID': 2, 'OriginID': 3},
      {'Total_Length': 3, 'DestinationID': 3, 'OriginID': 1},
      {'Total_Length': 0, 'DestinationID': 3, 'OriginID': 2}]
    begDist  = 0
    distInc  = .5
    numBands = 3

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, numBands)
    self.assertEqual(nkc.getBeginningDistance(), 0)
    self.assertEqual(nkc.getDistanceIncrement(), .5)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 3)

    # Each distance band length.
    self.assertEqual(len(nkc.getDistanceBands()), 3)
    self.assertEqual(nkc.getDistanceBands()[0]["distanceBand"], 0)
    self.assertEqual(nkc.getDistanceBands()[1]["distanceBand"], .5)
    self.assertEqual(nkc.getDistanceBands()[2]["distanceBand"], 1)

    # The count on each distance band.
    self.assertEqual(nkc.getDistanceBands()[0]["count"], 2)
    self.assertEqual(nkc.getDistanceBands()[1]["count"], 2)
    self.assertEqual(nkc.getDistanceBands()[2]["count"], 2)

  # Checks the derived distance band calculation.
  def test_distance_band_calc(self):
    netLen  = 14
    begDist = 0
    distInc = 1
    odDists = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, None)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 5) # 0, 1, 2, 3, 4

    begDist = 2
    distInc = 1
    odDists = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, None)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 3) # 2, 3, 4

    begDist = 0
    distInc = .75
    odDists = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, None)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 7) # 0, .75, 1.5, 2.25, 3, 3.75, 4.5

    begDist = 2
    distInc = .75
    odDists = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, None)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 4) # 2, 2.75, 3.5, 4.25

    begDist  = 0
    distInc  = .75
    numBands = 4
    odDists  = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, numBands)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 4) # User limited.

    begDist  = 0
    distInc  = .75
    numBands = 19
    odDists  = [
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 1}]

    nkc = NetworkKCalculation(netLen, odDists, begDist, distInc, numBands)
    self.assertEqual(nkc.getnumberOfDistanceBands(), 7) # User limited, but there aren't this many bands.
