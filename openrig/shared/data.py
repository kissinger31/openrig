"""Core functionality for data serialization using JSON or YAML."""
import os
import time
import pprint
import json
import yaml


class Data(object):

    """Core data object and functionality for data serialization. Contains getter and setter
    properties for "data" as well as methods to "save()" and "load()" JSON and YAML files.

    NODES AND ATTRIBUTES
    ####################
    The "Data" class and it's descendant classes assumes a paradigm of nodes and attrs. The
    principle data object is a dictionary. All dictionary entries are considered "nodes" unless
    they start with a period ("."). Data entries with a leading period are considered
    "attributes" of their parent entry.

    **Node With Attributes**
    In this example "node" has 1 child ("childNode") and 2 attributes ("attr1" and "attr2"). Any
    subsequent child entries are considered data blocks or categories unique to the type of data
    being serialized (point data, animation curves, deformer weights, etc.).

    *Dictionary*
    {"node":
        {".attr1": 0,
        ".attr2": 5,
        "dataBlock":
            {"1": 0.0,
            "2": 5.0,
            "3": 10.0,
            }
        }
    }

    STANDARD PROPERTIES
    ###################
    +----------+----------------------------------------------------------------------+
    | Property |  Description                                                         |
    +==========+======================================================================+
    | "data"   | Alias for the data attribute ("__data"). It is a getter and setter.  |
    +----------+----------------------------------------------------------------------+
    | "nodes"  | Returns top level node names found in data as a list.                |
    +----------+----------------------------------------------------------------------+
    | "attrs"  | Returns any root level attributes as a list.                         |
    +----------+----------------------------------------------------------------------+

    NODE AND ATTR METHODS
    #####################
    +----------------+----------------------------------------------------------------------+
    | Method         |  Description                                                         |
    +================+======================================================================+
    | "getNodeData"  | Returns the sub-dictionary of data for given top level node name.    |
    +----------------+----------------------------------------------------------------------+
    | "getNodeAttrs" | Returns attributes for given top level node as a list.               |
    +----------------+----------------------------------------------------------------------+
    """

    def __init__(self, data=None):
        """Initializes the "__data" attribute. Provided data is expected to be a dictionary for
        serialization in the JSON or YAML formats.

        :param data: a dictionary of information to be serialized.
        :type data: dict (expected)
        """
        self.__data = data

    def __repr__(self):
        return '<%s.%s object at %s>\n\n%s' % (self.__class__.__module__,
                                               self.__class__.__name__,
                                               hex(id(self)),
                                               pprint.pformat(self.data))

    @property
    def data(self):
        """Get data.

        :returns: data stored under the "__data" attribute.
        :rtype: any | dict (expected)
        """
        return self.__data

    @data.setter
    def data(self, data=None):
        """Set data.

        :param data: data to be serialized.
        :type data: any | dict (expected)
        """
        self.__data = data

    @property
    def nodes(self):
        """Returns node names found in data.

        :returns: list of node names
        :rtype: list
        """
        return [n for n in self.data.keys() if not n.startswith('.')]

    @property
    def attrs(self):
        """Returns any root level attributes found in data.

        :returns list of attribute names
        :rtype: list
        """
        return sorted([a for a in self.data.keys() if a.startswith('.')])

    def getNodeData(self, node):
        """Returns stored data for given node.

        :param node: node to get stored data for.
        :type node: str

        :returns: dictionary of stored data for node.
        :rtype: dict
        """
        if not node in self.data.keys():
            raise Exception('Node not found in data.')

        return self.data[node]

    def getNodeAttrs(self, node):
        """Returns stored attribute data (any entry starting with a period '.').

        :param node: node to get attributes for (None)
        :type node: str

        :returns: list of attributes found for node.
        :rtype: list
        """
        node = self.findNode()
        return sorted([a for a in self.data[node].keys() if a.startswith('.')])

    def findNode(self, node):
        """Returns the node name if it exists in "data".

        :param node: node name to find
        :type node: str

        :returns: node name
        :rtype: str
        """
        if node in self.data.keys():
            return node
        else:
            raise Exception('Node "%s" not found in data.' % node)

    def getNodes(self, nodes):
        """Returns a list of provided node names if they are found in "data".

        :param nodes: node names to look for
        :type node: str

        :returns: list of node names
        :rtype: list
        """
        if not isinstance(nodes, list): nodes = [nodes]
        foundNodes = list()
        for node in nodes:
            foundNodes.append(self.findNode(node))

        return foundNodes

    def save(self, filepath, file_format='json'):
        """Save data to file. Valid file formats are "json" and "yaml".

        :param filepath: full file path to save to (dir path and file name with extension)
        :type filepath: str

        :param file_format: file format ("json")
        :type file_format: str

        :returns: filepath
        :rtype: str
        """
        s = time.time()

        # get data
        data = self.data

        # get file directory
        filedir = str(os.path.dirname(filepath))
        os.path.isdir(filedir)
        if not os.path.isdir(filedir):
            os.makedirs(filedir)

        # save file
        if file_format == 'json':
            with open(filepath, 'w') as stream:
                json.dump(data, stream, indent=4)
        elif file_format == 'yaml':
            with open(filepath, 'w') as stream:
                yaml.safe_dump(data, stream, default_flow_style=False, indent=4, width=2000)
        else:
            raise Exception('Provided file format "%s" not supported.' % file_format)

        # time
        e = time.time()
        print 'DATA: File saved in  %s seconds:' % round(e - s, 2)
        print filepath + '\n'
        return filepath

    def load(self, filepath):
        """Load data from file.

        :param filepath: file path
        :type filepath: str

        :returns: data dictionary of nodes and attributes
        :rtype: dict
        """
        # check file
        if not os.path.exists(filepath):
            raise Exception('File not found: \n\t %s' % filepath)

        s = time.time()

        # load file
        data = dict()
        with open(filepath, 'r') as stream:
            stream = stream.read()
            if stream.startswith('{'):
                try:
                    data = json.loads(stream)
                    def string_keys(dictionary):
                        for k, v in dictionary.iteritems():
                            if isinstance(k, unicode):
                                dictionary[str(k)] = dictionary.pop(k, None)
                                if isinstance(v, dict):
                                    string_keys(dictionary[k])
                    # Todo: is this necessary?
                    # string_keys(data)
                except:
                    print('File not loaded.')
            else:
                try:
                    data = yaml.load(stream)
                except yaml.YAMLError as exc:
                    print(exc)
        self.data = data

        # time
        e = time.time()
        print 'DATA: File loaded in  %s seconds.' % round(e - s, 2)
        print filepath + '\n'
