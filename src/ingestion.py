import pandas as pd

def load_csv(file_path):
    """
    load restaurant data from a csv file
    
    args:
        file_path (str): path to the csv file
        
    returns:
        pandas.DataFrame: loaded data
    """
    return pd.read_csv(file_path)

if __name__ == "__main__":
    df = load_csv('../data/restaurant_data.csv')
    print(df.head())
