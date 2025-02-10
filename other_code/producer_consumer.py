import time
import threading
import queue


class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self._queue = q

    def run(self):
        while True:
            try:
                msg = self._queue.get(timeout=1)
                if isinstance(msg, str) and msg == "quit":
                    break
                print(f"I'm a thread, and I received {msg}!!")
                self._queue.task_done()
            except queue.Empty:
                continue
        self._queue.task_done()
        print("Bye byes!")


class Producer(threading.Thread):
    def __init__(self, q, duration=5):
        super().__init__()
        self._queue = q
        self._duration = duration

    def run(self):
        start_time = time.time()
        while time.time() - start_time < self._duration:
            self._queue.put("something at %s" % time.time())
            time.sleep(1)
        self._queue.put("quit")


if __name__ == "__main__":
    q = queue.Queue()
    consumer = Consumer(q)
    producer = Producer(q, duration=5)

    consumer.start()
    producer.start()

    producer.join()
    q.join()
    consumer.join()
