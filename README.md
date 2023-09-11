## Description
PyPSATopo is a tool that allows generating the topographical representation of any arbitrary [PyPSA](https://pypsa.org)-based network (thanks to the [DOT language](https://graphviz.org/doc/info/lang.html)). Besides easing the understanding of a network by providing its graphical representation, the tool helps debug it given that broken links and missing buses are shown in (slightly) different shapes and colors. Technically speaking, PyPSATopo can be thought of as a [reverse engineering](https://en.wikipedia.org/wiki/Reverse_engineering) tool for PyPSA-based networks.

To get a quick overview of the capabilities of PyPSATopo, simply launch it in a terminal as follows:

```bash
python pypsatopo.py
```

This will create a PyPSA-based network made of the following components:

```python
# create dummy (PyPSA-based) network
network = pypsa.Network(name = "My Dummy Network")

# add some dummy components to dummy network
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
... as well as generate the corresponding topographical representation of the network in the SVG format:

<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/topography.svg" alt = "Topographical representation of network 'My Dummy Network'" style = "background-color: white;" width = 520>
</kbd>


## Installation
PyPSATopo can be installed in the machine using [pip](https://en.wikipedia.org/wiki/Pip_(package_manager)), a package management system for [Python](https://en.wikipedia.org/wiki/Python_(programming_language)). To install the tool using pip, open a terminal and execute the following:

```bash
pip install pypsatopo
```

PyPSATopo leverages from several components to accomplish its functionalities, namely: [Python](https://www.python.org), [PyPSA](https://pypsa.org), [Pandas](https://pandas.pydata.org) and [Dot](https://graphviz.org) (from Graphviz). Consequently, these should be installed before running PyPSATopo. While PyPSA and Pandas are automatically installed by PyPSATopo in case these are missing, Dot must be manually installed by the user (see [download](https://graphviz.org/download) for additional details). As a reference, PyPSATopo is known to work correctly with the following versions of the components:

- Python 3.10.8

- PyPSA 0.21.3

- Pandas 1.5.3

- Dot 2.40.1

In addition, PyPSATopo should work in any platform (i.e. operating system) as long as the components that this tool depends on are supported in the target platform. As a reference, the tool is known to work correctly in Windows, Linux and macOS.


## Usage
PyPSATopo can be used in two different ways to generate the topographical representation of a PyPSA-based network, either through its [application programming interface](https://en.wikipedia.org/wiki/API) or a [command-line interface](https://en.wikipedia.org/wiki/Command-line_interface).

To use PyPSATopo through its application programming interface, the following (generic) recipe should be followed:

```python
# import PyPSATopo module
import pypsatopo

# create (PyPSA-based) network named 'my_network'
my_network = pypsa.Network()

# add components to network 'my_network'
# (...)

# generate topographical representation of network 'my_network' in the SVG format
pypsatopo.generate(my_network)
```

To use PyPSATopo through a command-line interface, execute the following in a terminal (where `my_network.nc` refers to the [NetCDF](https://en.wikipedia.org/wiki/NetCDF) file containing the PyPSA-based network):

```bash
python pypsatopo.py my_network.nc
```

In addition, to see all the valid parameters accepted by the tool, specify parameter `--help` when executing it in a terminal. In other words:

```bash
python pypsatopo.py --help
```


## PyPSA Components
Currently, PyPSATopo supports some of the most important PyPSA components, namely: [Bus](https://pypsa.readthedocs.io/en/latest/components.html#bus), [Generator](https://pypsa.readthedocs.io/en/latest/components.html#generator), [Load](https://pypsa.readthedocs.io/en/latest/components.html#load), [Store](https://pypsa.readthedocs.io/en/latest/components.html#store), [Link](https://pypsa.readthedocs.io/en/latest/components.html#link) and [Line](https://pypsa.readthedocs.io/en/latest/components.html#line). These are graphically represented as follows in PyPSATopo:

- Bus (fundamental component of the network, to which components like loads, generators and stores attach. It enforces energy conservation for all elements feeding in and out of it - i.e. like Kirchhoff’s Current Law).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_bus.png" alt = "Graphical representation of a bus in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>
</br>

- Generator (attaches to a single bus and can feed in power. It converts energy from its carrier to the carrier-type of the bus to which it is attached).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_generator.png" alt = "Graphical representation of a generator in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>
</br>

- Load (attaches to a single bus and consumes power as a PQ load).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_load.png" alt = "Graphical representation of a load in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>
</br>

- Store (attaches to a single bus and stores energy only (it cannot convert between energy carriers). It inherits its energy carrier from the bus to which it is attached).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_store.png" alt = "Graphical representation of a store in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>
</br>

- Link (component for controllable directed flows between two buses with arbitrary energy carriers. It can have an efficiency loss and a marginal cost).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_link.png" alt = "Graphical representation of a link in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_bidirectional_link.png" alt = "Graphical representation of a bidirectional link in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_multi_link.png" alt = "Graphical representation of a multi-link in PyPSATopo" style = "background-color: white;" width = 715>
</kbd>
</br>
</br>
</br>

- Line (represents transmission and distribution lines. It can connect either AC buses or DC buses).
<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsatopo_line.png" alt = "Graphical representation of a line in PyPSATopo" style = "background-color: white;" width = 350>
</kbd>
</br>
</br>


## Functionalities
As stated previously, PyPSATopo is a tool that allows generating the topographical representation of any arbitrary PyPSA-based network. It basically allows to reverse engineer such type of network to ease its understanding. To that end, PyPSATopo provides several functionalities to cover as many [use-cases](https://en.wikipedia.org/wiki/Use_case) as possible. These functionalities are described below and their usage exemplified using both the application programming interface and the command-line interface.

- When generating the topographical representation of a network and in case parameter `file_output` is not specified, PyPSATopo saves the output either in (1) a file named `topography` with an extension equal to the file format if the tool is used through its application programming interface or (2) a file named as the network file with an extension equal to the file format if the tool is used through a command-line interface. To specify the file name where to save the output, set parameter `file_output` with the appropriate value. As an example, the following generates the topographical representation of a network and saves the output in a file named `my_network.svg`:

    ```python
    pypsatopo.generate(my_network, file_output = "my_network.svg")
    ```

    ```bash
    python pypsatopo.py my_network.nc --file-output my_network.svg
    ```

- PyPSATopo is able to generate the topographical representation a network in different formats, namely: [SVG](https://en.wikipedia.org/wiki/SVG), [PNG](https://en.wikipedia.org/wiki/PNG), [JPG](https://en.wikipedia.org/wiki/JPEG), [GIF](https://en.wikipedia.org/wiki/GIF) and [PS](https://en.wikipedia.org/wiki/Postscript). To specify the format, set parameter `file_format` with the appropriate value. Otherwise, in case the parameter is not set, the default format is SVG. As an example, the following generates the topographical representation of a network in the GIF format:

    ```python
    pypsatopo.generate(my_network, file_format = "gif")
    ```

    ```bash
    python pypsatopo.py my_network.nc --file-format gif
    ```

- By default, PyPSATopo generates the topographical representation of the entire network. This might be particularly overwhelming (visually speaking) depending on the complexity of the network - see [PyPSA-Eur network topographical representation](https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsa-eur_topography.svg) to get an idea. To mitigate this, parameters `focus` and `neighbourhood` may be utilized (in combination) to focus on a particular aspect/segment of the network. The former tells PyPSATopo which bus to start visiting, while the latter tells how much neighbourhood (around the bus) should be visited (in other words, how much (indirect) components attached to the bus should be included in the representation). For instance, setting parameters `focus = "DK1 0 low voltage"` and `neighbourhood = 2` (which focuses/starts on bus `DK1 0 low voltage` and includes all the components attached to it up to a maximum neighbourhood degree of `2`) yields this [result](https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/pypsa-eur_dk1_0_low_voltage_topography.svg) upon generating PyPSA-Eur network topographical representation. As an example, the following generates the topographical representation of a network focusing/starting on bus `co2 atmosphere` and including all the components attached to it up to a maximum neighbourhood degree of `3`:

    ```python
    pypsatopo.generate(my_network, focus = "co2 atmosphere", neighbourhood = 3)
    ```

    ```bash
    python pypsatopo.py my_network.nc --focus "co2 atmosphere" --neighbourhood 3
    ```

    Alternatively, parameters `focus` and `neighbourhood` may be set with a list of buses and respective neighbourhoods to enable focusing on several aspects/segments of the network at the same time (as opposite to just one bus and respective neighbourhood). Setting these parameters with a list of buses/neighbourhoods (instead of a scalar) enables PyPSATopo to visit and combine the output of each bus into one single topographical representation, potentially generating a [disjoint union of graphs](https://en.wikipedia.org/wiki/Disjoint_union_of_graphs). As an example, the following generates the topographical representation of a network by focusing/starting on buses `my_bus0` and `my_bus1`, and including all the components attached to these buses up to a maximum neighbourhood degree of `2` and `3`, respectively:

    ```python
    pypsatopo.generate(my_network, focus = ["my_bus0", "my_bus1"], neighbourhood = [2, 3])
    ```

    ```bash
    python pypsatopo.py my_network.nc --focus my_bus0 my_bus1 --neighbourhood 2 3
    ```

- Just like for links with positive efficiencies, PyPSATopo represents links with negative efficiencies with a line going from *bus0* to, e.g., *bus1* and an arrow at the end of the line pointing to the latter. In case of need to invert the sense of the arrow (i.e. to point to *bus0* instead) when dealing with negative efficiencies, set parameter `negative_efficiency = False`. As an example, the following generates the topographical representation of a network with no negative efficiencies (i.e. all links with negative efficiencies will have their arrows inverted):

    ```python
    pypsatopo.generate(my_network, negative_efficiency = False)
    ```

    ```bash
    python pypsatopo.py my_network.nc --no-negative-efficiency
    ```

- All broken links and missing buses are included in the topographical representation of a network by default, and are shown in (slightly) different shapes and colors. To exclude these from the representation, set parameter `broken_missing = False`. As an example, the following generates the topographical representation of a network where broken links and missing buses are excluded from it:

    ```python
    pypsatopo.generate(my_network, broken_missing = False)
    ```

    ```bash
    python pypsatopo.py my_network.nc --no-broken-missing
    ```

- To color a certain component (namely: bus, generator, load, store or line) in function of its carrier, set parameter `carrier_color` with a dictionary containing key-value pairs, where key is the name of a carrier and value is a color assigned to it. Acceptable colors are defined [here](https://graphviz.org/doc/info/colors.html). As an example, the following generates the topographical representation of a network with its components colored in `red`, `green` or `blue` whenever their carriers are `my_carrier0`, `my_carrier1` or `my_carrier2`, respectively:

    ```python
    pypsatopo.generate(my_network, carrier_color = {"my_carrier0": "red", "my_carrier1": "green", "my_carrier2": "blue"})
    ```

    ```bash
    python pypsatopo.py my_network.nc --carrier-color my_carrier0 red my_carrier1 green my_carrier2 blue
    ```

    Alternatively, in case `carrier_color` is set to `True` (instead of a dictionary), PyPSATopo automatically assigns a new color to each distinct carrier found in the network and colors all the components associated to the carrier with this color. As an example, the following generates the topographical representation of a network with its components colored in function of their carriers:

    ```python
    pypsatopo.generate(my_network, carrier_color = True)
    ```

    ```bash
    python pypsatopo.py my_network.nc --carrier-color
    ```

- In case fine-grained selection/visiting logic is needed, parameters `bus_filter`, `generator_filter`, `load_filter`, `store_filter`, `link_filter` and `line_filter` may be utilized in combination or separately. These parameters are expected to be set with (user-defined) [regular expressions](https://en.wikipedia.org/wiki/Regular_expression). While parameters `bus_filter`, `generator_filter`, `load_filter` and `store_filter` tell PyPSATopo which buses, generators, loads and stores to include/exclude, respectively, parameters `link_filter` and `line_filter` tell which links and lines may be visited (or not) upon generating the topographical representation of a network. As an example, the following generates the topographical representation of a network where only the generators containing the words `wind` or `solar` in their names are selected (and all other generators are excluded):

    ```python
    pypsatopo.generate(my_network, generator_filter = "wind|solar")
    ```

    ```bash
    python pypsatopo.py my_network.nc --generator-filter "wind|solar"
    ```

- By default, excluded components (due to, e.g., filtering) are not shown in the topographical representation of a network. In certain situations, however, it might be useful to understand where selected (included) components are located in the full representation (i.e. among excluded components). To show selected components in the topographical representation of a network among excluded components, set parameter `context = True`. While selected components are shown with the appropriate colors, excluded components are shown with faded colors (to distinguish these from the formers visually speaking). As an example, the following generates the topographical representation of a network where only the loads containing the word `agriculture` in their names are selected (and all other loads are displayed with faded colors):

    ```python
    pypsatopo.generate(my_network, load_filter = "agriculture", context = True)
    ```

    ```bash
    python pypsatopo.py my_network.nc --load-filter agriculture --context
    ```

- Given that it may take some time to process a complex network, PyPSATopo is capable of displaying log messages while processing such network. Log messages not only facilitate understanding of the stage at which the tool is in the processing pipeline but also potential issues that the network may have. To enable PyPSATopo displaying log messages, set parameter `quiet = False`. Otherwise, in case the parameter is not set, the tool behaves quietly by default (i.e. no log messages are displayed). As an example, the following displays log messages while generating the topographical representation of a network:

    ```python
    pypsatopo.generate(my_network, quiet = False)
    ```

    ```bash
    python pypsatopo.py my_network.nc --no-quiet
    ```


## Support
PyPSATopo is actively developed and maintained by the Energy Systems Group at [Aarhus University](https://www.au.dk) (Denmark). Please open a ticket [here](https://github.com/ricnogfer/pypsatopo/issues) in case a bug was found or a feature is missing in this tool.

