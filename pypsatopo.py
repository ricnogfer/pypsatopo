#!/usr/bin/env python3



__project__ = "PyPSATopo"
__version__ = "0.11.0"
__description__ = "PyPSATopo is a tool that allows generating the topographical representation of any arbitrary PyPSA-based network"
__license__ = "BSD 3-Clause"
__author__ = "Energy Systems Group at Aarhus University (Denmark)"
__contact__ = "ricardo.fernandes@mpe.au.dk"
__status__ = "Development"



# import necessary modules
from collections import deque
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
DOT_REPRESENTATION = {"BUS": "   \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bus: %s\nCarrier: %s\nUnit: %s\nGenerators: %d\nLoads: %d\nStores: %d\nIncoming links: %d\nOutgoing links: %d\nLines: %d\n\nPower time series: %s %s\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f)\", color = \"%s\"]",
                      "MISSING_BUS": "   \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bus: %s (missing)\nGenerators: %d\nLoads: %d\nStores: %d\nIncoming links: %d\nOutgoing links: %d\nLines: %d\n\nPower time series: N/A %s\", shape = \"underline\", width = %.2f, height = 0.30, style = \"setlinewidth(%.2f), dashed\", color = \"%s\"]",
                      "GENERATOR": "   \"%s (generator)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Generator: %s\nBus: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f %s\nPower set: %s %s\nEfficiency: %.2f\nCapital cost: %.2f currency/%s\nMarginal cost: %s currency/%sh\n\nOptimised nominal power: %.2f %s\nPower time series: %s %s\", shape = \"circle\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (generator)\" -> \"%s (bus)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "LOAD": "   \"%s (load)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Load: %s\nBus: %s\nCarrier: %s\nPower set: %s %s\", shape = \"invtriangle\", width = %.2f, height = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (load)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "STORE": "   \"%s (store)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Store: %s\nBus: %s\nCarrier: %s\nExtendable nominal energy: %s\nNominal energy: %.2f %sh\nPower set: %s %s\nCyclic energy: %s\nCapital cost: %.2f currency/%s\nMarginal cost: %s currency/%sh\n\nOptimised nominal energy: %.2f %sh\nEnergy time series: %s %sh\nPower time series: %s %s\", shape = \"box\", width = %.2f, style = \"setlinewidth(%.2f)\", color = \"%s\"]   \"%s (bus)\" -> \"%s (store)\" [style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (%s): N/A MW\nPower time series (%s): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: 1.00\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\nPower time series (p1): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "BROKEN_BIDIRECTIONAL_LINK": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Bidirectional link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: 1.00\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (p0): N/A MW\nPower time series (p1): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "MULTI_LINK_POINT": "   \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\n%s\nCarrier: %s\nExtendable nominal energy: %s\nNominal power: %.2f MW\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\", shape = \"point\", width = %.2f, color = \"%s\"]",
                      "MULTI_LINK_TRUNK": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\n%s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (p0): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"none\"]",
                      "BROKEN_MULTI_LINK_TRUNK": "   \"%s (bus)\" -> \"%s (multi-link)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s (bus0)\n%s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (p0): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"none\"]",
                      "MULTI_LINK_BRANCH": "   \"%s\" -> \"%s\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: %.2f MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "BROKEN_MULTI_LINK_BRANCH": "   \"%s\" -> \"%s\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Multi-link: %s\nFrom: %s\nTo: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MW\nEfficiency: %.2f\nCapital cost: %.2f currency/MW\nMarginal cost: %s currency/MWh\n\nOptimised nominal power: 0.00 MW\nPower time series (%s): %s MW\nPower time series (%s): %s MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowsize = %.2f]",
                      "LINE": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Line: %s\nBus0: %s\nBus1: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MVA\nCapital cost: %.2f currency/MVA\n\nOptimised nominal power: %.2f MVA\nPower time series (p0): %s MW\nPower time series (p1): %s MW\", style = \"setlinewidth(%.2f)\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]",
                      "BROKEN_LINE": "   \"%s (bus)\" -> \"%s (bus)\" [label = <<font color = \"%s\">%s</font>>, tooltip = \"Line: %s\nBus0: %s\nBus1: %s\nCarrier: %s\nExtendable nominal power: %s\nNominal power: %.2f MVA\nCapital cost: %.2f currency/MVA\n\nOptimised nominal power: 0.00 MVA\nPower time series (p0): N/A MW\nPower time series (p1): N/A MW\", style = \"setlinewidth(%.2f), dashed\", color = \"%s\", arrowhead = \"%s\", arrowtail = \"%s\", arrowsize = %.2f, dir = \"both\"]"
                     }
FILE_OUTPUT = "topography.svg"
FILE_FORMAT = "svg"   # acceptable values are: "svg", "png", "jpg", "gif" and "ps"
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
MULTI_LINK_POINT_WIDTH = 0.06
LINE_THICKNESS = 1.5
LINE_COLOR = "black"
LINE_ARROW_SHAPE = "diamond"   # acceptable values are: "vee", "normal", "onormal", "diamond", "odiamond", "curve" and "none"
LINE_ARROW_SIZE = 1.2
BROKEN_MISSING_COLOR = "grey60"
FADED_TEXT_COLOR = "#ffb0b0"
FADED_COMPONENT_COLOR = "grey90"



# declare (private) global variables (these should not be overwritten by the caller)
_MISSING_BUS_COUNT = 0



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
        result = "[%.2f]" % values.iloc[0]
    elif length == 2:
        result = "[%.2f, %.2f]" % (values.iloc[0], values.iloc[1])
    elif length == 3:
        result = "[%.2f, %.2f, %.2f]" % (values.iloc[0], values.iloc[1], values.iloc[2])
    elif length == 4:
        result = "[%.2f, %.2f, %.2f, %.2f]" % (values.iloc[0], values.iloc[1], values.iloc[2],
                                               values.iloc[3])
    elif length == 5:
        result = "[%.2f, %.2f, %.2f, %.2f, %.2f]" % (values.iloc[0], values.iloc[1], values.iloc[2],
                                                     values.iloc[3], values.iloc[4])
    else:   # length > 5
        result = "[%.2f, %.2f, %.2f, %.2f, %.2f, ...]" % (values.iloc[0], values.iloc[1],
                                                          values.iloc[2], values.iloc[3],
                                                          values.iloc[4])

    return result



def _replace(text):
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



