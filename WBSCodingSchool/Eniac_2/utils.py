import pandas as pd

def check_dots(df, column_name):
    """ To che
    """
    res = df[column_name].str.count(".").value_counts()
    print(res)

def to_remove_extra_dots(df, column_name):
    """
        To check number of dots in object which should be a number (float)
        and convert it to float
    """
    if df[column_name].dtype == 'object':
    #looking for rows with more than 1 '.'
        check_dot_in_mask = (df[column_name].str.count("\.") > 1) 
    #queried a Series on this mask 
        series_to_apply_changes = (df.loc[check_dot_in_mask, column_name].str.replace(".", "", n=1))
    #applying changes on checking mask with Series as a replace mask
        df[column_name] = pd.to_numeric(df[column_name].where(~check_dot_in_mask,series_to_apply_changes))  
        print("********\nHave Done\n********")
    elif df[column_name].dtype == 'float64':
        print(f"********\nThis data is already float\n********")

def price_correction(row):
    """
        To correct price column
    """
    if row["unit_price"] == 0:
        return row["price"]
    
    if row["price"]/ row["unit_price"] < 2.601:
        return row["price"]
    else:
        return row["price"]/10
    
def category_defenition_type(df, dictionary):
    for name in df.type:
        for keys in dictionary:
            for item in dictionary.get(keys):
                if item.lower() in name.lower():
                    mask = ((df.type == name) & (df.category == ""))
                    df.loc[mask, 'category'] += str(keys)
                    # +', '
                else: 
                    continue

def category_defenition_SKU(df, dictionary):
    for name in df.sku:
        for keys in dictionary:
            for item in dictionary.get(keys):
                if item.lower() in name.lower():
                    mask = ((df.sku == name) & (df.category == ""))
                    df.loc[mask, 'category'] += str(keys)
                    # +', '
                else: 
                    continue

