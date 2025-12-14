from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

from lxml.etree import _Element

from .xml_utils import BpmnContext
from .xml_constants import (
    ATTR_ID,
    ATTR_NAME,
    ATTR_CALLED_ELEMENT,
    BPMN_NS,
    CAMUNDA_NS_URI,
    XPATH_CALL_ACTIVITY,
    XPATH_SERVICE_TASK,
    XPATH_CAMUNDA_SCRIPT,
    XPATH_CAMUNDA_INPUT_PARAMETER,
)

# Camunda-specific attribute using namespace URI
CAMUNDA_CLASS_ATTR = f"{{{CAMUNDA_NS_URI}}}class"

UNKNOWN_VALUE = "unknown"
DEFAULT_SCRIPT_NAME = "script"
DEFAULT_PARAM_NAME = "inputParameter"
JEXL_SCRIPT_PLACEHOLDER = "[See JEXL Scripts]"

# JEXL expression pattern - matches both #{ } and ${ } style expressions
# Compiled at module level for efficiency
JEXL_PATTERN = re.compile(r"[#$]\{\s")

# Node type
NODE_TYPE_CALL_ACTIVITY = "callActivity"
NODE_TYPE_SERVICE_TASK = "serviceTask"


@dataclass
class Node:
    """Represents a BPMN node (callActivity or serviceTask)."""

    name: str
    type: str
    target: str


@dataclass
class Parameter:
    """Represents an input parameter.

    Attributes:
        node_name: Name of the node containing this parameter
        param_name: Name of the parameter
        value: Parameter value (or placeholder if has_script is True)
        has_script: Whether this parameter has an associated JEXL script.
                   Reserved for future use (e.g., styling parameters with
                   scripts differently in PDF output).
    """

    node_name: str
    param_name: str
    value: str
    has_script: bool


@dataclass
class Script:
    """Represents a JEXL script."""

    text: str
    node_name: str
    param_name: str


@dataclass
class BpmnExtractResult:

    nodes: List[Node]
    parameters: List[Parameter]
    scripts: List[Script]


def find_parent_with_id(element: _Element) -> str:
    """Traverse up the tree to find the first ancestor with an
    'id' attribute
    """
    current = element
    while current is not None:
        if "id" in current.attrib:
            return current.get("id")
        current = current.getparent()
    return UNKNOWN_VALUE


def _get_element_name(element: _Element, default: str = UNKNOWN_VALUE) -> str:
    """Get the name of an element, falling back to its ID or a default."""
    return element.get(ATTR_NAME, element.get(ATTR_ID, default))


def _is_jexl_expression(text: str) -> bool:
    return JEXL_PATTERN.search(text) is not None


def _simplify_class_name(class_name: str) -> str:
    """Extract the simple class name from a fully qualified class name.

    Args:
        class_name: Fully qualified class name (e.g., 'com.example.MyClass')

    Returns:
        Simple class name (e.g., 'MyClass') or empty string
    """
    return class_name.rsplit(".", 1)[-1] if class_name else ""


def _get_node_info(
    element: _Element, id_to_name: Dict[str, str]
) -> Tuple[str, str]:
    """Extract node name and parameter name from an element.

    Args:
        element: The XML element to extract info from
        id_to_name: Mapping from element IDs to their names

    Returns:
        Tuple of (node_name, param_name) where:
        - node_name: Name of the parent node containing this element
        - param_name: Name attribute of the element or default value
    """
    node_id = find_parent_with_id(element)
    node_name = id_to_name.get(node_id, node_id)
    return node_name, element.get(ATTR_NAME, DEFAULT_PARAM_NAME)


def _create_parameter(
    node_name: str, param_name: str, value: str, has_script: bool
) -> Parameter:
    return Parameter(node_name, param_name, value, has_script)


def _process_script_element(node_name: str, param_name: str) -> Parameter:
    """Process an input parameter that contains a script element.

    Args:
        node_name: Name of the node this parameter belongs to
        param_name: Name of the parameter
    """
    parameter = _create_parameter(
        node_name, param_name, JEXL_SCRIPT_PLACEHOLDER, True
    )
    return parameter


