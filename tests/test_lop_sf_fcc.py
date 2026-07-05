#! /usr/bin/env python3

# Python standard library imports
import unittest

# Local Library package imports
from lop_sf_fcc.lop_sf_fcc import calculate_sf_fcc_order_parameter


class TestLopSfFcc(unittest.TestCase):
    def test_lop_sf_fcc_single_atom(self):
        self.assertAlmostEqual(calculate_sf_fcc_order_parameter(),0.00000,places=3)

# ----------
# Public members
# ----------

if __name__ == "__main__":
    unittest.main()
