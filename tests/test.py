import sys
from multiprocessing import Pool
import time

sys.path.append("/opt/andrew")

from andrew import conn
from andrew import logger


log = logger.get_event_logger("/tmp/event.log", echo=True)


def check_memory(h: str) -> None:
    an = conn.CONN(h, "genius", password="genius", open=True)
    an.set_logger("/tmp/conn_{}.log".format(h))

    an.send("df -h / | tail -n1 | awk '{print $5}'\r", expectphrase="]$", timeout=60)
    log.info("{} - {}".format(h, an.buf.splitlines()[0]))
    an.close()
    return


hosts = ["10.167.16.43", "10.167.16.42", "10.167.16.41"]

# start_time = time.time()
# for host in hosts:
#     check_memory(host)
# log.debug("serial costs {}".format(time.time() - start_time))


start_time = time.time()
# for host in ["10.167.16.43", "10.167.16.42", "10.167.16.41"]:
#     p = Process(target=check_memory, args=(host,))
#     p.start()
# p.join()

with Pool(len(hosts)) as p:
    p.map(check_memory, hosts)
log.debug("parallel costs {}".format(time.time() - start_time))

#
# an = conn.CONN("10.167.16.43", "genius")
# start_time = time.time()
#
# an.set_logger("/tmp/conn.log")
# log.error("Open Connection...")
# an.open()
# # input("Hold for while...")
#
#
# an.get("/tmp/genius-service-uwsgi.log", "/tmp/genius-service-uwsgi1.log")
# an.put("/tmp/genius-service-uwsgi1.log", "/tmp/")
#
# an.send("ls -lt /tmp\r", expectphrase="]$", timeout=60)
#
# # print(an.buf)
#
# # an.close()
# # an.open()
# an.send("cd\r", expectphrase="]$", timeout=60)
# an.send("free -h | grep Mem:\r", expectphrase="]$", timeout=60)
# an.close()
# log.critical("test costs {}".format(time.time() - start_time))

"""
[root@focdev1 andrew]# cd tests/
[root@focdev1 tests]# python3 test.py 
10.167.16.43 - 34%
10.167.16.42 - 15%
10.167.16.41 - 3%
serial costs 1.0282611846923828
10.167.16.42 - 15%
10.167.16.43 - 34%
10.167.16.41 - 3%
parallel costs 0.5189542770385742
[root@focdev1 tests]# 
[root@focdev1 tests]# python3 test.py 
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.43 - 34%">
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.42 - 15%">
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.41 - 3%">
<LogRecord: EVENT, 10, test.py, 26, "serial costs 1.0288100242614746">
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.42 - 15%">
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.43 - 34%">
<LogRecord: EVENT, 20, test.py, 17, "10.167.16.41 - 3%">
<LogRecord: EVENT, 10, test.py, 37, "parallel costs 0.5167901515960693">
[root@focdev1 tests]# 
[root@focdev1 tests]# cat /tmp/event.log 
Mon 04 May 2020 16:44:18|INFO    : 10.167.16.43 - 34%
Mon 04 May 2020 16:44:18|INFO    : 10.167.16.42 - 15%
Mon 04 May 2020 16:44:18|INFO    : 10.167.16.41 - 3%
Mon 04 May 2020 16:44:18|DEBUG   : serial costs 1.0288100242614746
Mon 04 May 2020 16:44:19|INFO    : 10.167.16.42 - 15%
Mon 04 May 2020 16:44:19|INFO    : 10.167.16.43 - 34%
Mon 04 May 2020 16:44:19|INFO    : 10.167.16.41 - 3%
Mon 04 May 2020 16:44:19|DEBUG   : parallel costs 0.5167901515960693
[root@focdev1 tests]#
[root@focdev1 tests]# cat /tmp/conn_10.167.16.41.log
[genius@gitlab-server ~]$ df -h / | tail -n1 | awk '{print $5}'
3%
[genius@gitlab-server ~]$ 
----------Connection is closed----------
[root@focdev1 tests]# 
"""