import unittest
import redis
import pickle

from andrew import config


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.r = redis.Redis("localhost", 6379)
        self.r.flushall()

    def tearDown(self):
        del self.r

    def test_add_station(self):
        """ Test add Test Station.
        1. add a station "PCBST" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        2. add another station "PCBP2" to see if 1&2 are in redis["CONFIGURATION:STATION_LIST"]
        3. add "PCBST" again, to see if `add_test_station` filter the duplicated station name.

        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(value, {"PCBST": False})
        #
        station = gen.add_test_station("PCBP2")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        #
        station = gen.add_test_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        return

    def test_add_station_pre_sequence(self):
        """
        Create Station "PCBST"
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
        Create Station "PCBST"
        1. add sequence map "TEST1"/"test.case1" to see if it is in redis["PCBST:SEQUENCE_MAP"]
        2. add sequence map "TEST2"/"test.case2" to see if both 1&2 in redis["PCBST:SEQUENCE_MAP"]
        3. add sequence map "TEST1"/"test.case2",to see if it is in redis["PCBST:SEQUENCE_MAP"]
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        # 1
        station.add_sequence_map("TEST1", "test.case1")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case1")
        # 2
        station.add_sequence_map("TEST2", "test.case2")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case1")
        self.assertIn("TEST2", value)
        self.assertEqual(value.get("TEST2"), "test.case2")
        # 3
        station.add_sequence_map("TEST1", "test.case3")
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        # print(value)
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case3")
        self.assertIn("TEST2", value)
        self.assertEqual(value.get("TEST2"), "test.case2")
        return

    def test_add_station_sync_group(self):
        """
        Create Station "PCBST"
        1. add sync map "GROUP1"/["UUT00", "UUT01"] to see if it is in redis["PCBST:SYNC_GROUP"]
        2. add sync map "GROUP2"/["UUT00", "UUT02"] to see if both 1&2 in redis["PCBST:SYNC_GROUP"]
        3. add sync map "GROUP1"/["UUT00", "UUT03"],to see if it is in redis["PCBST:SYNC_GROUP"]

        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        # 1
        station.add_sync_group("GROUP1", ["UUT00", "UUT01"])
        value = pickle.loads(self.r["PCBST:SYNC_GROUP"])
        self.assertIn("GROUP1", value)
        self.assertEqual(value.get("GROUP1"), ["UUT00", "UUT01"])
        # 2
        station.add_sync_group("GROUP2", ["UUT00", "UUT02"])
        value = pickle.loads(self.r["PCBST:SYNC_GROUP"])
        self.assertIn("GROUP1", value)
        self.assertEqual(value.get("GROUP1"), ["UUT00", "UUT01"])
        self.assertIn("GROUP2", value)
        self.assertEqual(value.get("GROUP2"), ["UUT00", "UUT02"])
        # 3
        station.add_sync_group("GROUP1", ["UUT00", "UUT03"])
        value = pickle.loads(self.r["PCBST:SYNC_GROUP"])
        # print(value)
        self.assertIn("GROUP1", value)
        self.assertEqual(value.get("GROUP1"), ["UUT00", "UUT03"])
        self.assertIn("GROUP2", value)
        self.assertEqual(value.get("GROUP2"), ["UUT00", "UUT02"])
        return

    def test_add_station_configuration_data(self):
        """
        Create Station "PCBST"
        1. add configuration_data "key1"/["UUT00", "UUT01"] to see if it is in redis["PCBST:CONFIGURATION_DATA"]
        2. add configuration_data "key2"/{"hello": "world"} to see if both 1&2 in redis["PCBST:CONFIGURATION_DATA"]
        3. add configuration_data "key3"/"nice.job",to see if it is in redis["PCBST:CONFIGURATION_DATA"]
        4. add configuration_data "key1"/"great.job",to see if it is in redis["PCBST:CONFIGURATION_DATA"]
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_test_station("PCBST")
        # 1
        station.add_configuration_data("key1", ["UUT00", "UUT01"])
        value = pickle.loads(self.r["PCBST:CONFIGURATION_DATA"])
        self.assertIn("key1", value)
        self.assertEqual(value.get("key1"), ["UUT00", "UUT01"])
        # 2
        station.add_configuration_data("key2", {"hello": "world"})
        value = pickle.loads(self.r["PCBST:CONFIGURATION_DATA"])
        self.assertIn("key1", value)
        self.assertEqual(value.get("key1"), ["UUT00", "UUT01"])
        self.assertIn("key2", value)
        self.assertEqual(value.get("key2"), {"hello": "world"})
        # 3
        station.add_configuration_data("key3", "nice.job")
        value = pickle.loads(self.r["PCBST:CONFIGURATION_DATA"])
        self.assertIn("key1", value)
        self.assertEqual(value.get("key1"), ["UUT00", "UUT01"])
        self.assertIn("key2", value)
        self.assertEqual(value.get("key2"), {"hello": "world"})
        self.assertIn("key3", value)
        self.assertEqual(value.get("key3"), "nice.job")
        # 4
        station.add_configuration_data("key1", "great.job")
        value = pickle.loads(self.r["PCBST:CONFIGURATION_DATA"])
        self.assertIn("key1", value)
        self.assertEqual(value.get("key1"), "great.job")
        self.assertIn("key2", value)
        self.assertEqual(value.get("key2"), {"hello": "world"})
        self.assertIn("key3", value)
        self.assertEqual(value.get("key3"), "nice.job")
        return

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
