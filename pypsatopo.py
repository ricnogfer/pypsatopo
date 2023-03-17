#!/usr/bin/env python3



__author__ = "Energy Systems Group at Aarhus University (Denmark)"
__project__ = "PyPSATopo"
__description__ = "The PyPSATopo tool allows generating the topographical representation of any arbitrary PyPSA-based network (thanks to the DOT language - https://graphviz.org)"
__license__ = "BSD 3-Clause"
__contact__ = "ricardo.fernandes@mpe.au.dk"
__version__ = "0.1.0"
__status__ = "Development"



# import necessary modules
import os
import sys
import re
import datetime
import subprocess
import pypsa



# declare global variables (these can be overwritten by the caller to adjust/personalize the topographical representation of the PyPSA-based network)
DOT_REPRESENTATION = {"BUS": "   \"%s (bus)\" [label = \"%s\", tooltip = \"Carrier: %s\nUnit: %s\", shape = \"underline\", width = %.1f, height = 0.3, style = \"setlinewidth(%.1f)\", color = \"%s\"]",
                      "GENERATOR": "   \"%s (generator)\" [label = \"%s\", tooltip = \"Carrier: %s\nEfficiency: %.2f\", shape = \"circle\", width = %.1f, style = \"setlinewidth(%.1f)\", color = \"%s\"]   \"%s (generator)\" -> \"%s (bus)\" [style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"none\"]",
                      "LOAD": "   \"%s (load)\" [label = \"%s\", tooltip = \"Carrier: %s\", shape = \"invtriangle\", width = %.1f, height = %.1f, style = \"setlinewidth(%.1f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (load)\" [style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"none\"]",
                      "STORE": "   \"%s (store)\" [label = \"%s\", tooltip = \"Carrier: %s\", shape = \"box\", width = %.1f, style = \"setlinewidth(%.1f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (store)\" [style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"vee\"]   \"%s (store)\" -> \"%s (bus)\" [style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"vee\"]",
                      "LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Carrier: %s\nEfficiency: %.2f\", style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"vee\"]",
                      "BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Carrier: %s\nEfficiency: 1.00\", style = \"setlinewidth(%.1f)\", color = \"%s\", arrowhead = \"vee\", arrowtail = \"vee\", dir = \"both\"]"
                     }
NETWORK_NAME = "My Network"
FILE_FORMAT = "svg"   # possible values are: "svg", "png", "jpg", "gif" and "ps"
FILE_NAME = "topography.%s" % FILE_FORMAT
RANK_DIRECTION = "TB"   # possible values are: "TB" (top to bottom), "BT" (bottom to top), "LR" (left to right) and "RL" (right to left)
RANK_SEPARATION = 1.0
NODE_SEPARATION = 1.0
EDGE_STYLE = "polyline"   # possible values are: "polyline", "curved", "ortho" and "none"
TEXT_FONT = "Courier New"
TEXT_SIZE = 8.0
TEXT_COLOR = "red"
BUS_MINIMUM_WIDTH = 2.5
BUS_THICKNESS = 6.0
BUS_COLOR = "black"
GENERATOR_MINIMUM_WIDTH = 1.1
GENERATOR_THICKNESS = 2.0
GENERATOR_COLOR = "black"
LOAD_MINIMUM_WIDTH = 1.4
LOAD_MINIMUM_HEIGHT = 1.1
LOAD_THICKNESS = 2.0
LOAD_COLOR = "black"
STORE_MINIMUM_WIDTH = 1.3
STORE_THICKNESS = 2.0
STORE_COLOR = "black"
LINK_THICKNESS = 1.5
LINK_COLOR = "black"



def _get_buses(network):
    """
    Parameters
    ----------
    network : PyPSA network object (pypsa.Network())
        The PyPSA network to get all the buses that it contains.

    Returns
    -------
    result : Python dictionary (dict())
        A dictionary containing all the buses found in the PyPSA network.
    """

    result = dict()


    for i in range(len(network.buses)):
        bus = network.buses.index.values[i]
        carrier = network.buses.carrier[i]
        unit = "" if network.buses.unit[i] == "None" else network.buses.unit[i]
        result[bus] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "carrier": carrier, "unit": unit}


    return result



