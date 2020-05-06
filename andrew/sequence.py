import types
import re
import time
import datetime
import threading
from ..utils import utility
from andrew import broker


name_checker = re.compile('^[a-zA-Z0-9_\- ]+$')

step_total_count = 0
step_finish_count = 0
continue_on_error_list = []

step_branch_name = ""


class ParallelThread(threading.Thread):
    def __init__(self, target=None, name=None,
                 args=(), kwargs=None):
        self._target = None
        self._args = None
        super(ParallelThread, self).__init__(None, target=target,
                                             args=args, kwargs=kwargs, daemon=True)
        self.test_name = name
        self.exitcode = 0
        self.exception = None
        self.exc_traceback = ''

    def run(self):  # Overwrite run() method, put what you want the thread do here
        try:
            if self._target:
                self._target(*self._args)
        except Exception as e:
            self.exitcode = 1
            self.exception = e
            # self.exc_traceback = ''.join(traceback.format_exception(*sys.exc_info()))  # 在改成员变量中记录异常信息
            raise


class DefinitionBase(object):
    def __init__(self, **kwarg):
        """
        :param kwarg:
        """
        self.__args__ = {'adt_enabled': kwarg.get('adt_enabled', False),
                         'loop_on_error': kwarg.get('loop_on_error', 0),
                         'in_parallel': kwarg.get('in_parallel', False),
                         'iterations_qty': kwarg.get('iterations_qty', 1),
                         'iterations_time': kwarg.get('iterations_time', 0),
                         'continue_on_error': kwarg.get('continue_on_error', False),
                         'prerequisite': kwarg.get('prerequisite', True),
                         'finalization': kwarg.get('finalization', False),
                         }

        if not isinstance(self.__args__['adt_enabled'], bool):
            raise Exception(
                'adt_enabled should True or False, but it is {}'.format(type(self.__args__['adt_enabled'])))

        if not isinstance(self.__args__['iterations_qty'], int):
            raise Exception('iterations_qty should be number, but it is {}'.format(type(self.__args__['iterations_qty'])))

        if not isinstance(self.__args__['iterations_time'], int):
            raise Exception('iterations_time should be number, but it is {}'.format(type(self.__args__['iterations_time'])))

        if self.__args__['iterations_qty'] < 1:
            self.__args__['iterations_qty'] = 1

        if self.__args__['iterations_time'] < 0:
            self.__args__['iterations_time'] = 0

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    @property
    def finalization(self):
        """
        :return:
        """
        return self.__args__['finalization']

    @property
    def adt_enabled(self):
        """
        :return:
        """
        return self.__args__['adt_enabled']

    @property
    def in_parallel(self):
        """
        :return:
        """
        return self.__args__['in_parallel']

    @property
    def loop_on_error(self):
        """
        :return:
        """
        return self.__args__['loop_on_error']

    @property
    def iterations_qty(self):
        """
        :return:
        """
        return self.__args__['iterations_qty']

    @property
    def iterations_time(self):
        """
        :return:
        """
        return self.__args__['iterations_time']

    @property
    def continue_on_error(self):
        """
        :return:
        """
        return self.__args__['continue_on_error']

    @property
    def prerequisite(self):
        """
        :return:
        """
        if isinstance(self.__args__['prerequisite'], str):
            return eval(self.__args__['prerequisite'])
        return self.__args__['prerequisite']


class StepDefinition(DefinitionBase):
    def __init__(self, step, name, **kwarg):

        kwargs = kwarg
        self._step = step
        self._name = name

        # print(kwargs)

        if name_checker.match(self._name) is None:
            raise Exception('"name" needs to be a valid string(characters, 0-9, _, and space)' +
                            ' and currently set to: {}'.format(self._name))

        super(StepDefinition, self).__init__(**kwargs)
        self.set_name()
        self.set_step()

    def __repr__(self):
        return str(self.__args__)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def set_step(self):
        self.__args__['step'] = self._step

    def set_name(self):
        self.__args__['name'] = self._name

    @property
    def step(self):
        return self._step

    @property
    def name(self):
        return self._name


