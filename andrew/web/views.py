import socket
import re
import os
import json
import requests
import hashlib
import time
from base64 import b64encode as encode
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["get"])
def get_server_name(request):
    start_timestamp = time.time()
    server_name = socket.gethostname()
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Server Name Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": server_name,
            },
        }
    )


@api_view(["get"])
def get_notification(request):
    start_timestamp = time.time()
    try:
        notify = models.Notification.get_latest_notification()
    except Exception as e:
        print("Get Notification Meets Errors - [{}]".format(e))
        notify = {"notification": ""}
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Notification Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": notify,
            },
        }
    )


@api_view(["post"])
def set_notification(request):
    start_timestamp = time.time()
    data = request.data
    notify = data.get("notification", "No news is good news")
    username = data.get("username", "genius")
    # print('Notification - {}'.format(notify))
    models.Notification.create_notification(notify)
    models.History.save_one_message("{} set notification to [{}]".format(username, notify))
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Set Notification Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": "",
            },
        }
    )


@api_view(["post"])
def get_gac_authentication(request):
    pid = "PcrVO3vN3S13qcir9gEBa3rb2/o="  # it is 'genius'
    if request.method == "POST":
        data = request.data
        username = data.get("username", None)
        password = data.get("password", None)
        # print(username, password)
        if not username:
            return Response({"status": False, "msg": "Should provide username/password"})
        if not password:
            return Response({"status": False, "msg": "Should provide username/password"})
        # add a local account for engineer, in case LDAP server is unreachable.
        if username == "admin" and password == "Genius168!":
            return Response({"status": True, "user": "admin", "role": "engineer"})

        ldap_server = get_hosts().get("ldap-server", None)

        s = requests.Session()
        r = s.get("http://{}/get-signin-salt/?pid={}".format(ldap_server, pid))
        if not json.loads(r.text)["status"]:
            return Response({"status": False, "msg": "Wrong Project PID"})
        salt1 = json.loads(r.text)["salt1"]
        # print('salt1 - {}'.format(salt1))
        #
        secure = hashlib.sha1(pid.encode("utf-8"))
        secure.update(salt1.encode("utf-8"))
        result = encode(secure.digest() + salt1.encode("utf-8")).decode("utf-8")
        #
        # time.sleep(0.5)
        data = {"username": username, "password": password, "ssha": result}
        r = s.post("http://{}/post_signin/".format(ldap_server), data=data)
        # print('post - {}'.format(r.text))

        try:
            if not json.loads(r.text)["status"]:
                return Response({"status": False, "msg": "Incorrect username or password"})
        except Exception as e:
            return Response({"status": False, "msg": "Incorrect username or password"})
        user = json.loads(r.text)["profile"]["display_name"] + "(" + json.loads(r.text)["username"] + ")"
        if not json.loads(r.text)["project"]:
            return Response({"status": False, "msg": "{}, you dont have access to login".format(user)})
        if "engineer" in json.loads(r.text)["project"]:
            role = "engineer"
        else:
            role = "operator"
        del s
        return Response({"status": True, "user": user, "role": role})