def _get_generators(buses, generators):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    generators : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    for i in range(len(generators)):
        generator = generators.index.values[i]
        carrier = generators.carrier[i]
        efficiency = generators.efficiency[i]
        bus = generators.bus.values[i]
        if bus in buses:
            buses[bus]["GENERATORS"].append((generator, carrier, efficiency))



def _get_loads(buses, loads):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    loads : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    for i in range(len(loads)):
        load = loads.index.values[i]
        carrier = loads.carrier[i]
        bus = loads.bus.values[i]
        if bus in buses:
            buses[bus]["LOADS"].append((load, carrier))



def _get_stores(buses, stores):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    stores : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    for i in range(len(stores)):
        store = stores.index.values[i]
        carrier = stores.carrier[i]
        bus = stores.bus.values[i]
        if bus in buses:
            buses[bus]["STORES"].append((store, carrier))



def _get_links(buses, links):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    links : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    for i in range(len(links)):
        link = links.index.values[i]
        bus0 = links.bus0[i]
        bus1 = links.bus1[i]
        carrier = links.carrier[i]
        efficiency = links.efficiency[i]
        bidirectional = (links.efficiency[i] == 1 and links.marginal_cost[i] == 0 and links.p_min_pu[i] == -1)
        if bus1 in buses:
            buses[bus1]["LINKS"].append((link, bus0, carrier, efficiency, bidirectional))
        if bus0 in buses:
            buses[bus0]["LINKS"].append((link, bus1, carrier, efficiency, bidirectional))



def _represent_buses(buses, bus_filter):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    count = 0


    result.append(None)
    bus_representation = DOT_REPRESENTATION["BUS"]
    for i in range(len(buses)):
        bus = buses.index.values[i]
        carrier = buses.carrier[i]
        unit = "" if buses.unit[i] == "None" else buses.unit[i]
        if not bus_filter or bus_filter.match(bus):
            result.append(bus_representation % (bus, bus, carrier, unit, BUS_MINIMUM_WIDTH, BUS_THICKNESS, BUS_COLOR))
            count = count + 1


    result[0] = "   // Buses (%d)" % count


    return result



def _represent_generators(generators, bus_filter):
    """
    Parameters
    ----------
    generators : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    count = 0


    result.append(None)
    generator_representation = DOT_REPRESENTATION["GENERATOR"]
    for i in range(len(generators)):
        generator = generators.index.values[i]
        carrier = generators.carrier[i]
        efficiency = generators.efficiency[i]
        bus = generators.bus.values[i]
        if not bus_filter or bus_filter.match(bus):
            result.append(generator_representation % (generator, generator, carrier, efficiency, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, GENERATOR_COLOR, generator, bus, LINK_THICKNESS, GENERATOR_COLOR))
            count = count + 1


    result[0] = "   // Generators (%d)" % count


    return result



def _represent_loads(loads, bus_filter):
    """
    Parameters
    ----------
    loads : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    count = 0


    result.append(None)
    load_representation = DOT_REPRESENTATION["LOAD"]
    for i in range(len(loads)):
        load = loads.index.values[i]
        carrier = loads.carrier[i]
        bus = loads.bus.values[i]
        if not bus_filter or bus_filter.match(bus):
            result.append(load_representation % (load, load, carrier, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, LOAD_COLOR, bus, load, LINK_THICKNESS, LOAD_COLOR))
            count = count + 1


    result[0] = "   // Loads (%d)" % count


    return result