class SequenceDefinition(DefinitionBase):
    def __init__(self, name, instance=None, **kwarg):
        self._name = name
        self._instance = instance
        if name_checker.match(self._name) is None:
            raise Exception('"name" needs to be a valid string(characters, 0-9, _, and space)' +
                            ' and currently set to: {}'.format(self._name))
        self._steps = list()
        # self._in_parallel = kwarg.get('in_parallel')
        # if self._in_parallel:
        #     kwarg.pop('in_parallel')
        super(SequenceDefinition, self).__init__(**kwarg)
        if kwarg.get('sub_sequence'):
            self.sub_sequence = True
        else:
            self.sub_sequence = False

    def __repr__(self):
        return "Sequence '%s' with %d steps" % (self._name, len(self.steps))

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    @property
    def name(self):
        return self._name

    # @property
    # def in_parallel(self):
    #     return self._in_parallel

    def step_exists(self, name):
        """
        :param name:
        :return:
        """
        if not name:
            raise Exception('"Name" must be given on creation for a Step/Sequence definition')

        for step in self._steps:
            if name == step.name:
                raise Exception('Step/Sequence name "{}" already exist in the current sequence.'.format(name))
        return False

    @property
    def steps(self):
        return self._steps

    def add_step(self, step, name=None,
                 adt_enabled=False,
                 in_parallel=False,
                 loop_on_error=0,
                 iterations_qty=1,
                 iterations_time=0,
                 continue_on_error=False,
                 prerequisite=True,
                 finalization=False):
        """
        :param step:
        :param name:
        :param adt_enabled:
        :param in_parallel: the step will be run in parallel.
        :param loop_on_error:
        :param iterations_qty:  the step will be run for 'iterations_qty' times.
        :param iterations_time:  the step will be run for iterations_time, it is second.
        :param continue_on_error:  the test will continue even if step fails, but finally test will fail.
        :param prerequisite: Step will run ony prerequisite=True
        :param finalization:
        :return:
        """
        # class staticmethod is function...
        if isinstance(step, types.MethodType) or isinstance(step, types.FunctionType):
            # user gave us a function directly, use it to create the step
            # if he also gave a name, use it...if not name=function's name
            if not name:
                name = str(step.__name__)
            self.step_exists(name=name)
            if not self.sub_sequence:
                global step_total_count
                step_total_count += 1
            self._steps.append(StepDefinition(step,
                                              name,
                                              adt_enabled=adt_enabled,
                                              in_parallel=in_parallel,
                                              loop_on_error=loop_on_error,
                                              iterations_qty=iterations_qty,
                                              iterations_time=iterations_time,
                                              continue_on_error=continue_on_error,
                                              finalization=finalization,
                                              prerequisite=prerequisite,
                                              ))
            return
        else:
            raise Exception('"step" must be class-method/function for a Step/Sequence definition')

    def add_sequence(self, name,
                     in_parallel=False,
                     adt_enabled=False,
                     loop_on_error=0,
                     iterations_qty=1,
                     iterations_time=0,
                     continue_on_error=False,
                     prerequisite=True,
                     finalization=False):
        """
        :param name:
        :param in_parallel:
        :param adt_enabled:
        :param loop_on_error:
        :param iterations_qty:
        :param iterations_time:
        :param continue_on_error:
        :param prerequisite:
        :param finalization:
        :return:
        """
        # Only allow one level add_sequence.
        if self.sub_sequence:
            raise Exception('Sub Sequence does not allow to have another sub sequence.')
        self.step_exists(name=name)
        self._steps.append(SequenceDefinition(name,
                                              in_parallel=in_parallel,
                                              adt_enabled=adt_enabled,
                                              loop_on_error=loop_on_error,
                                              iterations_qty=iterations_qty,
                                              iterations_time=iterations_time,
                                              continue_on_error=continue_on_error,
                                              prerequisite=prerequisite,
                                              finalization=finalization,
                                              sub_sequence=True,
                                              ))
        return self._steps[-1:][0]


