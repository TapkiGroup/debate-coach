from time import perf_counter

class Timer:
    def __enter__(self):
        self.t0 = perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        self.dt = perf_counter() - self.t0
