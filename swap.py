import requests
import os 
import pandas as pd 
import numpy as np
from datetime import datetime,timedelta
import json
import subprocess

#function to download file
def download_sharepoint_file(url, save_path):
    session = requests.Session()

    # Set custom headers to simulate a browser request (optional)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    try:
        # Send the GET request
        response = session.get(url, headers=headers, stream=True)

        # Check if the request is successful
        response.raise_for_status()

        # If the response is valid and a file, save it to disk
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"File downloaded successfully and saved to {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# Example usage
url = "https://bidxmarkets.sharepoint.com/:x:/s/Operations/Ec68NemlfrlIrkhWwup5KecBlb6YcLjTyxfqaWTltCivOg?download=1"

current_folder = os.getcwd()
today = datetime.strftime(datetime.now(),"%Y%m%d")  
save_path = f"swap.xlsx"
filepath = os.path.join(current_folder,save_path)
download_sharepoint_file(url, filepath)

header = ["Symbol", "Name", "Digits", "Tick Size", "Min Volume", "Time", "Swap Long", "Swap Short", "From", "To"]
data = pd.read_excel("swap.xlsx",skiprows=9, names=header,sheet_name="Forex")
# print(data.index)
data.replace("nan",pd.NA,inplace=True)
data = data.dropna(subset=["Symbol"])
data["Symbol"] = data["Symbol"].str.replace("/","")

# change df to json file
sym_dict = {}
for index,row in data.iterrows():
    # print(row["Symbol"], row["Swap Long"], row["Swap Short"])
    if row["Symbol"] not in sym_dict:
        new_sym = row["Symbol"]
        sym_dict[new_sym] = {
            "long": 0.0,
            "short": 0.0
        }
    sym_dict[row["Symbol"]]["long"] = row["Swap Long"]
    sym_dict[row["Symbol"]]["short"] = row["Swap Short"]

with open ("symbol.json", "w") as file:
    json.dump(sym_dict,file,indent=4)