@api_view(["get"])
def get_machine_status(request):
    """ Get CPU/HDD/RAM running status.
    :param request:
    :return:
    """
    start_timestamp = time.time()
    s = ssh2.SSH("GET-MACHINE-STATUS")
    try:
        s.open()
        s.send("\r", expectphrase=["]#", "]$"], timeout=60)
        try:  # LXC does not support CPU Info Check
            s.send('cat /proc/cpuinfo |grep "physical id" | wc -l\r', expectphrase=["]#", "]$"], timeout=60)
            cpu_core = s.recbuf.splitlines()[1].strip()
            s.send("mpstat | grep all\r", expectphrase=["]#", "]$"], timeout=60)
            cpu_idle = s.recbuf.splitlines()[1].split()[-1]
            cpu_usage = "CPU Usage: {}%, {} cores".format(round(100.0 - float(cpu_idle), 2), cpu_core)
        except Exception as e:
            print(e)
            cpu_usage = ""
        s.send("free -h | grep Mem\r", expectphrase=["]#", "]$"], timeout=60)
        ram_total = s.recbuf.splitlines()[1].split()[1][:-1]
        ram_used = s.recbuf.splitlines()[1].split()[2]
        if 'M' in ram_used:
            ram_used = round(int(ram_used[:-1]) / 1024, 2)
        else:
            ram_used = ram_used[:-1]
        ram_usage = "RAM Usage: {}%, {}G/{}G".format(
            str(float(ram_used) / float(ram_total) * 100)[:4], ram_used, ram_total
        )
        s.send("df -h | grep centos_genius\r", expectphrase=["]#", "]$"], timeout=60)
        hdd_total = s.recbuf.splitlines()[1].split()[1]
        hdd_used = s.recbuf.splitlines()[1].split()[2]
        hdd_usage = "HDD Usage: {}, {}/{}".format(s.recbuf.splitlines()[1].split()[4], hdd_used, hdd_total)
        usage = {"hdd_usage": hdd_usage, "ram_usage": ram_usage}
        if cpu_usage:
            usage.update({"cpu_usage": cpu_usage})
        return Response(
            {
                "status": True,
                "payload": {
                    "message": "Get Machine Status Successfully",
                    "time": "the request cost {}s".format(time.time() - start_timestamp),
                    "data": usage,
                },
            }
        )
    except Exception as e:
        # print(e)
        return Response(
            {
                "status": False,
                "payload": {
                    "message": "Could not get machine status, Background Service issue.",
                    "time": "the request cost {}s".format(time.time() - start_timestamp),
                    "data": "",
                },
            }
        )
    finally:
        s.close()
        del s


@api_view(["get"])
def get_prod_version(request):

    s = ssh2.SSH("GET-PROD-VERSION")
    fusion_server = ''
    with open('/etc/hosts', 'r') as f:
        for host in f.readlines():
            if 'fusion-server' not in host:
                continue
            fusion_server = host.split()[0]
    try:
        s.open()
        s.send('find /opt/prod -maxdepth 2 -name __init__.py\r', expectphrase=["]#", "]$"], timeout=60)
        repos = {}
        for line in s.recbuf.splitlines():
            if '/__init__.py' not in line:
                continue
            if '/opt/prod/__init__.py' in line:
                continue
            with open(line, 'r') as f:
                version = f.read().split('=')[-1].strip().strip('"')
            repos.update({line.split('/')[3]: version})
        versions = []
        for target, current in repos.items():
            r = requests.get('http://{}:8000/genius/get-repository-package/?repository={}'.format(
                fusion_server, target))
            packages = json.loads(r.text)['payload']['data']
            if not packages:
                latest = 'master'
            else:
                latest = packages[-1]['url'].split('-')[-1].strip('.tar.gz')

            versions.append({"repo": target, "current": current, "latest": latest})

        # is to get remove genius latest version
        fusion_server = ""
        with open("/etc/hosts", "r") as f:
            for host in f.readlines():
                if "fusion-server" not in host:
                    continue
                fusion_server = host.split()[0]
        # print('Fusion Server - {}'.format(fusion_server))
        packages = ["master"]
        if not fusion_server:
            packages = []
        r = requests.get("http://{}:8000/genius/get-genius-package/".format(fusion_server))
        if r.status_code == 500:
            packages = []
        if packages:
            packages = json.loads(r.text)["payload"]["data"]
        tags = []
        genius_latest = "master"
        if packages:
            for package in packages:
                if ".tar.gz" not in package["url"]:
                    continue
                tags.append(package["name"])
                ltags = get_correct_version_order(tags, from_git=False)
                genius_latest = ltags[-1]

        genius_current = ""
        with open("/opt/genius/gui/__init__.py", "r") as f:
            for _version in f.readlines():
                if "_VERSION" not in _version:
                    continue
                genius_current = _version.split("=")[1].strip().strip('""')

        versions.insert(0, {"repo": "genius", "current": genius_current, "latest": genius_latest})

        details = []
        new_version = False
        for version in versions:
            if version["current"] != version["latest"]:
                new_version = True
            details.append(
                "{}: Current[{}], Latest[{}]\n".format(version["repo"], version["current"], version["latest"])
            )
        return Response(
            {"status": True, "genius_version": genius_current, "details": details, "new_version": new_version}
        )
    except Exception as e:
        print("Get Prod Version Meets Errors - [{}]".format(e))
        # print(e)
        return Response({"status": False, "msg": "Could not get PROD Code version, Background Service issue."})
    finally:
        s.close()
        del s


