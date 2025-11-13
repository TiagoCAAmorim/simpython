"""
Test script for the new PlotHandler class.
"""

import os
from bokeh.plotting import show
from rsimpy.cmg.sr3reader import Sr3Reader

def main():
    # Find a test SR3 file
    test_file = "tests/sr3/base_case_3a.sr3"

    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        print("Available SR3 files:")
        for root, dirs, files in os.walk("tests/sr3"):
            for file in files:
                if file.endswith(".sr3"):
                    print(f"  - {os.path.join(root, file)}")
        exit(1)

    print(f"Loading SR3 file: {test_file}")
    sr3 = Sr3Reader(test_file)

    print("\nAvailable grid properties:")
    for prop_name in sr3.grid.get_property().keys():
        print(f"  - {prop_name}")

    print("\nGrid dimensions:")
    ni, nj, nk = sr3.grid.get_size("nijk")
    print(f"  ni={ni}, nj={nj}, nk={nk}")

    print("\nAvailable days:")
    print(f"  {sr3.dates.get_days('grid')}")


    panel = sr3.plot.plot_map(
        element="matrix",
        property_name="PRES",
        days=sr3.dates.get_days('grid'),
        layers=1,
        title="Test Plot: Initial PRES",
        width=800,
        height=600
    )
    show(panel)

if __name__ == "__main__":
    main()

# Test 1: Plot a single layer for a single date
# print("\nTest 1: Plotting single layer, single date")
# try:
#     # Try to find a good property to plot
#     properties = list(sr3.grid.get_property().keys())
#     test_prop = None
#     for prop in ['PRESSURE', 'SO', 'SG', 'SW', 'PRES']:
#         if prop in properties:
#             test_prop = prop
#             break

#     if test_prop is None:
#         test_prop = properties[0]

#     print(f"  Property: {test_prop}")

#     panel = sr3.plot.plot_map(
#         element="matrix",
#         property_name=test_prop,
#         days=sr3.dates.get_days('grid')[0],
#         layers=1,
#         title=f"Test Plot - {test_prop}",
#         width=800,
#         height=600
#     )

#     output_file("test_plot_single.html")
#     show(panel)
#     print("  ✓ Success! Plot saved to test_plot_single.html")
# except Exception as e:
#     print(f"  ✗ Failed: {e}")
#     import traceback
#     traceback.print_exc()

# # Test 2: Plot multiple layers for a single date
# print("\nTest 2: Plotting multiple layers, single date")
# try:
#     panel = sr3.plot.plot_map(
#         element="matrix",
#         property_name=test_prop,
#         days=sr3.dates.get_days('grid')[0],
#         layers=[1, 2, 3] if nk >= 3 else list(range(1, nk+1)),
#         title=f"Test Plot - {test_prop} Multiple Layers",
#         width=800,
#         height=600
#     )

#     output_file("test_plot_multiple_layers.html")
#     show(panel)
#     print("  ✓ Success! Plot saved to test_plot_multiple_layers.html")
# except Exception as e:
#     print(f"  ✗ Failed: {e}")
#     import traceback
#     traceback.print_exc()

# # Test 3: Plot multiple dates for a single layer
# print("\nTest 3: Plotting single layer, multiple dates")
# try:
#     available_days = sr3.dates.get_days('grid')
#     if len(available_days) >= 3:
#         test_days = [available_days[0], available_days[len(available_days)//2], available_days[-1]]
#     else:
#         test_days = available_days[:min(3, len(available_days))]

#     panel = sr3.plot.plot_map(
#         element="matrix",
#         property_name=test_prop,
#         days=test_days,
#         layers=1,
#         title=f"Test Plot - {test_prop} Time Series",
#         width=800,
#         height=600
#     )

#     output_file("test_plot_multiple_days.html")
#     show(panel)
#     print("  ✓ Success! Plot saved to test_plot_multiple_days.html")
# except Exception as e:
#     print(f"  ✗ Failed: {e}")
#     import traceback
#     traceback.print_exc()

# print("\n✓ All tests completed!")
