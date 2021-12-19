import os
import re
import pandas as pd

#----------------------------------------------------------------------------

class OptionsData:
    data_dir = "data"
    default_filename = "isx2010C.xls"
    
    def __init__(self, filename=default_filename, clean=True):
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.isfile(filepath):
            faulty_filepath = filepath
            filepath = os.path.join(self.data_dir, self.default_filename)
            print(f"[{type(self).__name__}] Warning: could not find {faulty_filepath!r}; proceeding with {filepath!r}")
        self.__sheet_df_dict = pd.read_excel(filepath, sheet_name=None)
        sheets = list(self.__sheet_df_dict.keys())
        sheets = sheets[:2] + list(reversed(sheets[2:]))
        self.__sheet_succ = dict(zip(sheets, sheets[1:] + [sheets[-1]]))
        if clean:
            for key, val in self.__sheet_df_dict.items():
                self.__sheet_df_dict[key] = self.__clean_df(val)
                
    def __get_item__(self, key):
        return self.__sheet_df_dict[key]
    
    def get_sheet_names(self):
        return list(self.__sheet_succ.keys())
    
    def get_sheet_df_dict(self):
        return self.__sheet_df_dict
    
    def get_next_sheet_name(self, sheet_name):
        return self.__sheet_succ[sheet_name]
    
    def get_df(self, E=None, sheet_name=""):
        if not sheet_name:
            sheet_name = list(self.__sheet_df_dict.keys())[0]
            print(f"[{type(self).__name__}] Warning: sheet name not specified; proceeding with {sheet_name!r}")
        df = self.__sheet_df_dict[sheet_name]
        common = ["date", "T", "T_norm", "S", "r"]
        if not E:
            return df[[*common, *filter(lambda x: re.match(r"\d+", x), df.columns)]]
        strikes = E if type(E) is list or type(E) is tuple else [E]
        cols = [*common, *map(lambda x: str(int(x)), strikes)]
        return df[cols]
    
    def __clean_df(self, df):
        # Discard rows where no options data is available.
        df = df.dropna(how="all")
        # Save the date column for later.
        date = df[df.columns[-1]]
        # Rename the columns according to the following convention:
        #  T = Time to Maturity
        #  S = Price of the Underlying
        #  r = Risk-Free Interest Rate
        df = df.rename(lambda x: self.__rename_df_cols(str(x), df), axis="columns")
        # Adjust the interest rate properly.
        df["r"] = df["r"] / 100
        # Add new column with annual-normalized T (252 = no. trading days in a year).
        df["T_norm"] = df["T"] / 252
        # Re-arrange the columns.
        common = ["S", "r", "T", "T_norm"]
        cols = [*common, *filter(lambda x: re.search("\d+", x), df.columns.astype(str))]
        df = df[cols]
        df["date"] = date
        return df
    
    def __rename_df_cols(self, col_name, df):
        ncol = len(df.columns)
        # Time to maturity | (price of the underlying | risk-free rate).
        regex = r"(?P<T>\d+(-\d{2}){2} (\d{2}:){2}\d{2})|(?P<Sr>Unnamed: (?P<idx>\d+))"
        match = re.match(regex, col_name)
        if not match:
            return col_name
        if match["T"]:
            return "T"
        elif match["Sr"]:
            col_idx = int(match["idx"])
            # Third last depicts the price of the underlying...
            if col_idx == ncol - 3:
                return "S"
            # ...and the second last the risk free rate.
            elif col_idx == ncol - 2:
                return "r"

#----------------------------------------------------------------------------

