from options_data import OptionsData
from hedger import Hedger

#----------------------------------------------------------------------------
# An example program that provides statistics from delta hedging a single
# option in every sheet with rehedging frequencies of two and ten days.

if __name__ == "__main__":
    data = OptionsData()
    h = Hedger()
    sheets = data.get_sheet_names()
    for schedule in [2, 10]:
        for sheet in sheets:
            stats = h.delta_hedge(data, sheet_name=sheet, portfolio_size=1, schedule=schedule)
            print(stats)
        print("-" * 100)
    
#----------------------------------------------------------------------------

