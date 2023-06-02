#!/usr/bin/env python3



__author__ = "Energy Systems Group at Aarhus University (Denmark)"
__project__ = "PyPSATopo"
__description__ = "PyPSATopo is a tool which allows generating the topographical representation of any arbitrary PyPSA-based network (thanks to the DOT language - https://graphviz.org)"
__license__ = "BSD 3-Clause"
__contact__ = "ricardo.fernandes@mpe.au.dk"
__version__ = "0.6.0"
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



# declare (public) global variables (these may be overwritten by the caller to adjust/personalize the topographical representation of the PyPSA-based network)
DOT_REPRESENTATION = {"BUS": "   \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bus: %s\nCarrier: %s\nUnit: %s\nGenerators: %d\nLoads: %d\nStores: %d\nIncoming links: %d\nOutgoing links: %d\nLines: %d\n\nPower time series: %s MW\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f)\", color = \"%s\"]",
                      "MISSING_BUS": "   \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bus: %s (missing)\nGenerators: %d\nLoads: %d\nStores: %d\nIncoming links: %d\nOutgoing links: %d\nLines: %d\n\nPower time series: N/A MW\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f), dashed\", color = \"%s\"]",
                      "GENERATOR": "   \"%s (generator)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Generator: %s\nBus: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nPower set: %s MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series: %s MW\", shape = \"circle\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (generator)\" -> \"%s (bus)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "LOAD": "   \"%s (load)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Load: %s\nBus: %s\nCarrier: %s\nPower set: %s MW\", shape = \"invtriangle\", width = %.2f, height = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (load)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "STORE": "   \"%s (store)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Store: %s\nBus: %s\nCarrier: %s\nExtendable nominal energy: %s\nNominal energy: %.2f MWh\nPower set: %s MW\nCyclic energy: %s\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal energy: %.2f MWh\nEnergy time series: %s MWh\nPower time series: %s MW\", shape = \"box\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (store)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (%s): N/A MW\nPower time series (%s): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: 1.00\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\nPower time series (p1): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "BROKEN_BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: 1.00\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (p0): N/A MW\nPower time series (p1): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "MULTI_LINK_POINT": "   \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\nTo: %s\nCarrier: %s\nExtendable nominal energy: %s\nNominal power: %.2f MW\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\", shape = \"point\", width = %.2f, color = \"%s\"]",
                      "MULTI_LINK_BUS_TO_POINT": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "BROKEN_MULTI_LINK_BUS_TO_POINT": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\n\nOptimised nominal power: 0.00 MW\nPower time series (p0): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"none\"]",
                      "MULTI_LINK_POINT_TO_BUS": "   \"%s\" -> \"%s\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\n\nOptimised nominal power: %.2f MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_MULTI_LINK_POINT_TO_BUS": "   \"%s\" -> \"%s\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\n\nOptimised nominal power: 0.00 MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "LINE": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Line: %s\nBus0: %s\nBus1: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MVA\nCapital cost: %.2f currency/MVA\n\nOptimised nominal power: %.2f MVA\nPower time series (p0): %s MW\nPower time series (p1): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "BROKEN_LINE": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Line: %s\nBus0: %s\nBus1: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MVA\nCapital cost: %.2f currency/MVA\n\nOptimised nominal power: 0.00 MVA\nPower time series (p0): N/A MW\nPower time series (p1): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]"
                     }
FILE_FORMAT = "svg"   # acceptable values are: "svg", "png", "jpg", "gif" and "ps"
FILE_NAME = "topography.%s" % FILE_FORMAT
BACKGROUND_COLOR = "transparent"
NETWORK_NAME = "My Network"
RANK_DIRECTION = "TB"   # acceptable values are: "TB" (top to bottom), "BT" (bottom to top), "LR" (left to right) and "RL" (right to left)
RANK_SEPARATION = 1.0
NODE_SEPARATION = 1.0
EDGE_STYLE = "polyline"   # acceptable values are: "polyline", "curved", "ortho" and "none"
TEXT_FONT = "Courier New"
TEXT_SIZE = 8.0
TEXT_COLOR = "red"
BUS_MINIMUM_WIDTH = 3.3
BUS_THICKNESS = 7.3
BUS_COLOR = "black"
GENERATOR_MINIMUM_WIDTH = 1.1
GENERATOR_THICKNESS = 2.0
GENERATOR_COLOR = "black"
LOAD_MINIMUM_WIDTH = 1.5
LOAD_MINIMUM_HEIGHT = 1.2
LOAD_THICKNESS = 2.0
LOAD_COLOR = "black"
STORE_MINIMUM_WIDTH = 1.4
STORE_THICKNESS = 2.0
STORE_COLOR = "black"
LINK_THICKNESS = 1.5
LINK_COLOR = "black"
LINK_ARROW_SHAPE = "vee"   # acceptable values are: "vee", "normal", "onormal", "diamond", "odiamond", "curve" and "none"
LINK_ARROW_SIZE = 1.2
MULTI_LINK_POINT_WIDTH = 0.05
LINE_THICKNESS = 1.5
LINE_COLOR = "black"
LINE_ARROW_SHAPE = "diamond"   # acceptable values are: "vee", "normal", "onormal", "diamond", "odiamond", "curve" and "none"
LINE_ARROW_SIZE = 1.2
BROKEN_MISSING_COLOR = "grey60"
FADED_TEXT_COLOR = "#ffb0b0"
FADED_COMPONENT_COLOR = "grey90"



# declare (private) global variables (these should not be overwritten by the caller)
_MISSING_BUS_COUNT = 0



def _get_colors(n):
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



    hue_partition = 1.0 / (n + 1)

    result = []
    for i in range(n):
        result.append("#%02x%02x%02x" % HSVToRGB(hue_partition * i, 1.0, 1.0))

    return result



