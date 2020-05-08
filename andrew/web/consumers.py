import json
import logging
import logging.handlers
import subprocess
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

FMT = '%(asctime)s: %(message)s'
DATE_FMT = '%a %d %b %Y %H:%M:%S'

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt=FMT, datefmt=DATE_FMT)
rotating_file_handler = logging.handlers.RotatingFileHandler(filename="/tmp/andrew.log",
                                                             mode='a',
                                                             maxBytes=1024 * 1024 * 1,
                                                             backupCount=10,
                                                             )
rotating_file_handler.setFormatter(formatter)
LOGGER.addHandler(rotating_file_handler)


class StationConsumer(JsonWebsocketConsumer):
    group_name = ""  # _ws_genius

    def connect(self):
        # print(self.scope)
        self.group_name = self.scope["path"].replace("/", ".")
        # print(self.group_name)
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        return

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        # text_data_json = json.loads(text_data)
        # print(text_data_json)
        return

    def station_message(self, event):
        self.send(text_data=event["text"])
        return

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)


class ContainerConsumer(JsonWebsocketConsumer):
    group_name = ""  # .ws.genius.pcbst

    def connect(self):
        self.group_name = self.scope["path"].replace("/", ".")
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        station_name = self.group_name.split(".")[-1].upper()
        db = redis.Redis("{}__question".format(station_name))
        _question = db.get_question()
        if _question:
            message = {"ask_question": _question}
            self.send(json.dumps(message))
        del db
        return

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        # print(text_data_json)
        action = text_data_json.get("action", None)
        if not action:
            return
        container = Container.get_by_name(name=text_data_json["name"])
        if action in ["Start Test", "Stop Test", "Deposit Test"]:
            if container.get_locking_status():
                username = text_data_json.get("user", "")
                if container.lock_by_user != username:
                    message = {"snack_bar": "{} was locked by {}".format(
                        container.name, container.lock_by_user)}
                    self.send(json.dumps(message))
                    return
            if action == "Start Test":
                cmd = "free -h | grep Mem"
                pipe = subprocess.Popen(
                    cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                )
                mem = pipe.stdout.read().decode("UTF-8")
                ram_total = mem.split()[1][:-1]
                ram_used = mem.split()[2]
                if 'M' in ram_used:
                    ram_used = round(int(ram_used[:-1]) / 1024, 2)
                else:
                    ram_used = ram_used[:-1]
                ram_usage = str(float(ram_used) / float(ram_total) * 100)[:4]
                if float(ram_usage) > 90.:
                    message = {"snack_bar": "Current RAM Usage > 90%, Can't Start Test"}
                    self.send(json.dumps(message))
                    return
                #
                mode = text_data_json.get("mode", "PROD")
                username = text_data_json.get("user", "")
                container.start_test(mode=mode, username=username)
                return
            elif action == "Stop Test":
                stop_by_username = text_data_json.get("user", "")
                container.stop_test(stop_by_username)
                return
            elif action == "Deposit Test":
                container.deposit_test()
                return
        elif text_data_json["action"] == "Answer Question":
            answer = text_data_json["answer"]
            container.put_question_answer(answer=answer)
            return
        elif text_data_json["action"] in ["Block", "Unblock"]:
            container.block_unblock_container()
        return

    def question_message(self, event):
        self.send(text_data=event["text"])
        return

    def container_message(self, event):
        self.send(text_data=event["text"])
        return

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        return


