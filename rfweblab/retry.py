import time
from functools import wraps


def parameterized(decorator):
    @wraps(decorator)
    def wrapper(*args, **kwargs):
        def make_call(fn_call):
            return decorator(fn_call, *args, **kwargs)

        return make_call

    return wrapper


@parameterized
def retry_on(fn_call, exception, tries=2, delay=3, growth=1.5):
    @wraps(fn_call)
    def wrapper(*args, **kwargs):
        n_tries, f_delay = tries, delay
        while n_tries > 1:
            try:
                return fn_call(*args, **kwargs)

            except exception as e:
                time.sleep(f_delay)
                n_tries, f_delay = n_tries - 1, f_delay * growth

        return fn_call(*args, **kwargs)

    return wrapper
