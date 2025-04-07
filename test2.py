import asyncio
import random
import string
import time
import sys
import threading
import queue
import json

class Task:
    def __init__(self, tid, data):
        self.tid = tid
        self.data = data
        self.status = 'pending'
        self.result = None
    def process(self):
        time.sleep(random.uniform(0.1, 0.5))
        self.result = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        self.status = 'completed'
        return self.result

class Worker(threading.Thread):
    def __init__(self, task_q, result_q):
        super().__init__()
        self.task_q = task_q
        self.result_q = result_q
        self._stop = threading.Event()
    def run(self):
        while not self._stop.is_set():
            try:
                t = self.task_q.get(timeout=0.1)
                t.process()
                self.result_q.put(t)
                self.task_q.task_done()
            except queue.Empty:
                continue
    def stop(self):
        self._stop.set()

class Scheduler:
    def __init__(self, num_workers):
        self.task_q = queue.Queue()
        self.result_q = queue.Queue()
        self.workers = [Worker(self.task_q, self.result_q) for _ in range(num_workers)]
    def start(self):
        for w in self.workers:
            w.start()
    def add(self, t):
        self.task_q.put(t)
    def wait(self):
        self.task_q.join()
    def results(self):
        res = []
        while not self.result_q.empty():
            res.append(self.result_q.get())
        return res
    def stop(self):
        for w in self.workers:
            w.stop()
        for w in self.workers:
            w.join()

async def async_task(aid):
    await asyncio.sleep(random.uniform(0.1, 0.5))
    return f"async_{aid}_{''.join(random.choices(string.ascii_lowercase, k=5))}"

async def run_async(n):
    tasks = [asyncio.create_task(async_task(i)) for i in range(n)]
    res = await asyncio.gather(*tasks)
    return res

def complex_pipeline(n):
    sched = Scheduler(num_workers=5)
    sched.start()
    tasks = [Task(i, f"data_{i}") for i in range(n)]
    for t in tasks:
        sched.add(t)
    sched.wait()
    worker_res = sched.results()
    sched.stop()
    async_res = asyncio.run(run_async(n))
    combined = []
    for t, ar in zip(worker_res, async_res):
        combined.append({"id": t.tid, "data": t.data, "w_res": t.result, "a_res": ar})
    return combined

def export_results(res, fname):
    with open(fname, "w") as f:
        json.dump(res, f)

def main():
    n = 100
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except:
            n = 100
    res = complex_pipeline(n)
    export_results(res, "results.json")
    for r in res:
        print(r)

if __name__ == "__main__":
    main()