class ConnectionConsumer(JsonWebsocketConsumer):
    group_name = ""  # .ws.genius.pcbst.uut03

    def connect(self):
        # print(self.scope)
        # print(self.scope["path"])
        self.group_name = self.scope["path"].replace("/", ".")
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        # print(self.group_name)
        station_name = self.group_name.split(".")[-2].upper()
        container_name = self.group_name.split(".")[-1].upper()
        # print(station_name)
        # print(container_name)
        container = Container.get_by_name(name="{}:{}".format(station_name, container_name))
        container_serializer = ContainerSerializer(container)
        connections = Connection.get_all_connection_names(container=container)

        db = redis.Redis("{}__question".format(station_name))
        _question = db.get_question()
        message = {
            "payload": container_serializer.data,
            "controllerList": connections,
            # "container_name": "{}:{}".format(station_name, container_name),
        }
        if _question:
            message.update({"ask_question": _question})
        self.send(json.dumps(message))
        del db
        return

    def receive(self, text_data=None, bytes_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        # print(text_data_json)
        if text_data_json.get("cmd", ""):
            cmd = text_data_json["cmd"]
            user = text_data_json["user"]
            connection = text_data_json["name"].upper() + ":" + text_data_json["controller"]
            db = redis.Redis("CONN")
            conn1 = db.get1(connection)
            db1 = redis.Redis(connection)
            db1.put("::LOGGER-CMD")
            try:
                LOGGER.debug(r"{} - [{}]: [{}]".format(user, connection, cmd.replace('\r', '\\r').replace('\n', '\\n')))
                if "::OPEN" == cmd:
                    conn1.open()
                elif "::CLOSE" == cmd:
                    conn1.close()
                else:
                    conn1.send(cmd, expectphrase="", timeout=60)
            except Exception as e:
                print(e)
                LOGGER.info("Errors Meet: [{}]".format(e))
            del db
            del db1
            return
        elif text_data_json.get("request", "") == "Steps":
            container_name = text_data_json["name"].upper()
            steps_sequence = StepSequence.get_sequence(container_name)
            message = {"steps": steps_sequence}
            self.send(json.dumps(message))
        elif text_data_json.get("request", "") == "Test Log":
            container_name = text_data_json["name"].upper()
            if text_data_json["controller"].upper() in ["SEQ_LOG", "INFO", "STEP"]:
                conn_name = "__{}:{}".format(container_name, text_data_json["controller"].upper())
                db = redis.Redis("{}_TEST_LOG".format(container_name))
                file_name = db.get_set(conn_name)
            else:
                conn_name = "{}:{}".format(container_name, text_data_json["controller"].upper())
                file_name = "/opt/logs/tmp/connection/logs/{}.log".format(conn_name.replace(":", "_"))
            if not file_name:
                return
            # print(file_name)
            cmd = "tail -n 300 {}".format(file_name)
            pipe = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            message = {"testLogController": text_data_json["controller"], "testLog": pipe.stdout.read().decode("UTF-8")}
            self.send(json.dumps(message))
            return
        elif text_data_json.get("request", "") == "Profile":
            container_name = text_data_json["name"].upper()
            conn_name = "__{}:{}".format(container_name, "SEQ_LOG")
            db = redis.Redis("{}_TEST_LOG".format(container_name))
            file_name = db.get_set(conn_name)
            if not file_name:
                return
            cmd = "grep 'Chamber Profile' {} | grep Current | grep Expected".format(file_name)
            pipe = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            buf = pipe.stdout.read().decode("UTF-8")
            profile = []
            if buf:
                for line in buf.splitlines():
                    other, current, expect, _time = line.split(",")
                    profile.append(
                        {
                            "time": _time.strip(),
                            "Actual": current.split()[-1].strip(),
                            "Expect": expect.split()[-1].strip(),
                        }
                    )
            message = {"profile": profile}
            self.send(json.dumps(message))
            return
        else:
            action = text_data_json.get("action", None)
            if not action:
                return
            container = Container.get_by_name(name=text_data_json["name"])
            if action in ["Start Test", "Stop Test", "Deposit Test"]:
                if container.get_locking_status():
                    username = text_data_json.get("user", "")
                    if container.lock_by_user != username:
                        message = {"snack_bar": "{} was locked by {}".format(
                            container.name, container.lock_by_user)}
                        self.send(json.dumps(message))
                        return
                if action == "Start Test":
                    cmd = "free -h | grep Mem"
                    pipe = subprocess.Popen(
                        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                    )
                    mem = pipe.stdout.read().decode("UTF-8")
                    ram_total = mem.split()[1][:-1]
                    ram_used = mem.split()[2]
                    if 'M' in ram_used:
                        ram_used = round(int(ram_used[:-1]) / 1024, 2)
                    else:
                        ram_used = ram_used[:-1]
                    ram_usage = str(float(ram_used) / float(ram_total) * 100)[:4]
                    if float(ram_usage) > 90.:
                        message = {"snack_bar": "Current RAM Usage > 90%, Can't Start Test"}
                        self.send(json.dumps(message))
                        return
                    #
                    mode = text_data_json.get("mode", "PROD")
                    username = text_data_json.get("user", "")
                    container.start_test(mode=mode, username=username)
                    return
                elif action == "Stop Test":
                    stop_by_username = text_data_json.get("user", "")
                    container.stop_test(stop_by_username)
                    return
                elif action == "Deposit Test":
                    container.deposit_test()
                    return
            elif text_data_json["action"] == "Answer Question":
                answer = text_data_json["answer"]
                container.put_question_answer(answer=answer)
                return

    def question_message(self, event):
        self.send(text_data=event["text"])
        return

    def step_message(self, event):
        self.send(text_data=event["text"])
        return

    def udp_message(self, event):
        self.send(text_data=event["text"])
        return

    def connection_message(self, event):
        self.send(text_data=event["text"])
        return

    def url_message(self, event):
        self.send(text_data=event["text"])
        return

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)
        return
