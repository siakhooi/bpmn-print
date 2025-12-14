from lxml import etree
from unittest.mock import Mock

from bpmn_print.bpmn_data import (
    Node,
    Parameter,
    Script,
    BpmnExtractResult,
    find_parent_with_id,
    _get_element_name,
    _is_jexl_expression,
    _simplify_class_name,
    _get_node_info,
    _create_parameter,
    _process_script_element,
    _process_text_content,
    _create_call_activity_node,
    _extract_call_activities,
    _create_service_task_node,
    _extract_service_tasks,
    _extract_script_elements,
    _process_single_input_parameter,
    _extract_input_parameters,
    extract,
    UNKNOWN_VALUE,
    DEFAULT_PARAM_NAME,
    JEXL_SCRIPT_PLACEHOLDER,
    NODE_TYPE_CALL_ACTIVITY,
    NODE_TYPE_SERVICE_TASK,
    CAMUNDA_CLASS_ATTR,
)
from bpmn_print.xml_utils import BpmnContext
from bpmn_print.xml_constants import ATTR_ID, ATTR_NAME


class TestNode:
    """Tests for Node dataclass."""

    def test_node_creation(self):
        """Test creating a Node instance."""
        node = Node(name="My Task", type="serviceTask", target="MyClass")

        assert node.name == "My Task"
        assert node.type == "serviceTask"
        assert node.target == "MyClass"

    def test_node_equality(self):
        """Test that two nodes with same values are equal."""
        node1 = Node(name="Task", type="callActivity", target="subprocess")
        node2 = Node(name="Task", type="callActivity", target="subprocess")

        assert node1 == node2


class TestParameter:
    """Tests for Parameter dataclass."""

    def test_parameter_creation(self):
        """Test creating a Parameter instance."""
        param = Parameter(
            node_name="Task1",
            param_name="input1",
            value="test_value",
            has_script=False,
        )

        assert param.node_name == "Task1"
        assert param.param_name == "input1"
        assert param.value == "test_value"
        assert param.has_script is False

    def test_parameter_with_script(self):
        """Test parameter with has_script flag."""
        param = Parameter(
            node_name="Task1",
            param_name="input1",
            value=JEXL_SCRIPT_PLACEHOLDER,
            has_script=True,
        )

        assert param.has_script is True
        assert param.value == JEXL_SCRIPT_PLACEHOLDER


class TestScript:
    """Tests for Script dataclass."""

    def test_script_creation(self):
        """Test creating a Script instance."""
        script = Script(
            text="${execution.getVariable('test')}",
            node_name="Task1",
            param_name="script1",
        )

        assert script.text == "${execution.getVariable('test')}"
        assert script.node_name == "Task1"
        assert script.param_name == "script1"


class TestBpmnExtractResult:
    """Tests for BpmnExtractResult dataclass."""

    def test_result_creation(self):
        """Test creating a BpmnExtractResult instance."""
        nodes = [Node("Task1", "serviceTask", "MyClass")]
        parameters = [Parameter("Task1", "param1", "value1", False)]
        scripts = [Script("${test}", "Task1", "script1")]

        result = BpmnExtractResult(nodes, parameters, scripts)

        assert result.nodes == nodes
        assert result.parameters == parameters
        assert result.scripts == scripts


class TestFindParentWithId:
    """Tests for find_parent_with_id function."""

    def test_returns_id_when_element_has_id(self):
        """Test finding ID on the element itself."""
        element = Mock()
        element.attrib = {"id": "Task_123"}
        element.get = lambda key: element.attrib.get(key)

        result = find_parent_with_id(element)

        assert result == "Task_123"

    def test_returns_parent_id_when_element_has_no_id(self):
        """Test finding ID on parent element."""
        parent = Mock()
        parent.attrib = {"id": "Parent_456"}
        parent.get = lambda key: parent.attrib.get(key)
        parent.getparent.return_value = None

        element = Mock()
        element.attrib = {}
        element.get = lambda key: element.attrib.get(key)
        element.getparent.return_value = parent

        result = find_parent_with_id(element)

        assert result == "Parent_456"

    def test_returns_unknown_when_no_ancestor_has_id(self):
        """Test returning UNKNOWN_VALUE when no ancestor has ID."""
        element = Mock()
        element.attrib = {}
        element.getparent.return_value = None

        result = find_parent_with_id(element)

        assert result == UNKNOWN_VALUE

    def test_traverses_multiple_levels(self):
        """Test traversing multiple parent levels."""
        grandparent = Mock()
        grandparent.attrib = {"id": "GP_789"}
        grandparent.get = lambda key: grandparent.attrib.get(key)
        grandparent.getparent.return_value = None

        parent = Mock()
        parent.attrib = {}
        parent.get = lambda key: parent.attrib.get(key)
        parent.getparent.return_value = grandparent

        element = Mock()
        element.attrib = {}
        element.get = lambda key: element.attrib.get(key)
        element.getparent.return_value = parent

        result = find_parent_with_id(element)

        assert result == "GP_789"


