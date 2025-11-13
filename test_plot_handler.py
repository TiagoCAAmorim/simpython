"""
Test script for the new PlotHandler class.
"""

from bokeh.plotting import show
from rsimpy.cmg.sr3reader import Sr3Reader

def main():
    # Find a test SR3 file
    test_file = "tests/sr3/base_case_3a.sr3"
    print(f"Loading SR3 file: {test_file}")
    sr3 = Sr3Reader(test_file)

    # panel = sr3.plot.plot_map(
    #     element="matrix",
    #     property_name="PRES",
    #     days=sr3.dates.get_days('grid'),
    #     layers=[89],
    #     title="Test Plot: Initial PRES",
    #     width=800,
    #     height=600
    # )
    # show(panel)

    panel = sr3.plot.plot_map(
        element="matrix",
        property_name="PERMI",
        days=sr3.dates.get_days('grid')[0],
        layers=[89],
        # title="Test Plot: PERMI",
        width=800,
        height=600,
        palette='Turbo',
        log_scale=True,
        color_limits=(0.1, 500),
        # out_of_range_colors=('gray', 'gray'),
        # nan_inf_color='gray',
        # colorbar_label='PERMI',
    )
    show(panel)

if __name__ == "__main__":
    main()
