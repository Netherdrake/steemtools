import time

from funcy import contextmanager


@contextmanager
def timeit():
    t1 = time.time()
    yield
    print("Time Elapsed: %.2f" % (time.time() - t1))
