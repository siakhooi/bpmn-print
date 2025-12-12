"""Styling configuration for BPMN diagram nodes and edges.

This module contains all styling constants and node type configurations
for rendering BPMN diagrams with Graphviz.
"""

# BPMN namespace mapping for XML parsing
# Maps the "bpmn" prefix to the official BPMN 2.0 namespace URI.
# This is used with lxml's findall() and find() methods to query
# BPMN elements in XML documents.
BPMN_NS = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}


class NodeStyle:
    """Constants for node styling attributes."""
    # Event node dimensions
    EVENT_WIDTH = "0.6"
    EVENT_HEIGHT = "0.6"

    # Colors
    START_EVENT_COLOR = "lightgreen"
    END_EVENT_COLOR = "lightcoral"
    TASK_COLOR = "lightyellow"
    SERVICE_TASK_COLOR = "lightblue"
    CALL_ACTIVITY_COLOR = "wheat"
    EXCLUSIVE_GATEWAY_COLOR = "yellow"
    PARALLEL_GATEWAY_COLOR = "orange"

    # Edge styling
    CONDITION_FONT_SIZE = "11"
    CONDITION_FONT_COLOR = "red"
    FLOW_NAME_FONT_SIZE = "10"


# Node type configuration: maps BPMN element types to their styling
# All XPath queries use the "bpmn:" prefix and must be executed with
# the BPMN_NS namespace mapping when calling findall() or find()
NODE_TYPE_CONFIG = {
    "startEvent": {
        "xpath": ".//bpmn:startEvent",  # XPath with BPMN namespace prefix
        "default_name": "Start",
        "shape": "circle",
        "style": "filled",
        "fillcolor": NodeStyle.START_EVENT_COLOR,
        "width": NodeStyle.EVENT_WIDTH,
        "height": NodeStyle.EVENT_HEIGHT,
        "fixedsize": "true",
    },
    "endEvent": {
        "xpath": ".//bpmn:endEvent",
        "default_name": "End",
        "shape": "doublecircle",
        "style": "filled",
        "fillcolor": NodeStyle.END_EVENT_COLOR,
        "width": NodeStyle.EVENT_WIDTH,
        "height": NodeStyle.EVENT_HEIGHT,
        "fixedsize": "true",
    },
    "task": {
        "xpath": ".//bpmn:task",
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": NodeStyle.TASK_COLOR,
    },
    "serviceTask": {
        "xpath": ".//bpmn:serviceTask",
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": NodeStyle.SERVICE_TASK_COLOR,
        "penwidth": "2",
    },
    "callActivity": {
        "xpath": ".//bpmn:callActivity",
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled,bold",
        "fillcolor": NodeStyle.CALL_ACTIVITY_COLOR,
        "penwidth": "3",
    },
    "exclusiveGateway": {
        "xpath": ".//bpmn:exclusiveGateway",
        "default_name": "X",
        "shape": "diamond",
        "style": "filled",
        "fillcolor": NodeStyle.EXCLUSIVE_GATEWAY_COLOR,
    },
    "parallelGateway": {
        "xpath": ".//bpmn:parallelGateway",
        "default_name": "+",
        "shape": "diamond",
        "style": "filled",
        "fillcolor": NodeStyle.PARALLEL_GATEWAY_COLOR,
    },
}
