# Run with python -B -m unittest network_k_analysis_spec

import unittest

from random import shuffle
from network_k_analysis import NetworkKAnalysis

class NetworkKAnalysisSuite(unittest.TestCase):
  # Helper function to get a random Network K Calculation result set.
  def getRandNetK(self, count):
    netKCalculations = []

    # Generate sequential distance band counts, then shuffle them up randomly.
    # (The data are shuffled to ensure that the sorting of the data is working.)
    for i in range(0, count - 1):
      netKCalc = []
      for j in range(0, 3):
        netKCalc.append({"distanceBand": j * 2, "count": i * j})
      netKCalculations.append(netKCalc)
    shuffle(netKCalculations)

    # The first element is the observed data.
    netKCalculations.insert(0, [{"distanceBand": 0.0, "count": 0}, {"distanceBand": 2.0, "count": 12}, {"distanceBand": 4.0, "count": 20}])

    return netKCalculations

  # Basic getters.
  def test_getters(self):
    confInt          = .95
    netKCalculations = [
      [{"distanceBand": 0.0, "count": 0}, {"distanceBand": 2.0, "count": 12}, {"distanceBand": 4.0, "count": 20}], 
      [{"distanceBand": 0.0, "count": 0}, {"distanceBand": 2.0, "count": 6}, {"distanceBand": 4.0, "count": 18}], 
      [{"distanceBand": 0.0, "count": 0}, {"distanceBand": 2.0, "count": 12}, {"distanceBand": 4.0, "count": 20}], 
      [{"distanceBand": 0.0, "count": 0}, {"distanceBand": 2.0, "count": 10}, {"distanceBand": 4.0, "count": 20}]]

    netKAn = NetworkKAnalysis(confInt, netKCalculations)

    self.assertEqual(netKAn.getConfidenceInterval(), .95)
    self.assertEqual(netKAn.getNumberOfBands(), 3)
    self.assertEqual(netKAn.getNumberOfPermutations(), 3)
    self.assertEqual(netKAn.getEnvelopeSize(), 3)

  # Check the confidence envelope.
  def test_confidence_envelope(self):
    confInt          = .95
    netKCalculations = self.getRandNetK(1000)

    # There should be 25 below the confidence interval, and 25 above.
    # Envelope size = 999 * .95 = 949
    # 25 below the envelope, so the index of lower envelope should be 25.
    # 25 above the envelope, so the index of the upper envelope should be 973.
    # e.g. [25 - 973] are in the envelope, inclusive.
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[0]["count"], 0)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 25)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[2]["count"], 50)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[0]["count"], 0)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 973)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[2]["count"], 1946)

    # 948 - 50 + 1 = 899 = 999 * .90
    confInt          = .90
    netKCalculations = self.getRandNetK(1000)
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getEnvelopeSize(), 899)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 50)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 948)

    # 95 - 2 + 1 = 94 = 99 * .95
    # Note that the extra permuation is distributed above the envelope (2 below and 3 above).
    confInt          = .95
    netKCalculations = self.getRandNetK(100)
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getEnvelopeSize(), 94)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 2)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 95)

    confInt          = .90
    netKCalculations = self.getRandNetK(100)
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getEnvelopeSize(), 89)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 5)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 93)

    confInt          = .95
    netKCalculations = self.getRandNetK(10)
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getEnvelopeSize(), 9)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 0)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 8)

    confInt          = .90
    netKCalculations = self.getRandNetK(10)
    netKAn = NetworkKAnalysis(confInt, netKCalculations)
    self.assertEqual(netKAn.getEnvelopeSize(), 8)
    self.assertEqual(netKAn.getLowerConfidenceEnvelope()[1]["count"], 0)
    self.assertEqual(netKAn.getUpperConfidenceEnvelope()[1]["count"], 7)
