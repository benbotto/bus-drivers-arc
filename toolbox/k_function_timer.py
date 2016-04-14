import time

###
# Basic timer for reporting ETA.
###
class KFunctionTimer(object):
  ###
  # Initialize the timer.
  # @param numIterations The total number of iterations (for eta calculation).
  ###
  def __init__(self, numPerms):
    self.numPerms  = numPerms
    self.startTime = time.time()
    self.iteration = 0

  # Get the elapsed time as a formatted string hh:mm:ss.
  def getElapsedTime(self):
    timeDelta = time.time() - self.startTime
    return time.strftime("%H:%M:%S", time.gmtime(timeDelta))

  # Get the estimated time remaining.
  def getETA(self):
    timeDelta = time.time() - self.startTime
    eta       = timeDelta / self.iteration * (self.numPerms - self.iteration)
    return time.strftime("%H:%M:%S", time.gmtime(eta))

  # Increment the current iteration.
  def increment(self):
    self.iteration += 1