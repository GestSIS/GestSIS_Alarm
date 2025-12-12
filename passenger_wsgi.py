import importlib.util
import importlib.machinery
import os
import sys


def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


sys.path.insert(0, os.path.dirname(__file__))

wsgi = load_source("wsgi", "gestsis_alarm/wsgi.py")
application = wsgi.application
