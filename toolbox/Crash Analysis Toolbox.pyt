# Don't make compiled pyc files (caching fix).
import sys
sys.dont_write_bytecode = True

import crash_radius_density
import crash_network_density
import network_k_function
import network_dataset_length

# Live reload each module at runtime (otherwise ArcMap has to be closed and
# reopened rather than just refreshing the toolbox).
crash_radius_density   = reload(crash_radius_density)
crash_network_density  = reload(crash_network_density)
network_k_function     = reload(network_k_function)
network_dataset_length = reload(network_dataset_length)

from crash_radius_density import CrashRadiusDensity
from crash_network_density import CrashNetworkDensity
from network_k_function import NetworkKFunction
from network_dataset_length import NetworkDatasetLength

class CrashAnalysisToolbox(object):
  def __init__(self):

    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"

    # List of tool classes associated with this toolbox
    self.tools = [CrashRadiusDensity, CrashNetworkDensity, NetworkKFunction, NetworkDatasetLength]
