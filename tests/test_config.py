import unittest
import redis
import pickle

from andrew import config


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.r = redis.Redis("localhost", 6379)

    def tearDown(self):
        self.r.flushall()
        del self.r

    def test_add_station(self):
        """ Test add Test Station.
        1. add a station "PCBST" to see if it is in redis["CONFIGURATION:STATION_LIST"]
        2. add another station "PCBP2" to see if 1&2 are in redis["CONFIGURATION:STATION_LIST"]
        3. add "PCBST" again, to see if `add_station` filter the duplicated station name.

        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_station("PCBST")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(value, {"PCBST": False})
        #
        station = gen.add_station("PCBP2")
        value = pickle.loads(self.r["CONFIGURATION:STATION_LIST"])
        self.assertEqual(value, {"PCBST": False, "PCBP2": False})
        #
        station = gen.add_station("PCBST")
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
        station = gen.add_station("PCBST")
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
        station = gen.add_station("PCBST")
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
        station = gen.add_station("PCBST")
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
        station = gen.add_station("PCBST")
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
        Create Station "PCBST"
        1. add connection "name1"/protocol="dummy", port=22, host="web1" to see if it is in redis["PCBST:CONNECTION_LIST"]
        2. add connection "name2"/protocol="telnet", port=22, host="web2" to see if both 1&2 in redis["PCBST:CONNECTION_LIST"]
        3. add connection "name1"/protocol="ssh", port=22, host="web3",to see if it is in redis["PCBST:CONNECTION_LIST"]

        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_station("PCBST")
        # 1
        station.add_connection("name1", protocol="dummy", port=22, host="web1")
        value = pickle.loads(self.r["PCBST:CONNECTION_LIST"])
        self.assertIn("NAME1", value)
        self.assertEqual(value.get("NAME1"), {"protocol": "dummy", "port": 22, "host": "web1", "shared_conn": "PCBST:NAME1"})
        # 2
        station.add_connection("name2", protocol="telnet", port=22, host="web2")
        value = pickle.loads(self.r["PCBST:CONNECTION_LIST"])
        self.assertIn("NAME1", value)
        self.assertEqual(value.get("NAME1"), {"protocol": "dummy", "port": 22, "host": "web1", "shared_conn": "PCBST:NAME1"})
        self.assertIn("NAME2", value)
        self.assertEqual(value.get("NAME2"), {"protocol": "telnet", "port": 22, "host": "web2", "shared_conn": "PCBST:NAME2"})
        # 3
        station.add_connection("name1", protocol="ssh", port=22, host="web3")
        value = pickle.loads(self.r["PCBST:CONNECTION_LIST"])
        # print(value)
        self.assertIn("NAME1", value)
        self.assertEqual(value.get("NAME1"), {"protocol": "ssh", "port": 22, "host": "web3", "shared_conn": "PCBST:NAME1"})
        self.assertIn("NAME2", value)
        self.assertEqual(value.get("NAME2"), {"protocol": "telnet", "port": 22, "host": "web2", "shared_conn": "PCBST:NAME2"})
        return

    def test_add_container(self):
        """ Test Add Test Container.
        Create Station "PCBST"
        1. add container "UUT00" to see if it is in redis["PCBST:CONTAINER_LIST"]
        2. add container "UUT01" to see if 1&2 are in redis["PCBST:CONTAINER_LIST"]
        3. add container "UUT00" to see if `add_container` filter the duplicated station name.
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_station("PCBST")
        # 1
        station.add_container("UUT00")
        value = pickle.loads(self.r["PCBST:CONTAINER_LIST"])
        self.assertEqual(value, {"PCBST:UUT00": False})
        # 2
        station.add_container("UUT01", disabled=True)
        value = pickle.loads(self.r["PCBST:CONTAINER_LIST"])
        self.assertEqual(value, {"PCBST:UUT00": False, "PCBST:UUT01": True})
        # 3
        station.add_container("UUT00", disabled=True)
        value = pickle.loads(self.r["PCBST:CONTAINER_LIST"])
        self.assertEqual(value, {"PCBST:UUT00": True, "PCBST:UUT01": True})
        return

    def test_add_container_pre_sequence(self):
        """
        Create Station "PCBST"
        Create Container "UUT00"
        1. add pre sequence "hello.world" to station, container would inherit it.
        2. add pre sequence "good.job" to container, container will rewrite it.
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_station("PCBST")
        station.add_pre_sequence("hello.world")
        container = station.add_container("UUT00")
        # 1
        value = pickle.loads(self.r["PCBST:PRE_SEQUENCE"])
        self.assertEqual(value, "hello.world")
        value = pickle.loads(self.r["PCBST:UUT00:PRE_SEQUENCE"])
        self.assertEqual(value, "hello.world")
        # 2
        container.add_pre_sequence("good.job")
        value = pickle.loads(self.r["PCBST:UUT00:PRE_SEQUENCE"])
        self.assertEqual(value, "good.job")
        return

    def test_add_container_sequence_map(self):
        """
        Create Station "PCBST"
        Create Container "UUT00"
        1. add sequence map "TEST1"/"test.case1" to station, container will inherit it.
        2. add sequence map "test2"/"test.case2" to container, it could be found in ["PCBST:UUT00:SEQUENCE_MAP"]
        3. add sequence map "TEST1"/"test.case3" to container, it could be found in ["PCBST:UUT00:SEQUENCE_MAP"]
        :return:
        """
        gen = config.TestConfiguration()
        station = gen.add_station("PCBST")
        station.add_sequence_map("TEST1", "test.case1")
        container = station.add_container("UUT00")
        # 1
        value = pickle.loads(self.r["PCBST:SEQUENCE_MAP"])
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case1")
        value = pickle.loads(self.r["PCBST:UUT00:SEQUENCE_MAP"])
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case1")
        # 2
        container.add_sequence_map("test2", "test.case2")
        value = pickle.loads(self.r["PCBST:UUT00:SEQUENCE_MAP"])
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case1")
        self.assertIn("test2", value)
        self.assertEqual(value.get("test2"), "test.case2")
        # 3
        container.add_sequence_map("TEST1", "test.case3")
        self.assertIn("TEST1", value)
        self.assertEqual(value.get("TEST1"), "test.case3")
        self.assertIn("test2", value)
        self.assertEqual(value.get("test2"), "test.case2")
        return

    def test_add_container_sync_group(self):
        """
        :return:
        """
        pass

    def test_add_container_configuration_data(self):
        """
        :return:
        """
        pass

    def test_add_container_connection(self):
        """
        :return:
        """
        pass

if __name__ == "__main__":
    unittest.main()
