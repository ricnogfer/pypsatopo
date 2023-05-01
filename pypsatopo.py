#!/usr/bin/env python3



__author__ = "Energy Systems Group at Aarhus University (Denmark)"
__project__ = "PyPSATopo"
__description__ = "PyPSATopo is a tool which allows generating the topographical representation of any arbitrary PyPSA-based network (thanks to the DOT language - https://graphviz.org)"
__license__ = "BSD 3-Clause"
__contact__ = "ricardo.fernandes@mpe.au.dk"
__version__ = "0.4.0"
__status__ = "Development"



# import necessary modules
import os
import sys
import re
import argparse
import datetime
import subprocess
import colorsys
import pypsa
import pandas



# declare (public) global variables (these can be overwritten by the caller to adjust/personalize the topographical representation of the PyPSA-based network)
DOT_REPRESENTATION = {"BUS": "   \"%s (bus)\" [label = \"%s\", tooltip = \"Bus: %s\nCarrier: %s\nUnit: %s\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f)\", color = \"%s\"]",
                      "MISSING_BUS": "   \"%s (bus)\" [label = \"%s\", tooltip = \"Bus: %s (missing)\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f), dashed\", color = \"%s\"]",
                      "GENERATOR": "   \"%s (generator)\" [label = \"%s\", tooltip = \"Generator: %s\nCarrier: %s\nP-nom: %s MW\nP-set: %s MW\nEfficiency: %.2f\", shape = \"circle\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (generator)\" -> \"%s (bus)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "LOAD": "   \"%s (load)\" [label = \"%s\", tooltip = \"Load: %s\nCarrier: %s\nP-set: %s MW\", shape = \"invtriangle\", width = %.2f, height = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (load)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "STORE": "   \"%s (store)\" [label = \"%s\", tooltip = \"Store: %s\nCarrier: %s\nE-cyclic: %s\", shape = \"box\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (store)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nEfficiency: %.2f\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nEfficiency: %.2f\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nEfficiency: 1.00\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "BROKEN_BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nEfficiency: 1.00\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "MULTI_LINK_POINT": "   \"%s (multi-link)\" [label = \"%s\", tooltip = \"Multi-link: %s\nFrom: %s (bus0)\nTo: %d buses (%d missing)\", shape = \"point\", width = %.2f, color = \"%s\"]",
                      "MULTI_LINK_BUS_TO_POINT": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = \"%s\", tooltip = \"Multi-link: %s\nCarrier: %s\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "MULTI_LINK_POINT_TO_BUS": "   \"%s\" -> \"%s\" [label = \"%s\", tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nEfficiency: %.2f\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_MULTI_LINK_POINT_TO_BUS": "   \"%s (multi-link)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Multi-link: %s (broken)\nFrom: %s (bus0)\nTo: %s\nCarrier: %s\nEfficiency: %.2f\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]"
                     }
FILE_FORMAT = "svg"   # possible values are: "svg", "png", "jpg", "gif" and "ps"
FILE_NAME = "topography.%s" % FILE_FORMAT
BACKGROUND_COLOR = "transparent"
NETWORK_NAME = "My Network"
RANK_DIRECTION = "TB"   # possible values are: "TB" (top to bottom), "BT" (bottom to top), "LR" (left to right) and "RL" (right to left)
RANK_SEPARATION = 1.0
NODE_SEPARATION = 1.0
EDGE_STYLE = "polyline"   # possible values are: "polyline", "curved", "ortho" and "none"
TEXT_FONT = "Courier New"
TEXT_SIZE = 8.0
TEXT_COLOR = "red"
BUS_MINIMUM_WIDTH = 3.0
BUS_THICKNESS = 7.0
BUS_COLOR = "black"
MISSING_BUS_COLOR = "grey65"
GENERATOR_MINIMUM_WIDTH = 1.1
GENERATOR_THICKNESS = 2.0
GENERATOR_COLOR = "black"
LOAD_MINIMUM_WIDTH = 1.4
LOAD_MINIMUM_HEIGHT = 1.2
LOAD_THICKNESS = 2.0
LOAD_COLOR = "black"
STORE_MINIMUM_WIDTH = 1.3
STORE_THICKNESS = 2.0
STORE_COLOR = "black"
LINK_THICKNESS = 1.5
LINK_COLOR = "black"
LINK_ARROW_SHAPE = "vee"   # possible values are: "vee", "normal", "onormal", "diamond", "odiamond", "curve" and "none"
LINK_ARROW_SIZE = 1.2
BROKEN_LINK_COLOR = "grey65"
MULTI_LINK_POINT_WIDTH = 0.05



# declare (private) global variables (these should not be overwritten by the caller)
_MISSING_BUS_COUNT = 0