def _get_components(network, focus, log, log_info, log_warning):
    """
    Parameters
    ----------
    network : TYPE
        DESCRIPTION.
    focus : TYPE
        DESCRIPTION.
    log : TYPE
        DESCRIPTION.
    log_info : TYPE
        DESCRIPTION.
    log_warning : TYPE
        DESCRIPTION.

    Returns
    result : TYPE
    -------
        DESCRIPTION.
    """

    global _MISSING_BUS_COUNT


    result = dict()


    # get buses from (PyPSA) network
    if log or log_info:
        print("[INF] Retrieving buses from network...")
    buses = network.buses
    buses_t = getattr(network, "buses_t", None)
    for i in range(len(buses)):
        bus = buses.index[i]
        carrier = buses.carrier.iloc[i]
        unit = "MW" if buses.unit.iloc[i] == "None" else buses.unit.iloc[i]
        p_time_series = _format_series(buses_t.p[bus]) if buses_t and bus in buses_t.p else "N/A"
        result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": False, "selected": False, "carrier": carrier, "unit": unit, "p_time_series": p_time_series}


    # get generators from (PyPSA) network
    if log or log_info:
        print("[INF] Retrieving generators from network...")
    generators = network.generators
    generators_t = getattr(network, "generators_t", None)
    for i in range(len(generators)):
        generator = generators.index[i]
        bus = generators.bus.iloc[i]
        carrier = generators.carrier.iloc[i]
        tmp = buses.loc[bus].unit
        unit = "MW" if tmp == "None" else tmp
        p_nom_extendable = "True" if generators.p_nom_extendable.iloc[i] else "False"
        p_nom = generators.p_nom.iloc[i]
        p_set = _format_series(generators_t.p_set[generator]) if generators_t and generator in generators_t.p_set else "%.2f" % generators.p_set.iloc[i]
        efficiency = generators.efficiency.iloc[i]
        capital_cost = generators.capital_cost.iloc[i]
        marginal_cost = _format_series(generators_t.marginal_cost[generator]) if generators_t and generator in generators_t.marginal_cost else "%.2f" % generators.marginal_cost.iloc[i]
        p_nom_opt = generators.p_nom_opt.iloc[i]
        p_time_series = _format_series(generators_t.p[generator]) if generators_t and generator in generators_t.p else "N/A"
        if bus:
            if bus in result:
                if result[bus]["missing"]:
                    if log or log_warning:
                        print("[WAR] Generator '%s' connects to bus '%s' which does not exist..." % (generator, bus))
            else:
                if log or log_warning:
                    print("[WAR] Generator '%s' connects to bus '%s' which does not exist..." % (generator, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if log or log_warning:
                print("[WAR] Generator '%s' does not have a bus specified..." % generator)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["generators"].append([generator, carrier, unit, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, False])


    # get loads from (PyPSA) network
    if log or log_info:
        print("[INF] Retrieving loads from network...")
    loads = network.loads
    loads_t = getattr(network, "loads_t", None)
    for i in range(len(loads)):
        load = loads.index[i]
        bus = loads.bus.iloc[i]
        carrier = loads.carrier.iloc[i]
        tmp = buses.loc[bus].unit
        unit = "MW" if tmp == "None" else tmp
        p_set = _format_series(loads_t.p_set[load]) if loads_t and load in loads_t.p_set else "%.2f" % loads.p_set.iloc[i]
        if bus:
            if bus in result:
                if result[bus]["missing"]:
                    if log or log_warning:
                        print("[WAR] Load '%s' connects to bus '%s' which does not exist..." % (load, bus))
            else:
                if log or log_warning:
                    print("[WAR] Load '%s' connects to bus '%s' which does not exist..." % (load, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if log or log_warning:
                print("[WAR] Load '%s' does not have a bus specified..." % load)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["loads"].append([load, carrier, unit, p_set, False])


    # get stores from (PyPSA) network
    if log or log_info:
        print("[INF] Retrieving stores from network...")
    stores = network.stores
    stores_t = getattr(network, "stores_t", None)
    for i in range(len(stores)):
        store = stores.index[i]
        bus = stores.bus.iloc[i]
        carrier = stores.carrier.iloc[i]
        tmp = buses.loc[bus].unit
        unit = "MW" if tmp == "None" else tmp
        e_nom_extendable = "True" if stores.e_nom_extendable.iloc[i] else "False"
        e_nom = stores.e_nom.iloc[i]
        p_set = _format_series(stores_t.p_set[store]) if stores_t and store in stores_t.p_set else "%.2f" % stores.p_set.iloc[i]
        e_cyclic = "True" if stores.e_cyclic.iloc[i] else "False"
        capital_cost = stores.capital_cost.iloc[i]
        marginal_cost = _format_series(stores_t.marginal_cost[store]) if stores_t and store in stores_t.marginal_cost else "%.2f" % stores.marginal_cost.iloc[i]
        e_nom_opt = stores.e_nom_opt.iloc[i]
        e_time_series = _format_series(stores_t.e[store]) if stores_t and store in stores_t.p else "N/A"
        p_time_series = _format_series(stores_t.p[store]) if stores_t and store in stores_t.p else "N/A"
        if bus:
            if bus in result:
                if result[bus]["missing"]:
                    if log or log_warning:
                        print("[WAR] Store '%s' connects to bus '%s' which does not exist..." % (store, bus))
            else:
                if log or log_warning:
                    print("[WAR] Store '%s' connects to bus '%s' which does not exist..." % (store, bus))
                result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        else:
            if log or log_warning:
                print("[WAR] Store '%s' does not have a bus specified..." % store)
            bus = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
        result[bus]["stores"].append([store, carrier, unit, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, False])


    # get declared buses that links connect to
    if log or log_info:
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
            link = links.index[i]
            bus0 = links.bus0.iloc[i]
            bus1 = links.bus1.iloc[i]
            carrier = links.carrier.iloc[i]
            p_nom_extendable = "True" if links.p_nom_extendable.iloc[i] else "False"
            p_nom = links.p_nom.iloc[i]
            efficiency = links.efficiency.iloc[i]
            capital_cost = links.capital_cost.iloc[i]
            marginal_cost = _format_series(links_t.marginal_cost[link]) if links_t and link in links_t.marginal_cost else "%.2f" % links.marginal_cost.iloc[i]
            p_nom_opt = links.p_nom_opt.iloc[i]
            p0_time_series = _format_series(links_t.p0[link]) if links_t and link in links_t.p0 else "N/A"
            p1_time_series = _format_series(links_t.p1[link]) if links_t and link in links_t.p1 else "N/A"
            bidirectional = (efficiency == 1 and links.marginal_cost.iloc[i] == 0 and links.p_min_pu.iloc[i] == -1)
            if bus0:
                if bus0 in result:
                    if result[bus0]["missing"]:
                        if log or log_warning:
                            print("[WAR] Link '%s' connects to bus '%s' (bus0) which does not exist..." % (link, bus0))
                    missing0 = result[bus0]["missing"]
                else:
                    if log or log_warning:
                        print("[WAR] Link '%s' connects to bus '%s' (bus0) which does not exist..." % (link, bus0))
                    result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    missing0 = True
            else:
                if log or log_warning:
                    print("[WAR] Link '%s' does not have bus0 specified..." % link)
                bus0 = "bus #%d" % _MISSING_BUS_COUNT
                _MISSING_BUS_COUNT += 1
                result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing0 = True
            if bus1:
                if bus1 in result:
                    if result[bus1]["missing"]:
                        if log or log_warning:
                            print("[WAR] Link '%s' connects to bus '%s' (bus1) which does not exist..." % (link, bus1))
                    missing1 = result[bus1]["missing"]
                else:
                    if log or log_warning:
                        print("[WAR] Link '%s' connects to bus '%s' (bus1) which does not exist..." % (link, bus1))
                    result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    missing1 = True
            else:
                if log or log_warning:
                    print("[WAR] Link '%s' does not have bus1 specified..." % link)
                bus1 = "bus #%d" % _MISSING_BUS_COUNT
                _MISSING_BUS_COUNT += 1
                result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing1 = True
            result[bus0]["links"].append([link, bus1, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, True, missing0 or missing1, False])
            if focus:
                result[bus1]["links"].append([link, bus0, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, False, missing0 or missing1, False])

        else:   # multi-link

            # check that buses that the link connects to exist
            missing = 0
            for key, value in specified_buses.items():
                bus_value, bus_efficiency = value
                if bus_value:
                    if bus_value in result:
                        if result[bus_value]["missing"]:
                            if log or log_warning:
                                print("[WAR] Link '%s' connects to bus '%s' (%s) which does not exist..." % (links.index[i], bus_value, key))
                            if key != "bus0":
                                missing += 1
                    else:
                        if log or log_warning:
                            print("[WAR] Link '%s' connects to bus '%s' (%s) which does not exist..." % (links.index[i], bus_value, key))
                        result[bus_value] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                        if key != "bus0":
                            missing += 1
                else:
                    if log or log_warning:
                        print("[WAR] Link '%s' does not have %s specified..." % (links.index[i], key))
                    bus_value = "bus #%d" % _MISSING_BUS_COUNT
                    _MISSING_BUS_COUNT += 1
                    result[bus_value] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                    value[0] = bus_value
                    if key != "bus0":
                        missing += 1


            # process multi-link
            link = links.index[i]
            carrier = links.carrier.iloc[i]
            p_nom_extendable = "True" if links.p_nom_extendable.iloc[i] else "False"
            p_nom = links.p_nom.iloc[i]
            capital_cost = links.capital_cost.iloc[i]
            marginal_cost = _format_series(links_t.marginal_cost[link]) if links_t and link in links_t.marginal_cost else "%.2f" % links.marginal_cost.iloc[i]
            p_nom_opt = links.p_nom_opt.iloc[i]
            p0_time_series = _format_series(links_t.p0[link]) if links_t and link in links_t.p0 else "N/A"
            bus0_value, bus0_efficiency = specified_buses["bus0"]
            index = len(result[bus0_value]["multi_link_trunks"])
            bus_to = []
            for key, value in specified_buses.items():
                bus_value, bus_efficiency = value
                if key != "bus0":
                    bus_to.append("To: %s (%s)" % (bus_value, key))
                    px = "p%s" % key[3:]
                    px_time_series = _format_series(links_t[px][link]) if links_t and px in links_t and link in links_t[px] else "N/A"
                    result[bus0_value]["multi_link_branches"].append([link, bus_value, key, carrier, p_nom_extendable, p_nom, bus_efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, True, False])
                    if focus:
                        result[bus_value]["multi_link_branches"].append([link, bus0_value, key, carrier, p_nom_extendable, p_nom, bus_efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, False, False])
            result[bus0_value]["multi_link_trunks"].append([link, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, len(specified_buses) - 1, missing, False])


    # get lines from (PyPSA) network
    if log or log_info:
        print("[INF] Retrieving lines from network...")
    lines = network.lines
    lines_t = getattr(network, "lines_t", None)
    for i in range(len(lines)):
        line = lines.index[i]
        bus0 = lines.bus0.iloc[i]
        bus1 = lines.bus1.iloc[i]
        carrier = lines.carrier.iloc[i]
        s_nom_extendable = "True" if lines.s_nom_extendable.iloc[i] else "False"
        s_nom = lines.s_nom.iloc[i]
        capital_cost = lines.capital_cost.iloc[i]
        s_nom_opt = lines.s_nom_opt.iloc[i]
        p0_time_series = _format_series(lines_t.p0[line]) if lines_t and line in lines_t.p0 else "N/A"
        p1_time_series = _format_series(lines_t.p1[line]) if lines_t and line in lines_t.p1 else "N/A"
        if bus0:
            if bus0 in result:
                if result[bus0]["missing"]:
                    if log or log_warning:
                        print("[WAR] Line '%s' connects to bus '%s' (bus0) which does not exist..." % (line, bus0))
                missing0 = result[bus0]["missing"]
            else:
                if log or log_warning:
                    print("[WAR] Line '%s' connects to bus '%s' (bus0) which does not exist..." % (line, bus0))
                result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing0 = True
        else:
            if log or log_warning:
                print("[WAR] Line '%s' does not have bus0 specified..." % line)
            bus0 = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus0] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
            missing0 = True
        if bus1:
            if bus1 in result:
                if result[bus1]["missing"]:
                    if log or log_warning:
                        print("[WAR] Line '%s' connects to bus '%s' (bus1) which does not exist..." % (line, bus1))
                missing1 = result[bus1]["missing"]
            else:
                if log or log_warning:
                    print("[WAR] Line '%s' connects to bus '%s' (bus1) which does not exist..." % (line, bus1))
                result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
                missing1 = True
        else:
            if log or log_warning:
                print("[WAR] Line '%s' does not have bus1 specified..." % line)
            bus1 = "bus #%d" % _MISSING_BUS_COUNT
            _MISSING_BUS_COUNT += 1
            result[bus1] = {"generators": list(), "loads": list(), "stores": list(), "links": list(), "multi_link_trunks": list(), "multi_link_branches": list(), "lines": list(), "generators_count": 0, "loads_count": 0, "stores_count": 0, "incoming_links_count": 0, "outgoing_links_count": 0, "lines_count": 0, "missing": True, "selected": False, "carrier": "", "unit": "", "p_time_series": ""}
            missing1 = True
        result[bus0]["lines"].append([line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, True, missing0 or missing1, False])
        if focus:
            result[bus1]["lines"].append([line, bus0, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, False, missing0 or missing1, False])


    return result



def _process_components(buses, bus_filter, generator_filter, load_filter, store_filter, link_filter, line_filter, carrier_filter, negative_efficiency, broken_missing, carrier_color, context):
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
    carrier_filter : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_missing : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    context : TYPE
        DESCRIPTION.

    Returns
    -------
    carriers : TYPE
        DESCRIPTION.
    """

    carriers = dict()


    # loop through existing buses
    for bus, values0 in buses.items():

        # process bus
        if (not values0["missing"] or broken_missing) and (not bus_filter or bus_filter.match(bus)) and (not carrier_filter or carrier_filter.match(values0["carrier"])):
            if carrier_color:
                carrier = values0["carrier"]
                if carrier and carrier not in carriers:
                    carriers[carrier] = None
            values0["selected"] = True


        # process generators (attached to the bus)
        generators = values0["generators"]
        for values1 in generators:
            generator, carrier, unit, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, selected = values1
            if values0["selected"] and (not generator_filter or generator_filter.match(generator)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                buses[bus]["generators_count"] += 1
            elif context:
                buses[bus]["generators_count"] += 1


        # process loads (attached to the bus)
        loads = values0["loads"]
        for values1 in loads:
            load, carrier, unit, p_set, selected = values1
            if values0["selected"] and (not load_filter or load_filter.match(load)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                buses[bus]["loads_count"] += 1
            elif context:
                buses[bus]["loads_count"] += 1


        # process stores (attached to the bus)
        stores = values0["stores"]
        for values1 in stores:
            store, carrier, unit, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, selected = values1
            if values0["selected"] and (not store_filter or store_filter.match(store)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                buses[bus]["stores_count"] += 1
            elif context:
                buses[bus]["stores_count"] += 1


        # process links (attached to the bus)
        links = values0["links"]
        for values1 in links:
            link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected = values1
            if not missing or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)) and (not carrier_filter or carrier_filter.match(carrier)):
                    values1[-1] = True
                if values1[-1] or context:
                    if bidirectional:
                        buses[bus]["incoming_links_count"] += 1
                        buses[bus]["outgoing_links_count"] += 1
                        buses[bus_to]["incoming_links_count"] += 1
                        buses[bus_to]["outgoing_links_count"] += 1
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            buses[bus]["outgoing_links_count"] += 1
                            buses[bus_to]["incoming_links_count"] += 1
                        else:
                            buses[bus]["incoming_links_count"] += 1
                            buses[bus_to]["outgoing_links_count"] += 1
                    else:
                        if direction:
                            buses[bus]["incoming_links_count"] += 1
                            buses[bus_to]["outgoing_links_count"] += 1
                        else:
                            buses[bus]["outgoing_links_count"] += 1
                            buses[bus_to]["incoming_links_count"] += 1


        # process multi-link trunks (attached to the bus)
        multi_link_trunks = values0["multi_link_trunks"]
        multi_link_branches = values0["multi_link_branches"]
        for values1 in multi_link_trunks:
            link_trunk, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, count, missing, selected = values1
            not_missing = count - missing
            if not_missing or broken_missing:
                if values0["selected"] and (not link_filter or link_filter.match(link_trunk)) and (not carrier_filter or carrier_filter.match(carrier)):
                    if bus_filter:
                        for values2 in multi_link_branches:
                            link_branch, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected = values2
                            if link_trunk == link_branch:
                                if not values0["missing"] and not buses[bus_to]["missing"] or broken_missing:
                                    if bus_filter.match(bus_to):
                                        values1[-1] = True
                                        break
                    else:
                        values1[-1] = True


        # process multi-link branches (attached to the bus)
        for values1 in multi_link_branches:
            link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected = values1
            if not values0["missing"] and not buses[bus_to]["missing"] or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)) and (not carrier_filter or carrier_filter.match(carrier)):
                    values1[-1] = True
                if values1[-1] or context:   # TODO: test logic
                    if negative_efficiency or efficiency >= 0:
                        if direction:
                            buses[bus]["outgoing_links_count"] += 1
                            buses[bus_to]["incoming_links_count"] += 1
                        else:
                            buses[bus]["incoming_links_count"] += 1
                            buses[bus_to]["outgoing_links_count"] += 1
                    else:
                        if direction:
                            buses[bus]["incoming_links_count"] += 1
                            buses[bus_to]["outgoing_links_count"] += 1
                        else:
                            buses[bus]["outgoing_links_count"] += 1
                            buses[bus_to]["incoming_links_count"] += 1


        # process lines (attached to the bus)
        lines = values0["lines"]
        for values1 in lines:
            line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, direction, missing, selected = values1
            if not missing or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not line_filter or line_filter.match(line)) and (not carrier_filter or carrier_filter.match(carrier)):
                    if carrier_color:
                        if carrier and carrier not in carriers:
                            carriers[carrier] = None
                    values1[-1] = True
                if values1[-1] or context:
                    buses[bus]["lines_count"] += 1
                    buses[bus1]["lines_count"] += 1


    return carriers



def _represent_components(buses, carriers, negative_efficiency, broken_missing, carrier_color, context, log, log_info, log_warning):
    """
    Parameters
    ----------
    buses : TYPE
        DESCRIPTION.
    carriers : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_missing : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    context : TYPE
        DESCRIPTION.
    log : TYPE
        DESCRIPTION.
    log_info : TYPE
        DESCRIPTION.
    log_warning : TYPE
        DESCRIPTION.

    Returns
    -------
    result : TYPE
        DESCRIPTION.
    """

    result = list()
    result_buses = list()
    result_generators = list()
    result_loads = list()
    result_stores = list()
    result_links = list()
    result_multi_link_trunks = list()
    result_multi_link_branches = list()
    result_lines = list()


    # add carrier color table
    if carrier_color:
        if isinstance(carrier_color, bool) and carrier_color:
            hue = 1.0 / (len(carriers) + 1)
            i = 0
            for key in carriers.keys():
                red, green, blue = colorsys.hsv_to_rgb(hue * i, 1.0, 1.0)
                carriers[key] = "#%02x%02x%02x" % (int(255 * red), int(255 * green), int(255 * blue))
                i += 1
        else:   # dictionary
            carriers = carrier_color
        result.append("   // carrier color table")
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
    multi_link_trunk_representation = DOT_REPRESENTATION["MULTI_LINK_TRUNK"]
    broken_multi_link_trunk_representation = DOT_REPRESENTATION["BROKEN_MULTI_LINK_TRUNK"]
    multi_link_branch_representation = DOT_REPRESENTATION["MULTI_LINK_BRANCH"]
    broken_multi_link_branch_representation = DOT_REPRESENTATION["BROKEN_MULTI_LINK_BRANCH"]
    line_representation = DOT_REPRESENTATION["LINE"]
    broken_line_representation = DOT_REPRESENTATION["BROKEN_LINE"]


    # loop through existing buses
    for bus, values in buses.items():

        # represent bus in DOT
        if values["missing"]:
            if values["selected"]:
                result_buses.append(missing_bus_representation % (bus, TEXT_COLOR, _replace(bus), bus, buses[bus]["generators_count"], buses[bus]["loads_count"], buses[bus]["stores_count"], buses[bus]["incoming_links_count"], buses[bus]["outgoing_links_count"], buses[bus]["lines_count"], values["unit"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, BROKEN_MISSING_COLOR))
            elif context and broken_missing:
                result_buses.append(missing_bus_representation % (bus, FADED_TEXT_COLOR, _replace(bus), bus, buses[bus]["generators_count"], buses[bus]["loads_count"], buses[bus]["stores_count"], buses[bus]["incoming_links_count"], buses[bus]["outgoing_links_count"], buses[bus]["lines_count"], values["unit"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, FADED_COMPONENT_COLOR))
        else:
            if values["selected"]:
                bus_color = carriers[values["carrier"]] if values["carrier"] in carriers else BUS_COLOR
                result_buses.append(bus_representation % (bus, TEXT_COLOR, _replace(bus), bus, values["carrier"], values["unit"], buses[bus]["generators_count"], buses[bus]["loads_count"], buses[bus]["stores_count"], buses[bus]["incoming_links_count"], buses[bus]["outgoing_links_count"], buses[bus]["lines_count"], values["p_time_series"], values["unit"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, bus_color))
            elif context:
                result_buses.append(bus_representation % (bus, FADED_TEXT_COLOR, _replace(bus), bus, values["carrier"], values["unit"], buses[bus]["generators_count"], buses[bus]["loads_count"], buses[bus]["stores_count"], buses[bus]["incoming_links_count"], buses[bus]["outgoing_links_count"], buses[bus]["lines_count"], values["p_time_series"], values["unit"], BUS_MINIMUM_WIDTH, BUS_THICKNESS, FADED_COMPONENT_COLOR))


        # represent generators (attached to the bus) in DOT
        generators = values["generators"]
        for generator, carrier, unit, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, selected in generators:
            if selected:
                generator_color = carriers[carrier] if carrier in carriers else GENERATOR_COLOR
                result_generators.append(generator_representation % (generator, TEXT_COLOR, _replace(generator), generator, bus, carrier, p_nom_extendable, p_nom, unit, p_set, unit, efficiency, capital_cost, unit, marginal_cost, unit, p_nom_opt, unit, p_time_series, unit, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, generator_color, generator, bus, LINK_THICKNESS, generator_color))
            elif context and (not values["missing"] or broken_missing):
                result_generators.append(generator_representation % (generator, FADED_TEXT_COLOR, _replace(generator), generator, bus, carrier, p_nom_extendable, p_nom, unit, p_set, unit, efficiency, capital_cost, unit, marginal_cost, unit, p_nom_opt, unit, p_time_series, unit, GENERATOR_MINIMUM_WIDTH, GENERATOR_THICKNESS, FADED_COMPONENT_COLOR, generator, bus, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # represent loads (attached to the bus) in DOT
        loads = values["loads"]
        for load, carrier, unit, p_set, selected in loads:
            if selected:
                load_color = carriers[carrier] if carrier in carriers else LOAD_COLOR
                result_loads.append(load_representation % (load, TEXT_COLOR, _replace(load), load, bus, carrier, p_set, unit, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, load_color, bus, load, LINK_THICKNESS, load_color))
            elif context and (not values["missing"] or broken_missing):
                result_loads.append(load_representation % (load, FADED_TEXT_COLOR, _replace(load), load, bus, carrier, p_set, unit, LOAD_MINIMUM_WIDTH, LOAD_MINIMUM_HEIGHT, LOAD_THICKNESS, FADED_COMPONENT_COLOR, bus, load, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # represent stores (attached to the bus) in DOT
        stores = values["stores"]
        for store, carrier, unit, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, selected in stores:
            if selected:
                store_color = carriers[carrier] if carrier in carriers else STORE_COLOR
                result_stores.append(store_representation % (store, TEXT_COLOR, _replace(store), store, bus, carrier, e_nom_extendable, e_nom, unit, p_set, unit, e_cyclic, capital_cost, unit, marginal_cost, unit, e_nom_opt, unit, e_time_series, unit, p_time_series, unit, STORE_MINIMUM_WIDTH, STORE_THICKNESS, store_color, bus, store, LINK_THICKNESS, store_color, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            elif context and (not values["missing"] or broken_missing):
                result_stores.append(store_representation % (store, FADED_TEXT_COLOR, _replace(store), store, bus, carrier, e_nom_extendable, e_nom, unit, p_set, unit, e_cyclic, capital_cost, unit, marginal_cost, unit, e_nom_opt, unit, e_time_series, unit, p_time_series, unit, STORE_MINIMUM_WIDTH, STORE_THICKNESS, FADED_COMPONENT_COLOR, bus, store, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent links (attached to the bus) in DOT
        links = values["links"]
        for link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected in links:
            if missing:
                if broken_missing:
                    if selected:
                        if bidirectional:
                            if direction:   # TODO: check if this "if" makes sense for bidirectional links
                                result_links.append(broken_bidirectional_link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_bidirectional_link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))   # TODO: check if "p0_time_series" needs to be inverted with "p1_time_series"
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result_links.append(broken_link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", "p1", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result_links.append(broken_link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, "p1", "p0", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif context:
                        if bidirectional:
                            if direction:   # TODO: check if this "if" makes sense for bidirectional links
                                result_links.append(broken_bidirectional_link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_bidirectional_link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        elif negative_efficiency or efficiency >= 0:
                            if direction:
                                result_links.append(broken_link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", "p1", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            if direction:
                                result_links.append(broken_link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, "p1", "p0", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            else:
                                result_links.append(broken_link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            else:
                if selected:
                    if bidirectional:
                        if direction:   # TODO: check if this "if" makes sense for bidirectional links
                            result_links.append(bidirectional_link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(bidirectional_link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result_links.append(link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_links.append(link_representation % (bus_to, bus, TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, "p1", p1_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus, bus_to, TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, "p1", p1_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                elif context:
                    if bidirectional:
                        if direction:   # TODO: check if this "if" makes sense for bidirectional links
                            result_links.append(bidirectional_link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(bidirectional_link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            result_links.append(link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (bus1)" % bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (bus1)" % bus, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, "p1", p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_links.append(link_representation % (bus_to, bus, FADED_TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (bus1)" % bus_to, "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, "p1", p1_time_series, "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_links.append(link_representation % (bus, bus_to, FADED_TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (bus1)" % bus, "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent multi-link trunks (attached to the bus) in DOT
        multi_link_trunks = values["multi_link_trunks"]
        for link, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, count, missing, selected in multi_link_trunks:
            not_missing = count - missing
            #bus_to = "1 bus (%d missing)" % missing if not_missing == 1 else "%d buses (%d missing)" % (not_missing, missing)
            if not_missing == 0:
                if broken_missing:
                    bus_to = "\n".join(bus_to)
                    if selected:
                        result_multi_link_trunks.append(multi_link_point_representation % (link, TEXT_COLOR, _replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, BROKEN_MISSING_COLOR))
                        result_multi_link_trunks.append(broken_multi_link_trunk_representation % (bus, link, TEXT_COLOR, _replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, LINK_THICKNESS, BROKEN_MISSING_COLOR))
                    elif context:
                        result_multi_link_trunks.append(multi_link_point_representation % (link, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, FADED_COMPONENT_COLOR))
                        result_multi_link_trunks.append(broken_multi_link_trunk_representation % (bus, link, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, LINK_THICKNESS, FADED_COMPONENT_COLOR))
            else:
                bus_to = "\n".join(bus_to) if broken_missing else "\n".join(bus_to[:not_missing])
                if selected:
                    result_multi_link_trunks.append(multi_link_point_representation % (link, TEXT_COLOR, _replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, LINK_COLOR))
                    result_multi_link_trunks.append(multi_link_trunk_representation % (bus, link, TEXT_COLOR, _replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, LINK_THICKNESS, LINK_COLOR))
                elif context:
                    result_multi_link_trunks.append(multi_link_point_representation % (link, FADED_TEXT_COLOR, _replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, MULTI_LINK_POINT_WIDTH, FADED_COMPONENT_COLOR))
                    result_multi_link_trunks.append(multi_link_trunk_representation % (bus, link, FADED_TEXT_COLOR, _replace(link), link, bus, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR))


        # process multi-link branches (attached to the bus)
        # TODO: test this logic
        multi_link_branches = values["multi_link_branches"]
        for link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected in multi_link_branches:
            if values["missing"] or buses[bus_to]["missing"]:
                if broken_missing:
                    if selected:
                        if negative_efficiency or efficiency >= 0:
                            #if direction:
                            if True:
                                result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            #else:
                            #    result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            #if direction:
                            if True:
                                result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            #else:
                            #    result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, BROKEN_MISSING_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    elif context:
                        if negative_efficiency or efficiency >= 0:
                            #if direction:
                            if True:
                                result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            #else:
                            #    result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, FADED_TEXT_COLOR, _replace(link), "%s (broken)" % link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, "p0", p0_time_series, px, "N/A", LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            #if direction:
                            if True:
                                result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, FADED_TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                            #else:
                            #    result_multi_link_branches.append(broken_multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, FADED_TEXT_COLOR, _replace(link), "%s (broken & inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, px, "N/A", "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
            else:   # TODO: ok in terms of the logic in this "else"
                if selected:
                    if negative_efficiency or efficiency >= 0:
                        if direction:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus, TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (%s)" % (bus, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (bus)" % bus, "%s (multi-link)" % link, TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (%s)" % (bus, bus_value), "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, LINK_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                elif context:
                    if negative_efficiency or efficiency >= 0:
                        if direction:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus_to, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus, "%s (%s)" % (bus_to, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (multi-link)" % link, "%s (bus)" % bus, FADED_TEXT_COLOR, _replace(link), link, "%s (bus0)" % bus_to, "%s (%s)" % (bus, bus_value), carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, "p0", p0_time_series, px, px_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                    else:
                        if direction:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (bus)" % bus_to, "%s (multi-link)" % link, FADED_TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (%s)" % (bus_to, bus_value), "%s (bus0)" % bus, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))
                        else:
                            result_multi_link_branches.append(multi_link_branch_representation % ("%s (bus)" % bus, "%s (multi-link)" % link, FADED_TEXT_COLOR, _replace(link), "%s (inverted)" % link, "%s (%s)" % (bus, bus_value), "%s (bus0)" % bus_to, carrier, p_nom_extendable, p_nom, -efficiency, capital_cost, marginal_cost, p_nom_opt, px, px_time_series, "p0", p0_time_series, LINK_THICKNESS, FADED_COMPONENT_COLOR, LINK_ARROW_SHAPE, LINK_ARROW_SIZE))


        # represent lines (attached to the bus) in DOT
        lines = values["lines"]
        for line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, direction, missing, selected in lines:
            if missing:
                if broken_missing:
                    if selected:
                        if direction:
                            result_lines.append(broken_line_representation % (bus, bus1, TEXT_COLOR, _replace(line), "%s (broken)" % line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, BROKEN_MISSING_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                        else:
                            result_lines.append(broken_line_representation % (bus1, bus, TEXT_COLOR, _replace(line), "%s (broken)" % line, bus1, bus, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, BROKEN_MISSING_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                    elif context:
                        if direction:
                            result_lines.append(broken_line_representation % (bus, bus1, FADED_TEXT_COLOR, _replace(line), "%s (broken)" % line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                        else:
                            result_lines.append(broken_line_representation % (bus1, bus, FADED_TEXT_COLOR, _replace(line), "%s (broken)" % line, bus1, bus, carrier, s_nom_extendable, s_nom, capital_cost, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
            else:
                if selected:
                    line_color = carriers[carrier] if carrier in carriers else LINE_COLOR
                    if direction:
                        result_lines.append(line_representation % (bus, bus1, TEXT_COLOR, _replace(line), line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, LINE_THICKNESS, line_color, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                    else:
                        result_lines.append(line_representation % (bus1, bus, TEXT_COLOR, _replace(line), line, bus1, bus, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, LINE_THICKNESS, line_color, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                elif context:
                    if direction:
                        result_lines.append(line_representation % (bus, bus1, FADED_TEXT_COLOR, _replace(line), line, bus, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))
                    else:
                        result_lines.append(line_representation % (bus1, bus, FADED_TEXT_COLOR, _replace(line), line, bus1, bus, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p1_time_series, p0_time_series, LINE_THICKNESS, FADED_COMPONENT_COLOR, LINE_ARROW_SHAPE, LINE_ARROW_SHAPE, LINE_ARROW_SIZE))


    # add buses to result
    result.append("   // buses (%d)" % len(result_buses))
    result.extend(result_buses)
    result.append("")


    # add generators to result
    result.append("   // generators (%d)" % len(result_generators))
    result.extend(result_generators)
    result.append("")


    # add loads to result
    result.append("   // loads (%d)" % len(result_loads))
    result.extend(result_loads)
    result.append("")


    # add stores to result
    result.append("   // stores (%d)" % len(result_stores))
    result.extend(result_stores)
    result.append("")


    # add links to result
    result.append("   // links (%d)" % len(result_links))
    result.extend(result_links)
    result.append("")


    # add multi-link trunks to result
    result.append("   // multi-link trunks (%d)" % (len(result_multi_link_trunks) / 2))
    result.extend(result_multi_link_trunks)
    result.append("")


    # add multi-link branches to result
    result.append("   // multi-link branches (%d)" % len(result_multi_link_branches))
    result.extend(result_multi_link_branches)
    result.append("")


    # add lines to result
    result.append("   // lines (%d)" % len(result_lines))
    result.extend(result_lines)


    return result, len(result_buses), len(result_generators), len(result_loads), len(result_stores), len(result_links) + len(result_multi_link_trunks) / 2, len(result_lines)



def _focus(components, bus, neighbourhood, bus_filter, generator_filter, load_filter, store_filter, link_filter, line_filter, carrier_filter, negative_efficiency, broken_missing, carrier_color, context, log, log_info, log_warning, carriers):
    """
    Parameters
    ----------
    components : TYPE
        DESCRIPTION.
    bus : TYPE
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
    carrier_filter : TYPE
        DESCRIPTION.
    negative_efficiency : TYPE
        DESCRIPTION.
    broken_missing : TYPE
        DESCRIPTION.
    carrier_color : TYPE
        DESCRIPTION.
    context : TYPE
        DESCRIPTION.
    log : TYPE
        DESCRIPTION.
    log_info : TYPE
        DESCRIPTION.
    log_warning : TYPE
        DESCRIPTION.
    carriers : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    result = list()
    visited = set()
    queue = deque()


    # add initial bus and neighbourhood to queue
    queue.append((bus, neighbourhood))


    # process queue
    while queue:

        # retrieve bus and neighbourhood from queue
        bus, neighbourhood = queue.popleft()


        # check if bus has already been visited (processed)
        key = "%s (bus)" % bus
        if key in visited:
            continue
        visited.add(key)


        # display info message
        if log or log_info:
            print("[INF] Focusing on bus '%s'..." % bus)


        # process bus
        values0 = components[bus]
        if len(visited) == 1 or ((not values0["missing"] or broken_missing) and (not bus_filter or bus_filter.match(bus))) and (not carrier_filter or carrier_filter.match(values0["carrier"])):
            if carrier_color:
                carrier = values0["carrier"]
                if carrier and carrier not in carriers:
                    carriers[carrier] = None
            values0["selected"] = True


        # check if neighbourhood visiting reached the limit
        if neighbourhood == 0:
            continue


        # process generators (attached to the bus currently on focus)
        generators = values0["generators"]
        for values1 in generators:
            generator, carrier, unit, p_nom_extendable, p_nom, p_set, efficiency, capital_cost, marginal_cost, p_nom_opt, p_time_series, selected = values1
            if values0["selected"] and (not generator_filter or generator_filter.match(generator)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                components[bus]["generators_count"] += 1
            elif context:
                components[bus]["generators_count"] += 1


        # process loads (attached to the bus currently on focus)
        loads = values0["loads"]
        for values1 in loads:
            load, carrier, unit, p_set, selected = values1
            if values0["selected"] and (not load_filter or load_filter.match(load)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                components[bus]["loads_count"] += 1
            elif context:
                components[bus]["loads_count"] += 1


        # process stores (attached to the bus currently on focus)
        stores = values0["stores"]
        for values1 in stores:
            store, carrier, unit, e_nom_extendable, e_nom, p_set, e_cyclic, capital_cost, marginal_cost, e_nom_opt, e_time_series, p_time_series, selected = values1
            if values0["selected"] and (not store_filter or store_filter.match(store)) and (not carrier_filter or carrier_filter.match(carrier)):
                if carrier_color:
                    if carrier and carrier not in carriers:
                        carriers[carrier] = None
                values1[-1] = True
                components[bus]["stores_count"] += 1
            elif context:
                components[bus]["stores_count"] += 1


        # process links (attached to the bus currently on focus)
        links = values0["links"]
        for values1 in links:
            link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected = values1
            key = "%s (link)" % link
            if key in visited:
                continue
            visited.add(key)
            if not missing or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)) and (not carrier_filter or carrier_filter.match(carrier)):
                    values1[-1] = True
                if values1[-1] or context:
                    if bidirectional:
                        components[bus]["incoming_links_count"] += 1
                        components[bus]["outgoing_links_count"] += 1
                        components[bus_to]["incoming_links_count"] += 1
                        components[bus_to]["outgoing_links_count"] += 1
                    elif negative_efficiency or efficiency >= 0:
                        if direction:
                            components[bus]["outgoing_links_count"] += 1
                            components[bus_to]["incoming_links_count"] += 1
                        else:
                            components[bus]["incoming_links_count"] += 1
                            components[bus_to]["outgoing_links_count"] += 1
                    else:
                        if direction:
                            components[bus]["incoming_links_count"] += 1
                            components[bus_to]["outgoing_links_count"] += 1
                        else:
                            components[bus]["outgoing_links_count"] += 1
                            components[bus_to]["incoming_links_count"] += 1
                    key = "%s (bus)" % bus_to
                    if key not in visited:
                        queue.append((bus_to, neighbourhood - 1))   # add neighbouring (adjacent) bus to queue


        # process multi-link trunks (attached to the bus currently on focus)
        multi_link_trunks = values0["multi_link_trunks"]
        multi_link_branches = values0["multi_link_branches"]
        for values1 in multi_link_trunks:
            link_trunk, bus_to, carrier, p_nom_extendable, p_nom, capital_cost, marginal_cost, p_nom_opt, p0_time_series, count, missing, selected = values1
            not_missing = count - missing
            if not_missing or broken_missing:
                if values0["selected"] and (not link_filter or link_filter.match(link_trunk)) and (not carrier_filter or carrier_filter.match(carrier)):
                    if bus_filter:
                        for values2 in multi_link_branches:
                            link_branch, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected = values2
                            if link_trunk == link_branch:
                                if not values0["missing"] and not components[bus_to]["missing"] or broken_missing:
                                    if bus_filter.match(bus_to):
                                        values1[-1] = True
                                        break
                    else:
                        values1[-1] = True


        # process multi-link branches (attached to the bus currently on focus)
        for values1 in multi_link_branches:
            link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected = values1
            if not values0["missing"] and not components[bus_to]["missing"] or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus_to)) and (not link_filter or link_filter.match(link)) and (not carrier_filter or carrier_filter.match(carrier)):
                    values1[-1] = True
                    if not direction or neighbourhood > 1:
                        multi_link_trunks = components[bus_to]["multi_link_trunks"]
                        if index < len(multi_link_trunks):
                            multi_link_trunks[index][-1] = True
                if values1[-1] or context:   # TODO: test logic
                    if negative_efficiency or efficiency >= 0:
                        if direction:
                            components[bus]["outgoing_links_count"] += 1
                            components[bus_to]["incoming_links_count"] += 1
                        else:
                            components[bus]["incoming_links_count"] += 1
                            components[bus_to]["outgoing_links_count"] += 1
                    else:
                        if direction:
                            components[bus]["incoming_links_count"] += 1
                            components[bus_to]["outgoing_links_count"] += 1
                        else:
                            components[bus]["outgoing_links_count"] += 1
                            components[bus_to]["incoming_links_count"] += 1
                    queue.append((bus_to, neighbourhood - 1))   # add neighbouring (adjacent) bus to queue


        # process lines (attached to the bus currently on focus)
        lines = values0["lines"]
        for values1 in lines:
            line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, direction, missing, selected = values1
            key = "%s (line)" % line
            if key in visited:
                continue
            visited.add(key)
            if not missing or broken_missing:
                if values0["selected"] and (not bus_filter or bus_filter.match(bus1)) and (not line_filter or line_filter.match(line)) and (not carrier_filter or carrier_filter.match(carrier)):
                    if carrier_color:
                        if carrier and carrier not in carriers:
                            carriers[carrier] = None
                    values1[-1] = True
                if values1[-1] or context:
                    components[bus]["lines_count"] += 1
                    components[bus1]["lines_count"] += 1
                    key = "%s (bus)" % bus1
                    if key not in visited:
                        queue.append((bus1, neighbourhood - 1))   # add neighbouring (adjacent) bus to queue



def _generate_output(dot_representation, file_output, file_format, log, log_info, log_warning):
    """
    Parameters
    ----------
    dot_representation : TYPE
        DESCRIPTION.
    file_output : TYPE
        DESCRIPTION.
    file_format : TYPE
        DESCRIPTION.
    log : TYPE
        DESCRIPTION.
    log_info : TYPE
        DESCRIPTION.
    log_warning : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    # write DOT representation of (PyPSA) network into a DOT file
    file_output_dot = "%s.dot" % file_output.rsplit(".", 1)[0]
    if log or log_info:
        print("[INF] Writing DOT file '%s'..." % file_output_dot)
    try:
        with open(file_output_dot, "w") as handle:
            for line in dot_representation:
                handle.write("%s%s" % (line, os.linesep))
            handle.write(os.linesep)
    except:
        print("[ERR] The file '%s' could not be written!" % file_output_dot)
        return -1   # return unsuccessfully


    # launch the tool 'dot' passing DOT file to it
    if log or log_info:
        print("[INF] Generating topographical representation of the network based on DOT file '%s'..." % file_output_dot)
    try:
        result = subprocess.run(["dot", "-T%s" % file_format, file_output_dot], capture_output = True)
    except KeyboardInterrupt:
        if log or log_warning:
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
    if log or log_info:
        print("[INF] Writing output file '%s' in the %s format..." % (file_output, file_format.upper()))
    try:
        with open(file_output, "wb") as handle:
            handle.write(result.stdout)
    except:
        print("[ERR] The file '%s' could not be written!" % file_output)
        return -1   # return unsuccessfully


    return 0   # return successfully



def generate(network, focus = None, neighbourhood = 0, bus_filter = None, generator_filter = None, load_filter = None, store_filter = None, link_filter = None, line_filter = None, carrier_filter = None, negative_efficiency = True, broken_missing = False, carrier_color = None, context = False, file_output = FILE_OUTPUT, file_format = FILE_FORMAT, log = False, log_info = False, log_warning = False):
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
    carrier_filter : TYPE, optional
        DESCRIPTION. The default is None.
    negative_efficiency : TYPE, optional
        DESCRIPTION. The default is True.
    broken_missing : TYPE, optional
        DESCRIPTION. The default is False.
    carrier_color : TYPE, optional
        DESCRIPTION. The default is None.
    context : TYPE, optional
        DESCRIPTION. The default is False.
    file_output : TYPE, optional
        DESCRIPTION. The default is FILE_OUTPUT.
    file_format : TYPE, optional
        DESCRIPTION. The default is FILE_FORMAT.
    log : TYPE, optional
        DESCRIPTION. The default is False.
    log_info : TYPE, optional
        DESCRIPTION. The default is False.
    log_warning : TYPE, optional
        DESCRIPTION. The default is False.

    Returns
    -------
    TYPE
        DESCRIPTION.
    """

    result = list()
    visited = set()


    # check if neighbourhood is valid
    if isinstance(neighbourhood, int):
        if neighbourhood < 0:
            print("[ERR] The neighbourhood should be equal or greater than 0")
            return -1   # return unsuccessfully
    else:   # list
        for value in neighbourhood:
            if value < 0:
                print("[ERR] The neighbourhood should be equal or greater than 0")
                return -1   # return unsuccessfully


    # check if file format is valid
    if file_format not in ("svg", "png", "jpg", "gif", "ps"):
        print("[ERR] The file format '%s' is not valid (acceptable formats are: 'svg', 'png', 'jpg', 'gif' or 'ps')!" % file_format)
        return -1   # return unsuccessfully


    # read (PyPSA) network
    if isinstance(network, str):
        if log or log_info:
            print("[INF] Reading file '%s' containing PyPSA-based network..." % network)
        pypsa_network = pypsa.Network(network)
    else:   # pypsa.components.Network
        pypsa_network = network


    # check if bus to focus on exists in (PyPSA) network
    if focus:
        buses = pypsa_network.buses.index
        if isinstance(focus, str):
            if focus not in buses:
                print("[ERR] The bus '%s' to focus on does not exist!" % focus)
                return -1   # return unsuccessfully
        else:   # list
            for bus in focus:
                if bus not in buses:
                    print("[ERR] The bus '%s' to focus on does not exist!" % bus)
                    return -1   # return unsuccessfully


    # compile regular expressions
    bus_filter_regexp = re.compile(bus_filter) if bus_filter else None
    generator_filter_regexp = re.compile(generator_filter) if generator_filter else None
    load_filter_regexp = re.compile(load_filter) if load_filter else None
    store_filter_regexp = re.compile(store_filter) if store_filter else None
    link_filter_regexp = re.compile(link_filter) if link_filter else None
    line_filter_regexp = re.compile(line_filter) if line_filter else None
    carrier_filter_regexp = re.compile(carrier_filter) if carrier_filter else None


    # get network name
    if pypsa_network.name:
        network_name = pypsa_network.name
        if log or log_info:
            print("[INF] Start generating topographical representation of the network '%s'..." % network_name)
    else:
        network_name = NETWORK_NAME
        if log or log_info:
            print("[INF] Start generating topographical representation of the network...")


    # get components from (PyPSA) network
    components = _get_components(pypsa_network, focus is not None, log, log_info, log_warning)


    # process components
    if focus:

        # focus on bus
        carriers = dict()
        if isinstance(focus, str):
            if isinstance(neighbourhood, int):
                value = neighbourhood
            else:   # list
                value = neighbourhood[0] if len(neighbourhood) else 0
            _focus(components, focus, value, bus_filter_regexp, generator_filter_regexp, load_filter_regexp, store_filter_regexp, link_filter_regexp, line_filter_regexp, negative_efficiency, broken_missing, carrier_color, context, log, log_info, log_warning, carriers)
        else:   # list
            for i in range(len(focus)):
                bus = focus[i]
                if bus not in visited:   # skip bus as it has already been visited (processed)
                    if isinstance(neighbourhood, int):
                        value = neighbourhood
                    else:   # list
                        value = neighbourhood[i] if i < len(neighbourhood) else 0
                    _focus(components, bus, value, bus_filter_regexp, generator_filter_regexp, load_filter_regexp, store_filter_regexp, link_filter_regexp, line_filter_regexp, carrier_filter_regexp, negative_efficiency, broken_missing, carrier_color, context, log, log_info, log_warning, carriers)
                    visited.add(bus)


        # remove redundant (duplicated) links
        remove = dict()
        for bus, values in components.items():
            links = values["links"]
            for link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected in links:
                if link not in remove or selected:
                    remove[link] = [selected, False]
        for bus, values in components.items():
            links = values["links"]
            for i in range(len(links) - 1, -1, -1):
                link, bus_to, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, p1_time_series, bidirectional, direction, missing, selected = links[i]
                if remove[link][0]:
                    if not selected:
                        del links[i]
                else:
                    if remove[link][1]:
                        del links[i]
                    else:
                        remove[link][1] = True


        # remove redundant (duplicated) multi-links
        remove = dict()
        for bus, values in components.items():
            multi_link_branches = values["multi_link_branches"]
            for link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected in multi_link_branches:
                key = (link, bus_value)
                if key not in remove:
                    remove[key] = [False, 0, 0]
                if selected:
                    remove[key][0] = True
                    remove[key][1] += 1
                else:
                    remove[key][2] += 1
        for bus, values in components.items():
            multi_link_branches = values["multi_link_branches"]
            for i in range(len(multi_link_branches) - 1, -1, -1):
                link, bus_to, bus_value, carrier, p_nom_extendable, p_nom, efficiency, capital_cost, marginal_cost, p_nom_opt, p0_time_series, px, px_time_series, index, direction, selected = multi_link_branches[i]
                key = (link, bus_value)
                if selected:
                    if remove[key][0] and remove[key][1] > 1:
                        del multi_link_branches[i]
                        remove[key][1] -= 1
                else:
                    if remove[key][0] or remove[key][2] > 1:
                        del multi_link_branches[i]
                        remove[key][2] -= 1


        # remove redundant (duplicated) lines
        remove = dict()
        for bus, values in components.items():
            lines = values["lines"]
            for line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, direction, missing, selected in lines:
                if line not in remove or selected:
                    remove[line] = [selected, False]
        for bus, values in components.items():
            lines = values["lines"]
            for i in range(len(lines) - 1, -1, -1):
                line, bus1, carrier, s_nom_extendable, s_nom, capital_cost, s_nom_opt, p0_time_series, p1_time_series, direction, missing, selected = lines[i]
                if remove[line][0]:
                    if not selected:
                        del lines[i]
                else:
                    if remove[line][1]:
                        del lines[i]
                    else:
                        remove[line][1] = True

    else:
        carriers = _process_components(components, bus_filter_regexp, generator_filter_regexp, load_filter_regexp, store_filter_regexp, link_filter_regexp, line_filter_regexp, carrier_filter_regexp, negative_efficiency, broken_missing, carrier_color, context)


    # get DOT representation of components
    representation, buses_count, generators_count, loads_count, stores_count, links_count, lines_count = _represent_components(components, carriers, negative_efficiency, broken_missing, carrier_color, context, log, log_info, log_warning)


    # add metadata to digraph
    now = datetime.datetime.now()
    result.append("//")
    result.append("// Generated by %s version %s (on the %04d/%02d/%02d at %02d:%02d:%02d) using the following parameters: " % (__project__, __version__, now.year, now.month, now.day, now.hour, now.minute, now.second))
    result.append("//")
    if isinstance(network, str):
        result.append("//    file_input=%s" % network)
    else:   # pypsa.components.Network
        result.append("//    file_input=None")
    result.append("//    focus=%s" % focus)
    result.append("//    neighbourhood=%s" % neighbourhood)
    result.append("//    bus_filter=%s" % bus_filter)
    result.append("//    generator_filter=%s" % generator_filter)
    result.append("//    load_filter=%s" % load_filter)
    result.append("//    store_filter=%s" % store_filter)
    result.append("//    link_filter=%s" % link_filter)
    result.append("//    line_filter=%s" % line_filter)
    result.append("//    carrier_filter=%s" % carrier_filter)
    result.append("//    negative_efficiency=%s" % negative_efficiency)
    result.append("//    broken_missing=%s" % broken_missing)
    result.append("//    carrier_color=%s" % carrier_color)
    result.append("//    context=%s" % context)
    result.append("//    file_output=%s" % file_output)
    result.append("//    file_format=%s" % file_format)
    result.append("//    log=%s" % log)
    result.append("//    log_info=%s" % log_info)
    result.append("//    log_warning=%s" % log_warning)
    result.append("//")
    result.append("")


    # declare digraph header
    result.append("digraph \"%s\"" % network_name)


    # open digraph body
    result.append("{")


    # configure digraph layout
    result.append("   // digraph layout")
    result.append("   bgcolor = \"%s\"" % BACKGROUND_COLOR)
    result.append("   labelloc = \"t\"")
    result.append("   label = \"%s\n\n\n           \"" % network_name)
    result.append("   tooltip = \"Network: %s\nBuses: %d (out of %d)\nGenerators: %d (out of %d)\nLoads: %s (out of %d)\nStores: %d (out of %d)\nLinks: %d (out of %d)\nLines: %d (out of %d)\nSnapshots: %d\"" % (network_name, buses_count, len(pypsa_network.buses), generators_count, len(pypsa_network.generators), loads_count, len(pypsa_network.loads), stores_count, len(pypsa_network.stores), links_count, len(pypsa_network.links), lines_count, len(pypsa_network.lines), len(pypsa_network.snapshots)))
    result.append("   rankdir = \"%s\"" % RANK_DIRECTION)
    result.append("   ranksep = %.2f" % RANK_SEPARATION)
    result.append("   nodesep = %.2f" % NODE_SEPARATION)
    result.append("   splines = \"%s\"" % EDGE_STYLE)
    result.append("   node [fontname = \"%s\", fontsize = %.2f]" % (TEXT_FONT, TEXT_SIZE))
    result.append("   edge [fontname = \"%s\", fontsize = %.2f]" % (TEXT_FONT, TEXT_SIZE))
    result.append("")


    # add DOT representation of components to result
    result.extend(representation)


    # close digraph body
    result.append("}")


    # generate output files based on (PyPSA) network DOT representation
    status = _generate_output(result, file_output, file_format, log, log_info, log_warning)


    # display info message
    if not status:
        if log or log_info:
            print("[INF] Finished generating topographical representation of the network!")


    return status



if __name__ == "__main__":

    # parse arguments passed to PyPSATopo
    parser = argparse.ArgumentParser()
    parser.add_argument("--focus", nargs = "+", help = "Focus on one or more buses to start visiting")
    parser.add_argument("--neighbourhood", nargs = "+", type = int, help = "Specify how much neighbourhood (around the bus to focus on) should be visited")
    parser.add_argument("--bus-filter", action = "store", help = "Include/exclude buses in/from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--generator-filter", action = "store", help = "Include/exclude generators in/from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--load-filter", action = "store", help = "Include/exclude loads in/from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--store-filter", action = "store", help = "Include/exclude stores in/from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--link-filter", action = "store", help = "Include/exclude links in/from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--line-filter", action = "store", help = "Include/exclude lines in /from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--carrier-filter", action = "store", help = "Include/exclude components based on their carriers in /from the topographical representation of the network in function of a regular expression")
    parser.add_argument("--no-negative-efficiency", action = "store_true", help = "Invert the sense of the arrow (i.e. to point to bus0 instead) when dealing with links with negative efficiencies")
    parser.add_argument("--broken-missing", action = "store_true", help = "Include broken links and missing buses in the topographical representation of the network")
    parser.add_argument("--carrier-color", nargs = "*", help = "Specify a palette to color components in function of their carriers")
    parser.add_argument("--context", action = "store_true", help = "Show selected components in the topographical representation of the network among excluded components")
    parser.add_argument("--file-output", nargs = "+", help = "Specify the file name where to save the topographical representation of the network")
    parser.add_argument("--file-format", choices = ["svg", "png", "jpg", "gif", "ps"], help = "Specify the file format that the topographical representation of the network is saved as")
    parser.add_argument("--log", action = "store_true", help = "Show all log messages while generating the topographical representation of the network")
    parser.add_argument("--log-info", action = "store_true", help = "Show only info log messages while generating the topographical representation of the network")
    parser.add_argument("--log-warning", action = "store_true", help = "Show only warning log messages while generating the topographical representation of the network")
    args, files = parser.parse_known_args()


    # process arguments
    if args.neighbourhood is None:
        neighbourhood = 0
    else:
        neighbourhood = args.neighbourhood[0] if len(args.neighbourhood) == 1 else args.neighbourhood
    bus_filter = args.bus_filter if args.bus_filter else None
    generator_filter = args.generator_filter if args.generator_filter else None
    load_filter = args.load_filter if args.load_filter else None
    store_filter = args.store_filter if args.store_filter else None
    link_filter = args.link_filter if args.link_filter else None
    line_filter = args.line_filter if args.line_filter else None
    carrier_filter = args.carrier_filter if args.carrier_filter else None
    carrier_color = args.carrier_color if args.carrier_color else None
    if args.carrier_color is None:
        carrier_color = None
    else:
        length = len(args.carrier_color)
        if length == 0:
            carrier_color = True
        elif length % 2 != 0:
            print("[ERR] The number of arguments specified for argument 'carrier_color' is not even (each specified carrier should have a color associated to it)!")
            sys.exit(-1)   # set exit code to unsuccessful and exit
        else:
            carrier_color = dict()
            for i in range(0, len(args.carrier_color), 2):
                carrier_color[args.carrier_color[i]] = args.carrier_color[i + 1]
    file_format = args.file_format if args.file_format else FILE_FORMAT


    # display PyPSATopo information
    if args.log or args.log_info:
        print("[INF] %s version %s" % (__project__, __version__))


    if files:

        # loop through files passed as arguments
        for i in range(len(files)):

            # generate output file name
            file_output = args.file_output[i] if args.file_output and i < len(args.file_output) else "%s.%s" % (files[i].rsplit(".", 1)[0], file_format)


            # generate topographical representation of network
            status = generate(files[i], focus = args.focus, neighbourhood = neighbourhood, bus_filter = bus_filter, generator_filter = generator_filter, load_filter = load_filter, store_filter = store_filter, link_filter = link_filter, line_filter = line_filter, carrier_filter = carrier_filter, negative_efficiency = not args.no_negative_efficiency, broken_missing = args.broken_missing, carrier_color = carrier_color, context = args.context, file_output = file_output, file_format = file_format, log = args.log, log_info = args.log_info, log_warning = args.log_warning)


            # check status of generation
            if status:
                sys.exit(status)   # set exit code with returned status and exit

    else:

        # process arguments
        file_output = args.file_output if args.file_output else FILE_OUTPUT


        # create dummy (PyPSA) network
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


        # generate topographical representation of dummy network
        status = generate(network, focus = args.focus, neighbourhood = neighbourhood, bus_filter = bus_filter, generator_filter = generator_filter, load_filter = load_filter, store_filter = store_filter, link_filter = link_filter, line_filter = line_filter, carrier_filter = carrier_filter, negative_efficiency = not args.no_negative_efficiency, broken_missing = args.broken_missing, carrier_color = carrier_color, context = args.context, file_output = file_output, file_format = file_format, log = args.log, log_info = args.log_info, log_warning = args.log_warning)


    # set exit code and finish
    sys.exit(status)

