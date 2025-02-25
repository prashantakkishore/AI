import time


def decorator_time_taken(fnc):
    def inner(*args, **kwargs):  # Accept both positional and keyword arguments
        start = time.process_time()
        ret = fnc(*args, **kwargs)  # Pass arguments to the decorated function
        end = time.process_time()
        print("{} took {} seconds".format(fnc.__name__, round((end - start), 6)))  # Use fnc.__name__ for clearer output
        return ret

    return inner
