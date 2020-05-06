import re
from andrew import broker

checker = re.compile("^[a-zA-Z0-9_]+$")


class TestConfiguration(object):

    def __init__(self):
        self.b = broker.Broker("CONFIGURATION")
        self.station_map = dict()
        return

    def __repr__(self):
        return "Andrew Configuration"

    def add_test_station(self, name: str):
        station_name = name.upper()
        if not checker.match(station_name):
            raise Exception("Station name should not contain special characters - [{}]".format(station_name))
        self.station_map.setdefault(station_name, False)
        self.b.set("STATION_LIST", self.station_map)
        return TestStation(station_name)


class TestStation(object):
    def __init__(self, station_name: str):
        self.station_name = station_name
        self.b = broker.Broker(self.station_name)
        self.sequence_map = dict()
        self.sync_group_map = dict()
        self.configuration_data_map = dict()
        self.container_map = dict()
        self.connection_map = dict()
        return

    def add_sequence_map(self, name: str, sequence_definition: str):
        self.sequence_map.setdefault(name, sequence_definition)
        self.b.set("SEQUENCE_MAP", self.sequence_map)
        return

    def assign_pre_sequence(self, sequence_definition: str):
        self.b.set("PRE_SEQUENCE", sequence_definition)
        return

    def add_sync_group(self, name: str, container_list: list):
        self.sync_group_map.setdefault(name, container_list)
        self.b.set("SYNC_GROUP", self.sync_group_map)
        return

    def add_configuration_data(self, key: str, value):
        self.configuration_data_map.setdefault(key, value)
        self.b.set("CONFIGURATION_DATA", self.configuration_data_map)
        return

    def add_connection(self, name: str, **connection_config):
        forbidden_list = ["EVENT", "INFO", "STEP", "event", "info", "step"]
        if name in forbidden_list:
            raise Exception("name should not in {}, yours - {}".format(forbidden_list, name))
        if not checker.match(name):
            raise Exception("connection name should not contain special characters - [{}]".format(name))
        if connection_config.get("protocol") not in ["telnet", "ssh", "dummy"]:
            raise Exception("protocol should be in telnet/ssh/dummy")

        connection_name = ":".join([self.station_name, name]).upper()
        connection_config.setdefault("shared_conn", connection_name)
        self.connection_map.setdefault(name.upper(), connection_config)
        self.b.set("CONNECTION_LIST", self.connection_map)
        return

    def add_container(self, name: str, disabled: bool = False):
        if not checker.match(name):
            raise Exception("container name should not contain special characters - [{}]".format(name))
        container_name = ":".join([self.station_name, name]).upper()
        self.container_map.setdefault(container_name, disabled)
        self.b.set("CONTAINER_LIST", self.container_map)
        return TestContainer(self.station_name, name)


class TestContainer(object):
    def __init__(self, station_name: str, container_name: str):
        self.station_name = station_name
        self.container_name = container_name
        self.b = broker.Broker(":".join([self.station_name, self.container_name]).upper())

        self.sequence_map = broker.Broker(self.station_name).get_dict("SEQUENCE_MAP")
        self.configuration_data_map = broker.Broker(self.station_name).get_dict("CONFIGURATION_DATA")
        self.station_connection_map = broker.Broker(self.station_name).get_dict("CONNECTION_LIST")
        self.connection_map = dict()

    def add_sequence_map(self, name: str, sequence_definition: str):
        self.sequence_map.setdefault(name, sequence_definition)
        self.b.set("SEQUENCE_MAP", self.sequence_map)
        return

    def assign_pre_sequence(self, sequence_definition: str):
        self.b.set("PRE_SEQUENCE", sequence_definition)
        return

    def add_configuration_data(self, key: str, value):
        self.configuration_data_map.setdefault(key, value)
        self.b.set("CONFIGURATION_DATA", self.configuration_data_map)
        return

    def add_connection(self, name: str, **connection_config):
        forbidden_list = ["EVENT", "INFO", "STEP", "event", "info", "step"]
        if name in forbidden_list:
            raise Exception("name should not in {}, yours - {}".format(forbidden_list, name))
        if not checker.match(name):
            raise Exception("connection name should not contain special characters - [{}]".format(name))

        shared_conn = connection_config.get("shared_conn", None)
        connection_name = ":".join([self.station_name, self.container_name, name]).upper()
        if shared_conn:
            for conn, conf in self.station_connection_map.items():
                if conn == shared_conn:
                    self.connection_map.setdefault(connection_name, conf)
                    break
            else:
                raise Exception("Could not find shared_conn [{}] from Station".format(shared_conn))
        else:
            if connection_config.get("protocol") not in ["telnet", "ssh", "dummy"]:
                raise Exception("protocol should be in telnet/ssh/dummy")
            self.connection_map.setdefault(connection_name, connection_config)

        self.b.set("CONNECTION_LIST", self.connection_map)
        return
