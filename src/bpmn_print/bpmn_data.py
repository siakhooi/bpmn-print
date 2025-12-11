from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from lxml import etree
from lxml.etree import _Element, XMLSyntaxError

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


def _simplify_class_name(class_name: str) -> str:
    """Extract the simple class name from a fully qualified class name.

    Args:
        class_name: Fully qualified class name (e.g., 'com.example.MyClass')

    Returns:
        Simple class name (e.g., 'MyClass') or empty string
    """
    return class_name.rsplit('.', 1)[-1] if class_name else ''


def _build_id_to_name_mapping(root: _Element) -> Dict[str, str]:
    """Build a mapping from element IDs to their names."""
    return {
        elem.get('id'): elem.get('name', elem.get('id'))
        for elem in root.findall(".//*[@id]")
    }


def _get_node_info(
    element: _Element, id_to_name: Dict[str, str]
) -> Tuple[str, str]:
    """Extract node name and parameter name from an element.

    Args:
        element: The XML element to extract info from
        id_to_name: Mapping from element IDs to their names

    Returns:
        Tuple of (node_name, param_name)
    """
    node_id = find_parent_with_id(element)
    node_name = id_to_name.get(node_id, node_id)
    return node_name, element.get('name', DEFAULT_PARAM_NAME)


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
    script_elem: _Element, node_name: str, param_name: str
) -> Tuple[Parameter, Optional[Script]]:
    """Process an input parameter that contains a script element.

    Args:
        script_elem: The script XML element
        node_name: Name of the node this parameter belongs to
        param_name: Name of the parameter

    Returns:
        Tuple of (Parameter, Script or None). Script is None because
        standalone script elements are handled separately.
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
        Tuple of (Parameter, Script or None). Script is included if
        the text is a JEXL expression.
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


def _extract_call_activities(root: _Element) -> List[Node]:
    """Extract all callActivity nodes from the BPMN XML."""
    return [
        Node(
            _get_element_name(call_activity),
            NODE_TYPE_CALL_ACTIVITY,
            call_activity.get('calledElement', '')
        )
        for call_activity in root.findall(".//bpmn:callActivity", BPMN_NS)
    ]


def _extract_service_tasks(root: _Element) -> List[Node]:
    """Extract all serviceTask nodes from the BPMN XML."""
    return [
        Node(
            _get_element_name(service_task),
            NODE_TYPE_SERVICE_TASK,
            _simplify_class_name(service_task.get(CAMUNDA_CLASS_ATTR, ''))
        )
        for service_task in root.findall(".//bpmn:serviceTask", BPMN_NS)
    ]


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
        node_name, param_name = _get_node_info(inp, id_to_name)

        # Check if it contains a script element
        script_elem = inp.find(".//camunda:script", BPMN_NS)
        if script_elem is not None:
            # Has script element - will be shown in scripts section
            parameter, _ = _process_script_element(
                script_elem, node_name, param_name
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
        FileNotFoundError: If the XML file does not exist
        XMLSyntaxError: If the XML file is malformed or invalid
        etree.XMLSyntaxError: If the XML cannot be parsed
    """
    try:
        tree = etree.parse(xml_file)
    except OSError as e:
        raise FileNotFoundError(
            f"BPMN file not found or cannot be read: {xml_file}"
        ) from e
    except XMLSyntaxError as e:
        raise XMLSyntaxError(
            f"Invalid XML syntax in BPMN file: {xml_file}"
        ) from e

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

    return BpmnExtractResult(nodes, parameters, scripts)