def _represent_stores(stores, bus_filter):
    """
    Parameters
    ----------
    stores : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    count = 0


    result.append(None)
    store_representation = DOT_REPRESENTATION["STORE"]
    for i in range(len(stores)):
        store = stores.index.values[i]
        carrier = stores.carrier[i]
        bus = stores.bus.values[i]
        if not bus_filter or bus_filter.match(bus):
            result.append(store_representation % (store, store, carrier, STORE_MINIMUM_WIDTH, STORE_THICKNESS, STORE_COLOR, bus, store, LINK_THICKNESS, STORE_COLOR, store, bus, LINK_THICKNESS, STORE_COLOR))
            count = count + 1


    result[0] = "   // Stores (%d)" % count


    return result



def _represent_links(links, bus_filter, link_filter):
    """
    Parameters
    ----------
    links : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    link_filter : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    count = 0


    result.append(None)
    link_representation = DOT_REPRESENTATION["LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    for i in range(len(links)):
        link = links.index.values[i]
        bus0 = links.bus0[i]
        bus1 = links.bus1[i]
        carrier = links.carrier[i]
        efficiency = links.efficiency[i]
        if (not bus_filter or (bus_filter.match(bus0) and bus_filter.match(bus1))) and (not link_filter or link_filter.match(link)):
            bidirectional = (links.efficiency[i] == 1 and links.marginal_cost[i] == 0 and links.p_min_pu[i] == -1)
            if bidirectional:
                result.append(bidirectional_link_representation % (bus0, bus1, link, carrier, LINK_THICKNESS, LINK_COLOR))
            else:
                result.append(link_representation % (bus0, bus1, link, carrier, efficiency, LINK_THICKNESS, LINK_COLOR))
            count = count + 1


    result[0] = "   // Links (%d)" % count


    return result



def _focus_bus(buses, focus, neighbourhood, bus_filter, link_filter, quiet, visited_buses, visited_links):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    focus : TYPE
        DESCRIPTION.
    neighbourhood : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    link_filter : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.
    visited_buses : TYPE
        DESCRIPTION.
    visited_links : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()


    # display info message
    if not quiet:
        print("Focusing on bus '%s'..." % focus)


    # stop processing as neighbourhood cannot be negative
    if neighbourhood < 0:
        return result


    # check if bus has already been visited (processed)
    if focus in visited_buses:
        return result
    visited_buses.add(focus)


    # represent bus (currently on focus) in DOT
    bus_representation = DOT_REPRESENTATION["BUS"]
    carrier = buses[focus]["carrier"]
    unit = buses[focus]["unit"]
    result.append(bus_representation % (focus, focus, carrier, unit, BUS_MINIMUM_WIDTH, BUS_THICKNESS, BUS_COLOR))


    # stop processing as neighbourhood visiting reached its limit
    if neighbourhood == 0:
        return result


    # represent generators (attached to the bus currently on focus) in DOT
    generator_representation = DOT_REPRESENTATION["GENERATOR"]
    for generator, carrier, efficiency in buses[focus]["GENERATORS"]:
        result.append(generator_representation % (generator, generator, carrier, efficiency, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, GENERATOR_COLOR, generator, focus, LINK_THICKNESS, GENERATOR_COLOR))


    # represent loads (attached to the bus currently on focus) in DOT
    load_representation = DOT_REPRESENTATION["LOAD"]
    for load, carrier in buses[focus]["LOADS"]:
        result.append(load_representation % (load, load, carrier, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, LOAD_COLOR, focus, load, LINK_THICKNESS, LOAD_COLOR))


    # represent stores (attached to the bus currently on focus) in DOT
    store_representation = DOT_REPRESENTATION["STORE"]
    for store, carrier in buses[focus]["STORES"]:
        result.append(store_representation % (store, store, carrier, STORE_MINIMUM_WIDTH, STORE_THICKNESS, STORE_COLOR, focus, store, LINK_THICKNESS, STORE_COLOR, store, focus, LINK_THICKNESS, STORE_COLOR))


    # represent links (attached to the bus currently on focus) in DOT
    link_representation = DOT_REPRESENTATION["LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    for link, bus, carrier, efficiency, bidirectional in buses[focus]["LINKS"]:
        if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
            if link not in visited_links:
                visited_links.add(link)
                if bidirectional:
                    result.append(bidirectional_link_representation % (bus, focus, link, carrier, LINK_THICKNESS, LINK_COLOR))
                else:
                    result.append(link_representation % (bus, focus, link, carrier, efficiency, LINK_THICKNESS, LINK_COLOR))
                result.extend(_focus_bus(buses, bus, neighbourhood - 1, bus_filter, link_filter, quiet, visited_buses, visited_links))


    return result



def _generate_output(dot_representation, file_name, file_format, quiet):
    """
    Parameters
    ----------
    dot_representation : TYPE
        DESCRIPTION.
    file_name : TYPE
        DESCRIPTION.
    file_format : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    # write DOT representation of (PyPSA) network into a DOT file
    file_name_dot = "%s.dot" % file_name.rsplit(".", 1)[0]
    if not quiet:
        print("Generating output file '%s'..." % file_name_dot)
    try:
        with open(file_name_dot, "w") as handle:
            for line in dot_representation:
                handle.write("%s%s" % (line, os.linesep))
            handle.write("%s" % os.linesep)
    except Exception:
        print("The file '%s' could not be generated/written!" % file_name_dot)
        return -1   # return unsuccessfully


    # launch the tool 'dot' passing DOT file to it
    if not quiet:
        print("Launching the tool 'dot'...")
    try:
        result = subprocess.run(["dot", "-T%s" % file_format, file_name_dot], capture_output = True)
    except FileNotFoundError:
        print("The tool 'dot' is not installed or could not be found!")
        return -1   # return unsuccessfully
    except Exception:
        print("The tool 'dot' generated an error!")
        return -1   # return unsuccessfully
    if result.check_returncode():
        print("The tool 'dot' generated an error!")
        return result.check_returncode()   # return unsuccessfully


    # write result generated by the tool 'dot' into an output file
    if not quiet:
        print("Generating output file '%s'..." % file_name)
    try:
        with open(file_name, "wb") as handle:
            handle.write(result.stdout)
    except Exception:
        print("The file '%s' could not be generated/written!" % file_name)
        return -1   # return unsuccessfully


    return 0   # return successfully



def generate(network, focus = None, neighbourhood = 0, bus_filter = None, link_filter = None, carrier_legend = False, file_name = FILE_NAME, file_format = FILE_FORMAT, quiet = True):
    """
    Parameters
    ----------
    network : TYPE
        DESCRIPTION.
    focus : TYPE, optional
        DESCRIPTION. The default is None.
    neighbourhood : TYPE, optional
        DESCRIPTION. The default is 0.
    bus_filter : TYPE, optional
        DESCRIPTION. The default is None.
    link_filter : TYPE, optional
        DESCRIPTION. The default is None.
    carrier_legend : TYPE, optional
        DESCRIPTION. The default is True.
    file_name : TYPE, optional
        DESCRIPTION. The default is FILE_NAME.
    file_format : TYPE, optional
        DESCRIPTION. The default is FILE_FORMAT.
    quiet : TYPE, optional
        DESCRIPTION. The default is True.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    result = list()
    visited = set()


    # display info message
    if not quiet:
        print("Start generating topographical representation of the network...")


    # check if file format is valid
    if file_format not in ("svg", "png", "jpg", "gif", "ps"):
        print("The file format '%s' is not valid (acceptable formats are 'svg', 'png', 'jpg', 'gif' or 'ps')!" % file_format)
        return -1


    # check basic conditions
    if focus:

        # get buses from (PyPSA) network
        if not quiet:
            print("Retrieving buses...")
        buses = _get_buses(network)


        # check if bus to focus on exists in (PyPSA) network
        if isinstance(focus, str):
            if focus not in buses:
                print("The bus '%s' to focus on does not exist!" % focus)
                return -1
        else:   # list
            for bus in focus:
                if bus not in buses:
                    print("The bus '%s' to focus on does not exist!" % bus)
                    return -1


        # check if focus specification matches neighbourhood specification
        if isinstance(focus, str):
            if not isinstance(neighbourhood, int):
                print("The neighbourhood should be a scalar!")
                return -1
        else:   # list
            if not isinstance(neighbourhood, int) and len(neighbourhood) != len(focus):
                print("The number of neighbourhoods should be the same as the number of buses to focus on!")
                return -1


    # compile regular expressions
    bus_filter_regexp = re.compile(bus_filter) if bus_filter else None
    link_filter_regexp = re.compile(link_filter) if link_filter else None


    # get network name
    network_name = network.name if network.name else NETWORK_NAME


    # add metadata to digraph
    now = datetime.datetime.now()
    result.append("//")
    result.append("// Generated by %s version %s on the %04d/%02d/%02d at %02d:%02d:%02d" % (__project__, __version__, now.year, now.month, now.day, now.hour, now.minute, now.second))
    result.append("//")
    result.append("")


    # declare digraph header
    result.append("digraph \"%s\"" % network_name)


    # open digraph body
    result.append("{")


    # configure digraph layout
    result.append("   // configure digraph layout")
    result.append("   labelloc = \"t\"")
    result.append("   label = \"%s\n\n           \"" % network_name)
    result.append("   rankdir = \"%s\"" % RANK_DIRECTION)
    result.append("   ranksep = %.1f" % RANK_SEPARATION)
    result.append("   nodesep = %.1f" % NODE_SEPARATION)
    result.append("   splines = \"%s\"" % EDGE_STYLE)
    result.append("   node [fontname = \"%s\", fontsize = %.1f, fontcolor = \"%s\"]" % (TEXT_FONT, TEXT_SIZE, TEXT_COLOR))
    result.append("   edge [fontname = \"%s\", fontsize = %.1f, fontcolor = \"%s\"]" % (TEXT_FONT, TEXT_SIZE, TEXT_COLOR))
    result.append("")


    # generate carrier legend
    if carrier_legend:
        # to be implemented
        pass


    if focus:
        # get generators from (PyPSA) network
        if not quiet:
            print("Retrieving generators...")
        _get_generators(buses, network.generators)


        # get loads from (PyPSA) network
        if not quiet:
            print("Retrieving loads...")
        _get_loads(buses, network.loads)


        # get stores from (PyPSA) network
        if not quiet:
            print("Retrieving stores...")
        _get_stores(buses, network.stores)


        # get links from (PyPSA) network
        if not quiet:
            print("Retrieving links...")
        _get_links(buses, network.links)


        # focus on bus
        if isinstance(focus, str):
            result.extend(_focus_bus(buses, focus, neighbourhood, bus_filter_regexp, link_filter_regexp, quiet, set(), set()))
        else:   # list
            for i in range(len(focus)):
                bus = focus[i]
                if bus not in visited:   # skip bus as it has already been visited (processed)
                    if isinstance(neighbourhood, int):
                        result.extend(_focus_bus(buses, bus, neighbourhood, bus_filter_regexp, link_filter_regexp, quiet, set(), set()))
                    else:   # list
                        result.extend(_focus_bus(buses, bus, neighbourhood[i], bus_filter_regexp, link_filter_regexp, quiet, set(), set()))
                    visited.add(bus)

    else:

        # represent buses in DOT
        if not quiet:
            print("Processing buses...")
        result.extend(_represent_buses(network.buses, bus_filter_regexp))
        result.append("")


        # represent generators in DOT
        if not quiet:
            print("Processing generators...")
        result.extend(_represent_generators(network.generators, bus_filter_regexp))
        result.append("")


        # represent loads in DOT
        if not quiet:
            print("Processing loads...")
        result.extend(_represent_loads(network.loads, bus_filter_regexp))
        result.append("")


        # represent stores in DOT
        if not quiet:
            print("Processing stores...")
        result.extend(_represent_stores(network.stores, bus_filter_regexp))
        result.append("")


        # represent links in DOT
        if not quiet:
            print("Processing links...")
        result.extend(_represent_links(network.links, bus_filter_regexp, link_filter_regexp))


    # close digraph body
    result.append("}")


    # generate output files based on (PyPSA) network DOT representation
    status = _generate_output(result, file_name, file_format, quiet)


    # display info message
    if not quiet:
        print("... finished generating topographical representation of the network!")


    return status



if __name__ == "__main__":

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
    network.add("Link", "ICE", bus0 = "oil", bus1 = "transport")
    network.add("Link", "BEV", bus0 = "electricity", bus1 = "transport")


    # generate topographical representation of dummy (PyPSA) network
    status = generate(network)


    # set exit code and finish
    sys.exit(status)