def get_correct_version_order(recbuf, from_git=True):
    tags = []
    if from_git:
        for line in recbuf.splitlines():
            if "tags" not in line:
                continue
            if r"{}" in line:
                continue
            if "v" not in line:
                continue
            tags.append(line.split("/")[-1].strip())
    else:
        tags = recbuf

    ntags = []
    tag_raw = []
    tag_num = []
    for tag in tags:
        version, datestamp = tag.split("_")
        if len(datestamp) != 8:  # remove the bad tag
            continue
        if not re.match("v[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}", version):  # remove the bad tag
            continue
        ntags.append(tag)
        x = version[1:]  # remove 'v'
        num = ""
        for n in x.split("."):
            num += "{:03}".format(int(n))
        tag_num.append(int(num))
        tag_raw.append(int(num))
    tag_num.sort()
    final_tags = []
    for x in tag_num[-5:]:  # only use last 5 tag
        if ntags[tag_raw.index(x)] not in final_tags:
            final_tags.append(ntags[tag_raw.index(x)])
    return final_tags


@api_view(["post"])
def validate_gac_username(request):
    """ Login Step 1: Validate username
    :param request:
    :return:
    """
    start_timestamp = time.time()
    data = request.data
    username = data.get("username", None)
    fusion_server = get_hosts().get("fusion-server", None)
    if not fusion_server:
        fusion_server = "10.167.16.43"
    # print(fusion_server)
    if username in ['genius', 'engineer']:
        return Response(
            {
                "status": True,
                "payload": {
                    "message": "Login as dummy user.",
                    "time": "the request cost {}s".format(time.time() - start_timestamp),
                    "data": 'dummy',
                },
            }
        )
    if isinstance(username, str):
        username = username.upper()
    r = requests.post("http://{}:8000/acpro/validate-gac-username/".format(fusion_server), {"username": username})
    # print(r.text)
    salt = json.loads(r.text)["payload"]["data"]["salt"] if json.loads(r.text)["payload"]["data"] else ""
    return Response(
        {
            "status": json.loads(r.text)["status"],
            "payload": {
                "message": json.loads(r.text)["payload"]["message"],
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": salt,
            },
        }
    )


@api_view(["post"])
def get_gac_authentication2(request):
    """ Login Step 2: validate username & password(password is hashed already)
    :param request:
    :return:
    """
    start_timestamp = time.time()
    data = request.data
    user = {}
    username = data.get("username", None)
    password = data.get("password", None)

    if username in ['genius', 'engineer']:
        if (username == 'genius' and password == 'genius') or (username == 'engineer' and password == 'engineer'):
            status = True
            message = 'Login Successfully'
            token = 'genius'
            user.update({"username": username})
            user.update({"role": 'operator' if username == 'genius' else 'engineer'})
        else:
            status = False
            message = 'Username/Password NOT Match!'
            token = ''
        return Response(
            {
                "status": status,
                "payload": {
                    "message": message,
                    "time": "the request cost {}s".format(time.time() - start_timestamp),
                    "data": user,
                    "token": token,
                },
            }
        )

    fusion_server = get_hosts().get("fusion-server", None)
    if not fusion_server:
        fusion_server = "10.167.16.43"
    if username[0].isalpha() and username[1].isdigit():  # upper username for FOC ID.
        username = username.upper()
    r = requests.post(
        "http://{}:8000/acpro/get-gac-authentication/".format(fusion_server),
        {"username": username, "password": password},
    )
    if not json.loads(r.text)["status"]:
        return Response(
            {
                "status": False,
                "payload": {
                    "message": json.loads(r.text)["payload"]["message"],
                    "time": "the request cost {}s".format(time.time() - start_timestamp),
                    "data": [],
                },
            }
        )
    data = json.loads(r.text)["payload"]["data"]
    name = data["profile"]["name"] + "(" + data["username"] + ")"
    user.update({"username": name})
    user.update({"updated_at": data["profile"]["updated_at"]})
    user.update({"expire": data["profile"]["expire"]})
    status = json.loads(r.text)["status"]
    message = json.loads(r.text)["payload"]["message"]
    if json.loads(r.text)["status"]:
        r1 = requests.get(
            "http://{}:8000/acpro/get-gac-project-access/".format(fusion_server),
            {"username": username, "project": "genius"},
        )

        if not json.loads(r1.text)["payload"]["data"]:
            status = False
            message = "{} doesn't have any access to genius".format(username)
            user = {}
        else:
            role = json.loads(r1.text)["payload"]["data"][0]
            # role = {'genius': ['engineer']}
            if isinstance(role, dict):  # 20190427, since fusion change the logic.
                role = role["genius"][0]
            user.update({"role": role})
            if role not in ["engineer", "operator", "manager"]:
                status = False
                message = "{} doesn't have access to genius".format(username)
                user = {}

    return Response(
        {
            "status": status,
            "payload": {
                "message": message,
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": user,
                "token": 'genius',
            },
        }
    )


