from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

from lxml.etree import _Element

from .xml_utils import parse_bpmn_xml, build_id_to_name_mapping
from .xml_constants import (
    ATTR_ID, ATTR_NAME, ATTR_CALLED_ELEMENT,
    XPATH_CALL_ACTIVITY, XPATH_SERVICE_TASK,
    XPATH_CAMUNDA_SCRIPT, XPATH_CAMUNDA_INPUT_PARAMETER
)

# BPMN namespace constants
BPMN_NS = {
    "camunda": "http://camunda.org/schema/1.0/bpmn",
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
}
CAMUNDA_NS_URI = BPMN_NS["camunda"]
CAMUNDA_CLASS_ATTR = f'{{{CAMUNDA_NS_URI}}}class'

UNKNOWN_VALUE = 'unknown'
DEFAULT_SCRIPT_NAME = 'script'
DEFAULT_PARAM_NAME = 'inputParameter'
JEXL_SCRIPT_PLACEHOLDER = '[See JEXL Scripts]'

# JEXL expression pattern - matches both #{ } and ${ } style expressions
# Compiled at module level for efficiency
JEXL_PATTERN = re.compile(r'[#$]\{\s')

# Node type
NODE_TYPE_CALL_ACTIVITY = 'callActivity'
NODE_TYPE_SERVICE_TASK = 'serviceTask'


@dataclass
class Node:
    """Represents a BPMN node (callActivity or serviceTask)."""
    name: str
    type: str
    target: str

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.name, self.type, self.target))


@dataclass
class Parameter:
    """Represents an input parameter."""
    node_name: str
    param_name: str
    value: str
    has_script: bool

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((
            self.node_name, self.param_name, self.value, self.has_script
        ))


@dataclass
class Script:
    """Represents a JEXL script."""
    text: str
    node_name: str
    param_name: str

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.text, self.node_name, self.param_name))


@dataclass
class BpmnExtractResult:
    """Result of BPMN data extraction.

    Contains all nodes, parameters, and scripts extracted from a BPMN XML file.
    This dataclass supports tuple unpacking for backward compatibility:
        nodes, parameters, scripts = extract(xml_file)
    """
    nodes: List[Node]
    parameters: List[Parameter]
    scripts: List[Script]

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.nodes, self.parameters, self.scripts))


def find_parent_with_id(element: _Element) -> str:
    """Traverse up the tree to find the first ancestor with an
    'id' attribute
    """
    current = element
    while current is not None:
        if 'id' in current.attrib:
            return current.get('id')
        current = current.getparent()
    return UNKNOWN_VALUE


def _get_element_name(element: _Element, default: str = UNKNOWN_VALUE) -> str:
    """Get the name of an element, falling back to its ID or a default.

    Args:
        element: The XML element to get the name from
        default: Default value if neither name nor id exists

    Returns:
        The element's name, id, or default value
    """
    return element.get(ATTR_NAME, element.get(ATTR_ID, default))


def _is_jexl_expression(text: str) -> bool:
    """Check if text contains JEXL expression patterns.

    This function uses a compiled regex pattern to efficiently detect
    JEXL expressions that use either #{...} or ${...} syntax.

    Args:
        text: The text to check for JEXL patterns

    Returns:
        True if text contains JEXL expression markers (#{ or ${)
    """
    return JEXL_PATTERN.search(text) is not None


def _simplify_class_name(class_name: str) -> str:
    """Extract the simple class name from a fully qualified class name.

    Args:
        class_name: Fully qualified class name (e.g., 'com.example.MyClass')

    Returns:
        Simple class name (e.g., 'MyClass') or empty string
    """
    return class_name.rsplit('.', 1)[-1] if class_name else ''


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
    """Create a Parameter instance.

    Args:
        node_name: Name of the node this parameter belongs to
        param_name: Name of the parameter
        value: Parameter value (or placeholder if has_script is True)
        has_script: Whether this parameter has an associated script

    Returns:
        A Parameter instance
    """
    return Parameter(node_name, param_name, value, has_script)


