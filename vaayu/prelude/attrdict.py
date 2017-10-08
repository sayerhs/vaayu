# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors,bad-continuation,signature-differs,no-else-return

"""\
Attribute Dictionary
--------------------

"""

__all__ = ["AttrDict"]

from abc import ABCMeta
from collections import OrderedDict, MutableMapping, Mapping
import json
import six
try:
    import ruyamel_yaml as yaml
except ImportError:
    import yaml
import numpy as np

def _merge(this, that):
    """Recursive merge from *that* mapping to *this* mapping

    A utility function to recursively merge entries. New entries are added, and
    existing entries are updated.

    Args:
        this (dict): Mapping that is updated
        that (dict): Mapping to be merged. Unmodified within the function
    """
    this_keys = frozenset(this)
    that_keys = frozenset(that)

    # Items only in 'that' dict
    for k in (that_keys - this_keys):
        this[k] = that[k]

    for k in (this_keys & that_keys):
        vorig = this[k]
        vother = that[k]

        if (isinstance(vorig, Mapping) and
            isinstance(vother, Mapping) and
            (id(vorig) != id(vother))):
            _merge(vorig, vother)
        else:
            this[k] = vother

def merge(a, b, *args):
    """Recursively merge mappings and return consolidated dict.

    Accepts a variable number of dictionary mappings and returns a new
    dictionary that contains the merged entries from all dictionaries. Note
    that the update occurs left to right, i.e., entries from later dictionaries
    overwrite entries from preceeding ones.

    Returns:
        dict: The consolidated map
    """
    out = a.__class__()
    _merge(out, a)
    _merge(out, b)

    for c in args:
        _merge(out, c)

    return out

def gen_yaml_decoder(cls):
    """Generate a custom YAML decoder with non-default mapping class

    Args:
        cls: Class used for mapping
    """
    def attrdict_constructor(loader, node):
        """Custom constructor for AttrDict"""
        return cls(loader.construct_pairs(node))

    class AttrDictYAMLLoader(yaml.Loader):
        """Custom YAML loader for AttrDict data"""

        def __init__(self, *args, **kwargs):
            yaml.Loader.__init__(self, *args, **kwargs)
            self.add_constructor(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                attrdict_constructor)

    return AttrDictYAMLLoader

def gen_yaml_encoder(cls):
    """Generate a custom YAML dumper for AttrDict and subclasses.

    Args:
        cls: Class used for mappping
    """
    def attrdict_representer(dumper, data):
        """Convert AttrDict to YAML dictionary"""
        return dumper.represent_dict(list(data.items()))

    def numpy_representer(dumper, data):
        """Converty numpy array to YAML list"""
        return dumper.represent_list(data.tolist())

    def numpy_scalar_representer(dumper, data):
        """Format 64-bit numpy data properly"""
        if isinstance(data, np.int64):
            return dumper.represent_int(int(data))
        else:
            return dumper.represent_float(float(data))


    class AttrDictYAMLDumper(yaml.Dumper):
        """Custom YAML dumper for AttrDict data"""

        def __init__(self, *args, **kwargs):
            yaml.Dumper.__init__(self, *args, **kwargs)
            self.add_representer(cls,
                                 attrdict_representer)
            self.add_representer(np.ndarray,
                                 numpy_representer)
            self.add_representer(np.int64,
                                 numpy_scalar_representer)
            self.add_representer(np.float64,
                                 numpy_scalar_representer)

        def represent_data(self, data):
            if isinstance(data, np.ndarray):
                return self.represent_list(data.tolist())
            else:
                return super(AttrDictYAMLDumper, self).represent_data(data)

    return AttrDictYAMLDumper

class AttrDictMeta(ABCMeta):
    """Custom YAML/JSON loader/dumper registration.

    Enable custom registration of YAML/JSON readers and writers before the
    class creation.
    """

    def __new__(mcls, name, bases, cdict):
        yload = cdict.pop("yaml_loader", None)
        ydump = cdict.pop("yaml_dumper", None)
        cls = super(AttrDictMeta, mcls).__new__(mcls, name, bases, cdict)
        cls.yaml_loader = yload or gen_yaml_decoder(cls)
        cls.yaml_dumper = ydump or gen_yaml_encoder(cls)
        return cls

