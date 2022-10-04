import unittest
from unit_test_csv_show_shared import ShowCSVSharedFunctionsTests
from unit_test_csv_show_db import *
from unit_test_csv_show_format import *
from unit_test_csv_show import *


def suite():
    my_suite = unittest.TestSuite()
    my_suite.addTest(unittest.makeSuite(ShowCSVSharedFunctionsTests))
    my_suite.addTest(unittest.makeSuite(ShowCSVDBTests))
    my_suite.addTest(unittest.makeSuite(ShowCSVPrintFormatterTests))
    my_suite.addTest(unittest.makeSuite(ShowCSVTests))
    return my_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
