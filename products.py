

import pandas as pd
from tabulate import tabulate


df = pd.read_csv("ecom_items.csv")

class display:
    def __init__(self) -> None:
      
        random_items = df[['Item', 'Selling Price']].sample(n=15)


        return print(tabulate(random_items, headers='keys', tablefmt='grid', showindex=False))