@six.add_metaclass(AttrDictMeta)
class AttrDict(OrderedDict, MutableMapping):
    """Attribute Dictionary

    A dictionary mapping data structure that allows both key and attribute
    access. The mapping has the following properties:

      #. Preserves ordering of members as initialized (subclassed from
         OrderedDict).

      #. Key and attribute access. Attribute access is limited to keys that are
         valid python variable names.

      #. Import/export from JSON and YAML formats.
    """

    @classmethod
    def from_yaml(cls, stream):
        """Initialize mapping from a YAML string.

        Args:
            stream: A string or valid file handle

        Returns:
            AttrDict: YAML data as a python object
        """
        return cls(yaml.load(stream, Loader=cls.yaml_loader))

    @classmethod
    def load_yaml(cls, filename):
        """Load a YAML file

        Args:
            filename (str): Absolute path to YAML file

        Returns:
            AttrDict: YAML data as python object
        """
        with open(filename, 'r') as fh:
            return cls.from_yaml(fh)

    @classmethod
    def from_json(cls, stream):
        """Initialize mapping from a JSON string/stream"""
        if isinstance(stream, six.string_types):
            obj = json.loads(stream, object_pairs_hook=cls)
        else:
            obj = json.load(stream, object_pairs_hook=cls)
        return obj

    @classmethod
    def load_json(cls, filename):
        """Initialize dictionary from JSON input file

        Args:
            filename (path): Absolute path to the JSON file
        """
        with open(filename, 'r') as fh:
            return cls.from_json(fh)

    def _getattr(self, key):
        return super(AttrDict, self).__getattribute__(key)

    def _setattr(self, key, value):
        super(AttrDict, self).__setattr__(key, value)

    def __setitem__(self, key, value):
        if (isinstance(value, Mapping) and
            not isinstance(value, AttrDict)):
            out = self.__class__()
            _merge(out, value)
            super(AttrDict, self).__setitem__(key, out)
        else:
            super(AttrDict, self).__setitem__(key, value)

    def __setattr__(self, key, value):
        # Workaround for Python 2.7 OrderedDict
        if not key.startswith('_OrderedDict'):
            self[key] = value
        else:
            super(AttrDict, self).__setattr__(key, value)

    def __getattr__(self, key):
        if key not in self:
            raise AttributeError("No attribute named "+key)
        else:
            return self[key]

    def merge(self, *args):
        """Recursively update dictionary

        Merge entries from maps provided such that new entries are added and
        existing entries are updated.
        """
        for other in args:
            _merge(self, other)

    def to_yaml(self, stream=None, default_flow_style=False, **kwargs):
        """Convert mapping to YAML format.

        Args:
            stream (file): A file handle where YAML is output

            default_flow_style (bool):
                - False - pretty printing
                - True  - No pretty printing
        """
        return yaml.dump(self, stream=stream,
                         Dumper=self.__class__.yaml_dumper,
                         default_flow_style=default_flow_style,
                         **kwargs)

    def to_json(self, stream=None, indent=2, **kwargs):
        """Convert mapping to JSON format

        Args:
            stream (file): A file handle for output
            indent (int): Default indentation (use None for compressed)

        Returns:
            str or None: If stream is a file, returns None.
                Otherwise, returns the JSON structure as string
        """
        if stream:
            json.dump(self, stream, indent=indent, **kwargs)
        else:
            return json.dumps(self, indent=indent, **kwargs)

    def walk(self, _node=("root", )):
        """Yields (key, value) pairs by recursively iterating the mapping.

        The keys yielded are tuples containing the list of the keys necessary
        to access this particular entry in the dictionary hierarcy.

        Args:
            node (tuple): A tuple indicating the root mapping

        Examples:

            >>> mydict = AttrDict(a=1, b=2, c=AttrDict(x=[10, 20, 100]))
            >>> for k, v in mydict.walk():
            ...     print (k, v)
        """
        for key, value in self.items():
            node = _node + (key,) if _node else (key,)
            if isinstance(value, AttrDict):
                for kk, vv in value.walk(node):
                    yield kk, vv
            else:
                yield node, value

    def pget(self, path, sep="."):
        """Get value from a nested dictionary entry.

        A convenience method that serves various purposes:

          - Access values from a deeply nested dictionary if any of the keys
            are not valid python variable names.

          - Return None if any of the intermediate keys are missing. Does not
            raise AttributeError.

        By default, the method uses the ``.`` character to split keys similar
        to attribute access. However, this can be overridden by providing and
        extra ``sep` ` argument.

        Args:
            path (str): The keys in individual dictionarys separated by sep
            sep (str): Separator for splitting keys (default: ".")

        Returns: Value corresponding to the key, or None if any of the keys
            don't exist.

        """
        key_clean = path.strip().strip(sep)
        key_list = key_clean.split(sep)

        rhs = self
        for k in key_list:
            rhs = rhs.get(k, None)
            if rhs is None:
                return None
        return rhs

    def pset(self, path, value, sep="."):
        """Set value for a nested dictionary entry.

        A convenience method to set values in a nested mapping hierarchy
        without individually creating the intermediate dictionaries. Missing
        intermediate dictionaries will automatically be created with the same
        mapping class as the class of ``self``.

        Args:
            path (str): The keys in individual dictionarys separated by sep
            value (object): Object assigned to innermost key
            sep (str): Separator for splitting keys (default: ".")

        Raises:
            AttributeError: If the object assigned to is a non-mapping type
            and not the final key.
        """
        key_clean = path.strip().strip(sep)
        key_list = key_clean.split(sep)
        cls = self.__class__
        lhs = self

        for k in key_list[:-1]:
            lhs = lhs.setdefault(k, cls())
        lval = lhs.get(key_list[-1], None)
        if hasattr(lval, "merge"):
            lval.merge(value)
        else:
            lhs[key_list[-1]] = value