def HSVToRGB(h, s, v):
    """
    Parameters
    ----------
    h : TYPE
        DESCRIPTION.
    s : TYPE
        DESCRIPTION.
    v : TYPE
        DESCRIPTION.
    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    (r, g, b) = colorsys.hsv_to_rgb(h, s, v)

    return (int(255 * r), int(255 * g), int(255 * b))



def _get_distinct_colors(n):
    """
    Parameters
    ----------
    n : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    huePartition = 1.0 / (n + 1)

    result = []
    for i in range(n):
        result.append("#%02x%02x%02x" % HSVToRGB(huePartition * i, 1.0, 1.0))

    return result



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
        result[bus] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": carrier, "unit": unit, "missing": False}


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
        p_nom = generators.p_nom[i]
        p_set = generators.p_set[i]
        efficiency = generators.efficiency[i]
        bus = generators.bus.values[i]
        if bus in buses:
            buses[bus]["GENERATORS"].append((generator, carrier, p_nom, p_set, efficiency))



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
        p_set = loads.p_set[i]
        bus = loads.bus.values[i]
        if bus in buses:
            buses[bus]["LOADS"].append((load, carrier, p_set))



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
        e_cyclic = "True" if stores.e_cyclic[i] else "False"
        bus = stores.bus.values[i]
        if bus in buses:
            buses[bus]["STORES"].append((store, carrier, e_cyclic))



def _get_links(buses, links, quiet):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    links : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    global _MISSING_BUS_COUNT


    # get declared buses that links connect to
    bus_regexp = re.compile("^bus[0-9]+$")
    declared_buses = list()
    for column in links.columns:
        if bus_regexp.match(column):
            declared_buses.append(column)


    # get declared efficiencies that links have
    efficiency_regexp = re.compile("^efficiency[0-9]*$")
    declared_efficiencies = set()
    for column in links.columns:
        if efficiency_regexp.match(column):
            if column == "efficiency":
                declared_efficiencies.add("0")
            else:
                declared_efficiencies.add(column[10:])


    # loop through existing links
    for i in range(len(links)):


        # get specified buses (from declared buses) that the link connects to as well as efficiency values
        link = links.iloc[i]
        specified_buses = list()
        for bus in declared_buses:
            value = link[bus]
            if not pandas.isna(value):
                number = bus[3:]
                if number == "0":
                    efficiency = 1.0
                elif number == "1":
                    if "0" in declared_efficiencies:
                        efficiency = link["efficiency"]
                        if pandas.isna(efficiency):
                            efficiency = 1.0
                    else:
                        efficiency = 1.0
                elif number in declared_efficiencies:
                    efficiency = link["efficiency%s" % number]
                    if pandas.isna(efficiency):
                        efficiency = 1.0
                else:
                    efficiency = 1.0
                specified_buses.append([bus, value, efficiency])


        # check that buses that the link connects to exist
        broken = 0
        for value in specified_buses:
            bus_name, bus_value, bus_efficiency = value
            if bus_value in buses:
                value.append(True)
            else:
                value.append(False)
                broken = broken + 1
                if not quiet:
                    if bus_value:
                        print("Link '%s' connects to bus '%s' which does not exist..." % (links.index.values[i], bus_value))
                    else:
                        print("Link '%s' connects to bus '%s' which does not have a value..." % (links.index.values[i], bus_name))


        # process link
        if len(specified_buses) < 3:   # mono-link
            link = links.index.values[i]
            bus0 = links.bus0[i]
            bus1 = links.bus1[i]
            carrier = links.carrier[i]
            efficiency = links.efficiency[i]
            bidirectional = (efficiency == 1 and links.marginal_cost[i] == 0 and links.p_min_pu[i] == -1)
            if bus0:   # specified
                if bus1:   # specified
                    missing = False
                    if bus0 not in buses:
                        buses[bus0] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
                        missing = True
                    if bus1 not in buses:
                        buses[bus1] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
                        missing = True
                else:   # not specified
                    missing = True
                    if bus0 not in buses:
                        buses[bus0] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
                    bus1 = "bus #%d" % _MISSING_BUS_COUNT
                    _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                    buses[bus1] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
            else:   # not specified
                missing = True
                bus0 = "bus #%d" % _MISSING_BUS_COUNT
                _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                buses[bus0] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
                if bus1:   # specified
                    if bus1 not in buses:
                        buses[bus1] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
                else:   # not specified
                    bus1 = "bus #%d" % _MISSING_BUS_COUNT
                    _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                    buses[bus1] = {"GENERATORS": list(), "LOADS": list(), "STORES": list(), "LINKS": list(), "MULTI_LINK_POINTS": list(), "MULTI_LINK_BUS_TO_POINTS": list(), "MULTI_LINK_POINT_TO_BUSES": list(), "carrier": "", "unit": "", "missing": True}
            buses[bus0]["LINKS"].append((link, bus1, carrier, efficiency, bidirectional, True, missing))
            buses[bus1]["LINKS"].append((link, bus0, carrier, efficiency, bidirectional, False, missing))
        else:   # multi-link
            # TODO
            pass



