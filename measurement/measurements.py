import typing

from measurement.results import MeasurementResult


class BaseMeasurement(object):
    """Interface for creating measurements.

    This base class is designed to be sub-classed and used as an
    interface for creating new measurement types.
    """

    def __init__(self, id: str):
        """Initialisation of a base measurement

        :param id: A unique identifier for the measurement.
        """
        super().__init__()
        self.id = id

    def measure(self) -> typing.List[typing.Type[MeasurementResult]]:
        """Perform the measurement and return the measurement results.
        """
        raise NotImplementedError