def gac_authentication(username, password):
    pid = "PcrVO3vN3S13qcir9gEBa3rb2/o="  # it is 'genius'
    ldap_server = get_hosts().get("ldap-server", None)
    s = requests.Session()
    r = s.get("http://{}/get-signin-salt/?pid={}".format(ldap_server, pid))
    if not json.loads(r.text)["status"]:
        return {"status": False, "msg": "Wrong Project PID"}
    salt1 = json.loads(r.text)["salt1"]
    # print('salt1 - {}'.format(salt1))
    #
    secure = hashlib.sha1(pid.encode("utf-8"))
    secure.update(salt1.encode("utf-8"))
    result = encode(secure.digest() + salt1.encode("utf-8")).decode("utf-8")
    #
    # time.sleep(0.5)
    data = {"username": username, "password": password, "ssha": result}
    r = s.post("http://{}/post_signin/".format(ldap_server), data=data)
    # print('post - {}'.format(r.text))

    try:
        if not json.loads(r.text)["status"]:
            return {"status": False, "msg": "Incorrect username or password"}
    except Exception as e:
        return {"status": False, "msg": "Wrong username or password!"}

    user = json.loads(r.text)["profile"]["display_name"] + "(" + json.loads(r.text)["username"] + ")"
    if not json.loads(r.text)["project"]:
        return {"status": False, "msg": "{}, you dont have access to login".format(user)}
    if "engineer" in json.loads(r.text)["project"]:
        role = "engineer"
    else:
        role = "operator"
    del s
    return {"status": True, "user": user, "role": role}


def get_hosts():
    hosts = {}
    with open("/etc/hosts", "r") as f:
        for host in f.readlines():
            if "-server" not in host:
                continue
            server = host.split()[1]
            ip_address = host.split()[0]
            hosts[server] = ip_address
    return hosts


@api_view(["get"])
def get_hosts_name(request):
    start_timestamp = time.time()
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get /etc/hosts Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": get_hosts(),
            },
        }
    )


@api_view(["get"])
def get_current_log(request):
    start_timestamp = time.time()
    connection = request.GET.get("connection", None)
    host = request.GET.get("host", None)
    container = connection.split(":")[0] + ":" + connection.split(":")[1]
    db = redis.Redis("{}_TEST_LOG".format(container.upper()))
    file_name = db.get_set("__" + connection.upper())
    path = file_name.replace("/opt/genius/gen/", "https://{}/".format(host))

    # cmd = "tail -n 300 {}".format(file_name)
    # pipe = subprocess.Popen(
    #     cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    # )
    # log = pipe.stdout.read().decode("UTF-8")
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Current Test Log Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": {
                    "path": path,
                    # "log": log,
                },
            },
        }
    )


@api_view(["post"])
def get_record_by_sernum(request):
    """ Get data from Data Center, only use for Vision
    :param request:
    :return:
    """
    data = request.data
    fusion_server = get_hosts().get("fusion-server", None)
    month = data.get("month", 3)
    if month < 1:
        month = 3
    data["month"] = month
    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.post("http://{}:8000/vision/get-record-by-sernum/".format(fusion_server), data=data)
    return Response(json.loads(r.text))


@api_view(["get"])
def get_record_by_sernum2(request):
    """ This API is used for Other Genius Server to get test data.
    :param request:
    :return:
    """
    start_time = time.time()

    sernum = request.GET.get("sernum", "")
    month = request.GET.get("month", 3)
    if month < 1:
        month = 3
    test_data = models.TestData.get_test_data(sernum, month)
    test_data_serializer = serializers.TestDataSerializer(test_data, many=True)
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Test Data Successfully",
                "time": "the request cost {}s".format(time.time() - start_time),
                "data": test_data_serializer.data,
            },
        }
    )


