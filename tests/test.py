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
