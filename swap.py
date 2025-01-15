import requests
import os 
import pandas as pd 
import numpy as np
from datetime import datetime,timedelta
import json
import subprocess
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime,timedelta
import logging
import io
import time

#information of liquity provider
mail = "email.com"
password = "bqlrklwltyjqsfcn"
EQUITI_sender = "broker.com"
BROC_sender = "dealing.com"
GBE_sender = "l.schobe.com"
imap_server = "imap.gmail.com"

#create file log for everyday
today = datetime.now().strftime("%d%m%Y")
logging.basicConfig(filename=f'{today}.log', level=logging.INFO)
current_directory = os.getcwd()
logging.debug(f'Current working directory: {current_directory}')

#function to download file for mas market
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

        logging.info(f"File downloaded successfully and saved to {save_path}")
        # print(f"File downloaded successfully and saved to {save_path}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def mas_swap():
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
    sym_dict_m = {}
    for index,row in data.iterrows():
        # print(row["Symbol"], row["Swap Long"], row["Swap Short"])
        if row["Symbol"] + ".k" not in sym_dict_m or row["Symbol"] not in sym_dict_m:
            new_sym_k= row["Symbol"] + ".k"
            sym_dict_m[new_sym_k] = {
                "long": 0.0,
                "short": 0.0
            }
            new_sym = row["Symbol"]
            sym_dict_m[new_sym] = {
                "long": 0.0,
                "short": 0.0
            }

        #code prepare for calculate 
        if row["Digits"] == 3:
            sym_dict_m[row["Symbol"] + ".k"]["long"] = row["Swap Long"] * 1000
            sym_dict_m[row["Symbol"] + ".k"]["short"] = row["Swap Short"] * 1000

            if row["Swap Long"] > 0:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 1000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 1000* 1.2
            
            if row["Swap Short"] > 0:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 1000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 1000 * 1.2

            # print(row["Symbol"][3:], " aaaa")
        elif row["Digits"] == 4:
            sym_dict_m[row["Symbol"] + ".k"]["long"] = row["Swap Long"] * 10000
            sym_dict_m[row["Symbol"] + ".k"]["short"] = row["Swap Short"] * 10000

            if row["Swap Long"] > 0:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 10000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 10000* 1.2
            
            if row["Swap Short"] > 0:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 10000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 10000 * 1.2
            # print(row["Symbol"][3:], " bbbb")
        else:
            sym_dict_m[row["Symbol"] + ".k"]["long"] = row["Swap Long"] * 100000
            sym_dict_m[row["Symbol"] + ".k"]["short"] = row["Swap Short"] * 100000
            if row["Swap Long"] > 0:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 100000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["long"] = row["Swap Long"] * 100000* 1.2
            
            if row["Swap Short"] > 0:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 100000 * 0.8
            else:
                sym_dict_m[row["Symbol"]]["short"] = row["Swap Short"] * 100000 * 1.2
            # print(row["Symbol"][3:], " cccc")

    # with open ("Swap\symbol.json", "w") as file:
    #     json.dump(sym_dict_m,file,indent=4)
    logging.info("Finishing to process data for mas")
    print("Finishing to process data for mas")
    return sym_dict_m

#function to get 3 days before
def get_3_days_before():
    current_date = datetime.now()
    pre_3_days = current_date - timedelta(days = 3)

    return datetime.strftime(pre_3_days,"%d-%b-%Y")

#function to process data  for broctagon and equity. fetch the lastest email instead of take from date
def equity_swap():
    msg = login_server_and_getswap(mail,password,imap_server,EQUITI_sender)
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
                    
        if part.get('Content-Disposition') is None:
            continue

        # If attachment is Excel
        filename = part.get_filename()
        if filename and filename.endswith(('.xlsx', '.xls')):
            print(f"Reading Attachment: {filename}")

            attachment_data = part.get_payload(decode=True)
            excel_file = io.BytesIO(attachment_data)

            # Read Excel using pandas
            headers = ["Symbol", "Long", "Short", "Type", "3 day swaps"]
            df = pd.read_excel(excel_file, skiprows=1,names=headers)
            # print(df.head())  # Show top rows of the Excel file
            # return df
            sym_dict_e = {}
            for idx, row in df.iterrows():
                if row["Symbol"] + ".y" not in sym_dict_e or row["Symbol"] + ".e" not in sym_dict_e or row["Symbol"] + ".g" not in sym_dict_e:
                    new_sym_y = row["Symbol"] + ".y"
                    new_sym_e = row["Symbol"] + ".e"
                    new_sym_g = row["Symbol"] + ".g"

                    sym_dict_e[new_sym_y] = {
                        "long": 0.0,
                        "short": 0.0
                    }
                    sym_dict_e[new_sym_e] = {
                        "long": 0.0,
                        "short": 0.0
                    }
                    sym_dict_e[new_sym_g] = {
                        "long": 0.0,
                        "short": 0.0
                    }
                sym_dict_e[row["Symbol"] + ".y"]["long"] = row["Long"]
                sym_dict_e[row["Symbol"] + ".y"]["short"] = row["Short"]
                sym_dict_e[row["Symbol"] + ".g"]["long"] = row["Long"]
                sym_dict_e[row["Symbol"] + ".g"]["short"] = row["Short"]
                sym_dict_e[row["Symbol"] + ".e"]["long"] = row["Long"]
                sym_dict_e[row["Symbol"] + ".e"]["short"] = row["Short"]
            
            # with open ("Swap\symbol.json", "w") as file:
            #     json.dump(sym_dict_e,file,indent=4)
            
            logging.info("Finishing processing for Equity Swap")
            print("Finishing processing for Equity Swap")
            return sym_dict_e