def _format_series(values):
    """
    Parameters
    ----------
    values : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    length = len(values)
    if length == 0:
        result = "[]"
    elif length == 1:
        result = "[%.2f]" % values[0]
    elif length == 2:
        result = "[%.2f, %.2f]" % (values[0], values[1])
    elif length == 3:
        result = "[%.2f, %.2f, %.2f]" % (values[0], values[1], values[2])
    elif length == 4:
        result = "[%.2f, %.2f, %.2f, %.2f]" % (values[0], values[1], values[2], values[3])
    elif length == 5:
        result = "[%.2f, %.2f, %.2f, %.2f, %.2f]" % (values[0], values[1], values[2], values[3], values[4])
    else:   # length > 5
        result = "[%.2f, %.2f, %.2f, %.2f, %.2f, ...]" % (values[0], values[1], values[2], values[3], values[4])


    return result



def _get_components(network, quiet):
    """
    Parameters
    ----------
    network : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    global _MISSING_BUS_COUNT


    result = dict()


    # get buses from (PyPSA) network
    if not quiet:
        print("[INF] Retrieving buses from network...")
    buses = network.buses
    buses_t = getattr(network, "buses_t", None)
    for i in range(len(buses)):
        bus = buses.index.values[i]
        carrier = buses.carrier[i]
        unit = "" if buses.unit[i] == "None" else buses.unit[i]
        p_time_series = _format_series(buses_t.p[bus]) if buses_t and bus in buses_t.p else "N/A"
        result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": False, "selected": False, "carrier": carrier, "unit": unit, "p_time_series": p_time_series}


    # get generators from (PyPSA) network
    if not quiet:
        print("[INF] Retrieving generators from network...")
    generators = network.generators
    generators_t = getattr(network, "generators_t", None)
    for i in range(len(generators)):
        generator = generators.index.values[i]
        bus = generators.bus.values[i]
        carrier = generators.carrier[i]
        p_nom_extendable = "True" if generators.p_nom_extendable[i] else "False"
        p_nom = generators.p_nom[i]
        p_set = _format_series(generators_t.p_set[generator]) if generators_t and generator in generators_t.p_set else "%.2f" % generators.p_set[i]
        efficiency = generators.efficiency[i]
        capital_cost = generators.capital_cost[i]
        marginal_cost = _format_series(generators_t.marginal_cost[generator]) if generators_t and generator in generators_t.marginal_cost else "%.2f" % generators.marginal_cost[i]
        p_nom_opt = generators.p_nom_opt[generator]
        p_time_series = _format_series(generators_t.p[generator]) if generators_t and generator in generators_t.p else "N/A"
        if bus:
            if bus not in result:
                if not quiet:
                    print("[WAR] Generator '%s' connects to bus '%s' which does not exist..." % (generator, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if not quiet:
                print("[WAR] Generator '%s' does not have a bus specified..." % generator)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["generators"].append([generator, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, False])


    # get loads from (PyPSA) network
    if not quiet:
        print("[INF] Retrieving loads from network...")
    loads = network.loads
    loads_t = getattr(network, "loads_t", None)
    for i in range(len(loads)):
        load = loads.index.values[i]
        bus = loads.bus.values[i]
        carrier = loads.carrier[i]
        p_set = _format_series(loads_t.p_set[load]) if loads_t and load in loads_t.p_set else "%.2f" % loads.p_set[i]
        if bus:
            if bus in result:
                if result[bus]["missing"] and not quiet:
                    print("[WAR] Load '%s' connects to bus '%s' which does not exist..." % (load, bus))
            else:
                if not quiet:
                    print("[WAR] Load '%s' connects to bus '%s' which does not exist..." % (load, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if not quiet:
                print("[WAR] Load '%s' does not have a bus specified..." % load)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["loads"].append([load, carrier, p_set, False])


    # get stores from (PyPSA) network
    if not quiet:
        print("[INF] Retrieving stores from network...")
    stores = network.stores
    stores_t = getattr(network, "stores_t", None)
    for i in range(len(stores)):
        store = stores.index.values[i]
        bus = stores.bus.values[i]
        carrier = stores.carrier[i]
        e_nom_extendable = "True" if stores.e_nom_extendable[i] else "False"
        e_nom = stores.e_nom[i]
        p_set = _format_series(stores_t.p_set[store]) if stores_t and store in stores_t.p_set else "%.2f" % stores.p_set[i]
        e_cyclic = "True" if stores.e_cyclic[i] else "False"
        capital_cost = stores.capital_cost[i]
        marginal_cost = _format_series(stores_t.marginal_cost[store]) if stores_t and store in stores_t.marginal_cost else "%.2f" % stores.marginal_cost[i]
        e_nom_opt = stores.e_nom_opt[store]
        e_time_series = _format_series(stores_t.e[store]) if stores_t and store in stores_t.p else "N/A"
        p_time_series = _format_series(stores_t.p[store]) if stores_t and store in stores_t.p else "N/A"
        if bus:
            if bus in result:
                if result[bus]["missing"] and not quiet:
                    print("[WAR] Store '%s' connects to bus '%s' which does not exist..." % (store, bus))
            else:
                if not quiet:
                    print("[WAR] Store '%s' connects to bus '%s' which does not exist..." % (store, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if not quiet:
                print("[WAR] Store '%s' does not have a bus specified..." % store)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["stores"].append([store, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, False])


    # get declared buses that links connect to
    if not quiet:
        print("[INF] Retrieving links from network...")
    links = network.links
    links_t = getattr(network, "links_t", None)
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


        # process link
        if len(specified_buses) < 3:   # mono-link

            # process mono-link
            link = links.index.values[i]
            bus0 = links.bus0[i]
            bus1 = links.bus1[i]
            carrier = links.carrier[i]
            p_nom_extendable = "True" if links.p_nom_extendable[i] else "False"
            p_nom = links.p_nom[i]
            efficiency = links.efficiency[i]
            capital_cost = links.capital_cost[i]
            marginal_cost = _format_series(links_t.marginal_cost[link]) if links_t and link in links_t.marginal_cost else "%.2f" % links.marginal_cost[i]
            p_nom_opt = links.p_nom_opt[link]
            p0_time_series = _format_series(links_t.p0[link]) if links_t and link in links_t.p0 else "N/A"
            p1_time_series = _format_series(links_t.p1[link]) if links_t and link in links_t.p1 else "N/A"
            bidirectional = (efficiency == 1 and links.marginal_cost[i] == 0 and links.p_min_pu[i] == -1)
            if bus0:
                if bus0 in result:
                    if result[bus0]["missing"] and not quiet:
                        print("[WAR] Link '%s' connects to bus '%s' (bus0) which does not exist..." % (link, bus0))
                    missing0 = result[bus0]["missing"]
                else:
                    if not quiet:
                        print("[WAR] Link '%s' connects to bus '%s' (bus0) which does not exist..." % (link, bus0))
                    result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    missing0 = True
            else:
                if not quiet:
                    print("[WAR] Link '%s' does not have bus0 specified..." % link)
                bus0 = "bus #%d" % _MISSING_BUS_COUNT
                _MISSING_BUS_COUNT += 1
                result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing0 = True
            if bus1:
                if bus1 in result:
                    if result[bus1]["missing"] and not quiet:
                        print("[WAR] Link '%s' connects to bus '%s' (bus1) which does not exist..." % (link, bus1))
                    missing1 = result[bus1]["missing"]
                else:
                    if not quiet:
                        print("[WAR] Link '%s' connects to bus '%s' (bus1) which does not exist..." % (link, bus1))
                    result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    missing1 = True
            else:
                if not quiet:
                    print("[WAR] Link '%s' does not have bus1 specified..." % link)
                bus1 = "bus #%d" % _MISSING_BUS_COUNT
                _MISSING_BUS_COUNT += 1
                result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing1 = True
            result[bus0]["links"].append([link, bus1, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, True, missing0 or missing1, False])

        else:   # multi-link

            # check that buses that the link connects to exist
            missing = 0
            for key, value in specified_buses.items():
                bus_value, bus_efficiency = value
                if bus_value:
                    if bus_value in result:
                        if result[bus_value]["missing"]:
                            if not quiet:
                                print("[WAR] Link '%s' connects to bus '%s' (%s) which does not exist..." % (links.index.values[i], bus_value, key))
                            if key != "bus0":
                                missing += 1
                    else:
                        if not quiet:
                            print("[WAR] Link '%s' connects to bus '%s' (%s) which does not exist..." % (links.index.values[i], bus_value, key))
                        result[bus_value] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                        if key != "bus0":
                            missing += 1
                else:
                    if not quiet:
                        print("[WAR] Link '%s' does not have %s specified..." % (links.index.values[i], key))
                    bus_value = "bus #%d" % _MISSING_BUS_COUNT
                    _MISSING_BUS_COUNT += 1
                    result[bus_value] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    value[0] = bus_value
                    if key != "bus0":
                        missing += 1


            # process multi-link
            link = links.index.values[i]
            carrier = links.carrier[i]
            p_nom_extendable = "True" if links.p_nom_extendable[i] else "False"
            p_nom = links.p_nom[i]
            p_nom_opt = links.p_nom_opt[link]
            p0_time_series = _format_series(links_t.p0[link]) if links_t and link in links_t.p0 else "N/A"
            bus0_value, bus0_efficiency = specified_buses["bus0"]
            result[bus0_value]["multi_link_points"].append([link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, len(specified_buses) - 1, missing, False])
            result[bus0_value]["multi_link_bus_to_points"].append([link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, len(specified_buses) - 1, missing, False])
            for key, value in specified_buses.items():
                bus_value, bus_efficiency = value
                if key != "bus0":
                    px = "p%s" % key[3:]
                    px_time_series = _format_series(links_t[px][link]) if links_t and px in links_t and link in links_t[px] else "N/A"
                    result[bus0_value]["multi_link_point_to_buses"].append([link, bus_value, key, carrier, p_nom_extendable, p_nom, bus_efficiency, p_nom_opt, p0_time_series, px, px_time_series, False])


    # get lines from (PyPSA) network
    if not quiet:
        print("[INF] Retrieving lines from network...")
    lines = network.lines
    lines_t = getattr(network, "lines_t", None)
    for i in range(len(lines)):
        line = lines.index.values[i]
        bus0 = lines.bus0.values[i]
        bus1 = lines.bus1.values[i]
        carrier = lines.carrier[i]
        s_nom_extendable = "True" if lines.s_nom_extendable[i] else "False"
        s_nom = lines.s_nom[i]
        capital_cost = lines.capital_cost[i]
        s_nom_opt = lines.s_nom_opt[line]
        p0_time_series = _format_series(lines_t.p0[line]) if lines_t and line in lines_t.p0 else "N/A"
        p1_time_series = _format_series(lines_t.p1[line]) if lines_t and line in lines_t.p1 else "N/A"
        if bus0:
            if bus0 in result:
                if result[bus0]["missing"] and not quiet:
                    print("[WAR] Line '%s' connects to bus '%s' (bus0) which does not exist..." % (line, bus0))
                missing0 = result[bus0]["missing"]
            else:
                if not quiet:
                    print("[WAR] Line '%s' connects to bus '%s' (bus0) which does not exist..." % (line, bus0))
                result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing0 = True
        else:
            if not quiet:
                print("[WAR] Line '%s' does not have bus0 specified..." % line)
            bus0 = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
            missing0 = True
        if bus1:
            if bus1 in result:
                if result[bus1]["missing"] and not quiet:
                    print("[WAR] Line '%s' connects to bus '%s' (bus1) which does not exist..." % (line, bus1))
                missing1 = result[bus1]["missing"]
            else:
                if not quiet:
                    print("[WAR] Line '%s' connects to bus '%s' (bus1) which does not exist..." % (line, bus1))
                result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing1 = True
        else:
            if not quiet:
                print("[WAR] Line '%s' does not have bus1 specified..." % line)
            bus1 = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_points": list(), "multi_link_bus_to_points": list(), "multi_link_point_to_buses": list(), "lines": list(), "incoming_links": 0, "outgoing_links": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
            missing1 = True
        result[bus0]["lines"].append([line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, missing0 or missing1, False])


    return result



def _represent_components(buses, bus_filter, generator_filter, load_filter, store_filter, link_filter, line_filter, negative_efficiency, broken_missing, carrier_color, context, quiet):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    bus_filter : TYPE
        DESCRIPTION.
    generator_filter : TYPE
        DESCRIPTION.
    load_filter : TYPE
        DESCRIPTION.
    store_filter : TYPE
        DESCRIPTION.
    link_filter : TYPE
        DESCRIPTION.
    line_filter : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_missing : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    context : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """



    def replace(text):
        """
        Parameters
        ----------
        text : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.
        """

        result = []

        for c in text:
            if c == ">":
                result.append("&gt;")
            elif c == "<":
                result.append("&lt;")
            elif c == "&":
                result.append("&amp;")
            else:
                result.append(c)

        return "".join(result)



    result = list()
    result_buses = list()
    result_generators = list()
    result_loads = list()
    result_stores = list()
    result_links = list()
    result_multi_link_points = list()
    result_multi_link_bus_to_points = list()
    result_multi_link_point_to_buses = list()
    result_lines = list()
    metrics = dict()
    carriers = dict()


    # get component DOT representations
    bus_representation = DOT_REPRESENTATION["BUS"]
    missing_bus_representation = DOT_REPRESENTATION["MISSING_BUS"]
    generator_representation = DOT_REPRESENTATION["GENERATOR"]
    load_representation = DOT_REPRESENTATION["LOAD"]
    store_representation = DOT_REPRESENTATION["STORE"]
    link_representation = DOT_REPRESENTATION["LINK"]
    broken_link_representation = DOT_REPRESENTATION["BROKEN_LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    broken_bidirectional_link_representation = DOT_REPRESENTATION["BROKEN_BIDIRECTIONAL_LINK"]
    multi_link_point_representation = DOT_REPRESENTATION["MULTI_LINK_POINT"]
    multi_link_bus_to_point_representation = DOT_REPRESENTATION["MULTI_LINK_BUS_TO_POINT"]
    broken_multi_link_bus_to_point_representation = DOT_REPRESENTATION["BROKEN_MULTI_LINK_BUS_TO_POINT"]
    multi_link_point_to_bus_representation = DOT_REPRESENTATION["MULTI_LINK_POINT_TO_BUS"]
    broken_multi_link_point_to_bus_representation = DOT_REPRESENTATION["BROKEN_MULTI_LINK_POINT_TO_BUS"]
    line_representation = DOT_REPRESENTATION["LINE"]
    broken_line_representation = DOT_REPRESENTATION["BROKEN_LINE"]


    # loop through existing buses
    for bus, values0 in buses.items():

        # set metrics for bus
        if bus not in metrics:
            metrics[bus] = {"generators": 0, "loads": 0, "stores": 0, "incoming_links": 0, "outgoing_links": 0, "lines": 0}


        # process bus
        if (not values0["missing"] or broken_missing) and (not bus_filter or bus_filter.match(bus)):
            if carrier_color:
                carrier = values0["carrier"]
                if carrier and carrier not in carriers:
                    carriers[carrier] = None
            values0["selected"] = True


        # process generators (attached to the bus)
        generators = values0["generators"]
        for values1 in generators:
            generator, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, selected = values1
            if values0["selected"] and (not generator_filter or generator_filter.match(generator)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                metrics[bus]["generators"] += 1
            elif context:
                metrics[bus]["generators"] += 1


        # process loads (attached to the bus)
        loads = values0["loads"]
        for values1 in loads:
            load, carrier, p_set, pselected = values1
            if values0["selected"] and (not load_filter or load_filter.match(load)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                metrics[bus]["loads"] += 1
            elif context:
                metrics[bus]["loads"] += 1


        # process stores (attached to the bus)
        stores = values0["stores"]
        for values1 in stores:
            store, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, selected = values1
            if values0["selected"] and (not store_filter or store_filter.match(store)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                metrics[bus]["stores"] += 1
            elif context:
                metrics[bus]["stores"] += 1


        # process links (attached to the bus)
        links = values0["links"]
        for values1 in links:
            link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected = values1
            if not missing or broken_missing:
                if bus_to not in metrics:
                    metrics[bus_to] = {"generators": 0, "loads": 0, "stores": 0, "incoming_links": 0, "outgoing_links": 0, "lines": 0}
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)):
                    values1[-1] = True
                if values1[-1] or context:
                    if bidirectional:
                        metrics[bus]["incoming_links"] += 1
                        metrics[bus]["outgoing_links"] += 1
                        metrics[bus_to]["incoming_links"] += 1
                        metrics[bus_to]["outgoing_links"] += 1
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            metrics[bus]["outgoing_links"] += 1
                            metrics[bus_to]["incoming_links"] += 1
                        else:
                            metrics[bus]["incoming_links"] += 1
                            metrics[bus_to]["outgoing_links"] += 1
                    else:
                        if direction:
                            metrics[bus]["incoming_links"] += 1
                            metrics[bus_to]["outgoing_links"] += 1
                        else:
                            metrics[bus]["outgoing_links"] += 1
                            metrics[bus_to]["incoming_links"] += 1


        # process multi-link points (attached to the bus)
        multi_link_points = values0["multi_link_points"]
        for values1 in multi_link_points:
            link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, count, missing, selected = values1
            not_missing = count - missing
            if not_missing or broken_missing:   # TODO: test logic
                if values0["selected"] and (not link_filter or link_filter.match(link)):
                    values1[-1] = True


        # process multi-link from bus to points (attached to the bus)
        multi_link_bus_to_points = values0["multi_link_bus_to_points"]
        for values1 in multi_link_bus_to_points:
            link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, count, missing, selected = values1
            not_missing = count - missing
            if not_missing or broken_missing:   # TODO: test logic
                if values0["selected"] and (not link_filter or link_filter.match(link)):
                    values1[-1] = True


        # process multi-link from point to buses (attached to the bus)
        multi_link_point_to_buses = values0["multi_link_point_to_buses"]
        for values1 in multi_link_point_to_buses:
            link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt, p0_time_series, px, px_time_series, selected = values1
            if bus_to not in metrics:
                metrics[bus_to] = {"generators": 0, "loads": 0, "stores": 0, "incoming_links": 0, "outgoing_links": 0, "lines": 0}
            if values0["missing"] or buses[bus_to]["missing"] or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)):
                    values1[-1] = True
            if values1[-1] or context:   # TODO: test logic
                if broken_missing:
                    if negative_efficiency or efficiency >= 0:
                        metrics[bus]["outgoing_links"] += 1
                        metrics[bus_to]["incoming_links"] += 1
                    else:
                        metrics[bus]["incoming_links"] += 1
                        metrics[bus_to]["outgoing_links"] += 1
                else:
                    if negative_efficiency or efficiency >= 0:
                        metrics[bus]["outgoing_links"] += 1
                        metrics[bus_to]["incoming_links"] += 1
                    else:
                        metrics[bus]["incoming_links"] += 1
                        metrics[bus_to]["outgoing_links"] += 1


        # process lines (attached to the bus)
        lines = values0["lines"]
        for values1 in lines:
            line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, missing, selected = values1
            if not missing or broken_missing:
                if bus1 not in metrics:
                    metrics[bus1] = {"generators": 0, "loads": 0, "stores": 0, "incoming_links": 0, "outgoing_links": 0, "lines": 0}
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not line_filter or line_filter.match(line)):
                    if carrier_color:
                        if carrier and carrier not in carriers:
                            carriers[carrier] = None
                    values1[-1] = True
                if values1[-1] or context:
                    metrics[bus]["lines"] += 1
                    metrics[bus1]["lines"] += 1


    # add carrier color table (if requested)
    if carrier_color:
        if isinstance(carrier_color, bool) and carrier_color:
            colors = _get_colors(len(carriers))
            i = 0
            for key in carriers.keys():
                carriers[key] = colors[i]
                i += 1
        else:   # dictionary
            carriers = carrier_color
        result.append("   // add carrier color table")
        result.append("   \"Carrier Color Table\" [shape = \"none\" label = <")
        result.append("      <table border = \"0\" cellborder = \"1\" cellspacing = \"0\" cellpadding = \"5\">")
        result.append("         <tr>")
        result.append("            <td width = \"110\" bgcolor = \"grey90\"><font color = \"black\"><b>CARRIER</b></font></td><td width = \"130\" bgcolor = \"grey92\"><font color = \"black\"><b>COLOR</b></font></td>")
        result.append("         </tr>")
        for key, value in carriers.items():
            result.append("         <tr>")
            result.append("            <td width = \"110\">%s</td><td width = \"130\" bgcolor = \"%s\"></td>" % (key, value))
            result.append("         </tr>")
        result.append("      </table>")
        result.append("   >];")
        result.append("")


    # loop through existing buses
    for bus, values in buses.items():

        # represent bus in DOT
        if values["missing"]:
            if values["selected"]:
                result_buses.append(missing_bus_representation % (bus, TEXT_COLOR, replace(bus), bus, metrics[bus]["generators"], metrics[bus]["loads"], metrics[bus]["stores"], metrics[bus]["incoming_links"], metrics[bus]["outgoing_links"], metrics[bus]["lines"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, BROKEN_MISSING_COLOR))
            elif context and broken_missing:
                result_buses.append(missing_bus_representation % (bus, FADED_TEXT_COLOR, replace(bus), bus, metrics[bus]["generators"], metrics[bus]["loads"], metrics[bus]["stores"], metrics[bus]["incoming_links"], metrics[bus]["outgoing_links"], metrics[bus]["lines"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, FADED_COMPONENT_COLOR))
        else:
            if values["selected"]:
                bus_color = carriers[values["carrier"]] if values["carrier"] in carriers else BUS_COLOR
                result_buses.append(bus_representation % (bus, TEXT_COLOR, replace(bus), bus, values["carrier"], values["unit"], metrics[bus]["generators"], metrics[bus]["loads"], metrics[bus]["stores"], metrics[bus]["incoming_links"], metrics[bus]["outgoing_links"], metrics[bus]["lines"], values["p_time_series"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, bus_color))
            elif context:
                result_buses.append(bus_representation % (bus, FADED_TEXT_COLOR, replace(bus), bus, values["carrier"], values["unit"], metrics[bus]["generators"], metrics[bus]["loads"], metrics[bus]["stores"], metrics[bus]["incoming_links"], metrics[bus]["outgoing_links"], metrics[bus]["lines"], values["p_time_series"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, FADED_COMPONENT_COLOR))


        # represent generators (attached to the bus) in DOT
        generators = values["generators"]
        for generator, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, selected in generators:
            if selected:
                generator_color = carriers[carrier] if carrier in carriers else GENERATOR_COLOR
                result_generators.append(generator_representation % (generator, TEXT_COLOR, replace(generator), generator, bus, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, generator_color, generator, bus, LINK_THICKNESS, generator_color))
            elif context and (not values["missing"] or broken_missing):
                result_generators.append(generator_representation % (generator, FADED_TEXT_COLOR, replace(generator), generator, bus, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, FADED_COMPONENT_COLOR, generator, bus, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # represent loads (attached to the bus) in DOT
        loads = values["loads"]
        for load, carrier, p_set, selected in loads:
            if selected:
                load_color = carriers[carrier] if carrier in carriers else LOAD_COLOR
                result_loads.append(load_representation % (load, TEXT_COLOR, replace(load), load, bus, carrier, p_set, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, load_color, bus, load, LINK_THICKNESS, load_color))
            elif context and (not values["missing"] or broken_missing):
                result_loads.append(load_representation % (load, FADED_TEXT_COLOR, replace(load), load, bus, carrier, p_set, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, FADED_COMPONENT_COLOR, bus, load, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # represent stores (attached to the bus) in DOT
        stores = values["stores"]
        for store, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, selected in stores:
            if selected:
                store_color = carriers[carrier] if carrier in carriers else STORE_COLOR
                result_stores.append(store_representation % (store, TEXT_COLOR, replace(store), store, bus, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, STORE_MINIMUM_WIDTH, STORE_THICKNESS, store_color, bus, store, LINK_THICKNESS, store_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            elif context and (not values["missing"] or broken_missing):
                result_stores.append(store_representation % (store, FADED_TEXT_COLOR, replace(store), store, bus, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, STORE_MINIMUM_WIDTH, STORE_THICKNESS, FADED_COMPONENT_COLOR, bus, store, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent links (attached to the bus) in DOT
        links = values["links"]
        for link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected in links:
            if missing:
                if broken_missing:
                    if selected:
                        if bidirectional:
                            if direction:
                                result_links.append(broken_bidirectional_link_representation % (bus, bus_to, TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_bidirectional_link_representation % (bus_to, bus, TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result_links.append(broken_link_representation % (bus, bus_to, TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", "p1", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus_to, bus, TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result_links.append(broken_link_representation % (bus_to, bus, TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, "p1", "p0", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus, bus_to, TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif context:
                        if bidirectional:
                            if direction:
                                result_links.append(broken_bidirectional_link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_bidirectional_link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result_links.append(broken_link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", "p1", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result_links.append(broken_link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, "p1", "p0", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            else:
                if selected:
                    if bidirectional:
                        if direction:
                            result_links.append(bidirectional_link_representation % (bus, bus_to, TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(bidirectional_link_representation % (bus_to, bus, TEXT_COLOR, replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result_links.append(link_representation % (bus, bus_to, TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus_to, bus, TEXT_COLOR, replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_links.append(link_representation % (bus_to, bus, TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, "p1", p1_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus, bus_to, TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, p1_time_series, p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                elif context:
                    if bidirectional:
                        if direction:
                            result_links.append(bidirectional_link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(bidirectional_link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result_links.append(link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_links.append(link_representation % (bus_to, bus, FADED_TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, "p1", p1_time_series, "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus, bus_to, FADED_TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent multi-link points (attached to the bus) in DOT
        multi_link_points = values["multi_link_points"]
        for link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, count, missing, selected in multi_link_points:
            bus_to = "1 bus (%d missing)" % missing if not_missing == 1 else "%d buses (%d missing)" % (not_missing, missing)
            not_missing = count - missing
            if not_missing == 0:
                if broken_missing:
                    if selected:
                        result_multi_link_points.append(multi_link_point_representation % (link, TEXT_COLOR, replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, BROKEN_MISSING_COLOR))
                    elif context:
                        result_multi_link_points.append(multi_link_point_representation % (link, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, FADED_COMPONENT_COLOR))
            else:
                if selected:
                    result_multi_link_points.append(multi_link_point_representation % (link, TEXT_COLOR, replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, LINK_COLOR))
                elif context:
                    result_multi_link_points.append(multi_link_point_representation % (link, FADED_TEXT_COLOR, replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, FADED_COMPONENT_COLOR))


        # represent multi-link from bus to points (attached to the bus) in DOT
        multi_link_bus_to_points = values["multi_link_bus_to_points"]
        for link, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, count, missing, selected in multi_link_bus_to_points:
            bus_to = "1 bus (%d missing)" % missing if not_missing == 1 else "%d buses (%d missing)" % (not_missing, missing)
            not_missing = count - missing
            if not_missing == 0:
                if broken_missing:
                    if selected:
                        result_multi_link_bus_to_points.append(broken_multi_link_bus_to_point_representation % (bus, link, TEXT_COLOR, replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, LINK_THICKNESS, BROKEN_MISSING_COLOR))
                    elif context:
                        result_multi_link_bus_to_points.append(broken_multi_link_bus_to_point_representation % (bus, link, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, LINK_THICKNESS, FADED_COMPONENT_COLOR))
            else:
                if selected:
                    result_multi_link_bus_to_points.append(multi_link_bus_to_point_representation % (bus, link, TEXT_COLOR, replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, LINK_THICKNESS, LINK_COLOR))
                elif context:
                    result_multi_link_bus_to_points.append(multi_link_bus_to_point_representation % (bus, link, FADED_TEXT_COLOR, replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, p_nom_opt, p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # process multi-link from point to buses (attached to the bus)
        multi_link_point_to_buses = values["multi_link_point_to_buses"]
        for link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt, p0_time_series, px, px_time_series, selected in multi_link_point_to_buses:
            if values["missing"] or buses[bus_to]["missing"]:
                if broken_missing:
                    if selected:
                        if negative_efficiency or efficiency >= 0:
                            result_multi_link_point_to_buses.append(broken_multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_point_to_buses.append(broken_multi_link_point_to_bus_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif context:
                        if negative_efficiency or efficiency >= 0:
                            result_multi_link_point_to_buses.append(broken_multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, FADED_TEXT_COLOR, replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_point_to_buses.append(broken_multi_link_point_to_bus_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, FADED_TEXT_COLOR, replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            else:
                if selected:
                    if negative_efficiency or efficiency >= 0:
                        result_multi_link_point_to_buses.append(multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        result_multi_link_point_to_buses.append(multi_link_point_to_bus_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                elif context:
                    if negative_efficiency or efficiency >= 0:
                        result_multi_link_point_to_buses.append(multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, FADED_TEXT_COLOR, replace(link), link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        result_multi_link_point_to_buses.append(multi_link_point_to_bus_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, FADED_TEXT_COLOR, replace(link), "%s (inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent lines (attached to the bus) in DOT
        lines = values["lines"]
        for line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, missing, selected in lines:
            if missing:
                if broken_missing:
                    if selected:
                        result_lines.append(broken_line_representation % (bus, bus1, TEXT_COLOR, replace(line), "%s (broken)" % line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, BROKEN_MISSING_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                    elif context:
                        result_lines.append(broken_line_representation % (bus, bus1, FADED_TEXT_COLOR, replace(line), "%s (broken)" % line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
            else:
                if selected:
                    line_color = carriers[carrier] if carrier in carriers else LINE_COLOR
                    result_lines.append(line_representation % (bus, bus1, TEXT_COLOR, replace(line), line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, p_nom_opt, p0_time_series, p1_time_series, LINE_THICKNESS, line_color, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                elif context:
                    result_lines.append(line_representation % (bus, bus1, FADED_TEXT_COLOR, replace(line), line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, p_nom_opt, p0_time_series, p1_time_series, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))


    # add buses to result
    result.append("   // add buses (%d)" % len(result_buses))
    result.extend(result_buses)
    result.append("")


    # add generators to result
    result.append("   // add generators (%d)" % len(result_generators))
    result.extend(result_generators)
    result.append("")


    # add loads to result
    result.append("   // add loads (%d)" % len(result_loads))
    result.extend(result_loads)
    result.append("")


    # add stores to result
    result.append("   // add stores (%d)" % len(result_stores))
    result.extend(result_stores)
    result.append("")


    # add links to result
    result.append("   // add links (%d)" % len(result_links))
    result.extend(result_links)
    result.append("")


    # add multi-link points to result
    result.append("   // add multi-link points (%d)" % len(result_multi_link_points))
    result.extend(result_multi_link_points)
    result.append("")


    # add multi-link bus to points to result
    result.append("   // add multi-link bus to points (%d)" % len(result_multi_link_bus_to_points))
    result.extend(result_multi_link_bus_to_points)
    result.append("")


    # add multi-link point to buses to result
    result.append("   // add multi-link point to buses (%d)" % len(result_multi_link_point_to_buses))
    result.extend(result_multi_link_point_to_buses)
    result.append("")


    # add lines to result
    result.append("   // add lines (%d)" % len(result_lines))
    result.extend(result_lines)


    return result



def _focus_bus(buses, focus, neighbourhood, bus_filter, generator_filter, load_filter, store_filter, link_filter, line_filter, negative_efficiency, broken_missing, carrier_color, quiet, visited_buses, visited_links, visited_multi_link_points):
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
    generator_filter : TYPE
        DESCRIPTION.
    load_filter : TYPE
        DESCRIPTION.
    store_filter : TYPE
        DESCRIPTION.
    link_filter : TYPE
        DESCRIPTION.
    line_filter : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_missing : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    quiet : TYPE
        DESCRIPTION.
    visited_buses : TYPE
        DESCRIPTION.
    visited_links : TYPE
        DESCRIPTION.
    visited_multi_link_points : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()


    # display info message
    if not quiet:
        print("[INF] Focusing on bus '%s'..." % focus)


    # check if bus has already been visited (processed)
    if focus in visited_buses:
        return result
    visited_buses.add(focus)


    # represent bus (currently on focus) in DOT
    bus_representation = DOT_REPRESENTATION["BUS"]
    missing_bus_representation = DOT_REPRESENTATION["MISSING_BUS"]
    if buses[focus]["missing"]:
        if broken_missing:
            result.append(missing_bus_representation % (focus, focus, focus, 0, 0, 0, 0, 0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, BROKEN_MISSING_COLOR))
    else:
        carrier = buses[focus]["carrier"]
        unit = buses[focus]["unit"]
        bus_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else BUS_COLOR
        result.append(bus_representation % (focus, focus, focus, carrier, unit, 0, 0, 0, 0, 0, BUS_MINIMUM_WIDTH, BUS_THICKNESS, bus_color))


    # stop processing as neighbourhood visiting reached the limit
    if neighbourhood == 0:
        return result


    # represent generators (attached to the bus currently on focus) in DOT
    generator_representation = DOT_REPRESENTATION["GENERATOR"]
    for bus, generator, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt in buses[focus]["GENERATORS"]:
        generator_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else GENERATOR_COLOR
        result.append(generator_representation % (generator, generator, generator, bus, carrier, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, generator_color, generator, focus, LINK_THICKNESS, generator_color))


    # represent loads (attached to the bus currently on focus) in DOT
    load_representation = DOT_REPRESENTATION["LOAD"]
    for load, bus, carrier, p_set in buses[focus]["LOADS"]:
        load_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else LOAD_COLOR
        result.append(load_representation % (load, load, load, bus, carrier, p_set, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, load_color, focus, load, LINK_THICKNESS, load_color))


    # represent stores (attached to the bus currently on focus) in DOT
    store_representation = DOT_REPRESENTATION["STORE"]
    for store, bus, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt in buses[focus]["STORES"]:
        store_color = carrier_color[carrier] if carrier_color and carrier in carrier_color else STORE_COLOR
        result.append(store_representation % (store, store, store, bus, carrier, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, STORE_MINIMUM_WIDTH, STORE_THICKNESS, store_color, focus, store, LINK_THICKNESS, store_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


    # represent links (attached to the bus currently on focus) in DOT
    link_representation = DOT_REPRESENTATION["LINK"]
    broken_link_representation = DOT_REPRESENTATION["BROKEN_LINK"]
    bidirectional_link_representation = DOT_REPRESENTATION["BIDIRECTIONAL_LINK"]
    broken_bidirectional_link_representation = DOT_REPRESENTATION["BROKEN_BIDIRECTIONAL_LINK"]
    for link, bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, bidirectional, direction, missing in buses[focus]["LINKS"]:
        if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
            if link not in visited_links:
                visited_links.add(link)
                if missing:
                    if broken_missing:
                        if bidirectional:
                            if direction:
                                result.append(broken_bidirectional_link_representation % (focus, bus, link, "%s (broken)" % link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_bidirectional_link_representation % (bus, focus, link, "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result.append(broken_link_representation % (focus, bus, link, "%s (broken)" % link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_link_representation % (bus, focus, link, "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result.append(broken_link_representation % (focus, bus, link, "%s (broken & inverted)" % link, "%s (bus1)" % focus, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result.append(broken_link_representation % (bus, focus, link, "%s (broken & inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % focus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                else:
                    if bidirectional:
                        if direction:
                            result.append(bidirectional_link_representation % (focus, bus, link, link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(bidirectional_link_representation % (bus, focus, link, link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result.append(link_representation % (focus, bus, link, link, "%s (bus0)" % focus, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(link_representation % (bus, focus, link, link, "%s (bus0)" % bus, "%s (bus1)" % focus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result.append(link_representation % (bus, focus, link, "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % focus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result.append(link_representation % (focus, bus, link, "%s (inverted)" % link, "%s (bus1)" % focus, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                result.extend(_focus_bus(buses, bus, neighbourhood - 1, bus_filter, link_filter, negative_efficiency, broken_missing, carrier_color, quiet, visited_buses, visited_links, visited_multi_link_points))   # focus on neighbouring (adjacent) bus in a recursive fashion


    # represent multi-link points (attached to the bus currently on focus) in DOT
    multi_link_point_representation = DOT_REPRESENTATION["MULTI_LINK_POINT"]
    print(buses[focus]["MULTI_LINK_POINTS"])
    for link, bus_from, bus_to in buses[focus]["MULTI_LINK_POINTS"]:
        if (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)):
            if link not in visited_multi_link_points:
                visited_multi_link_points.add(link)
                #"MULTI_LINK_POINT": "   \"%s (multi-link)\" [label = \"%s\", tooltip = \"Multi-link: %s\nFrom: %s (bus0)\nTo: %s\", shape = \"point\", width = %.2f, color = \"%s\"]",
                result.append(multi_link_point_representation % (link, link, link, bus_from, bus_to, MULTI_LINK_POINT_WIDTH, LINK_COLOR))


    # represent multi-link from bus to points (attached to the bus currently on focus) in DOT
    multi_link_bus_to_point_representation = DOT_REPRESENTATION["MULTI_LINK_BUS_TO_POINT"]
    for bus, point, carrier, p_nom_extendable, p_nom, p_nom_opt in buses[focus]["MULTI_LINK_BUS_TO_POINTS"]:
        #if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
        #    if link not in visited_links:
        #        visited_links.add(link)
        if True:
            if link not in visited_links:
                visited_links.add(link)
                #"MULTI_LINK_BUS_TO_POINT": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = \"%s\", tooltip = \"Multi-link: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nOptimised nominal power: %.2f MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                result.append(multi_link_bus_to_point_representation % (bus, point, point, point, carrier, p_nom_extendable, p_nom, p_nom_opt, LINK_THICKNESS, LINK_COLOR))


    # represent multi-link from point to buses (attached to the bus currently on focus) in DOT
    multi_link_point_to_bus_representation = DOT_REPRESENTATION["MULTI_LINK_POINT_TO_BUS"]
    for point, bus, xxx, carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt in buses[focus]["MULTI_LINK_POINT_TO_BUSES"]:
        #if (not bus_filter or bus_filter.match(bus)) and (not link_filter or link_filter.match(link)):
        #    if link not in visited_links:
        #        visited_links.add(link)
        if True:

            #"MULTI_LINK_POINT_TO_BUS": "   \"%s (multi-link)\" -> \"%s (bus)\" [label = \"%s\", tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nOptimised nominal power: %.2f MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",

            #buses[bus0_value]["MULTI_LINK_POINT_TO_BUSES"].append((bus0_value, bus_value, link, link, carrier, 0, 0, bus_efficiency, 0))


            #result.append(multi_link_point_to_bus_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_value, link, link, "%s (bus0)" % bus0_value, "%s (%s)" % (bus_value, key), carrier, p_nom_extendable, p_nom, bus_efficiency, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))

            result.append(multi_link_point_to_bus_representation % ("%s (multi-link)" % point, "%s (bus)" % bus, point, point, "%s (bus0)" % focus, "%s (%s)" % (bus, xxx), carrier, p_nom_extendable, p_nom, efficiency, p_nom_opt, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))

            if bus:
                result.extend(_focus_bus(buses, bus, neighbourhood - 1, bus_filter, link_filter, negative_efficiency, broken_missing, carrier_color, quiet, visited_buses, visited_links, visited_multi_link_points))   # focus on neighbouring (adjacent) bus in a recursive fashion


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
        print("[INF] Writing DOT file '%s'..." % file_name_dot)
    try:
        with open(file_name_dot, "w") as handle:
            for line in dot_representation:
                handle.write("%s%s" % (line, os.linesep))
            handle.write("%s" % os.linesep)
    except:
        print("[ERR] The file '%s' could not be written!" % file_name_dot)
        return -1   # return unsuccessfully


    # launch the tool 'dot' passing DOT file to it
    if not quiet:
        print("[INF] Generating topographical representation of the network based on DOT file '%s'..." % file_name_dot)
    try:
        result = subprocess.run(["dot", "-T%s" % file_format, file_name_dot], capture_output = True)
    except KeyboardInterrupt:
        if not quiet:
            print("[WAR] Terminated by user request!")
        return 0   # return successfully
    except FileNotFoundError:
        print("[ERR] The tool 'dot' is not installed or could not be found (please visit https://graphviz.org/download to download and install it)!")
        return -1   # return unsuccessfully
    except:
        print("[ERR] The tool 'dot' generated an error!")
        return -1   # return unsuccessfully
    if result.check_returncode():
        print("[ERR] The tool 'dot' generated an error!")
        return result.check_returncode()   # return unsuccessfully


    # write result generated by the tool 'dot' into an output file
    if not quiet:
        print("[INF] Writing output file '%s' in the %s format..." % (file_name, file_format.upper()))
    try:
        with open(file_name, "wb") as handle:
            handle.write(result.stdout)
    except:
        print("[ERR] The file '%s' could not be written!" % file_name)
        return -1   # return unsuccessfully


    return 0   # return successfully



def generate(network, focus = None, neighbourhood = 0, bus_filter = None, generator_filter = None, load_filter = None, store_filter = None, link_filter = None, line_filter = None, negative_efficiency = True, broken_missing = True, carrier_color = None, context = False, file_name = FILE_NAME, file_format = FILE_FORMAT, quiet = True):
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
    generator_filter : TYPE, optional
        DESCRIPTION. The default is None.
    load_filter : TYPE, optional
        DESCRIPTION. The default is None.
    store_filter : TYPE, optional
        DESCRIPTION. The default is None.
    link_filter : TYPE, optional
        DESCRIPTION. The default is None.
    line_filter : TYPE, optional
        DESCRIPTION. The default is None.
    negative_efficiency : TYPE, optional
        DESCRIPTION. The default is True.
    broken_missing : TYPE, optional
        DESCRIPTION. The default is True.
    carrier_color : TYPE, optional
        DESCRIPTION. The default is None.
    context : TYPE, optional
        DESCRIPTION. The default is False.
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


    # check if file format is valid
    if file_format not in ("svg", "png", "jpg", "gif", "ps"):
        print("The file format '%s' is not valid (acceptable formats are: 'svg', 'png', 'jpg', 'gif' or 'ps')!" % file_format)
        return -1   # return unsuccessfully


    # check basic conditions
    if focus:

        # check if bus to focus on exists in (PyPSA) network
        buses = network.buses.index
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
    generator_filter_regexp = re.compile(generator_filter) if generator_filter else None
    load_filter_regexp = re.compile(load_filter) if load_filter else None
    store_filter_regexp = re.compile(store_filter) if store_filter else None
    link_filter_regexp = re.compile(link_filter) if link_filter else None
    line_filter_regexp = re.compile(line_filter) if line_filter else None


    # get network name
    if network.name:
        network_name = network.name
        if not quiet:
            print("[INF] Start generating topographical representation of the network '%s'..." % network_name)
    else:
        network_name = NETWORK_NAME
        if not quiet:
            print("[INF] Start generating topographical representation of the network...")


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
    result.append("   label = \"%s\n\n\n           \"" % network_name)
    result.append("   tooltip = \"Bus: %d\nGenerators: %d\nLoads: %s\nStores: %d\nLinks: %d\nLines: %d\nSnapshots: %d\"" % (len(network.buses), len(network.generators), len(network.loads), len(network.stores), len(network.links), len(network.lines), len(network.snapshots)))
    result.append("   rankdir = \"%s\"" % RANK_DIRECTION)
    result.append("   ranksep = %.2f" % RANK_SEPARATION)
    result.append("   nodesep = %.2f" % NODE_SEPARATION)
    result.append("   splines = \"%s\"" % EDGE_STYLE)
    result.append("   node [fontname = \"%s\", fontsize = %.2f]" % (TEXT_FONT, TEXT_SIZE))
    result.append("   edge [fontname = \"%s\", fontsize = %.2f]" % (TEXT_FONT, TEXT_SIZE))
    result.append("")


    # get components from (PyPSA) network
    components = _get_components(network, quiet)


    # process (PyPSA) network
    if focus:
        if isinstance(focus, str):
            result.extend(_focus_bus(buses, focus, neighbourhood, bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_missing, colors, quiet, set(), set(), set()))
        else:   # list
            for i in range(len(focus)):
                bus = focus[i]
                if bus not in visited:   # skip bus as it has already been visited (processed)
                    if isinstance(neighbourhood, int):
                        result.extend(_focus_bus(buses, bus, neighbourhood, bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_missing, colors, quiet, set(), set(), set()))
                    else:   # list
                        result.extend(_focus_bus(buses, bus, neighbourhood[i], bus_filter_regexp, link_filter_regexp, negative_efficiency, broken_missing, colors, quiet, set(), set(), set()))
                    visited.add(bus)
    else:
        result.extend(_represent_components(components, bus_filter_regexp, generator_filter_regexp, load_filter_regexp, store_filter_regexp, link_filter_regexp, line_filter_regexp, negative_efficiency, broken_missing, carrier_color, context, quiet))


    # close digraph body
    result.append("}")


    # generate output files based on (PyPSA) network DOT representation
    status = _generate_output(result, file_name, file_format, quiet)


    # display info message
    if not quiet and not status:
        print("[INF] Finished generating topographical representation of the network!")


    return status



if __name__ == "__main__":

    # parse arguments passed to PyPSATopo
    parser = argparse.ArgumentParser()
    parser.add_argument("-ff", "--file-format", choices = ["svg", "png", "jpg", "gif", "ps"], help = "Lorem Ipsum")
    parser.add_argument("-nn", "--no-negative-efficiency", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-nb", "--no-broken-missing", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-fo", "--focus", action = "store", help = "Lorem Ipsum")
    parser.add_argument("-ne", "--neighbourhood", type = int, action = "store", help = "Lorem Ipsum")
    parser.add_argument("-cc", "--carrier-color", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-co", "--context", action = "store_true", help = "Lorem Ipsum")
    parser.add_argument("-nq", "--no-quiet", action = "store_true", help = "Lorem Ipsum")
    args, files = parser.parse_known_args()


    # process arguments
    file_format = args.file_format if args.file_format else FILE_FORMAT
    neighbourhood = args.neighbourhood if args.neighbourhood else 0
    carrier_color = args.carrier_color if args.carrier_color else None


    # display PyPSATopo information
    if args.no_quiet:
        print("[INF] %s version %s" % (__project__, __version__))


    if files:

        # loop through files passed as arguments
        for file in files:

            # read (PyPSA) network stored in file
            if args.no_quiet:
                print("[INF] Reading file '%s' containing PyPSA-based network..." % file)
            network = pypsa.Network(file)


            # generate output file name based on input file name and file format
            file_name = "%s.%s" % (file.rsplit(".", 1)[0], file_format)


            # generate topographical representation of network
            status = generate(network, focus = args.focus, neighbourhood = neighbourhood, negative_efficiency = not args.no_negative_efficiency, broken_missing = not args.no_broken_missing, carrier_color = carrier_color, context = args.context, file_name = file_name, file_format = file_format, quiet = not args.no_quiet)


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
        network.add("Link", "ICEV", bus0 = "oil", bus1 = "transport")
        network.add("Link", "BEV", bus0 = "electricity", bus1 = "transport")


        # generate topographical representation of dummy (PyPSA) network
        status = generate(network, focus = args.focus, neighbourhood = neighbourhood, negative_efficiency = not args.no_negative_efficiency, broken_missing = not args.no_broken_missing, carrier_color = carrier_color, context = args.context, file_format = file_format, quiet = not args.no_quiet)


    # set exit code and finish
    sys.exit(status)

