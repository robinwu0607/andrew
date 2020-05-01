import argparse

__author__ = "Robin Wu"


parser = argparse.ArgumentParser(description="""Andrew CLI Interface Helper""")

parser.add_argument("--host", dest="Destination Host name or IP address")
parser.add_argument("--user", dest="Username to login Host")
parser.add_argument("--pswd", dest="Password to login Host")
parser.add_argument("--port", dest="SSH Port to login Host, default value: 22")

