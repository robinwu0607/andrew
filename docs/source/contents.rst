Welcome to Andrew!
==================================

Andrew is a python3 package name. It is Paramiko based Remote Execution.

Andrew provides a new method to interact with remote Shell **continuously**.

   >>> from andrew import conn
   >>> host = "web1"
   >>> an = conn.CONN(host, "username", password="pswd", open=True)
   >>> an.send("df -h / | tail -n1 | awk '{print $5}'\r", expectphrase="]$", timeout=60)
   >>> print("{} - {}".format(host, an.buf.splitlines()[0]))
   web1 - 34%

Andrew defined the **expectphrase** & **timeout** in **send()** method, once got ``]$`` within ``60s``, the **send()** finished.
``an.buf`` contains the all output from remote console.

How is it used?
-----------------
Create a function contains some commands.

   >>> def check_system(host: str) -> None:
   ...   an = conn.CONN(host, "username", password="pswd", open=True)
   ...   an.send("df -h / | tail -n1 | awk '{print $5}'\r", expectphrase="]$", timeout=60)
   ...   print(an.buf)
   ...   an.send("free -m\r", expectphrase="]$", timeout=60)
   ...   print(an.buf)
   ...   an.send("ls -lt\r", expectphrase="]$", timeout=60)
   ...   print(an.buf)
   ...   an.close()
   ...   return
   ...
   >>>

* Involve the function on individual hosts.

   >>> check_system("web1")

* Involve the function on multiple hosts, by serial.

   >>> hosts = ["web1", "web2", "web3"]
   >>> for host in hosts:
   ...  check_system(host)
   ...
   >>>

* Involve the function on multiple hosts, by parallel.

   >>> from multiprocessing import Pool
   >>> hosts = ["web1", "web2", "web3"]
   >>> with Pool(len(hosts)) as p:
   ...  p.map(check_memory, hosts)
   ...
   >>>

* Save Connection output log to local file.

   >>> from andrew import conn
   >>> from andrew import logger
   >>> host = "web1"
   >>> an = conn.CONN(host, "username", password="pswd", open=True)
   >>> an.set_logger("/tmp/conn.log")
   >>> an.send("df -h / | tail -n1 | awk '{print $5}'\r", expectphrase="]$", timeout=60)
   >>> print("{} - {}".format(host, an.buf.splitlines()[0]))
   web1 - 34%

The Connection log will be saved into ``/tmp/conn.log``, if you ``cat`` it, you could see::

   [root@web tests]# cat /tmp/conn.log
   [user@gitlab-server ~]$ df -h / | tail -n1 | awk '{print $5}'
   3%
   [user@gitlab-server ~]$
   ----------Connection is closed----------

* Save Event log to local file.

   >>> from andrew import conn
   >>> from andrew import logger
   >>> host = "web1"
   >>> an = conn.CONN(host, "username", password="pswd", open=True)
   >>> log = logger.get_event_logger("/tmp/event.log", echo=True)
   >>> an.send("df -h / | tail -n1 | awk '{print $5}'\r", expectphrase="]$", timeout=60)
   >>> log.info("{} - {}".format(host, an.buf.splitlines()[0]))
   <LogRecord: EVENT, 20, test.py, 17, "web1 - 34%">

The Event log will be saved into ``/tmp/event.log``, if you ``cat`` it, you could see::

   [root@web tests]# cat /tmp/event.log
   Mon 04 May 2020 16:44:18|INFO    : web1 - 34%


How is it Installed?
-----------------------
It is quite easy to install ``Andrew``::

   git clone https://github.com/andrew-wu2015/andrew.git
   cd andrew
   python3 setup.py install


That is ALL!!!
