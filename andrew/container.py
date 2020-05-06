from andrew import broker


class Container(object):

    def __init__(self, container_name: str):
        self.container_name = container_name
        self.b = broker.Broker(self.container_name)
        keys = self.b.get_dict(self.container_name)
        return

    def start_test(self, prod: str, username: str):
        return

    def stop_test(self, username: str):
        return

    def fail_test(self, username: str = "andrew"):
        return

    def pass_test(self, username: str = "andrew"):
        return

    def depository(self, username: str):
        return

    def set_display1(self, msg: str):
        return

    def set_display2(self, msg: str):
        return

    def set_display3(self, msg: str):
        return

    def set_progress(self, progress: int):
        return

    def set_container_block(self, block: bool = False):
        return

    def set_container_lock(self, lock: bool = False):
        return

    def set_container_color(self, color: str):
        return

    def set_queue_status(self, queue: str):
        return

    def set_sync_status(self, sync: str):
        return

    def set_starter_name(self):
        return

    def get_pre_sequence(self):
        pass

    def get_main_sequence(self, name: str):
        pass

    def get_container_status(self):
        return

    def get_starter_name(self):
        return

    def ask_question(
            self,
            question: str,
            answers: list,
            image: str,
            answer: str,
            visible: bool = True,
            timeout: int = 60 * 60,
    ):
        pass

    def update(self):
        return
