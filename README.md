Description
-----------
PyPSATopo is a tool which allows generating the topographical representation of any arbitrary PyPSA-based network (thanks to the DOT language). Besides easing understand of a network by providing its graphical illustration, the tool helps debugging it given that broken links and missing buses are shown in (slightly) different shapes and colors. Technically speaking, PyPSATopo can be thought of as a [reverse engineering](https://en.wikipedia.org/wiki/Reverse_engineering) tool for PyPSA-based networks. To get a quick overview of the capabilities of PyPSATopo, simply launch it in a terminal as follows:

    python pypsatopo.py

This will create a PyPSA-based network made of the following components:

```python
# create dummy (PyPSA) network
network = pypsa.Network(name = "My Dummy Network")

# add some dummy components to dummy (PyPSA) network
network.add("Bus", "oil")
network.add("Bus", "electricity")
network.add("Bus", "transport")
network.add("Generator", "oil", bus = "oil")
network.add("Generator", "solar", bus = "electricity")
network.add("Load", "vehicle", bus = "transport")
network.add("Store", "battery", bus = "electricity")
network.add("Link", "ICEV", bus0 = "oil", bus1 = "transport")
network.add("Link", "BEV", bus0 = "electricity", bus1 = "transport")
```
... as well as generate the corresponding topographical representation of the network in the [SVG](https://en.wikipedia.org/wiki/SVG) format:

<img src = "resources/topography.svg" alt = "Topographical representation of network 'My Dymmy Network'" style = "background-color: white;" width = 500>

In general, the following (generic) recipe should be followed to generate the topographical representation of a PyPSA-based network:

```python
# import PyPSATopo module
import pypsatopo

# create PyPSA-based network named 'my_network'
my_network = pypsa.Network()

# add components to network 'my_network'
# (...)

# generate topographical representation of network 'my_network' in the SVG format
pypsatopo.generate(my_network)
```

By default, PyPSATopo generates the topographical representation of a PyPSA-based network in SVG but other formats are also available (namely: [PNG](https://en.wikipedia.org/wiki/PNG), [JPG](https://en.wikipedia.org/wiki/JPEG), [GIF](https://en.wikipedia.org/wiki/GIF) and [PS](https://en.wikipedia.org/wiki/Postscript)), which can be specified through parameter `file_format`. Example:

```python
# generate topographical representation of network 'my_network' in the GIF format
pypsatopo.generate(my_network, file_format = "gif")
```

Also, by default, PyPSATopo generates the topographical representation of the entire network. This might be particularly overwhelming (visually speaking) depending on the complexity of the network - see [PyPSA-Eur network topographical representation](resources/pypsa-eur_topography.svg) as an example. To mitigate this, parameters `focus` and `neighbourhood` (in function `generate`) may be utilized in combination to focus on a particular aspect/segment of the network. The former tells PyPSATopo which bus to start visiting, while the latter tells how much neighbourhood (around the bus) should be visited (in other words, how much (indirect) components attached to the bus should be included in the representation). For example, setting parameters `focus = "DK1 0 low voltage"` and `neighbourhood = 2` (which focuses/starts on `DK1 0 low voltage` bus and includes all the components attached to it up to a maximum neighbourhood degree of `2`) yields this [result](resources/pypsa-eur_dk1_0_low_voltage_topography.svg) upon generating PyPSA-Eur network topographical representation.

Just like for links with positive efficiencies, links with negative efficiencies are represented by a line going from *bus0* to, e.g., *bus1* with an arrow pointing to the latter at the end of the line. In case of need to invert the sense of the arrow (i.e. to point to *bus0* instead) when dealing with negative efficiencies, set parameter `negative_efficiency = False` when calling function `generate`.

All broken links and missing buses are included in the topographical representation of a network by default, and are shown in (slightly) different shapes and colors. To exclude these from the representation, set parameter `broken_missing = False` when calling function `generate`.

To color a certain component (namely: bus, generator, load, store or line) in function of its carrier, set parameter `carrier_color` (when calling function `generate`) with a dictionary containing key-value pairs, where key is the name of a carrier and value is a color assigned to it. Example: setting parameter `carrier_color = {"my_carrier1": "red", "my_carrier2": "green", "my_carrier3": "blue"}` tells PyPSATopo to color a component in `red`, `green` or `blue` whenever its carrier is `my_carrier1`, `my_carrier2` or `my_carrier3`, respectively. Acceptable colors are defined [here](https://graphviz.org/doc/info/colors.html). Alternatively, in case `carrier_color` is set to `True` (instead of a dictionary), PyPSATopo automatically assigns a new color to each distinct carrier found in the network and colors all the components associated to the carrier with this color.

In case fine-grained selection/visiting logic is needed, parameters `bus_filter`, `generator_filter`, `load_filter`, `store_filter`, `link_filter` and `line_filter` (in function `generate`) may be utilized in combination or separately. These parameters are expected to be (user-defined) [regular expressions](https://en.wikipedia.org/wiki/Regular_expression). While parameters `bus_filter`, `generator_filter`, `load_filter` and `store_filter` tell PyPSATopo which buses, generators, loads and stores to include/exclude, parameters `link_filter` and `line_filter` tell which links and lines may be visited (or not) upon generating the topographical representation of a network.

By default, excluded components are not shown in the topographical representation of a network. In certain situations, however, it might be useful to understand where selected (included) components are located in the representation among excluded components. To show selected components in the topographical representation of a network among excluded components, set parameter `context = True` when calling function `generate`. While selected components are shown with the appropriate colors, excluded components are shown with faded colors (to distinguish these from the formers visually speaking).

Given that it may take some time to process a complex network, PyPSATopo is capable of displaying log messages while processing such network. Log messages not only describe the stage at which the tool is in the processing pipeline but also potential issues that the network may have. To enable PyPSATopo displaying log messages, set parameter `quiet = False` (when calling function `generate`). Otherwise, in case the parameter is not set, the tool behaves quietly by default (i.e. no log messages are displayed).


Platforms
---------
In principle, PyPSATopo should work in any platform (i.e. operating system) as long as the components that this tool depends on are supported in the target platform. As a reference, PyPSATopo is known to work correctly in:

- Windows

- Linux

- macOS


Dependencies
------------
PyPSATopo leverages from several components to accomplish its functionality, namely: [Python](https://www.python.org), [PyPSA](https://pypsa.org), [Pandas](https://pandas.pydata.org) and [Dot](https://graphviz.org) (from Graphviz). Consequently, these should be installed before running PyPSATopo. As a reference, PyPSATopo is known to work correctly with the following versions of the components:

- Python 3.10.8

- PyPSA 0.21.3

- Pandas 1.5.3

- Dot 2.40.1


Support
-------
PyPSATopo is actively developed and maintained by the Energy Systems Group at [Aarhus University](https://www.au.dk) (Denmark). Please open a ticket [here](https://github.com/ricnogfer/pypsatopo/issues) in case a bug was found or a feature is missing in this tool.

