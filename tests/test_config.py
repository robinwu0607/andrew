import unittest
import redis
import pickle

from andrew import config


class TestConfig(unittest.TestCase):

    station = None

    def setUp(self):
        self.r = redis.Redis("localhost", 6379)

    def tearDown(self):
        del self.r

    def test_add_station(self):
        """ Test add Test Station.
        1. add a station "PCBST" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        2. add another station "PCBP2" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        3. add "PCBST" again, to see if `add_test_station` filter the duplicated station name.

        :return:
        """
        gen = config.TestConfiguration()
        self.station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False})
        #
        self.station = gen.add_test_station("PCBP2")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        #
        self.station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})


if __name__ == "__main__":
    unittest.main()
