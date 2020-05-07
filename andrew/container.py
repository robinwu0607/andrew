from andrew import broker


class Container(object):
    container = dict(
        name="PCBST:UUT00",  # Container Name
        test_time="12:12:12",  # Test Time Total
        mode="PROD",  # PROD & DEBUG
        display1="SERNUM",
        display2="UUTTYPE",
        display3="STEP",
        progress=0,
        status="idle",  # stop, idle, fail, pass, run
        disabled=False,  # or True, define in config.py, if disabled=True, then there is not start icon.
        blocked=False,  # or True, if blocked=True, then could not start by other Container.
        locked=False,  # or True, if locked=True, then could not click start icon.
        queue="",  # "WAIT", "GOT", show queue icon on WEB.
        sync="",  # "WAIT", "LEAD", show sync icon on WEB.
        color="",  # "red", "green", "yellow", "white", show color on WEB.
        starter="andrew",  # the starter name
        stopper="andrew",  # the stopper name
        depositor="",  # the depositor name
        question="",  # the question title
        answers=[],  # the questions pre-define answers
        visible=True,  # show if answer is visible or not
        answer="",  # the answer user input.
        image="",  # the question image show on WEB.
        timeout=0,  # the question timeout, user should answer the question within timeout.
        pid=10000000,  # the current Container process pid.
    )

    def __init__(self, container_name: str):
        self.container_name = container_name
        self.b = broker.Broker("CONTAINER")
        container = self.b.get(container_name)
        self.container.update(container)
        return

    def start_test(self, mode: str, name: str):
        self.update({"starter": name, "mode": mode})
        return

    def stop_test(self, name: str):
        self.update({"stopper": name})
        return

    def fail_test(self):
        return

    def pass_test(self):
        return

    def deposit_test(self, name: str = "andrew"):
        self.update({"depositor": name})
        return

    def set_mode(self, mode: str):
        self.update({"mode": mode})
        return

    def set_display1(self, msg: str):
        self.update({"display1": msg})
        return

    def set_display2(self, msg: str):
        self.update({"display2": msg})
        return

    def set_display3(self, msg: str):
        self.update({"display3": msg})
        return

    def set_progress(self, progress: int):
        self.update({"progress": progress})
        return

    def set_container_block(self, block: bool = False):
        self.update({"blocked": block})
        return

    def set_container_lock(self, lock: bool = False):
        self.update({"lock": lock})
        return

    def set_container_color(self, color: str):
        self.update({"color": color})
        return

    def set_queue_status(self, queue: str):
        self.update({"queue": queue})
        return

    def set_sync_status(self, sync: str):
        self.update({"sync": sync})
        return

    def set_starter_name(self, name: str):
        self.update({"starter": name})
        return

    def set_stopper_name(self, name: str):
        self.update({"stopper": name})
        return

    def set_depositor_name(self, name: str):
        self.update({"depositor": name})
        return

    def set_answer(self, answer: str):
        self.update({"answer": answer})
        return

    def ask_question(
            self,
            question: str,
            answers: list,
            image: str,
            visible: bool = True,
            timeout: int = 60 * 60,
    ):
        self.update({
            "question": question,
            "answers": answers,
            "image": image,
            "visible": visible,
            "timeout": timeout,
        })

    def update(self, data: dict):
        self.b.set(self.container_name, self.container.update(data))
        return