def _represent_buses(buses, bus_filter, carrier_color):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    result.append(None)


    # get bus DOT representation
    bus_representation = DOT_REPRESENTATION["BUS"]


    # loop through existing buses
    for i in range(len(buses)):
        bus = buses.index.values[i]
        carrier = buses.carrier[i]
        unit = "" if buses.unit[i] == "None" else buses.unit[i]
        bus_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else BUS_COLOR
        if not bus_filter or bus_filter.match(bus):
            result.append(bus_representation % (bus, bus, bus, carrier, unit, BUS_MINIMUM_WIDTH, BUS_THICKNESS, bus_color))


    result[0] = "   // add buses (%d)" % (len(result) - 1)


    return result



def _represent_generators(generators, bus_filter, carrier_color):
    """
    Parameters
    ----------
    generators : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    result.append(None)


    # get generator DOT representation
    generator_representation = DOT_REPRESENTATION["GENERATOR"]


    # loop through existing generators
    for i in range(len(generators)):
        generator = generators.index.values[i]
        carrier = generators.carrier[i]
        p_nom = generators.p_nom[i]
        p_set = generators.p_set[i]
        efficiency = generators.efficiency[i]
        bus = generators.bus.values[i]
        generator_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else GENERATOR_COLOR
        if not bus_filter or bus_filter.match(bus):
            result.append(generator_representation % (generator, generator, generator, carrier, p_nom, p_set, efficiency, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, generator_color, generator, bus, LINK_THICKNESS, generator_color))


    result[0] = "   // add generators (%d)" % (len(result) - 1)


    return result



def _represent_loads(loads, bus_filter, carrier_color):
    """
    Parameters
    ----------
    loads : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    result.append(None)


    # get load DOT representation
    load_representation = DOT_REPRESENTATION["LOAD"]


    # loop through existing loads
    for i in range(len(loads)):
        load = loads.index.values[i]
        carrier = loads.carrier[i]
        p_set = loads.p_set[i]
        bus = loads.bus.values[i]
        load_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LOAD_COLOR
        if not bus_filter or bus_filter.match(bus):
            result.append(load_representation % (load, load, load, carrier, p_set, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, load_color, bus, load, LINK_THICKNESS, load_color))


    result[0] = "   // add loads (%d)" % (len(result) - 1)


    return result



