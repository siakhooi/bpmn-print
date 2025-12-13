# BPMN and Camunda namespace mappings for XML parsing
# These dictionaries map namespace prefixes to their official URIs.
# Used with lxml's findall() and find() methods to query elements.
# Note: These are XML namespace identifiers, not actual HTTP endpoints.
# The http:// URIs are defined by the BPMN/Camunda specifications and must
# match exactly.
BPMN_NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",  # NOSONAR
    "camunda": "http://camunda.org/schema/1.0/bpmn",  # NOSONAR
}

# Individual namespace URIs for direct reference
BPMN_NS_URI = BPMN_NS["bpmn"]
CAMUNDA_NS_URI = BPMN_NS["camunda"]

# XML attribute names used across BPMN parsing
ATTR_ID = "id"
ATTR_NAME = "name"
ATTR_SOURCE_REF = "sourceRef"
ATTR_TARGET_REF = "targetRef"
ATTR_CALLED_ELEMENT = "calledElement"

# XPath query patterns for BPMN elements
# These require the BPMN namespace mapping when used with findall()/find()
XPATH_ALL_WITH_ID = ".//*[@id]"
XPATH_START_EVENT = ".//bpmn:startEvent"
XPATH_END_EVENT = ".//bpmn:endEvent"
XPATH_TASK = ".//bpmn:task"
XPATH_SERVICE_TASK = ".//bpmn:serviceTask"
XPATH_CALL_ACTIVITY = ".//bpmn:callActivity"
XPATH_EXCLUSIVE_GATEWAY = ".//bpmn:exclusiveGateway"
XPATH_PARALLEL_GATEWAY = ".//bpmn:parallelGateway"
XPATH_SEQUENCE_FLOW = ".//bpmn:sequenceFlow"
XPATH_CONDITION_EXPRESSION = ".//bpmn:conditionExpression"

# XPath query patterns for Camunda extensions
XPATH_CAMUNDA_SCRIPT = ".//camunda:script"
XPATH_CAMUNDA_INPUT_PARAMETER = ".//camunda:inputParameter"
