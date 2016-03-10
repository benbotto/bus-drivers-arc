import math

class NetworkKAnalysis:
  ###
  # Initialize the object.
  # @param confInterval The confidence interval.
  # @param netKCalculations An array of network K calculations, each containing an
  #        array of distance bands as returned by the NetworkKCalculation class.
  #        The first element in the array should be observed data, and the other
  #        elements should be random point analyses.
  ###
  def __init__(self, confInterval, netKCalculations):
    self._confInterval = confInterval
    self._numBands     = len(netKCalculations[0])
    self._numPerms     = len(netKCalculations) - 1

    # The envelope size is the number of uniform point counts that are within the
    # confidence interval.  That is, if there are 999 permutations and the user
    # wants a 95% confidence interval, then the envelope size is 999 * .95 = 949.
    # That is, 949 of the 999 point counts are within (or on) the envelope.
    self._envSize = int(round(self._numPerms * self._confInterval))

    # This is how many point counts are outside of the envelope.  Following the
    # above example of 949 points on or within the envelope, there will be 50
    # point counts outside of the confidence envelope, 25 above and 25 below.
    # (999 - 949) / 2 = 25
    # Note the ceil and floor.  If the number of point counts outside the
    # envelope is not even, the the extra point will get added to the top.  For
    # example, 99 permutations, 95% confidence gives an envelope size of
    # 99 * .95 = 94
    # (99 - 94) / 2 = 2.5
    # 2 points on the bottom, 3 on the top.
    # Note: The 2.0 must be a float because the other parameters are ints
    # (int / int == int).
    onTop = int(math.ceil((self._numPerms - self._envSize) / 2.0))
    onBot = int(math.floor((self._numPerms - self._envSize) / 2.0))

    # Here are the indices of the confidence envelope thresholds.  envSize points
    # or on or within this area.
    botCIndex = onBot
    topCIndex = self._numPerms - onTop - 1

    # Find the confidence enevelope data.
    self._botCE = []
    self._topCE = []

    for bandNum in range(0, self._numBands):
      holdUniform = []

      # Loop over all but the first netK calc (the first is the observed data).
      for netKCalc in netKCalculations[1:]:
        holdUniform.append(netKCalc[bandNum])

      # Sort the uniform data based on the point count.
      holdUniform = sorted(holdUniform, key=lambda netKCalc: netKCalc["count"])

      # Get the point count at the top and bottom of the confidence envelope for
      # this distance band.
      self._botCE.append(holdUniform[botCIndex])
      self._topCE.append(holdUniform[topCIndex])

  # Get the confidence interval.
  def getConfidenceInterval(self):
    return self._confInterval

  # Get the number of distance bands.
  def getNumberOfBands(self):
    return self._numBands

  # Get the number of permutations.
  def getNumberOfPermutations(self):
    return self._numPerms

  # Get the envelope size (e.g. the number of permutations that fall within the
  # requested confidence interval).
  def getEnvelopeSize(self):
    return self._envSize

  # Get the bottom confidence envelope.
  def getLowerConfidenceEnvelope(self):
    return self._botCE

  # Get the top confidence envelope.
  def getUpperConfidenceEnvelope(self):
    return self._topCE


    