@api_view(["post"])
def data_visualization(request):
    """
    service:
    get-data-summary
    get-data-details
    get-data-excel
    delete-data-cache
    :param request:
    :return:
    """
    data = request.data
    fusion_server = get_hosts().get("fusion-server", None)
    service = data.get("service", "")
    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.post("http://{}:8000/vision/{}/".format(fusion_server, service), data=data)
    if service in ["get-data-excel"]:
        # Download file to local firstly.
        test_logs = json.loads(r.text)
        # print(test_logs)
        if test_logs.get("status"):
            if test_logs["payload"]["data"]:
                file_name = test_logs["payload"]["data"]["url"].split("/")[-1]
                file_path = "/opt/logs/tmp/{}".format(file_name)
                if not os.path.exists(file_path):
                    r = requests.get(test_logs["payload"]["data"]["url"], stream=True)
                    f = open(file_path, "wb")
                    for chunk in r.iter_content(chunk_size=512):
                        if chunk:
                            f.write(chunk)
                hostname = socket.gethostname()
                host = socket.gethostbyname(hostname)
                test_logs["payload"]["data"]["url"] = "https://{}/logs/tmp/{}".format(host, file_name)
                return Response(test_logs)
    return Response(json.loads(r.text))


@api_view(["get"])
def get_container_info(request):
    """ For Connection Page INFO window
    :param request:
    :return:
    """
    start_timestamp = time.time()
    container_name = request.GET.get("container", "")
    container = models.Container.get_by_name(container_name)
    station = container.station

    sequence = container.sequence
    pid_map = json.loads(container.pid_map) if container.pid_map else {}
    configuration_data = json.loads(container.configuration_data) if container.configuration_data else {}
    sync_group = json.loads(station.sync_group) if station.sync_group else {}
    connections = models.Connection.get_connections_by_container(container=container)

    info = "Pre SEQ: \r\n{}\r\n\r\n".format(sequence)
    info += "PID Map:\r\n"
    for key, value in pid_map.items():
        info += "{} = {}\r\n".format(key, value)
    info += "\r\nConfiguration Data:\r\n"
    for key, value in configuration_data.items():
        info += "{} = {}\r\n".format(key, value)
    info += "\r\nSync Group:\r\n"
    for key, value in sync_group.items():
        info += "{} = {}\r\n".format(key, value)
    info += "\r\nConnection Info:\r\n"

    for conn in connections:
        if "INFO" in conn.name:
            continue
        if "SEQ_LOG" in conn.name:
            continue
        if "STEP" in conn.name:
            continue
        if conn.protocol in ["terminalserver", "telnet"]:
            info += "{}: {}|{}|{}|{}|{}|{}\r\n".format(
                conn.name.split(":")[-1], conn.protocol, conn.host, conn.port, conn.username, conn.password, conn.prompt
            )
        else:
            info += "{}: {}\r\n".format(conn.name.split(":")[-1], conn.protocol)
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Container Information Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": info,
            },
        }
    )


@api_view(["get"])
def get_station_page(request):
    """ Render Station page
    :param request:
    :return:
    """
    start_timestamp = time.time()
    stations = models.Station.get_all_stations()
    station_serializer = serializers.StationSerializer(stations, many=True)
    data = station_serializer.data
    # print(data)
    data1 = dict()
    for d in data:
        data1.update({d["name"]: d})
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Station Page Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": data1,
            },
        }
    )


@api_view(["get"])
def get_container_page(request):
    """ Render container page base on station name.
    :param request:
    :return:
    """
    start_timestamp = time.time()
    station_name = request.GET.get("station_name", "").upper()
    station = models.Station.get_by_name(name=station_name.split("/")[-1])
    containers = models.Container.get_all_containers(station=station)
    container_serializer = serializers.ContainerSerializer(containers, many=True)
    data = container_serializer.data
    # print(data)
    data1 = dict()
    for d in data:
        data1.update({d["name"]: d})
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Container Page Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": data1,
            },
        }
    )


@api_view(["get"])
def get_history(request):
    start_timestamp = time.time()
    history = models.History.get_last_manipulation()
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get History Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": history,
            },
        }
    )


@api_view(["get"])
def get_container_style(request):
    start_timestamp = time.time()
    style = models.Configuration.get_style()
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Container Style Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": style,
            },
        }
    )


@api_view(["post"])
def set_container_style(request):
    start_timestamp = time.time()
    data = request.data
    style = data.get("style", "DYNAMIC")
    username = data.get("username", "genius")
    models.Configuration.set_style(style)
    models.History.save_one_message("{} set style to [{}]".format(username, style))
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Set Container Style Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": [],
            },
        }
    )