def _process_text_content(
    text: str, node_name: str, param_name: str
) -> Tuple[Parameter, Optional[Script]]:
    """Process an input parameter with text content.

    Args:
        text: The text content of the parameter
        node_name: Name of the node this parameter belongs to
        param_name: Name of the parameter

    Returns:
        Tuple of (Parameter, Optional[Script]) where:
        - Parameter: Always returned with the parameter information
        - Script: Included if text is a JEXL expression, None otherwise
    """
    if _is_jexl_expression(text):
        # JEXL expression - add to scripts
        script = Script(text, node_name, param_name)
        parameter = _create_parameter(
            node_name, param_name, JEXL_SCRIPT_PLACEHOLDER, True
        )
        return parameter, script
    else:
        # Simple value
        parameter = _create_parameter(node_name, param_name, text, False)
        return parameter, None


def _create_call_activity_node(call_activity: _Element) -> Node:
    return Node(
        name=_get_element_name(call_activity),
        type=NODE_TYPE_CALL_ACTIVITY,
        target=call_activity.get(ATTR_CALLED_ELEMENT, ""),
    )


def _extract_call_activities(root: _Element) -> List[Node]:
    return [
        _create_call_activity_node(call_activity)
        for call_activity in root.findall(XPATH_CALL_ACTIVITY, BPMN_NS)
    ]


def _create_service_task_node(service_task: _Element) -> Node:
    class_name = service_task.get(CAMUNDA_CLASS_ATTR, "")
    return Node(
        name=_get_element_name(service_task),
        type=NODE_TYPE_SERVICE_TASK,
        target=_simplify_class_name(class_name),
    )


def _extract_service_tasks(root: _Element) -> List[Node]:
    return [
        _create_service_task_node(service_task)
        for service_task in root.findall(XPATH_SERVICE_TASK, BPMN_NS)
    ]


def _extract_script_elements(
    root: _Element, id_to_name: Dict[str, str]
) -> List[Script]:
    scripts = []
    for scr in root.findall(XPATH_CAMUNDA_SCRIPT, BPMN_NS):
        node_id = find_parent_with_id(scr)
        node_name = id_to_name.get(node_id, node_id)
        param_name = scr.getparent().get(ATTR_NAME, DEFAULT_SCRIPT_NAME)
        scripts.append(Script(scr.text or "", node_name, param_name))
    return scripts


def _process_single_input_parameter(
    inp: _Element, node_name: str, param_name: str
) -> Tuple[Parameter, Optional[Script]]:
    """Process a single input parameter element.

    Args:
        inp: Input parameter XML element
        node_name: Name of the containing node
        param_name: Name of the parameter

    Returns:
        Tuple of (Parameter, Optional[Script])
    """
    # Check if it contains a script element
    script_elem = inp.find(XPATH_CAMUNDA_SCRIPT, BPMN_NS)
    if script_elem is not None:
        # Has script element - will be shown in scripts section
        return _process_script_element(node_name, param_name), None

    # Check if it has text content
    if inp.text:
        # Has text content - may be JEXL expression or simple value
        return _process_text_content(inp.text, node_name, param_name)

    # Empty or no content
    return _create_parameter(node_name, param_name, "", False), None


def _extract_input_parameters(
    root: _Element, id_to_name: Dict[str, str]
) -> Tuple[List[Parameter], List[Script]]:
    """Extract input parameters and their associated scripts.

    Args:
        root: Root element of the BPMN XML tree
        id_to_name: Mapping from element IDs to their names

    Returns:
        Tuple of (parameters, scripts) where:
        - parameters: List of Parameter instances
        - scripts: List of Script instances for JEXL expressions
    """
    parameters = []
    scripts = []

    for inp in root.findall(XPATH_CAMUNDA_INPUT_PARAMETER, BPMN_NS):
        node_name, param_name = _get_node_info(inp, id_to_name)

        # Process the parameter and check for associated script
        parameter, script = _process_single_input_parameter(
            inp, node_name, param_name
        )
        parameters.append(parameter)
        if script is not None:
            scripts.append(script)

    return parameters, scripts


def extract(context: BpmnContext) -> BpmnExtractResult:
    """Extract BPMN data from a BpmnContext.

    Args:
        context: BpmnContext containing parsed XML root and ID-to-name mapping

    Returns:
        BpmnExtractResult containing nodes, parameters, and scripts
    """
    root = context.root
    id_to_name = context.id_to_name

    # Extract nodes
    nodes = []
    nodes.extend(_extract_call_activities(root))
    nodes.extend(_extract_service_tasks(root))

    # Extract scripts and parameters
    scripts = _extract_script_elements(root, id_to_name)
    parameters, param_scripts = _extract_input_parameters(root, id_to_name)
    scripts.extend(param_scripts)

    return BpmnExtractResult(nodes, parameters, scripts)
