import unittest
import redis

from andrew import broker


class TestBroker(unittest.TestCase):

    def setUp(self):
        self.r = redis.Redis("localhost", 6379)
        self.b = broker.Broker("TEST")
        self.b1 = broker.Broker("TEST1")

    def tearDown(self):
        self.r.flushall()
        del self.r

    def test_push_pop(self):
        """
        Check if it works like First In First Out.
        :return:
        """
        self.b.push("hello")
        self.b1.push("world")
        self.b.push("good")
        self.b1.push("job")
        self.b.push("1111")
        self.b.push("3.1415926")

        self.assertEqual(self.b.pop(), "hello")
        self.assertEqual(self.b.pop(), "good")
        self.assertEqual(self.b.pop(), "1111")
        self.assertEqual(self.b.pop(), "3.1415926")

        self.assertEqual(self.b1.pop(), "world")
        self.assertEqual(self.b1.pop(), "job")
        return

    def test_append(self):
        """
        append str "hello" & "," & "world", to see if could get "hello,world"
        :return:
        """
        self.b.append("UUT00", "hello")
        self.b1.append("UUT00", "hello")
        self.b.append("UUT00", ",")
        self.b.append("UUT00", "world")
        self.assertEqual(self.r["TEST:UUT00"], "hello,world")
        self.assertEqual(self.r["TEST1:UUT00"], "hello")
        return

    def test_get(self):
        """
        if get nothing, then nothing is ""
        :return:
        """
        self.assertEqual(self.b.get("UUT00"), None)
        self.b.set("UUT00", ["LIST"])
        self.assertEqual(self.b.get("UUT00"), ["LIST"])
        return

    def test_get_str(self):
        """
        if get nothing, then nothing is ""
        :return:
        """
        self.assertEqual(self.b.get_str("UUT00"), "")
        self.b.set("UUT00", ["LIST"])
        self.assertEqual(self.b.get_str("UUT00"), ["LIST"])
        return

    def test_get_list(self):
        """
        if get nothing, then nothing is []
        :return:
        """
        self.assertEqual(self.b.get_list("UUT00"), [])
        self.b.set("UUT00", ["LIST"])
        self.assertEqual(self.b.get_list("UUT00"), ["LIST"])
        return

    def test_get_dict(self):
        """
        if get noting, then nothing is {}
        :return:
        """
        self.assertEqual(self.b.get_dict("UUT00"), {})
        self.b.set("UUT00", ["LIST"])
        self.assertEqual(self.b.get_dict("UUT00"), ["LIST"])
        return

    def test_get_keys(self):
        """
        set two pares, hello:world & good:job, will get ["hello", "good"]
        :return:
        """
        self.b.set("UUT00", ["LIST"])
        self.b.set("UUT01", ["LIST"])
        self.assertEqual(self.b.get_keys(), ["TEST:UUT00", "TEST:UUT01"])
        return


if __name__ == "__main__":
    unittest.main()
