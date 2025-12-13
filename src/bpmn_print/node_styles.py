from .xml_constants import (
    XPATH_START_EVENT,
    XPATH_END_EVENT,
    XPATH_TASK,
    XPATH_SERVICE_TASK,
    XPATH_CALL_ACTIVITY,
    XPATH_EXCLUSIVE_GATEWAY,
    XPATH_PARALLEL_GATEWAY,
)


class NodeStyle:
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


class GraphConfig:
    """Configuration for Graphviz graph rendering."""

    # Output format
    FORMAT = "png"

    # Graph layout direction
    # Options: "LR" (left-to-right), "TB" (top-to-bottom),
    #          "RL" (right-to-left), "BT" (bottom-to-top)
    RANKDIR = "LR"

    # Edge routing style
    # Options: "polyline", "spline", "line", "ortho"
    # polyline provides better label support
    SPLINES = "polyline"


NODE_TYPE_CONFIG = {
    "startEvent": {
        "xpath": XPATH_START_EVENT,
        "default_name": "Start",
        "shape": "circle",
        "style": "filled",
        "fillcolor": NodeStyle.START_EVENT_COLOR,
        "width": NodeStyle.EVENT_WIDTH,
        "height": NodeStyle.EVENT_HEIGHT,
        "fixedsize": "true",
    },
    "endEvent": {
        "xpath": XPATH_END_EVENT,
        "default_name": "End",
        "shape": "doublecircle",
        "style": "filled",
        "fillcolor": NodeStyle.END_EVENT_COLOR,
        "width": NodeStyle.EVENT_WIDTH,
        "height": NodeStyle.EVENT_HEIGHT,
        "fixedsize": "true",
    },
    "task": {
        "xpath": XPATH_TASK,
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": NodeStyle.TASK_COLOR,
    },
    "serviceTask": {
        "xpath": XPATH_SERVICE_TASK,
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled",
        "fillcolor": NodeStyle.SERVICE_TASK_COLOR,
        "penwidth": "2",
    },
    "callActivity": {
        "xpath": XPATH_CALL_ACTIVITY,
        "default_name": None,  # Use node_id as fallback
        "shape": "box",
        "style": "rounded,filled,bold",
        "fillcolor": NodeStyle.CALL_ACTIVITY_COLOR,
        "penwidth": "3",
    },
    "exclusiveGateway": {
        "xpath": XPATH_EXCLUSIVE_GATEWAY,
        "default_name": "X",
        "shape": "diamond",
        "style": "filled",
        "fillcolor": NodeStyle.EXCLUSIVE_GATEWAY_COLOR,
    },
    "parallelGateway": {
        "xpath": XPATH_PARALLEL_GATEWAY,
        "default_name": "+",
        "shape": "diamond",
        "style": "filled",
        "fillcolor": NodeStyle.PARALLEL_GATEWAY_COLOR,
    },
}