def _represent_stores(stores, bus_filter, carrier_color):
    """
    Parameters
    ----------
    stores : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    result.append(None)


    # get store DOT representation
    store_representation = DOT_REPRESENTATION["STORE"]


    # loop through existing stores
    for i in range(len(stores)):
        store = stores.index.values[i]
        carrier = stores.carrier[i]
        e_cyclic = "True" if stores.e_cyclic[i] else "False"
        bus = stores.bus.values[i]
        store_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else STORE_COLOR
        if not bus_filter or bus_filter.match(bus):
            result.append(store_representation % (store, store, store, carrier, e_cyclic, STORE_MINIMUM_WIDTH, STORE_THICKNESS, store_color, bus, store, LINK_THICKNESS, store_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


    result[0] = "   // add stores (%d)" % (len(result) - 1)


    return result



def _represent_links(buses, links, bus_filter, link_filter, negative_efficiency, broken_link, carrier_color, quiet):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    links : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    link_filter : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_link : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    global _MISSING_BUS_COUNT


    result = list()
    result.append(None)
    count = 0


    # get (mono, multi and bidirectional) link DOT representation
    missing_bus_representation = DOT_REPRESENTATION["MISSING_BUS"]
    link_representation = DOT_REPRESENTATION["LINK"]
    broken_link_representation = DOT_REPRESENTATION["BROKEN_LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    broken_bidirectional_link_representation = DOT_REPRESENTATION["BROKEN_BIDIRECTIONAL_LINK"]
    multi_link_point_representation = DOT_REPRESENTATION["MULTI_LINK_POINT"]
    multi_link_bus_to_point_representation = DOT_REPRESENTATION["MULTI_LINK_BUS_TO_POINT"]
    multi_link_point_to_bus_representation = DOT_REPRESENTATION["MULTI_LINK_POINT_TO_BUS"]
    broken_multi_link_point_to_bus_representation = DOT_REPRESENTATION["BROKEN_MULTI_LINK_POINT_TO_BUS"]


    # get declared buses that links connect to
    bus_regexp = re.compile("^bus[0-9]+$")
    declared_buses = list()
    for column in links.columns:
        if bus_regexp.match(column):
            declared_buses.append(column)


    # get declared efficiencies that links have
    efficiency_regexp = re.compile("^efficiency[0-9]*$")
    declared_efficiencies = set()
    for column in links.columns:
        if efficiency_regexp.match(column):
            if column == "efficiency":
                declared_efficiencies.add("0")
            else:
                declared_efficiencies.add(column[10:])


    # loop through existing links
    for i in range(len(links)):


        # get specified buses (from declared buses) that the link connects to as well as efficiency values
        link = links.iloc[i]
        specified_buses = dict()
        for bus in declared_buses:
            value = link[bus]
            if not pandas.isna(value):
                number = bus[3:]
                if number == "0":
                    efficiency = 1.0
                elif number == "1":
                    if "0" in declared_efficiencies:
                        efficiency = link["efficiency"]
                        if pandas.isna(efficiency):
                            efficiency = 1.0
                    else:
                        efficiency = 1.0
                elif number in declared_efficiencies:
                    efficiency = link["efficiency%s" % number]
                    if pandas.isna(efficiency):
                        efficiency = 1.0
                else:
                    efficiency = 1.0
                specified_buses[bus] = [value, efficiency]


        # check that buses that the link connects to exist
        broken = 0
        for key, value in specified_buses.items():
            bus_value, bus_efficiency = value
            if bus_value in buses.index:
                value.append(True)
            else:
                value.append(False)
                broken = broken + 1
                if not quiet:
                    if bus_value:
                        print("Link '%s' connects to bus '%s' which does not exist..." % (links.index.values[i], bus_value))
                    else:
                        print("Link '%s' connects to bus '%s' which does not have a value..." % (links.index.values[i], key))


        # process link
        link = links.index.values[i]
        if not link_filter or link_filter.match(link):
            if len(specified_buses) < 3:   # mono-link
                bus0 = links.bus0[i]
                bus1 = links.bus1[i]
                carrier = links.carrier[i]
                efficiency = links.efficiency[i]
                bidirectional = (efficiency == 1 and links.marginal_cost[i] == 0 and links.p_min_pu[i] == -1)
                link_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LINK_COLOR
                if bus0:   # specified
                    if bus1:   # specified
                        if not bus_filter or (bus_filter.match(bus0) and bus_filter.match(bus1)):
                            missing = False
                            if bus0 not in buses.index:
                                if broken_link:
                                    result.append(missing_bus_representation % (bus0, bus0, bus0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                missing = True
                            if bus1 not in buses.index:
                                if broken_link:
                                    result.append(missing_bus_representation % (bus1, bus1, bus1, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                missing = True
                            if missing:
                                if broken_link:
                                    if bidirectional:
                                        result.append(broken_bidirectional_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                    elif negative_efficiency or efficiency >= 0:
                                        result.append(broken_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                    else:
                                        result.append(broken_link_representation % (bus1, bus0, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus1, "%s (bus0)" % bus0, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                if bidirectional:
                                    result.append(bidirectional_link_representation % (bus0, bus1, link, link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                elif negative_efficiency or efficiency >= 0:
                                    result.append(link_representation % (bus0, bus1, link, link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                else:
                                    result.append(link_representation % (bus1, bus0, link, "%s (inverted)" % link, "%s (bus1)" % bus1, "%s (bus0)" % bus0, carrier, -efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            count = count + 1
                    else:   # not specified
                        if broken_link:
                            if not bus_filter or bus_filter.match(bus0):
                                if bus0 not in buses.index:
                                    result.append(missing_bus_representation % (bus0, bus0, bus0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                bus1 = "bus #%d" % _MISSING_BUS_COUNT
                                _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                                result.append(missing_bus_representation % (bus1, bus1, bus1, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                if bidirectional:
                                    result.append(broken_bidirectional_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                elif negative_efficiency or efficiency >= 0:
                                    result.append(broken_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                else:
                                    result.append(broken_link_representation % (bus1, bus0, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus1, "%s (bus0)" % bus0, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                count = count + 1
                else:   # not specified
                    if broken_link:
                        if bus1:   # specified
                            if not bus_filter or bus_filter.match(bus1):
                                bus0 = "bus #%d" % _MISSING_BUS_COUNT
                                _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                                result.append(missing_bus_representation % (bus0, bus0, bus0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                if bus1 not in buses.index:
                                    result.append(missing_bus_representation % (bus1, bus1, bus1, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                if bidirectional:
                                    result.append(broken_bidirectional_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                elif negative_efficiency or efficiency >= 0:
                                    result.append(broken_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                else:
                                    result.append(broken_link_representation % (bus1, bus0, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus1, "%s (bus0)" % bus0, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                count = count + 1
                        else:   # not specified
                            bus0 = "bus #%d" % _MISSING_BUS_COUNT
                            _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                            result.append(missing_bus_representation % (bus0, bus0, bus0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                            bus1 = "bus #%d" % _MISSING_BUS_COUNT
                            _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                            result.append(missing_bus_representation % (bus1, bus1, bus1, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                            if bidirectional:
                                result.append(broken_bidirectional_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            elif negative_efficiency or efficiency >= 0:
                                result.append(broken_link_representation % (bus0, bus1, link, "%s (broken)" % link, "%s (bus0)" % bus0, "%s (bus1)" % bus1, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_link_representation % (bus1, bus0, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus1, "%s (bus0)" % bus0, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            count = count + 1
            else:   # multi-link
                process = True
                if bus_filter:
                    for bus_value, bus_efficiency, bus_exists in specified_buses.values():
                        if bus_exists and bus_filter.match(bus_value):
                            process = False
                            break
                if process:
                    carrier = links.carrier[i]
                    link_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LINK_COLOR
                    if "bus0" in specified_buses:
                        bus0_value, bus0_efficiency, bus0_exists = specified_buses["bus0"]
                        if bus0_exists:
                            if broken == len(specified_buses) - 1:
                                result.append(multi_link_point_representation % (link, link, link, bus0_value, len(specified_buses) - 1, broken, MULTI_LINK_POINT_WIDTH, BROKEN_LINK_COLOR))
                                result.append(multi_link_bus_to_point_representation % (bus0_value, link, link, "%s (broken)" % link, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR))
                            else:
                                result.append(multi_link_point_representation % (link, link, link, bus0_value, len(specified_buses) - 1, broken, MULTI_LINK_POINT_WIDTH, link_color))
                                result.append(multi_link_bus_to_point_representation % (bus0_value, link, link, link, carrier, LINK_THICKNESS, link_color))
                        else:
                            if not bus0_value:
                                bus0_value = "bus #%d" % _MISSING_BUS_COUNT
                                _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                            result.append(missing_bus_representation % (bus0_value, bus0_value, bus0_value, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                            if broken == len(specified_buses):
                                result.append(multi_link_point_representation % (link, link, link, bus0_value, len(specified_buses), broken, MULTI_LINK_POINT_WIDTH, BROKEN_LINK_COLOR))
                                result.append(multi_link_bus_to_point_representation % (bus0_value, link, link, "%s (broken)" % link, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR))
                            else:
                                result.append(multi_link_point_representation % (link, link, link, bus0_value, len(specified_buses), broken, MULTI_LINK_POINT_WIDTH, link_color))
                                result.append(multi_link_bus_to_point_representation % (bus0_value, link, link, bus0_value, carrier, LINK_THICKNESS, link_color))
                    else:
                        bus0_value = "Unknown"
                    for key, value in specified_buses.items():
                        bus_value, bus_efficiency, bus_exists = value
                        if key != "bus0":
                            if bus_exists:
                                if negative_efficiency or bus_efficiency >= 0:
                                    result.append(multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_value, link, link, "%s (bus0)" % bus0_value, "%s (%s)" % (bus_value, key), carrier, bus_efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                                else:
                                    result.append(multi_link_point_to_bus_representation % ("%s (bus)" % bus_value, "%s (multi-link)" % link, link, "%s (inverted)" % link, "%s (%s)" % (bus_value, key), "%s (bus0)" % bus0_value, carrier, -bus_efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                if broken_link:
                                    if not bus_value:
                                        bus_value = "bus #%d" % _MISSING_BUS_COUNT
                                        _MISSING_BUS_COUNT = _MISSING_BUS_COUNT + 1
                                    result.append(missing_bus_representation % (bus_value, bus_value, bus_value, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
                                    result.append(broken_multi_link_point_to_bus_representation % (link, bus_value, link, link, bus0_value, "%s (%s)" % (bus_value, key), carrier, bus_efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    count = count + 1


    result[0] = "   // add links (%d)" % count


    return result



def _focus_bus(buses, focus, neighbourhood, bus_filter, link_filter, negative_efficiency, broken_link, carrier_color, quiet, visited_buses, visited_links):
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
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_link : TYPE
        DESCRIPTION.
    carrier_color : TYPE
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


    # check if bus has already been visited (processed)
    if focus in visited_buses:
        return result
    visited_buses.add(focus)


    # represent bus (currently on focus) in DOT
    bus_representation = DOT_REPRESENTATION["BUS"]
    missing_bus_representation = DOT_REPRESENTATION["MISSING_BUS"]
    if buses[focus]["missing"]:
        if broken_link:
            result.append(missing_bus_representation % (focus, focus, focus, BUS_MINIMUM_WIDTH, BUS_THICKNESS, MISSING_BUS_COLOR))
    else:
        carrier = buses[focus]["carrier"]
        unit = buses[focus]["unit"]
        bus_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else BUS_COLOR
        result.append(bus_representation % (focus, focus, focus, carrier, unit, BUS_MINIMUM_WIDTH, BUS_THICKNESS, bus_color))


    # stop processing as neighbourhood visiting reached the limit
    if neighbourhood == 0:
        return result


    # represent generators (attached to the bus currently on focus) in DOT
    generator_representation = DOT_REPRESENTATION["GENERATOR"]
    for generator, carrier, p_nom, p_set, efficiency in buses[focus]["GENERATORS"]:
        generator_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else GENERATOR_COLOR
        result.append(generator_representation % (generator, generator, generator, carrier, p_nom, p_set, efficiency, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, generator_color, generator, focus, LINK_THICKNESS, generator_color))


    # represent loads (attached to the bus currently on focus) in DOT
    load_representation = DOT_REPRESENTATION["LOAD"]
    for load, carrier, p_set in buses[focus]["LOADS"]:
        load_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LOAD_COLOR
        result.append(load_representation % (load, load, load, carrier, p_set, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, load_color, focus, load, LINK_THICKNESS, load_color))


    # represent stores (attached to the bus currently on focus) in DOT
    store_representation = DOT_REPRESENTATION["STORE"]
    for store, carrier, e_cyclic in buses[focus]["STORES"]:
        store_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else STORE_COLOR
        result.append(store_representation % (store, store, store, carrier, e_cyclic, STORE_MINIMUM_WIDTH, STORE_THICKNESS, store_color, focus, store, LINK_THICKNESS, store_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


    # represent links (attached to the bus currently on focus) in DOT
    link_representation = DOT_REPRESENTATION["LINK"]
    broken_link_representation = DOT_REPRESENTATION["BROKEN_LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    broken_bidirectional_link_representation = DOT_REPRESENTATION["BROKEN_BIDIRECTIONAL_LINK"]
    for link, bus, carrier, efficiency, bidirectional, direction, missing in buses[focus]["LINKS"]:
        if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
            if link not in visited_links:
                visited_links.add(link)
                if missing:
                    if broken_link:
                        if bidirectional:
                            if direction:
                                result.append(broken_bidirectional_link_representation % (focus, bus, link, "%s (broken)" % link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_bidirectional_link_representation % (bus, focus, link, "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result.append(broken_link_representation % (focus, bus, link, "%s (broken)" % link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_link_representation % (bus, focus, link, "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result.append(broken_link_representation % (focus, bus, link, "%s (broken & inverted)" % link, "%s (bus1)" % focus, "%s (bus0)" % bus, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_link_representation % (bus, focus, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % focus, carrier, -efficiency, LINK_THICKNESS, BROKEN_LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                else:
                    link_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LINK_COLOR
                    if bidirectional:
                        if direction:
                            result.append(bidirectional_link_representation % (focus, bus, link, link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(bidirectional_link_representation % (bus, focus, link, link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result.append(link_representation % (focus, bus, link, link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(link_representation % (bus, focus, link, link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result.append(link_representation % (bus, focus, link, "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % focus, carrier, -efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(link_representation % (focus, bus, link, "%s (inverted)" % link, "%s (bus1)" % focus, "%s (bus0)" % bus, carrier, -efficiency, LINK_THICKNESS, link_color, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                result.extend(_focus_bus(buses, bus, neighbourhood - 1, bus_filter, link_filter, negative_efficiency, broken_link, carrier_color, quiet, visited_buses, visited_links))   # focus on neighbouring (adjacent) bus in a recursive fashion


    """
    # represent multi-link points (attached to the bus currently on focus) in DOT
    multi_link_point_representation = DOT_REPRESENTATION["MULTI_LINK_POINT"]
    for bus in buses[focus]["MULTI_LINK_POINTS"]:
        if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
            #if link not in visited_links:
            #    visited_links.add(link)
            if True:
                #"MULTI_LINK_POINT": "   \"%s (multi-link)\" [label = \"%s\", shape = \"point\", style = \"setlinewidth(%.2f)\", color = \"%s\"]",
                result.append(multi_link_point_representation % (bus, bus, MULTI_LINK_POINT_WIDTH, LINK_COLOR))


    # represent multi-link from bus to points (attached to the bus currently on focus) in DOT
    multi_link_bus_to_point_representation = DOT_REPRESENTATION["MULTI_LINK_BUS_TO_POINT"]
    for bus, point, label, carrier in buses[focus]["MULTI_LINK_BUS_TO_POINTS"]:
        #if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
        #    if link not in visited_links:
        #        visited_links.add(link)
        if True:
            result.append(multi_link_bus_to_point_representation % (bus, point, label, carrier, LINK_THICKNESS, LINK_COLOR))


    # represent multi-link from point to buses (attached to the bus currently on focus) in DOT
    multi_link_point_to_bus_representation = DOT_REPRESENTATION["MULTI_LINK_POINT_TO_BUS"]
    for point, bus, label, carrier, efficiency in buses[focus]["MULTI_LINK_POINT_TO_BUSES"]:
        #if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
        #    if link not in visited_links:
        #        visited_links.add(link)
        if True:
            result.append(multi_link_point_to_bus_representation % (point, bus, label, carrier, efficiency, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            result.extend(_focus_bus(buses, bus, neighbourhood - 1, bus_filter, link_filter, quiet, visited_buses, visited_links))   # focus on neighbouring (adjacent) bus in a recursive fashion
    """


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
        print("Writing DOT file '%s'..." % file_name_dot)
    try:
        with open(file_name_dot, "w") as handle:
            for line in dot_representation:
                handle.write("%s%s" % (line, os.linesep))
            handle.write("%s" % os.linesep)
    except Exception:
        print("The file '%s' could not be written!" % file_name_dot)
        return -1   # return unsuccessfully


    # launch the tool 'dot' passing DOT file to it
    if not quiet:
        print("Generating topographical representation of the network based on DOT file '%s'..." % file_name_dot)
    try:
        result = subprocess.run(["dot", "-T%s" % file_format, file_name_dot], capture_output = True)
    except FileNotFoundError:
        print("The tool 'dot' is not installed or could not be found (please visit https://graphviz.org/download to download and install it)!")
        return -1   # return unsuccessfully
    except Exception:
        print("The tool 'dot' generated an error!")
        return -1   # return unsuccessfully
    if result.check_returncode():
        print("The tool 'dot' generated an error!")
        return result.check_returncode()   # return unsuccessfully


    # write result generated by the tool 'dot' into an output file
    if not quiet:
        print("Writing output file '%s' in the %s format..." % (file_name, file_format.upper()))
    try:
        with open(file_name, "wb") as handle:
            handle.write(result.stdout)
    except Exception:
        print("The file '%s' could not be written!" % file_name)
        return -1   # return unsuccessfully


    return 0   # return successfully



def generate(network, focus = None, neighbourhood = 0, bus_filter = None, link_filter = None, negative_efficiency = True, broken_link = True, carrier_color = None, file_name = FILE_NAME, file_format = FILE_FORMAT, quiet = True):
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
    negative_efficiency : TYPE, optional
        DESCRIPTION. The default is True.
    broken_link : TYPE, optional
        DESCRIPTION. The default is True.
    carrier_color : TYPE, optional
        DESCRIPTION. The default is None.
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


    # check if neighbourhood is valid
    if neighbourhood < 0:
        print("The neighbourhood should be equal or greater than 0")
        return -1   # return unsuccessfully


    # process carrier color
    if isinstance(carrier_color, bool) and carrier_color:
        carrier_color = dict()
        for i in range(len(network.buses)):
            carrier = network.buses.carrier[i]
            if carrier not in carrier_color:
                carrier_color[carrier] = None
        for i in range(len(network.generators)):
            carrier = network.generators.carrier[i]
            if carrier not in carrier_color:
                carrier_color[carrier] = None
        for i in range(len(network.loads)):
            carrier = network.loads.carrier[i]
            if carrier not in carrier_color:
                carrier_color[carrier] = None
        for i in range(len(network.stores)):
            carrier = network.stores.carrier[i]
            if carrier not in carrier_color:
                carrier_color[carrier] = None
        for i in range(len(network.links)):
            carrier = network.links.carrier[i]
            if carrier not in carrier_color:
                carrier_color[carrier] = None
        colors = _get_distinct_colors(len(carrier_color))
        i = 0
        for key in carrier_color.keys():
            carrier_color[key] = colors[i]
            i = i + 1


    # check if file format is valid
    if file_format not in ("svg", "png", "jpg", "gif", "ps"):
        print("The file format '%s' is not valid (acceptable formats are 'svg', 'png', 'jpg', 'gif' or 'ps')!" % file_format)
        return -1   # return unsuccessfully


    # display info message
    if not quiet:
        print("Start generating topographical representation of the network...")


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
                return -1   # return unsuccessfully
        else:   # list
            for bus in focus:
                if bus not in buses:
                    print("The bus '%s' to focus on does not exist!" % bus)
                    return -1   # return unsuccessfully


        # check if focus specification matches neighbourhood specification
        if isinstance(focus, str):
            if not isinstance(neighbourhood, int):
                print("The neighbourhood should be a scalar!")
                return -1   # return unsuccessfully
        else:   # list
            if not isinstance(neighbourhood, int) and len(neighbourhood) != len(focus):
                print("The number of neighbourhoods should be the same as the number of buses to focus on!")
                return -1   # return unsuccessfully


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
    result.append("   bgcolor = \"%s\"" % BACKGROUND_COLOR)
    result.append("   labelloc = \"t\"")
    result.append("   label = \"%s\n\n           \"" % network_name)
    result.append("   rankdir = \"%s\"" % RANK_DIRECTION)
    result.append("   ranksep = %.2f" % RANK_SEPARATION)
    result.append("   nodesep = %.2f" % NODE_SEPARATION)
    result.append("   splines = \"%s\"" % EDGE_STYLE)
    result.append("   node [fontname = \"%s\", fontsize = %.2f, fontcolor = \"%s\"]" % (TEXT_FONT, TEXT_SIZE, TEXT_COLOR))
    result.append("   edge [fontname = \"%s\", fontsize = %.2f, fontcolor = \"%s\"]" % (TEXT_FONT, TEXT_SIZE, TEXT_COLOR))
    result.append("")


    # add carrier color table (if requested)
    if carrier_color:
        result.append("   // add carrier color table")
        result.append("   \"Carrier Color Table\" [shape = \"none\" label = <")
        result.append("      <table border = \"0\" cellborder = \"1\" cellspacing = \"0\" cellpadding = \"5\">")
        result.append("         <tr>")
        result.append("            <td width = \"110\" bgcolor = \"grey92\"><font color = \"black\"><b>CARRIER</b></font></td><td width = \"130\" bgcolor = \"grey92\"><font color = \"black\"><b>COLOR</b></font></td>")
        result.append("         </tr>")
        for key, value in carrier_color.items():
            result.append("         <tr>")
            result.append("            <td width = \"110\">%s</td><td width = \"130\" bgcolor = \"%s\"></td>" % (key, value))
            result.append("         </tr>")
        result.append("      </table>")
        result.append("   >];")
        result.append("")


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
        _get_links(buses, network.links, quiet)


        # focus on bus
        if isinstance(focus, str):
            result.extend(_focus_bus(buses, focus, neighbourhood, bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_link, carrier_color, quiet, set(), set()))
        else:   # list
            for i in range(len(focus)):
                bus = focus[i]
                if bus not in visited:   # skip bus as it has already been visited (processed)
                    if isinstance(neighbourhood, int):
                        result.extend(_focus_bus(buses, bus, neighbourhood, bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_link, carrier_color, quiet, set(), set()))
                    else:   # list
                        result.extend(_focus_bus(buses, bus, neighbourhood[i], bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_link, carrier_color, quiet, set(), set()))
                    visited.add(bus)

    else:

        # represent buses in DOT
        if not quiet:
            print("Processing buses...")
        result.extend(_represent_buses(network.buses, bus_filter_regexp, carrier_color))
        result.append("")


        # represent generators in DOT
        if not quiet:
            print("Processing generators...")
        result.extend(_represent_generators(network.generators, bus_filter_regexp, carrier_color))
        result.append("")


        # represent loads in DOT
        if not quiet:
            print("Processing loads...")
        result.extend(_represent_loads(network.loads, bus_filter_regexp, carrier_color))
        result.append("")


        # represent stores in DOT
        if not quiet:
            print("Processing stores...")
        result.extend(_represent_stores(network.stores, bus_filter_regexp, carrier_color))
        result.append("")


        # represent links in DOT
        if not quiet:
            print("Processing links...")
        result.extend(_represent_links(network.buses, network.links, bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_link, carrier_color, quiet))


    # close digraph body
    result.append("}")


    # generate output files based on (PyPSA) network DOT representation
    status = _generate_output(result, file_name, file_format, quiet)


    # display info message
    if not quiet:
        print("... finished generating topographical representation of the network!")


    return status



if __name__ == "__main__":

    # parse arguments passed to PyPSATopo
    parser = argparse.ArgumentParser()
    parser.add_argument("-ff", "--file-format", choices = ["svg", "png", "jpg", "gif", "ps"], help = "Lorem Ipsum")
    parser.add_argument("-nn", "--no-negative-efficiency", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-nb", "--no-broken-link", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-fo", "--focus", action = "store", help = "Lorem Ipsum")
    parser.add_argument("-ne", "--neighbourhood", type = int, action = "store", help = "Lorem Ipsum")
    parser.add_argument("-cc", "--carrier-color", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-nq", "--no-quiet", action = "store_true", help = "Lorem Ipsum")
    args, files = parser.parse_known_args()


    # process file format argument
    file_format = args.file_format if args.file_format else FILE_FORMAT


    # process carrier_color argument
    carrier_color = args.carrier_color


    # process neighbourhood argument
    neighbourhood = args.neighbourhood if args.neighbourhood else 0


    if files:

        # loop through files passed as arguments
        for file in files:

            # read (PyPSA) network stored in file
            if args.no_quiet:
                print("Reading file '%s' containing PyPSA-based network..." % file)
            network = pypsa.Network(file)


            # generate output file name based on input file name and file format
            file_name = "%s.%s" % (file.rsplit(".", 1)[0], file_format)


            # generate topographical representation of network
            status = generate(network, focus = args.focus, neighbourhood = neighbourhood, negative_efficiency = not args.no_negative_efficiency, broken_link = not args.no_broken_link, carrier_color = args.carrier_color, file_name = file_name, file_format = file_format, quiet = not args.no_quiet)


            # check status of generation
            if status:
                sys.exit(status)   # return unsuccessfully

    else:

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
        status = generate(network, focus = args.focus, neighbourhood = neighbourhood, negative_efficiency = not args.no_negative_efficiency, broken_link = not args.no_broken_link, carrier_color = args.carrier_color, file_format = file_format, quiet = not args.no_quiet)


    # set exit code and finish
    sys.exit(status)

