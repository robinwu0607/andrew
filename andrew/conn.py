import paramiko
import time
import threading
from typing import Union, List


class CONN(object):
    def __init__(self, host: str, username: str, **kwargs) -> None:
        """

        :param name:
        :param kwargs:
        """
        self.__status = "close"
        self.__buf = ""
        self.__username = host
        self.__lock = threading.Lock()
        self.__thread = threading.Thread(None, self.__read_thread, host, (), {}, daemon=True)
        self.__timeout = kwargs.get("timeout", 300)

        self.__username = username
        self.__password = kwargs.get("password", None)
        self.__host = host
        self.__port = kwargs.get("port", 22)
        self.__allow_agent = kwargs.get("allow_agent", True)
        self.__echo = kwargs.get("echo", False)
        self.__ssh = None
        self.__chan = None
        self.__logger = None
        self.__sftp = None

        if not self.__username:
            self.__username = input("Input username[{}]: ".format(host))
            if not self.__username.strip():
                raise Exception("You should provide username for [{}]".format(host))

        self.__thread.start()

        if kwargs.get("open", False):
            self.open()
        return

    @property
    def buf(self) -> str:
        """

        :return:
        """
        # return self.__buf
        # remove the cmd sent
        return "\n\r".join(i for i in self.__buf.strip().splitlines()[1:])

    @property
    def host(self) -> str:
        """

        :return:
        """
        return self.__host

    @property
    def status(self) -> str:
        """

        :return:
        """
        return self.__status

    def set_logger(self, log: str) -> None:
        """
        :param log: log absolute path, eg: "/tmp/log.txt"”" for linux, "C:\\log.txt" for windows.
        :return:
        """
        from . import logger
        self.__logger = logger.get_conn_logger(log)
        return

    def __read_thread(self):
        """

        :return:
        """
        while True:
            time.sleep(0.04)
            data = self.__read()
            if not data:
                continue
            self.__lock.acquire()
            try:
                self.__buf += data
                self.__on_data_received(data)
            except Exception as e:
                pass
            finally:
                self.__lock.release()

    def __on_data_received(self, msg):
        """ Once get log from connection, save it to local file.

        :param msg:
        :return:
        """
        if self.__logger:
            self.__logger.info(msg)
        if self.__echo:
            print(msg, end="")

    def open(self) -> None:
        """

        :return:
        """
        if "open" in self.status:
            return
        try:
            self.__ssh = paramiko.SSHClient()
            # self.__ssh.load_system_host_keys()
            self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.__ssh.connect(
                self.__host,
                self.__port,
                self.__username,
                self.__password,
                allow_agent=self.__allow_agent,
            )
            self.__chan = self.__ssh.invoke_shell()
        except Exception as e:
            print(e)
            raise Exception("Could not open Connection") from e
        self.__status = "open"
        self.send("\r", expectphrase="{}@".format(self.__username), timeout=60)
        return

    def close(self) -> None:
        """

        :return:
        """
        if "close" == self.status:
            return
        try:
            self.__chan.close()
            self.__ssh.close()
        except Exception as e:
            raise Exception("Could not close Connection") from e
        finally:
            self.__status = "close"
            self.__buf = ""
            if self.__logger:
                self.__logger.info("\n\r{}Connection is closed{}\n\r".format("-" * 10, "-" * 10))
        return

    def __read(self, data_size=512):
        """

        :param data_size:
        :return:
        """
        if "close" == self.status:
            return ""
        try:
            data = self.__data_handler(self.__chan.recv(data_size))
        except Exception as e:
            data = ""
            # raise Exception("Could not read data from Connection\n" + str(e))
        return data

    @staticmethod
    def __data_handler(msg):
        return msg.decode("UTF-8")

    def received(self, expect: Union[str, list]) -> bool:
        """

        :param expect:
        :return:
        """
        if not expect:
            return False
        buf = self.__buf
        expect_list = expect if isinstance(expect, list) else [expect]
        for phrase in expect_list:
            if buf.find(phrase) >= 0:
                break
        else:
            return False
        return True

    def __write(self, cmd):
        """

        :param cmd:
        :return:
        """
        if "open" != self.status:
            msg = "Connection is not open yet, could not send before open it"
            raise Exception(msg)
        self.__buf = ""
        self.__chan.sendall(cmd)
        return True

    def send(self, cmd: str, expectphrase: Union[str, List[str]], timeout: int = 60) -> None:
        """ Send command to Connection.
        :param str cmd: the message to send
        :param str|list expectphrase: the expected phrase, should be a str or list
        :param num timeout: the time out should be more than 0
        """
        self.__write(cmd)
        start_time = time.time()

        if not expectphrase:
            return
        if timeout <= 0:
            timeout = 60
        expect = [expectphrase] if isinstance(expectphrase, str) else expectphrase

        while (time.time() - start_time) < timeout:
            time.sleep(0.1)
            if self.received(expect):
                return
        msg = "{} Did not received {} within [{}] seconds".format(cmd.replace("\r", "\\r"), expectphrase, timeout)
        raise Exception(msg)

    def capture(self, start: str, end: str) -> str:
        """ Capture string from start to end
        :param str start: Start string
        :param str end: End string
        :return: return the first captured string between start and end, or None
        """
        if not start or not end:
            return self.buf
        buf = self.__buf
        start_position = buf.find(r"{}".format(start))
        if start_position < 0:
            return ""
        start_position += len(start)
        end_position = buf.find(r"{}".format(end), start_position)
        if end_position < 0:
            return ""
        return buf[start_position: end_position].strip()

    def put(self, local: str, remote: str) -> None:
        """ Put local file to remote.

        :param local:
        :param remote:
        :return:
        """
        # if remote is a folder, will use local file name as remote file name.
        if remote.endswith("/"):
            remote = "/".join([remote, local.split("/")[-1]])
        if not self.__sftp:
            self.__sftp = self.__ssh.open_sftp()
        self.__sftp.put(local, remote)
        return

    def get(self, remote: str, local: str) -> None:
        """ Get remote file to local
        :param remote:
        :param local:
        :return:
        """
        # if local is a folder, will use remote file name as local file name.
        if local.endswith("/"):
            local = "/".join([local, remote.split("/")[-1]])
        if not self.__sftp:
            self.__sftp = self.__ssh.open_sftp()
        self.__sftp.get(remote, local)
        return