def sequence_iteration(sequence):
    """
    :param sequence:
    :return:
    """
    from ..utils import constant
    log = constant.SEQ_LOGGER
    global step_total_count
    global step_finish_count
    global continue_on_error_list
    global step_branch_name

    thread_pool = []
    for seq in sequence.steps:
        # if prerequisite=False, will JUMP the sequence.
        if not seq.prerequisite:
            jump_step(seq)
            continue

        # if branch name is working.
        if step_branch_name and seq.name != step_branch_name:
            jump_step(seq)
            continue
        # once reach branch name, set step_branch_name back to ""
        step_branch_name = ""
        # following is normal process.
        if isinstance(seq, SequenceDefinition):
            thread_sequence = ParallelThread(sequence_run, seq.name, (seq, ))
            thread_pool.append(thread_sequence)
            thread_sequence.start()
            if seq.in_parallel:  # if parallel, will parallel with the next step/sequence
                continue
        else:
            thread_step = ParallelThread(step_run, seq.name, (seq, ))
            thread_pool.append(thread_step)
            thread_step.start()
            if seq.in_parallel:  # if parallel, will parallel with the next step/sequence
                continue
        # Check if all thread are finished.
        while thread_pool:
            time.sleep(0.3)
            for thread in thread_pool:
                if thread.is_alive():
                    continue
                else:
                    if thread.exitcode == 0:
                        thread_pool.remove(thread)
                        continue
                    # constant.STEP_NAME = thread.test_name
                    # utility.set_display3('STEP: ' + thread.test_name)
                    raise thread.exception

        global step_finish_count
        step_finish_count += 1
        if step_total_count:
            progress = step_finish_count / step_total_count * 100
            models.Container.get_by_name(constant.CONTAINER_NAME).set_progress(progress=progress)

    # if step_branch_name, means the users' jumped step is not valid.
    if step_branch_name:
        raise Exception('Jump Step [{}] is invalid, go to failure'.format(step_branch_name))

    if continue_on_error_list:
        log.error('Continue on error list - {}'.format(continue_on_error_list))
        constant.STEP_NAME = continue_on_error_list[0]
        raise Exception('Sequence(continue on error) failed at step - [{}]'.format(constant.STEP_NAME))
    return


def step_run(_step):
    """
    Currently support below features:
    continue_on_error
    iterations_time
    iterations_qty

    in_parallel

    :param _step:
    :return:
    """
    from ..utils import constant
    log = constant.SEQ_LOGGER
    start_time = time.time()

    branch_name = ""
    global step_branch_name
    # Set Step to running
    models.StepSequence.update_sequence(
        constant.CONTAINER_NAME, _step.name, 'running'
    )
    # each for new step, will set STEP_NAME_TEMP to raw name.
    constant.STEP_NAME_TEMP = ""
    constant.STEP_NAME = _step.name
    utility.set_display3('STEP: ' + _step.name)

    log.info('---> [{}][{}][{}]'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                                        _step.step.__name__,
                                        _step.name))
    if _step.continue_on_error:
        log.info('Step [{}] is set as Continue On Error.'.format(_step.name))
    if _step.iterations_time:
        log.info('Step [{}] is set Iterations Time to [{}].'.format(_step.name, _step.iterations_time))
    try:
        for it in range(_step.iterations_qty):
            if _step.iterations_time:
                current_iteration = 0
                while True:
                    current_iteration += 1
                    branch_name = _step.step()  # at least run 1 time.
                    end_iterations_time = int(time.time() - start_time)
                    log.info('Step Iteration Time [{}]secs, '
                             '[{}]secs went, [{}]iterations finished'.format(_step.iterations_time,
                                                                             end_iterations_time,
                                                                             current_iteration))
                    if _step.iterations_time - end_iterations_time < 0:
                        break
            else:
                branch_name = _step.step()
                if _step.iterations_qty > 1:  # means it is 2 or above.
                    log.info('Step Iterations Qty is set to [{}], [{}] iterations finished'.format(_step.iterations_qty, it + 1))
    except Exception as e2:
        log.error(e2)

        if _step.continue_on_error:
            global continue_on_error_list
            continue_on_error_list.append(_step.name)
            log.info('Step - [{}] failed, but run continue on error'.format(_step.name))
        else:
            # Step failed.
            constant.STEP_NAME = _step.name  # if it is in_parallel test fails, then this is needed.
            utility.set_display3(
                'STEP: ' + constant.STEP_NAME_TEMP if constant.STEP_NAME_TEMP else 'STEP: ' + _step.name)

            models.StepSequence.update_sequence(constant.CONTAINER_NAME, _step.name, 'failed')
            #
            end_time = time.time()
            time_cost = int(end_time - start_time)
            log.info('###[{}] finished, cost [{}]secs, FAILED'.format(_step.name, time_cost))
            log.info('<--- [{}][{}][{}]'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                                                _step.step.__name__,
                                                _step.name))
            raise

    end_time = time.time()
    time_cost = int(end_time - start_time)

    if isinstance(branch_name, tuple) and branch_name[0] == "_jumped":
        step_branch_name = branch_name[1]
    else:
        step_branch_name = ""

    global continue_on_error_list
    if _step.name in continue_on_error_list:
        # Step continue on error
        result = "alarmed"
    elif isinstance(branch_name, str) and branch_name == "_skipped":
        # Step Skipped
        result = "skipped"
    else:
        # Step passed
        result = "passed"
    models.StepSequence.update_sequence(
        constant.CONTAINER_NAME, _step.name, result, '{:02}:{:02}:{:02}'.format(
            int(time_cost / 60 / 60),
            int(time_cost / 60 % 60),
            int(time_cost % 60),
        )
    )
    log.info('###[{}] finished, cost [{}]secs, {}'.format(_step.name, time_cost, result.upper()))
    log.info('<--- [{}][{}][{}]'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                                        _step.step.__name__,
                                        _step.name))
    # return Jump Step Name
    return branch_name if isinstance(branch_name, tuple) else ""  # this return only to sequence_run().


