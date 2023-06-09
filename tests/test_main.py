#! /usr/bin/env python3
# vim:fenc=utf-8

import unittest

from .. import *


class TestMain(unittest.TestCase):
    def test_main(self):
        self.assertRaises(FileNotFoundError, locate_toml)


if __name__ == "__main__":
    unittest.main()
