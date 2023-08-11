from geniusrise.core import Bolt


class TestBoltCtlBolt(Bolt):
    def test_method(self, *args, input_folder=None, kafka_consumer=None, **kwargs):
        print(args, kwargs)
        return sum(args) * sum(kwargs.values())