def brotagon_swap():
    msg = login_server_and_getswap(mail,password,imap_server,BROC_sender)
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
                    
        if part.get('Content-Disposition') is None:
            continue

        # If attachment is Excel
        filename = part.get_filename()
        if filename and filename.endswith(('.xlsx', '.xls')):
            print(f"Reading Attachment: {filename}")

            attachment_data = part.get_payload(decode=True)
            excel_file = io.BytesIO(attachment_data)

            headers = ["Symbol", "Long", "Short","Digits"]
            df = pd.read_excel(excel_file,usecols=[57,58,59,60], skiprows=1,names = headers, nrows=95)
            df["Symbol"] = df["Symbol"].str.replace("/","")
            # print(df)
            sym_dict = {}
            for idx, row in df.iterrows():
                if row["Symbol"] + ".b" not in sym_dict or row["Symbol"] + ".br" not in sym_dict:
                    new_sym_b = row["Symbol"] + ".b"
                    sym_dict[new_sym_b] = {
                        "long": 0.0,
                        "short": 0.0
                    }
                    new_sym_br = row["Symbol"] + ".br"
                    sym_dict[new_sym_br] = {
                        "long": 0.0,
                        "short": 0.0
                    }
                    
                sym_dict[row["Symbol"] + ".b"]["long"] = row["Long"]
                sym_dict[row["Symbol"] + ".b"]["short"] = row["Short"]
                sym_dict[row["Symbol"] + ".br"]["long"] = row["Long"]
                sym_dict[row["Symbol"] + ".br"]["short"] = row["Short"]

            # with open ("Swap\symbol.json", "w") as file:
            #     json.dump(sym_dict,file,indent=4)
            
            logging.info("Finishing processing for Broctagon Swap")
            # print("Finishing processing for Broctagon Swap")
            return sym_dict
            # print(df.head())  # Show top rows of the Excel file
            # return df


#function to get the list of emails
def get_emails(conn,messages):
    msgs = []
    for id in messages[0].split():
        typ,msg_data = conn.fetch(id,'(RFC822)')
        msgs.append(msg_data)

    return msgs

def login_server_and_getswap(mail,password,server,sender):
    #connect to mail server
    with imaplib.IMAP4_SSL(server) as conn:
        conn.login(mail,password)
        status, result = conn.select("Inbox")

        if status != "OK":
            print("Can not log in. Please check email and password...")
        
        else:
            #search email by senders
            pre_day = get_3_days_before()
            logging.info(f"Log in successfully. Preparing for searching swap data of {sender}")
            # print(f"Log in successfully. Preparing for searching swap data of {sender}")
            if sender == BROC_sender:
                status,messages = conn.search(None, f'(FROM "{sender}" SUBJECT "Broctagon Swaps" SINCE {pre_day})')
            else:
                status,messages = conn.search(None, f'(FROM "{sender}" SINCE {pre_day})')


        #processing email 
            msgs = get_emails(conn,messages)
            for res in msgs[-1]:
                if isinstance(res,tuple):
                    msg = email.message_from_bytes(res[1])
                    subject, encoding = decode_header(msg["Subject"])[0]

                    if isinstance(subject,bytes):
                        subject = subject.decode(encoding if encoding else 'utf-8')
                    
                    return msg


if __name__ == "__main__":
    
    start_time = time.time()
    masswap = mas_swap()
    equityswap = equity_swap()
    brocswap = brotagon_swap()

    # Save the merged swap data to a JSON file
    with open("Swap\symbol.json", "w") as file:  # Use raw string for path
        json.dump({**masswap, **equityswap, **brocswap}, file, indent=4)
        logging.info("Merged all swap dictionaries into JSON file")
        print("finishing merger")
    
    filepath_excute = r'D:\Hoang_report\MAS report\MT4 Swap\Swap\Swap.exe'
    

    # try:
    #     result = subprocess.run([filepath_excute], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #     # logging.info("Output:", result.stdout)
    #     # logging.info("Errors:", result.stderr)

    # except subprocess.CalledProcessError as e:
    #     logging.info("Error running the file:", e)
    # except FileNotFoundError:
    #     logging.info("The file was not found.")
    
    end_time = time.time()
       
    elapsed_time = end_time - start_time

    # Print the elapsed time in seconds
    logging.info(f"Elapsed time: {elapsed_time:.2f} seconds")



