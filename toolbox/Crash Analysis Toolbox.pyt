from NetworkKFunction import NetworkKFunction
from CrashRadiusDensity import CrashRadiusDensity
from CrashNetworkDensity import CrashNetworkDensity

class Toolbox(object):
  def __init__(self):
    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"

    # List of tool classes associated with this toolbox
    self.tools = [CrashRadiusDensity, CrashNetworkDensity, NetworkKFunction]
