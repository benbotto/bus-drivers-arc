#Bus Drivers
#Kian Faroughi
#Compute Observed K Function Bounds
#Look at excel file K_IH_CMC+Observed_Distances3_FINAL for where calculations are derived


class ComputeObservedKFunctionBounds:
    def __init__(self, nL, nOC):
        self._networkLength = nL
        self._numberOfCrashes = nOC
        self._densityExpected = self.calculateDensityExpected(self._networkLength, self._numberOfCrashes)
        self._uniformNetworkdData = []
       
        
    def calculateDensityExpected(self, networkLength, numberOfCrashes):
        crashFraction = numberOfCrashes * numberOfCrashes
        densityExpected = (networkLength / crashFraction)
        return densityExpected
    
    def calculateBound(self, boundUniformNetwork):
        bound = boundUniformNetwork*self._densityExpected
        return bound  


hello = ComputeObservedKFunctionBounds(1178996.0, 699.0)
networkLength = 1178996.0
numberOfCrashes = 699.0

#cells AI10 and AI12
uniformNetworkIncrementalDistanceLB = 750
uniformNetworkIncrementalDistanceUB = 914

#cells AI20 and AI22
uniformNetworkIncrementalDistanceLB2 = 760
uniformNetworkIncrementalDistanceUB2 = 896


#producing cells AI11 and AI13
LB2and5 = hello.calculateBound(uniformNetworkIncrementalDistanceLB)
UB2and5 = hello.calculateBound(uniformNetworkIncrementalDistanceUB)

#producing cells AI21 and AI23
LB5 = hello.calculateBound(uniformNetworkIncrementalDistanceLB2)
UB5 = hello.calculateBound(uniformNetworkIncrementalDistanceUB2)

print(LB2and5)
print(UB2and5)
print(LB5)
print(UB5)