@api_view(["get"])
def get_theme(request):
    start_timestamp = time.time()
    theme = models.Configuration.get_theme()
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Theme Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": theme,
            },
        }
    )


@api_view(["post"])
def set_theme(request):
    start_timestamp = time.time()
    data = request.data
    theme = data.get("theme", "purple")
    username = data.get("username", "genius")
    models.Configuration.set_theme(theme)
    models.History.save_one_message("{} set theme to [{}]".format(username, theme))
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Set Theme Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": [],
            },
        }
    )


@api_view(["post"])
def lock_container(request):
    start_timestamp = time.time()
    data = request.data
    container_name = data.get("container_name", "").upper()
    username = data.get("username", "genius")

    container = models.Container.get_by_name(container_name)
    if not container:
        message = "container [{}] is not found".format(container_name)
    else:
        if not container.get_locking_status():
            if container.set_locking_locked(username):
                message = "Lock container [{}] successfully".format(container_name)
                models.History.save_one_message("{} lock container [{}]".format(username, container_name))
            else:
                message = "Lock container [{}] meet Error".format(container_name)
        else:
            message = "container [{}] is locked already".format(container_name)
    return Response(
        {
            "status": True,
            "payload": {
                "message": message,
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": [],
            },
        }
    )


@api_view(["post"])
def unlock_container(request):
    start_timestamp = time.time()
    data = request.data
    container_name = data.get("container_name", "").upper()
    username = data.get("username", "genius")
    container = models.Container.get_by_name(container_name)
    if not container:
        message = "container [{}] is not found".format(container_name)
    else:
        if container.get_locking_status():
            if container.set_locking_unlocked():
                message = "Unlock container [{}] successfully".format(container_name)
                models.History.save_one_message("{} unlock container [{}]".format(username, container_name))
            else:
                message = "Unlock container [{}] meet Error".format(container_name)
        else:
            message = "container [{}] is unlocked already".format(container_name)
    return Response(
        {
            "status": True,
            "payload": {
                "message": message,
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": [],
            },
        }
    )


@api_view(["get"])
def get_parent_children(request):
    parent_serial_number = request.GET.get("parent_serial_number", "")
    fusion_server = get_hosts().get("fusion-server", None)
    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.get(
        "http://{}:8000/genius/get-parent-children/".format(fusion_server),
        {"parent_serial_number": parent_serial_number},
    )
    return Response(json.loads(r.text))


@api_view(["get"])
def get_parent_children(request):
    parent_serial_number = request.GET.get("parent_serial_number", "")
    fusion_server = get_hosts().get("fusion-server", None)
    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.get(
        "http://{}:8000/genius/get-parent-children/".format(fusion_server),
        {"parent_serial_number": parent_serial_number},
    )
    return Response(json.loads(r.text))


@api_view(["get"])
def get_test_log_list(request):
    time_stamp = request.GET.get("time_stamp", "")  # 2019-05-22 14:13:34.886663+08:00
    machine = request.GET.get("machine", "")
    container = request.GET.get("container", "")
    host = request.GET.get("host", "")
    if not host:
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)

    test_log_server = get_hosts().get("test-log-server", None)
    if not test_log_server:
        # test_log_server = '10.167.219.252'
        test_log_server = "10.167.16.43"
    r = requests.get(
        "http://{}:8000/genius/get-test-log/".format(test_log_server),
        {"machine": machine, "time_stamp": time_stamp, "container": container},
    )
    test_logs = json.loads(r.text)
    # print(test_logs)
    if test_logs.get("status"):
        for log in test_logs["payload"]["data"]:
            # print(log)
            if log:
                file_name = log["url"].split("/")[-1]
                file_path = "/opt/logs/tmp/{}".format(file_name)
                if not os.path.exists(file_path):
                    r = requests.get(log["url"], stream=True)
                    f = open(file_path, "wb")
                    for chunk in r.iter_content(chunk_size=512):
                        if chunk:
                            f.write(chunk)
                log["url"] = "https://{}/logs/tmp/{}".format(host, file_name)
    # print(test_logs)
    return Response(test_logs)


