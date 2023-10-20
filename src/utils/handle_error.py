import sys
import os


def handle_exceptions_method(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(self, *args, **kw):
        try:
            return fn(self, *args, **kw)
        except Exception as Ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("Handle Exceptions:", Ex, "type:", exc_type, "file_name:", file_name, "line no:", exc_tb.tb_lineno)
            return {'error': fn.__name__,
                    'ex': Ex}

    return wrapper


def handle_exceptions_static_method(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kw):
        try:
            return fn(*args, **kw)
        except Exception as Ex:
            # exception_handler(self.log)
            print("Handle Exceptions:", Ex)
            return {'error': fn.__name__,
                    'ex': Ex}

    return wrapper


def handle_exceptions_async_method(fn):
    from functools import wraps

    @wraps(fn)
    async def wrapper(*args, **kw):
        try:
            return await fn(*args, **kw)
        except Exception as Ex:
            print("Handle Exceptions:", Ex)
            return {'error': fn.__name__,
                    'ex': Ex}
            # exception_handler(self.log)

    return wrapper
