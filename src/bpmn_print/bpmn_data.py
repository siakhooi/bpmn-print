from dataclasses import dataclass
from typing import Dict, List, Tuple

from lxml import etree
from lxml.etree import _Element

# BPMN namespace constants
BPMN_NS = {
    "camunda": "http://camunda.org/schema/1.0/bpmn",
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
}
CAMUNDA_CLASS_ATTR = '{http://camunda.org/schema/1.0/bpmn}class'

UNKNOWN_VALUE = 'unknown'
DEFAULT_SCRIPT_NAME = 'script'
DEFAULT_PARAM_NAME = 'inputParameter'
JEXL_SCRIPT_PLACEHOLDER = '[See JEXL Scripts]'

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
    return element.get('name', element.get('id', default))


def _is_jexl_expression(text: str) -> bool:
    """Check if text contains JEXL expression patterns.

    Args:
        text: The text to check for JEXL patterns

    Returns:
        True if text contains JEXL expression markers (#{ or ${)
    """
    JEXL_PATTERN_HASH = '#{ '
    JEXL_PATTERN_DOLLAR = '${ '

    return JEXL_PATTERN_HASH in text or JEXL_PATTERN_DOLLAR in text


def _build_id_to_name_mapping(root: _Element) -> Dict[str, str]:
    """Build a mapping from element IDs to their names."""
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get('id')
        elem_name = elem.get('name', elem_id)
        id_to_name[elem_id] = elem_name
    return id_to_name


def _extract_call_activities(root: _Element) -> List[Node]:
    """Extract all callActivity nodes from the BPMN XML."""
    nodes = []
    for call_activity in root.findall(".//bpmn:callActivity", BPMN_NS):
        node_name = _get_element_name(call_activity)
        called_element = call_activity.get('calledElement', '')
        nodes.append(Node(node_name, NODE_TYPE_CALL_ACTIVITY, called_element))
    return nodes


def _extract_service_tasks(root: _Element) -> List[Node]:
    """Extract all serviceTask nodes from the BPMN XML."""
    nodes = []
    for service_task in root.findall(".//bpmn:serviceTask", BPMN_NS):
        node_name = _get_element_name(service_task)
        class_name = service_task.get(CAMUNDA_CLASS_ATTR, '')
        # Simplify class name - show only the last part
        simple_class = class_name.rsplit('.', 1)[-1] if class_name else ''
        nodes.append(Node(node_name, NODE_TYPE_SERVICE_TASK, simple_class))
    return nodes


def _extract_script_elements(
    root: _Element, id_to_name: Dict[str, str]
) -> List[Script]:
    """Extract standalone script elements from the BPMN XML."""
    scripts = []
    for scr in root.findall(".//camunda:script", BPMN_NS):
        node_id = find_parent_with_id(scr)
        node_name = id_to_name.get(node_id, node_id)
        param_name = scr.getparent().get('name', DEFAULT_SCRIPT_NAME)
        scripts.append(Script(scr.text or "", node_name, param_name))
    return scripts


def _extract_input_parameters(
    root: _Element, id_to_name: Dict[str, str]
) -> Tuple[List[Parameter], List[Script]]:
    """Extract input parameters and their associated scripts.

    Returns:
        tuple: (parameters, scripts) lists
    """
    parameters = []
    scripts = []

    for inp in root.findall(".//camunda:inputParameter", BPMN_NS):
        node_id = find_parent_with_id(inp)
        node_name = id_to_name.get(node_id, node_id)
        param_name = inp.get('name', DEFAULT_PARAM_NAME)

        # Check if it contains a script element
        script_elem = inp.find(".//camunda:script", BPMN_NS)
        if script_elem is not None:
            # Has script - will be shown in scripts section
            parameters.append(
                Parameter(node_name, param_name, JEXL_SCRIPT_PLACEHOLDER, True)
            )
        elif inp.text:
            # Has text content
            if _is_jexl_expression(inp.text):
                # JEXL expression - add to scripts
                scripts.append(Script(inp.text, node_name, param_name))
                parameters.append(
                    Parameter(
                        node_name, param_name, JEXL_SCRIPT_PLACEHOLDER, True
                    )
                )
            else:
                # Simple value
                parameters.append(
                    Parameter(node_name, param_name, inp.text, False)
                )
        else:
            # Empty or other
            parameters.append(Parameter(node_name, param_name, '', False))

    return parameters, scripts


def extract(xml_file: str) -> Tuple[List[Node], List[Parameter], List[Script]]:
    """Extract BPMN data from an XML file.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        tuple: (nodes, parameters, scripts) containing extracted data
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Build ID to name mapping
    id_to_name = _build_id_to_name_mapping(root)

    # Extract nodes
    nodes = []
    nodes.extend(_extract_call_activities(root))
    nodes.extend(_extract_service_tasks(root))

    # Extract scripts and parameters
    scripts = _extract_script_elements(root, id_to_name)
    parameters, param_scripts = _extract_input_parameters(root, id_to_name)
    scripts.extend(param_scripts)

    return nodes, parameters, scripts
