import abc

import six

from smqtk.exceptions import NoClassificationError
from smqtk.representation import SmqtkRepresentation
from smqtk.utils.plugin import Pluggable


__author__ = "paul.tunison@kitware.com"


NEG_INF = float('-inf')


class ClassificationElement(SmqtkRepresentation, Pluggable):
    """
    Classification result encapsulation.

    Contains a mapping of arbitrary (but hashable) label values to confidence
    values (floating point in ``[0,1]`` range). If a classifier does not
    produce continuous confidence values, it may instead assign a value of
    ``1.0`` to a single label, and ``0.0`` to the rest.

    UUIDs must maintain unique-ness when transformed into a string.

    Element equality based on classification labels and values, not the type or
    UUID.

    Since this base class defines ``__getstate__`` and ``__setstate__`` methods
    implementing classes must also extend these methods to support
    serialization. These methods have been marked as abstract to facilitate
    this requirement.

    """

    __slots__ = ('type_name', 'uuid')

    def __init__(self, type_name, uuid):
        """
        Initialize a new classification element.

        :param type_name: Name of the type of classifier this classification
            was generated by.
        :type type_name: str

        :param uuid: Unique ID reference of the classification
        :type uuid: collections.abc.Hashable

        """
        super(ClassificationElement, self).__init__()
        self.type_name = type_name
        self.uuid = uuid

    def __hash__(self):
        return hash((self.type_name, self.uuid))

    def __eq__(self, other):
        if isinstance(other, ClassificationElement):
            try:
                a = self.get_classification()
            except NoClassificationError:
                a = None
            try:
                b = other.get_classification()
            except NoClassificationError:
                b = None
            return a == b
        return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "%s{type_name: %s, uuid: %s}" \
            % (self.__class__.__name__, self.type_name, self.uuid)

    def __getitem__(self, label):
        """
        Get the confidence value for a specific label

        :param label: Classification label to get the confidence value for.
        :type label: collections.abc.Hashable

        :raises KeyError: The given label is not present in this
            classification.
        :raises NoClassificationError: No classification labels/confidences yet
            set.

        :return: Confidence value for the given label.
        :rtype: float

        """
        return self.get_classification()[label]

    def __nonzero__(self):
        """
        A ClassificationElement is considered non-zero if
        ``has_classifications`` returns True. See method documentation for
        details.

        :return: True if this instance is non-zero (see above), false
            otherwise.
        :rtype: bool
        """
        return self.has_classifications()

    __bool__ = __nonzero__

    @classmethod
    def get_default_config(cls):
        """
        Generate and return a default configuration dictionary for this class.
        This will be primarily used for generating what the configuration
        dictionary would look like for this class without instantiating it.

        By default, we observe what this class's constructor takes as
        arguments, turning those argument names into configuration
        dictionary keys. If any of those arguments have defaults, we will
        add those values into the configuration dictionary appropriately.
        The dictionary returned should only contain JSON compliant value types.

        It is not be guaranteed that the configuration dictionary returned
        from this method is valid for construction of an instance of this
        class.

        :return: Default configuration dictionary for the class.
        :rtype: dict

        """
        # similar to parent impl, except we remove the ``type_str`` and
        #  ``uuid`` configuration parameters as they are to be specified at
        # runtime.
        dc = super(ClassificationElement, cls).get_default_config()
        # These parameters must be specified at construction time.
        del dc['type_name'], dc['uuid']
        return dc

    # noinspection PyMethodOverriding
    @classmethod
    def from_config(cls, config_dict, type_name, uuid, merge_default=True):
        """
        Instantiate a new instance of this class given the configuration
        JSON-compliant dictionary encapsulating initialization arguments.

        This method should not be called via super unless and instance of the
        class is desired.

        :param config_dict: JSON compliant dictionary encapsulating
            a configuration.
        :type config_dict: dict

        :param type_name: Name of the type of classifier this classification
            was generated by.
        :type type_name: str

        :param uuid: Unique ID reference of the classification
        :type uuid: collections.abc.Hashable

        :param merge_default: Merge the given configuration on top of the
            default provided by ``get_default_config``.
        :type merge_default: bool

        :return: Constructed instance from the provided config.
        :rtype: ClassificationElement

        """
        # Shallow-copy config dict to modify
        config_dict = dict(config_dict)
        config_dict['type_name'] = type_name
        config_dict['uuid'] = uuid
        return super(ClassificationElement, cls).from_config(
            config_dict, merge_default=merge_default
        )

    def max_label(self):
        """
        Get the label with the highest confidence.

        :raises NoClassificationError: No classification set.

        :return: The label with the highest confidence.
        :rtype: collections.abc.Hashable

        """
        # Temp (label, confidence) tuple
        #: :type: (collections.abc.Hashable, float)
        m = (None, NEG_INF)
        for i in six.iteritems(self.get_classification()):
            if i[1] > m[1]:
                m = i
        if m[0] is None:
            raise NoClassificationError("No classifications set to pick the "
                                        "max of.")
        return m[0]

    #
    # Abstract methods
    #

    @abc.abstractmethod
    def __getstate__(self):
        return self.type_name, self.uuid

    @abc.abstractmethod
    def __setstate__(self, state):
        self.type_name, self.uuid = state

    @abc.abstractmethod
    def has_classifications(self):
        """
        :return: If this element has classification information set.
        :rtype: bool
        """

    @abc.abstractmethod
    def get_classification(self):
        """
        Get classification result map, returning a label-to-confidence dict.

        We do no place any guarantees on label value types as they may be
        represented in various forms (integers, strings, etc.).

        Confidence values are in the [0,1] range.

        :raises NoClassificationError: No classification labels/confidences yet
            set.

        :return: Label-to-confidence dictionary.
        :rtype: dict[collections.abc.Hashable, float]

        """

    @abc.abstractmethod
    def set_classification(self, m=None, **kwds):
        """
        Set the whole classification map for this element. This will strictly
        overwrite the entire label-confidence mapping (vs. updating it)

        Label/confidence values may either be provided via keyword arguments or
        by providing a dictionary mapping labels to confidence values.
        Non-string labels must be provided via an input dictionary (``m``
        parameter).

        NOTE TO IMPLEMENTORS: This abstract method will aggregate input into a
        single dictionary, checks that there is anything in it and return it.
        Thus, a ``super`` call should be made, which will return a dictionary.

        :param m: New labels-to-confidence mapping to set.
        :type m: dict[collections.abc.Hashable, float]

        :raises ValueError: The given label-confidence map was empty.

        """
        # TODO: Use template method pattern, create ``_set_classification``
        #       abstract method (removing abstract from this).
        m = m or {}
        m.update(kwds)
        if not m:
            raise ValueError("No classification labels/values given.")
        return m