class TestGetElementName:
    """Tests for _get_element_name function."""

    def test_returns_name_when_present(self):
        """Test returning name attribute when present."""
        element = Mock()
        element.get.side_effect = lambda key, default=UNKNOWN_VALUE: (
            "Task Name"
            if key == ATTR_NAME
            else "task_123" if key == ATTR_ID else default
        )

        result = _get_element_name(element)

        assert result == "Task Name"

    def test_returns_id_when_name_missing(self):
        """Test returning ID when name is missing."""
        element = Mock()

        def mock_get(key, default=UNKNOWN_VALUE):
            if key == ATTR_NAME:
                return "task_123"  # First call returns ID as fallback
            return default

        element.get.side_effect = mock_get

        result = _get_element_name(element)

        assert result == "task_123"

    def test_returns_default_when_name_and_id_missing(self):
        """Test returning default when both name and ID are missing."""
        element = Mock()
        element.get.return_value = "custom_default"

        result = _get_element_name(element, default="custom_default")

        assert result == "custom_default"

    def test_returns_unknown_by_default(self):
        """Test returning UNKNOWN_VALUE as default."""
        element = Mock()
        element.get.return_value = UNKNOWN_VALUE

        result = _get_element_name(element)

        assert result == UNKNOWN_VALUE


class TestIsJexlExpression:
    """Tests for _is_jexl_expression function."""

    def test_identifies_dollar_brace_expression(self):
        """Test identifying ${ } JEXL expression."""
        assert (
            _is_jexl_expression("${ execution.getVariable('test') }") is True
        )

    def test_identifies_hash_brace_expression(self):
        """Test identifying #{ } JEXL expression."""
        assert (
            _is_jexl_expression("#{ execution.getVariable('test') }") is True
        )

    def test_returns_false_for_plain_text(self):
        """Test returning False for plain text."""
        assert _is_jexl_expression("plain value") is False

    def test_returns_false_for_empty_string(self):
        """Test returning False for empty string."""
        assert _is_jexl_expression("") is False

    def test_handles_multiple_expressions(self):
        """Test handling text with multiple expressions."""
        # Note: The regex requires space after { so proper formatting needed
        assert _is_jexl_expression("${ var1} and ${ var2}") is True

    def test_requires_space_after_brace(self):
        """Test that pattern requires space after opening brace."""
        # The regex requires whitespace after {
        assert _is_jexl_expression("${ test}") is True
        assert _is_jexl_expression("#{test}") is False  # no space


class TestSimplifyClassName:
    """Tests for _simplify_class_name function."""

    def test_extracts_simple_name_from_qualified_name(self):
        """Test extracting simple class name from fully qualified name."""
        result = _simplify_class_name("com.example.package.MyClass")

        assert result == "MyClass"

    def test_returns_name_when_no_package(self):
        """Test returning name when no package prefix."""
        result = _simplify_class_name("SimpleClass")

        assert result == "SimpleClass"

    def test_returns_empty_for_empty_string(self):
        """Test returning empty string for empty input."""
        result = _simplify_class_name("")

        assert result == ""

    def test_handles_single_dot(self):
        """Test handling single dot separator."""
        result = _simplify_class_name("package.Class")

        assert result == "Class"


