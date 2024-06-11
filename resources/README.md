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
network.add("StorageUnit", "hydro", bus = "electricity")
network.add("Link", "ICEV", bus0 = "oil", bus1 = "transport")
network.add("Link", "BEV", bus0 = "electricity", bus1 = "transport")
```
... as well as generate the corresponding topographical representation of the network in the SVG format:

<kbd>
   <img src = "https://raw.githubusercontent.com/ricnogfer/pypsatopo/master/resources/topography.svg" alt = "Topographical representation of network 'My Dummy Network'" style = "background-color: white;" width = 520>
</kbd>