def sequence_run(sequence):
    """
    Iterate first level sequence. second level sequence is not acceptable.
    Currently support below features:

    # continue_on_error
    iterations_time
    iterations_qty

    in_parallel

    :param sequence:
    :return:
    """
    from ..utils import constant
    log = constant.SEQ_LOGGER
    global step_branch_name
    step_branch_name = ""
    branch_name = ""

    start_time = time.time()
    if sequence.iterations_time:
        log.info('Sequence [{}] is set Iterations Time to [{}].'.format(sequence.name, sequence.iterations_time))

    for it in range(sequence.iterations_qty):
        if sequence.iterations_time:
            current_iteration = 0
            while True:
                current_iteration += 1
                # at least run 1 time.
                for seq in sequence.steps:
                    if branch_name and branch_name != seq.name:
                        jump_step(seq)
                        continue
                    branch_name = ""
                    # if prerequisite=False, will JUMP the sequence. for Step
                    if not seq.prerequisite:
                        jump_step(seq)
                        continue

                    if isinstance(seq, SequenceDefinition):
                        raise Exception('Genius only allows 1 level sub-sequence')
                    else:
                        branch = step_run(seq)
                        if isinstance(branch, tuple) and branch[0] == "_jumped":
                            branch_name = branch[1]
                end_iterations_time = int(time.time() - start_time)
                log.info('Sequence Iteration Time [{}]secs, '
                         '[{}]secs went, [{}]iterations finished'.format(sequence.iterations_time,
                                                                         end_iterations_time,
                                                                         current_iteration))
                if sequence.iterations_time - end_iterations_time < 0:
                    break
                # if branch_name, means user's branch_name is not in sub-sequence.
                if branch_name:
                    step_branch_name = branch_name
                    break  # break the sequence, and try to find branch name outside.
        else:
            for seq in sequence.steps:
                if isinstance(seq, SequenceDefinition):
                    raise Exception('Genius only allows 1 level sub-sequence')
                else:
                    if branch_name and branch_name != seq.name:
                        jump_step(seq)
                        continue
                    branch_name = ""

                    # if prerequisite=False, will JUMP the sequence. for Step
                    if not seq.prerequisite:
                        jump_step(seq)
                        continue

                    branch = step_run(seq)
                    if isinstance(branch, tuple) and branch[0] == "_jumped":
                        branch_name = branch[1]

            if sequence.iterations_qty > 1:  # means it is 2 or above.
                log.info(
                    'Sequence Iterations Qty set to [{}], [{}] iterations finished'.format(
                        sequence.iterations_qty, it + 1))
            # if branch_name, means user's branch_name is not in sub-sequence.
            if branch_name:
                step_branch_name = branch_name
                break  # break the sequence, and try to find branch name outside.
        if step_branch_name:  # means user's branch_name is not in sub-sequence.
            log.info("Step [{}] is not in Sequence, try to find Step out of Sequence".format(step_branch_name))
            break
    return


def jump_step(seq):
    """
    :return:
    """
    if isinstance(seq, SequenceDefinition):
        for seq1 in seq.steps:
            jump_step(seq1)
        return
    from ..utils import constant
    log = constant.SEQ_LOGGER
    utility.set_display3('STEP: ' + seq.name)

    log.info('---> [{}][{}][{}]'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                                        seq.step.__name__,
                                        seq.name))
    models.StepSequence.update_sequence(constant.CONTAINER_NAME, seq.name, 'jumped', 'JUMPED')
    log.info('###[{}] finished, cost [{}]secs, JUMPED'.format(seq.name, 0))
    log.info('<--- [{}][{}][{}]'.format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                                        seq.step.__name__,
                                        seq.name))
    return
