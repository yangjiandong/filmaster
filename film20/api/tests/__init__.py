from django.utils import unittest
from django.utils.importlib import import_module
from film20.api.tests import test_oauth

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()

    for ver in ("1.0", "1.1", ):
    # for ver in ("1.1", ):
        module = import_module('film20.api.api_%s.tests' % ver.replace(".", "_"))
        s.addTests(loader.loadTestsFromModule(module))

    s.addTests(loader.loadTestsFromModule(test_oauth))

    return s
    