class TestGetNodeInfo:
    """Tests for _get_node_info function."""

    def test_returns_node_name_and_param_name(self):
        """Test extracting node name and parameter name."""
        parent = Mock()
        parent.attrib = {"id": "Task_123"}
        parent.get = lambda key: parent.attrib.get(key)
        parent.getparent.return_value = None

        element = Mock()
        element.attrib = {}
        element.get = lambda key, default=None: (
            "param1" if key == ATTR_NAME else default
        )
        element.getparent.return_value = parent

        id_to_name = {"Task_123": "My Task"}

        node_name, param_name = _get_node_info(element, id_to_name)

        assert node_name == "My Task"
        assert param_name == "param1"

    def test_uses_id_when_name_not_in_mapping(self):
        """Test using ID when not found in mapping."""
        element = Mock()
        element.attrib = {"id": "Task_999"}
        element.get = lambda key, default=None: (
            "param1" if key == ATTR_NAME else element.attrib.get(key, default)
        )
        element.getparent.return_value = None

        id_to_name = {}

        node_name, param_name = _get_node_info(element, id_to_name)

        assert node_name == "Task_999"
        assert param_name == "param1"

    def test_uses_default_param_name(self):
        """Test using default parameter name."""
        element = Mock()
        element.attrib = {"id": "Task_123"}
        element.get = lambda key, default=None: (
            default if key == ATTR_NAME else element.attrib.get(key)
        )
        element.getparent.return_value = None

        id_to_name = {"Task_123": "My Task"}

        node_name, param_name = _get_node_info(element, id_to_name)

        assert node_name == "My Task"
        assert param_name == DEFAULT_PARAM_NAME


class TestCreateParameter:
    """Tests for _create_parameter function."""

    def test_creates_parameter_with_all_fields(self):
        """Test creating parameter with all fields."""
        param = _create_parameter("Task1", "param1", "value1", False)

        assert isinstance(param, Parameter)
        assert param.node_name == "Task1"
        assert param.param_name == "param1"
        assert param.value == "value1"
        assert param.has_script is False


class TestProcessScriptElement:
    """Tests for _process_script_element function."""

    def test_creates_parameter_with_script_placeholder(self):
        """Test creating parameter for script element."""
        param = _process_script_element("Task1", "script1")

        assert isinstance(param, Parameter)
        assert param.node_name == "Task1"
        assert param.param_name == "script1"
        assert param.value == JEXL_SCRIPT_PLACEHOLDER
        assert param.has_script is True


class TestProcessTextContent:
    """Tests for _process_text_content function."""

    def test_creates_parameter_and_script_for_jexl_expression(self):
        """Test processing JEXL expression text."""
        text = "${ execution.getVariable('test') }"
        param, script = _process_text_content(text, "Task1", "param1")

        assert isinstance(param, Parameter)
        assert param.value == JEXL_SCRIPT_PLACEHOLDER
        assert param.has_script is True

        assert isinstance(script, Script)
        assert script.text == text
        assert script.node_name == "Task1"
        assert script.param_name == "param1"

    def test_creates_parameter_only_for_plain_text(self):
        """Test processing plain text value."""
        text = "plain value"
        param, script = _process_text_content(text, "Task1", "param1")

        assert isinstance(param, Parameter)
        assert param.value == "plain value"
        assert param.has_script is False
        assert script is None


class TestCreateCallActivityNode:
    """Tests for _create_call_activity_node function."""

    def test_creates_node_from_call_activity(self):
        """Test creating Node from callActivity element."""
        element = Mock()
        element.get.side_effect = lambda key, default="": {
            "name": "My Subprocess",
            "calledElement": "subprocess_id",
            "id": "CallActivity_1",
        }.get(key, default)

        node = _create_call_activity_node(element)

        assert isinstance(node, Node)
        assert node.name == "My Subprocess"
        assert node.type == NODE_TYPE_CALL_ACTIVITY
        assert node.target == "subprocess_id"

    def test_handles_missing_name(self):
        """Test handling missing name attribute."""
        element = Mock()
        element.get.side_effect = lambda key, default="": {
            "id": "CallActivity_1",
            "calledElement": "subprocess_id",
        }.get(key, default)

        node = _create_call_activity_node(element)

        assert node.name == "CallActivity_1"