def _process_script_element(
    node_name: str, param_name: str
) -> Tuple[Parameter, None]:
    """Process an input parameter that contains a script element.

    Args:
        node_name: Name of the node this parameter belongs to
        param_name: Name of the parameter

    Returns:
        Tuple of (Parameter, None). The second element is always None
        because standalone script elements are handled separately.
    """
    parameter = _create_parameter(
        node_name, param_name, JEXL_SCRIPT_PLACEHOLDER, True
    )
    return parameter, None


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
    """Create a Node from a callActivity XML element.

    Args:
        call_activity: XML element representing a callActivity

    Returns:
        Node instance with callActivity information
    """
    return Node(
        name=_get_element_name(call_activity),
        type=NODE_TYPE_CALL_ACTIVITY,
        target=call_activity.get(ATTR_CALLED_ELEMENT, '')
    )


def _extract_call_activities(root: _Element) -> List[Node]:
    """Extract all callActivity nodes from the BPMN XML.

    Args:
        root: Root element of the BPMN XML tree

    Returns:
        List of Node instances for all callActivity elements
    """
    return [
        _create_call_activity_node(call_activity)
        for call_activity in root.findall(XPATH_CALL_ACTIVITY, BPMN_NS)
    ]


def _create_service_task_node(service_task: _Element) -> Node:
    """Create a Node from a serviceTask XML element.

    Args:
        service_task: XML element representing a serviceTask

    Returns:
        Node instance with serviceTask information
    """
    class_name = service_task.get(CAMUNDA_CLASS_ATTR, '')
    return Node(
        name=_get_element_name(service_task),
        type=NODE_TYPE_SERVICE_TASK,
        target=_simplify_class_name(class_name)
    )


def _extract_service_tasks(root: _Element) -> List[Node]:
    """Extract all serviceTask nodes from the BPMN XML.

    Args:
        root: Root element of the BPMN XML tree

    Returns:
        List of Node instances for all serviceTask elements
    """
    return [
        _create_service_task_node(service_task)
        for service_task in root.findall(XPATH_SERVICE_TASK, BPMN_NS)
    ]


def _extract_script_elements(
    root: _Element, id_to_name: Dict[str, str]
) -> List[Script]:
    """Extract standalone script elements from the BPMN XML."""
    scripts = []
    for scr in root.findall(XPATH_CAMUNDA_SCRIPT, BPMN_NS):
        node_id = find_parent_with_id(scr)
        node_name = id_to_name.get(node_id, node_id)
        param_name = scr.getparent().get(ATTR_NAME, DEFAULT_SCRIPT_NAME)
        scripts.append(Script(scr.text or "", node_name, param_name))
    return scripts


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

        # Check if it contains a script element
        script_elem = inp.find(XPATH_CAMUNDA_SCRIPT, BPMN_NS)
        if script_elem is not None:
            # Has script element - will be shown in scripts section
            parameter, _ = _process_script_element(
                node_name, param_name
            )
            parameters.append(parameter)
        elif inp.text:
            # Has text content - may be JEXL expression or simple value
            parameter, script = _process_text_content(
                inp.text, node_name, param_name
            )
            parameters.append(parameter)
            if script is not None:
                scripts.append(script)
        else:
            # Empty or other
            parameter = _create_parameter(node_name, param_name, '', False)
            parameters.append(parameter)

    return parameters, scripts


def extract(xml_file: str) -> BpmnExtractResult:
    """Extract BPMN data from an XML file.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        BpmnExtractResult containing nodes, parameters, and scripts.
        Supports tuple unpacking: (nodes, parameters, scripts)

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid
    """
    root = parse_bpmn_xml(xml_file)

    # Build ID to name mapping
    id_to_name = build_id_to_name_mapping(root)

    # Extract nodes
    nodes = []
    nodes.extend(_extract_call_activities(root))
    nodes.extend(_extract_service_tasks(root))

    # Extract scripts and parameters
    scripts = _extract_script_elements(root, id_to_name)
    parameters, param_scripts = _extract_input_parameters(root, id_to_name)
    scripts.extend(param_scripts)

    return BpmnExtractResult(nodes, parameters, scripts)
