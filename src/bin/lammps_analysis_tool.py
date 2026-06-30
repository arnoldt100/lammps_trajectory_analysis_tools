#! /usr/bin/env python3

""" Computes an LOP-based order parameter for local structural order.

Calculates an order parameter that quantifies the degree of local structural 
order in the system, based on the local orientational order parameter (LOP). 
This quantity is commonly used to distinguish ordered (solid-like) regions 
from disordered (liquid-like) regions in coexistence simulations. 
The approach follows James Morris and Xueyu Song, "The melting lines of
model systems calculated from coexistence simulations," 
J. Chem. Phys. 116(21), 134503 (2002). 

"""

import lammps_analysis_tool_parser

def main ():
    print("Stud print for main.")

    my_args = lammps_analysis_tool_parser.top_level_parser.parse_args()

    my_args.do_data_analysis(my_args)

if __name__ == "__main__":
    main()