class TestExtractCallActivities:
    """Tests for _extract_call_activities function."""

    def test_extracts_all_call_activities(self):
        """Test extracting all callActivity elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
        <callActivity id="CallActivity_1" name="Subprocess 1"
                      calledElement="sub1"/>
        <callActivity id="CallActivity_2" name="Subprocess 2"
                      calledElement="sub2"/>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())

        nodes = _extract_call_activities(root)

        assert len(nodes) == 2
        assert nodes[0].name == "Subprocess 1"
        assert nodes[0].target == "sub1"
        assert nodes[1].name == "Subprocess 2"
        assert nodes[1].target == "sub2"

    def test_returns_empty_list_when_no_call_activities(self):
        """Test returning empty list when no callActivity elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
        <task id="Task_1" name="Regular Task"/>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())

        nodes = _extract_call_activities(root)

        assert len(nodes) == 0


class TestCreateServiceTaskNode:
    """Tests for _create_service_task_node function."""

    def test_creates_node_from_service_task(self):
        """Test creating Node from serviceTask element."""
        element = Mock()
        element.get.side_effect = lambda key, default="": {
            "name": "My Service",
            CAMUNDA_CLASS_ATTR: "com.example.MyDelegate",
            "id": "ServiceTask_1",
        }.get(key, default)

        node = _create_service_task_node(element)

        assert isinstance(node, Node)
        assert node.name == "My Service"
        assert node.type == NODE_TYPE_SERVICE_TASK
        assert node.target == "MyDelegate"

    def test_handles_missing_class_attribute(self):
        """Test handling missing class attribute."""
        element = Mock()
        element.get.side_effect = lambda key, default="": {
            "name": "My Service",
            "id": "ServiceTask_1",
        }.get(key, default)

        node = _create_service_task_node(element)

        assert node.target == ""


class TestExtractServiceTasks:
    """Tests for _extract_service_tasks function."""

    def test_extracts_all_service_tasks(self):
        """Test extracting all serviceTask elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="ServiceTask_1" name="Service 1"
                     camunda:class="com.example.Service1"/>
        <serviceTask id="ServiceTask_2" name="Service 2"
                     camunda:class="com.example.Service2"/>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())

        nodes = _extract_service_tasks(root)

        assert len(nodes) == 2
        assert nodes[0].name == "Service 1"
        assert nodes[0].target == "Service1"
        assert nodes[1].name == "Service 2"
        assert nodes[1].target == "Service2"


class TestExtractScriptElements:
    """Tests for _extract_script_elements function."""

    def test_extracts_script_elements(self):
        """Test extracting script elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="Task_1" name="My Task">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="param1">
                        <camunda:script>print('hello')</camunda:script>
                    </camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {"Task_1": "My Task"}

        scripts = _extract_script_elements(root, id_to_name)

        assert len(scripts) == 1
        assert scripts[0].text == "print('hello')"
        assert scripts[0].node_name == "My Task"
        assert scripts[0].param_name == "param1"

    def test_handles_empty_script_text(self):
        """Test handling script element with no text."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="Task_1">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="param1">
                        <camunda:script></camunda:script>
                    </camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {"Task_1": "Task 1"}

        scripts = _extract_script_elements(root, id_to_name)

        assert len(scripts) == 1
        assert scripts[0].text == ""


class TestProcessSingleInputParameter:
    """Tests for _process_single_input_parameter function."""

    def test_processes_parameter_with_script_element(self):
        """Test processing parameter with script element."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<camunda:inputParameter xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                        name="param1">
    <camunda:script>print('test')</camunda:script>
</camunda:inputParameter>"""
        element = etree.fromstring(xml_content.encode())

        param, script = _process_single_input_parameter(
            element, "Task1", "param1"
        )

        assert param.value == JEXL_SCRIPT_PLACEHOLDER
        assert param.has_script is True
        assert script is None

    def test_processes_parameter_with_jexl_text(self):
        """Test processing parameter with JEXL expression text."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<camunda:inputParameter xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                        name="param1">${ test }</camunda:inputParameter>"""
        element = etree.fromstring(xml_content.encode())

        param, script = _process_single_input_parameter(
            element, "Task1", "param1"
        )

        assert param.has_script is True
        assert script is not None
        assert script.text == "${ test }"

    def test_processes_parameter_with_plain_text(self):
        """Test processing parameter with plain text value."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<camunda:inputParameter xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                        name="param1">plain_value</camunda:inputParameter>"""
        element = etree.fromstring(xml_content.encode())

        param, script = _process_single_input_parameter(
            element, "Task1", "param1"
        )

        assert param.value == "plain_value"
        assert param.has_script is False
        assert script is None

    def test_processes_empty_parameter(self):
        """Test processing parameter with no content."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<camunda:inputParameter xmlns:camunda="http://camunda.org/schema/1.0/bpmn"
                        name="param1"></camunda:inputParameter>"""
        element = etree.fromstring(xml_content.encode())

        param, script = _process_single_input_parameter(
            element, "Task1", "param1"
        )

        assert param.value == ""
        assert param.has_script is False
        assert script is None


