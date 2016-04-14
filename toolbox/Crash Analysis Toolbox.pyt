# Don't make compiled pyc files (caching fix).
import sys
sys.dont_write_bytecode = True

import crash_radius_density
import crash_network_density
import network_dataset_length
import network_dataset_random_points
import global_k_function
import cross_k_function

# Live reload each module at runtime (otherwise ArcMap has to be closed and
# reopened rather than just refreshing the toolbox).
crash_radius_density          = reload(crash_radius_density)
crash_network_density         = reload(crash_network_density)
network_dataset_length        = reload(network_dataset_length)
network_dataset_random_points = reload(network_dataset_random_points)
global_k_function             = reload(global_k_function)
cross_k_function              = reload(cross_k_function)

from crash_radius_density          import CrashRadiusDensity
from crash_network_density         import CrashNetworkDensity
from network_dataset_length        import NetworkDatasetLength
from network_dataset_random_points import NetworkDatasetRandomPoints
from global_k_function             import GlobalKFunction
from cross_k_function              import CrossKFunction

class Toolbox(object):
  def __init__(self):

    """Define the toolbox (the name of the toolbox is the name of the
    .pyt file)."""
    self.label = "Crash Analysis Toolbox"
    self.alias = "crashAnalysis"

    # List of tool classes associated with this toolbox
    self.tools = [
      CrashRadiusDensity,
      CrashNetworkDensity,
      NetworkDatasetLength,
      NetworkDatasetRandomPoints,
      GlobalKFunction,
      CrossKFunction
    ]
