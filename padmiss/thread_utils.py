import logging
import sys
import threading

log = logging.getLogger(__name__)

# extended from https://stackoverflow.com/a/12223550
class CancellableThrowingThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()

    def exc_run(self):
        raise Exception("excRun was not defined")

    def run(self):
        self.exc = None
        log.debug("Starting thread")
        try:
            self.exc_run()
        except:
            self.exc = sys.exc_info()
        finally:
            log.debug("Thread stopped")

    def stop(self):
        log.debug("Stop signal received")
        self.stop_event.set()

    def join(self, *args, **kwargs):
        super(CancellableThrowingThread, self).join(*args, **kwargs)
        if self.exc:
            msg = "Thread '%s' threw an exception: %s" % (self.getName(), self.exc[1])
            new_exc = Exception(msg)
            raise new_exc.with_traceback(self.exc[2])


def start_and_wait_for_threads(stoppable_thread_list, should_stop_predicate=lambda: False):
    try:
        for thread in stoppable_thread_list:
            thread.start()

        while not should_stop_predicate():
            for thread in stoppable_thread_list:
                thread.join(0.1)
    finally:
        # daemon stopped? clean up and wait for them to stop
        for thread in stoppable_thread_list:
            if thread.is_alive():
                thread.stop()

        for thread in stoppable_thread_list:
            if thread.is_alive():
                thread.join()
