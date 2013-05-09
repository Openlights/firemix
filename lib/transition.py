


class Transition:
    """
    Defines the interface for a transition.

    Given two numpy arrays and a progress (0 to 1.0), it produces one output array.
    """

    def __init__(self):
        pass

    def __repr__(self):
        """
        Override this with the screen-friendly name of your transition
        """
        return "Transition"

    def setup(self):
        """
        This method will be called right before the transition is scheduled to start.
        """
        pass

    def get(self, start, end, progress):
        """
        This method will return a frame that is between start and end, according to progress
        """
        pass