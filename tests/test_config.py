import unittest
import redis

from andrew import config


class TestConfig(unittest.TestCase):

    station = None

    def setUp(self):
        self.r = redis.Redis("localhost", 6379)
        pass

    def tearDown(self):
        pass

    def test_add_station(self):
        """ Test add Test Station.
        1. add a station "PCBST" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        2. add another station "PCBP2" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        3. add "PCBST" again, to see if `add_test_station` filter the duplicated station name.

        :return:
        """
        gen = config.TestConfiguration()
        self.station = gen.add_test_station("PCBST")
        print(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(self.r["CONFIGURATION:STATION_LIST"], {"PCBST": False})
        #
        self.station = gen.add_test_station("PCBP2")
        print(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(self.r["CONFIGURATION:STATION_LIST"], {"PCBST": False, "PCBP2": False})
        #
        self.station = gen.add_test_station("PCBST")
        print(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(self.r["CONFIGURATION:STATION_LIST"], {"PCBST": False, "PCBP2": False})


if __name__ == "__main__":
    unittest.main()
