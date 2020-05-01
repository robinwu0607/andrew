from andrew import connection

an = connection.Connection("10.167.16.43", username="genius", password="genius")

an.set_logger("/tmp/test.log")
an.open()

#
# # an.get("/tmp/genius-service-uwsgi.log", "/tmp/genius-service-uwsgi1.log")
# # an.put("/tmp/genius-service-uwsgi1.log", "/tmp/")
#
an.send("ls -lt /tmp\r", expectphrase="]$", timeout=60)
# print(an.buf)

# an.close()
# an.open()
an.send("cd\r", expectphrase="]$", timeout=60)
an.send("free -h | grep Mem:\r", expectphrase="]$", timeout=60)
print(an.buf)
an.close()
