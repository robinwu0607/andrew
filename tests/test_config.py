import unittest
import redis
import pickle

from andrew import config


class TestConfig(unittest.TestCase):

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
        station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False})
        #
        station = gen.add_test_station("PCBP2")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        #
        station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        print(value)
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        return

    def test_add_station_pre_sequence(self):
        """
        1. add pre sequence "hello.world" to see if it equals redis["PCBST:PRE_SEQUENCE"]
        2. add pre sequence "good.job" to see if it equals redis["PCBST:PRE_SEQUENCE"]

        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        # 1
        station.add_pre_sequence("hello.world")
        value = pickle.loads(self.r["PCBST:PRE_SEQUENCE"])
        self.assertEqual(value, "hello.world")
        # 2
        station.add_pre_sequence("good.job")
        value = pickle.loads(self.r["PCBST:PRE_SEQUENCE"])
        self.assertEqual(value, "good.job")
        return

    def test_add_station_sequence_map(self):
        """
        1. add sequence map "TEST1"/"test.case1" to see if it is in redis["PCBST:SEQUENCE_MAP"]
        2. add sequence map "TEST2"/"test.case2" to see if both 1&2 in redis["PCBST:SEQUENCE_MAP"]
        3. add sequence map "TEST1"/"test.case2",to see if it is in redis["PCBST:SEQUENCE_MAP"]
            and map "TEST1"/"test.case2" is not in redis["PCBST:SEQUENCE_MAP"]
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        # 1
        station.add_sequence_map("TEST1", "test.case1")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertIn({"TEST1": "test.case1"}, value)
        # 2
        station.add_sequence_map("TEST2", "test.case2")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertIn({"TEST1": "test.case1"}, value)
        self.assertIn({"TEST2": "test.case2"}, value)
        # 3
        station.add_sequence_map("TEST1", "test.case3")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertNotIn({"TEST1": "test.case1"}, value)
        self.assertIn({"TEST2": "test.case2"}, value)
        self.assertIn({"TEST1": "test.case3"}, value)
        return

    def test_add_station_sync_group(self):
        """

        :return:
        """
        pass

    def test_add_station_configuration_data(self):
        """

        :return:
        """
        pass

    def test_add_station_connection(self):
        """
        :return:
        """
        pass

    def test_add_container(self):
        """ Test Add Test Container.
        1. add a container "UUT00" to see if it is in redis["PCBST:CONTAINER_LIST"]

        :return:
        """
        pass


if __name__ == "__main__":
    unittest.main()
