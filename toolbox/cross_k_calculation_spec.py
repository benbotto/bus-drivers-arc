import unittest

from cross_k_calculation import CrossKCalculation

class CrossKCalculationSuite(unittest.TestCase):

  # Checks the derived distance band calculation.
  def test_distance_band_calc(self):
    netLen  = 14
    begDist = 0
    distInc = 1
    odDists = [
      {'Total_Length': 2, 'DestinationID': 1, 'OriginID': 1},
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 3, 'DestinationID': 2, 'OriginID': 1},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 2}]

    ckc = CrossKCalculation(netLen, 2, odDists, begDist, distInc, None)
    #print(ckc.getDistanceBands())
    self.assertEqual(ckc.getNumberOfDistanceBands(), 5) # 0, 1, 2, 3, 4
    self.assertEqual(ckc.getDistanceBands()[0]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[1]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[2]["count"], 1)
    self.assertEqual(ckc.getDistanceBands()[3]["count"], 1)
    self.assertEqual(ckc.getDistanceBands()[4]["count"], 2)

    ckc = CrossKCalculation(netLen, 2, odDists, begDist, distInc, 3)
    self.assertEqual(ckc.getNumberOfDistanceBands(), 3) # 0, 1, 2
    self.assertEqual(ckc.getDistanceBands()[0]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[1]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[2]["count"], 1)

    begDist = 3
    distInc = .25
    odDists = [
      {'Total_Length': 2, 'DestinationID': 1, 'OriginID': 1},
      {'Total_Length': 4, 'DestinationID': 1, 'OriginID': 2},
      {'Total_Length': 3, 'DestinationID': 2, 'OriginID': 1},
      {'Total_Length': 4, 'DestinationID': 2, 'OriginID': 2}]

    ckc = CrossKCalculation(netLen, 2, odDists, begDist, distInc, None)
    self.assertEqual(ckc.getNumberOfDistanceBands(), 5) # 3, 3.25, 3.5, 3.75, 4
    self.assertEqual(ckc.getDistanceBands()[0]["count"], 1)
    self.assertEqual(ckc.getDistanceBands()[1]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[2]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[3]["count"], 0)
    self.assertEqual(ckc.getDistanceBands()[4]["count"], 2)
