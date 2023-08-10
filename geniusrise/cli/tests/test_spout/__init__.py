from geniusrise.core import Spout


class TestSpoutCtlSpout(Spout):
    def test_method(self, *args, **kwargs):
        return sum(args) * sum(kwargs.values())
