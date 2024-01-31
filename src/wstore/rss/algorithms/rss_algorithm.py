from abc import ABC, abstractmethod
import inspect
from importlib import import_module

# Add the name of the module of any new algorithms to the list.
RSS_ALGORITHM_MODULES = ["fixed_percentage"]


class RSSAlgorithm(ABC):
    id = "ALGORITHM_ID"
    name = "Algorithm Name"
    desc = "A description of what the algorithm does"

    def __new__(cls, *args, **kwags):
        raise TypeError("Revenue Sharing Algorithms are not meant to be instantiated. All methods are class methods.")

    @classmethod
    @abstractmethod
    def calculate_revenue_share(cls, rs_model, total_revenue):
        """
        Args:
            rs_model (RSSModel): The model to use for calculating the revenue share.
            total_revenue (Decimal): The total ammount to divide.

        Returns:
            dict: A dictionary representing an RSS Report (see RSS models) without
            currency or timestamp. For ease of implementation, you may return additional fields,
            in the main dictionary but not in nested fields like `stakeholders`.
        """
        ...

    @classmethod
    def to_dict(cls):
        return {"id": cls.id, "name": cls.name, "description": cls.desc}


def _get_all_algorithm_classes():
    """
    Loads and returns all classes that inherit from `RSSAlgorithm` inside the
    module `wstore.rss.algorithms`. This is used to create the variable
    `RSS_ALGORITHMS` for use elsewhere.
    """
    classes = []
    for submodule in RSS_ALGORITHM_MODULES:
        is_algorithm_class = (
            lambda x: inspect.isclass(x) and (not inspect.isabstract(x)) and issubclass(x, RSSAlgorithm)
        )
        submodule_classes = [
            cls[1]
            for cls in inspect.getmembers(import_module(f"wstore.rss.algorithms.{submodule}"), is_algorithm_class)
        ]
        classes.extend(submodule_classes)
    return classes


RSS_ALGORITHMS = {cls.id: cls for cls in _get_all_algorithm_classes()}