@api_view(["get"])
def get_test_status(request):
    start_timestamp = time.time()
    container = request.GET.get("container", "")
    container_obj = models.Container.get_by_name(name=container)
    if not container_obj:
        return Response({"result": False, "msg": "Could not find container - {}".format(container)})
    return Response({"result": True, "status": container_obj.status})


@api_view(["get"])
def start_test(request):
    start_timestamp = time.time()
    container = request.GET.get("container", "")
    container_obj = models.Container.get_by_name(name=container)
    if not container_obj:
        return Response({"result": False, "msg": "Could not find container - {}".format(container)})
    if container_obj.status != "idle":
        return Response(
            {
                "result": False,
                "msg": "{} current status is {}, only idle status could be started test".format(
                    container, container_obj.status
                ),
            }
        )
    mode = "PROD"
    username = "REST API"
    container_obj.start_test(mode=mode, username=username)
    return Response({"result": True, "msg": "{} is started Already".format(container)})


@api_view(["get"])
def stop_test(request):
    start_timestamp = time.time()
    container = request.GET.get("container", "")
    container_obj = models.Container.get_by_name(name=container)
    if not container_obj:
        return Response({"result": False, "msg": "Could not find container - {}".format(container)})
    if container_obj.status != "run":
        return Response(
            {
                "result": False,
                "msg": "{} current status is {}, only run status could be stopped test".format(
                    container, container_obj.status
                ),
            }
        )
    stop_by_username = "REST API"
    container_obj.stop_test(stop_by_username)
    return Response({"result": True, "msg": "{} is stopped Already".format(container)})


@api_view(["get"])
def deposit_test(request):
    start_timestamp = time.time()
    container = request.GET.get("container", "")
    container_obj = models.Container.get_by_name(name=container)
    if not container_obj:
        return Response({"result": False, "msg": "Could not find container - {}".format(container)})
    if container_obj.status not in ["stop", "fail"]:
        return Response(
            {
                "result": False,
                "msg": "{} current status is {}, only fail or stop status could be deposited test".format(
                    container, container_obj.status
                ),
            }
        )
    container_obj.deposit_test()
    return Response({"result": True, "msg": "{} is deposited Already".format(container)})


@api_view(["post"])
def create_vision(request):
    start_timestamp = time.time()
    data = request.data
    # print(data)
    models.Vision.create_vision(
        data.get("username"),
        data.get("project"),
        data.get("uuttype"),
        data.get("area"),
        data.get("machine"),
        data.get("sernum"),
        data.get("period"),
        data.get("result"),
        data.get("field"),
    )
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Create Vision Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": "",
            },
        }
    )


@api_view(["post"])
def update_vision(request):
    start_timestamp = time.time()
    data = request.data
    models.Vision.update_vision(
        data.get("idx"),
        data.get("username"),
        data.get("project"),
        data.get("uuttype"),
        data.get("area"),
        data.get("machine"),
        data.get("sernum"),
        data.get("period"),
        data.get("result"),
        data.get("field"),
    )
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Update Vision Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": "",
            },
        }
    )


@api_view(["post"])
def delete_vision(request):
    start_timestamp = time.time()
    data = request.data
    models.Vision.delete_vision(data.get("idx"))
    return Response(
        {
            "status": True,
            "payload": {
                "message": "Delete Vision Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": "",
            },
        }
    )


@api_view(["get"])
def get_vision(request):
    start_timestamp = time.time()
    username = request.GET.get("username")
    # print(username)
    data = models.Vision.get_vision(username)
    # print(data)
    vision_serializer = serializers.VisionSerializer(data, many=True)

    return Response(
        {
            "status": True,
            "payload": {
                "message": "Get Vision Successfully",
                "time": "the request cost {}s".format(time.time() - start_timestamp),
                "data": vision_serializer.data,
            },
        }
    )


@api_view(["post"])
def gac_account(request):
    data = request.data
    fusion_server = get_hosts().get("fusion-server", None)
    service = data.get("service", "")
    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.post("http://{}:8000/acpro/{}/".format(fusion_server, service), data=data)
    return Response(json.loads(r.text))


@api_view(["post"])
def genius_service(request):
    data = request.data
    fusion_server = get_hosts().get("fusion-server", None)
    service = data.get("service", "")
    data1 = data.get("data", "")

    if not fusion_server:
        fusion_server = "10.167.16.43"
    r = requests.post("http://{}:8000/genius/{}/".format(fusion_server, service), data=data1)
    return Response(json.loads(r.text))