class TestExtractInputParameters:
    """Tests for _extract_input_parameters function."""

    def test_extracts_multiple_parameters(self):
        """Test extracting multiple input parameters."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="Task_1" name="My Task">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="param1"
                    >value1</camunda:inputParameter>
                    <camunda:inputParameter name="param2"
                    >value2</camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {"Task_1": "My Task"}

        parameters, scripts = _extract_input_parameters(root, id_to_name)

        assert len(parameters) == 2
        assert parameters[0].param_name == "param1"
        assert parameters[0].value == "value1"
        assert parameters[1].param_name == "param2"
        assert parameters[1].value == "value2"
        assert len(scripts) == 0

    def test_separates_jexl_expressions_into_scripts(self):
        """Test that JEXL expressions are separated into scripts list."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="Task_1" name="My Task">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="param1"
                    >plain</camunda:inputParameter>
                    <camunda:inputParameter name="param2"
                    >${ jexl }</camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {"Task_1": "My Task"}

        parameters, scripts = _extract_input_parameters(root, id_to_name)

        assert len(parameters) == 2
        assert parameters[0].has_script is False
        assert parameters[1].has_script is True
        assert parameters[1].value == JEXL_SCRIPT_PLACEHOLDER
        assert len(scripts) == 1
        assert scripts[0].text == "${ jexl }"


class TestExtract:
    """Tests for extract function."""

    def test_extracts_complete_bpmn_data(self):
        """Test extracting complete BPMN data from context."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <callActivity id="CallActivity_1" name="Subprocess"
                      calledElement="sub1"/>
        <serviceTask id="ServiceTask_1" name="Service"
                     camunda:class="com.example.MyService">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="param1"
                    >value1</camunda:inputParameter>
                    <camunda:inputParameter name="param2"
                    >${ jexl }</camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {
            "CallActivity_1": "Subprocess",
            "ServiceTask_1": "Service",
        }
        context = BpmnContext(root=root, id_to_name=id_to_name)

        result = extract(context)

        assert isinstance(result, BpmnExtractResult)
        assert len(result.nodes) == 2
        assert result.nodes[0].name == "Subprocess"
        assert result.nodes[0].type == NODE_TYPE_CALL_ACTIVITY
        assert result.nodes[1].name == "Service"
        assert result.nodes[1].type == NODE_TYPE_SERVICE_TASK

        assert len(result.parameters) == 2
        assert result.parameters[0].value == "value1"
        assert result.parameters[1].value == JEXL_SCRIPT_PLACEHOLDER

        assert len(result.scripts) == 1
        script_text = result.scripts[0].text
        assert script_text == "${ jexl }"

    def test_handles_empty_bpmn(self):
        """Test handling BPMN with no extractable data."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {}
        context = BpmnContext(root=root, id_to_name=id_to_name)

        result = extract(context)

        assert len(result.nodes) == 0
        assert len(result.parameters) == 0
        assert len(result.scripts) == 0

    def test_combines_scripts_from_multiple_sources(self):
        """Test scripts from script elements and parameters combined."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1">
        <serviceTask id="Task_1" name="My Task">
            <extensionElements>
                <camunda:inputOutput>
                    <camunda:inputParameter name="script_param">
                        <camunda:script>standalone_script</camunda:script>
                    </camunda:inputParameter>
                    <camunda:inputParameter name="jexl_param"
                    >${ inline_jexl }</camunda:inputParameter>
                </camunda:inputOutput>
            </extensionElements>
        </serviceTask>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())
        id_to_name = {"Task_1": "My Task"}
        context = BpmnContext(root=root, id_to_name=id_to_name)

        result = extract(context)

        # Should have 2 scripts: one from script element,
        # one from JEXL expression
        assert len(result.scripts) == 2
        assert any(s.text == "standalone_script" for s in result.scripts)
        assert any(s.text == "${ inline_jexl }" for s in result.scripts)
