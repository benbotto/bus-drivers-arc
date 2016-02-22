#Bus Drivers
#Kian Faroughi
#Compute Observed K Function
#Look at excel file K_IH_CMC+Observed_Distances3_FINAL for where calculations are derived


class ComputeObservedKFunction:
  def __init__(self, nL, nOC):
    self._networkLength = nL
    self._numberOfCrashes = nOC
    self._density = self.calculateDensityObserved(self._networkLength, self._numberOfCrashes)
    self._data = []
    self._observedKFunctionIncremental = []
    self._observedKFunctionDensityIncrementalDistances = []
    self._observedKFunctionCumulative = []
    self.observedKFunctionDensityCumulative = []

  def calculateDensityObserved(self, networkLength, numberOfCrashes):
    numberOfCrashesOneDown = numberOfCrashes - 1
    crashFraction = numberOfCrashesOneDown * numberOfCrashes
    density = (networkLength / crashFraction)
    return density
  
  def cumulateSingleIteration(self, lastCumulativeObserved, observedThisIteration):
    observedCumulativeOneIteration = lastCumulativeObserved + observedThisIteration
    return observedCumulativeOneIteration  
       
  def observedKFunctionDensityIncrementalSingleIteration(self, observedKFunctionIncrementalDistance, densityObserved):
    observedKFunctionDensity = observedKFunctionIncrementalDistance * densityObserved
    return observedKFunctionDensity

hello = ComputeObservedKFunction(1178996.0, 699.0)
networkLength = 1178996.0
numberOfCrashes = 699.0
observedIncrementalDistance = 1712.0
observedIncrementalDistance2 = 1538.0;

kFunctionDensitySingleIteration = hello.observedKFunctionDensityIncrementalSingleIteration(observedIncrementalDistance, hello._density)
kFunctionDensitySingleIteration2 = hello.observedKFunctionDensityIncrementalSingleIteration(observedIncrementalDistance2, hello._density)
kFunctionCumulativeSingle = hello.cumulateSingleIteration(observedIncrementalDistance, observedIncrementalDistance2)
kFunctionDensityCumulativeSingle = hello.cumulateSingleIteration(kFunctionDensitySingleIteration, kFunctionDensitySingleIteration2)

print(kFunctionDensitySingleIteration)
print(kFunctionDensitySingleIteration2)
print(kFunctionCumulativeSingle)
print(kFunctionDensityCumulativeSingle)


