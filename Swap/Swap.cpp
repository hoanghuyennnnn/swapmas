// Swap.cpp : This file contains the 'main' function. Program execution begins and ends there.
// Necessary files for project

#include <winsock2.h>
#include <windows.h>  // Only after winsock2.h
#include <fstream> 
#include <iostream>
#include "StdAfx.h"   // Only include the header, not the .cpp
#include "MT4ManagerAPI.h"
#include "json.hpp"

#pragma comment(lib, "ws2_32.lib")  // Automatically link with ws2_32.lib


using namespace std;
using json = nlohmann::json;

// Define a structure to hold swap data from the JSON file
struct SwapData {
	string symbol;
	double swap_long;
	double swap_short;
};


// Function to read the JSON file and parse it into a list of SwapData
vector<SwapData> readSwapData(const string& filename) {
	vector<SwapData> swapDataList;

	// Open the JSON file
	ifstream file(filename);
	if (!file.is_open()) {
		cerr << "Error opening JSON file!" << endl;
		return swapDataList;
	}

	// Parse the JSON data
	json jsonData;
	file >>  jsonData;

	// Iterate over the JSON object and extract swap data for each symbol
	for (auto& item : jsonData.items()) {
		SwapData data;
		data.symbol = item.key();  // Symbol name as the key
		data.swap_long = item.value()["long"];  // Get the long swap value
		data.swap_short = item.value()["short"];  // Get the short swap value
		swapDataList.push_back(data); //resize container automatically if necessary
	}

	return swapDataList;
}


//connect to MT4 server 

void connectMT4(const string& address, const int id, const string& password, const vector<SwapData>& swapDataList)
{
	cout << "Connect to server " + address << endl; 
    CManagerFactory factory; // create the object(instance) with class is CmanagerFactory
    CManagerInterface* manager; //declacres a pointer 
    factory.Init("mtmanapi64.dll"); //This line calls the Init method of the CManagerFactory object (factory), passing the string "mtmanapi64.dll" as an argument.
    factory.WinsockStartup(); //This function likely initializes Winsock, which is the Windows Sockets API.
	if (factory.IsValid() == FALSE)
	{
		cout << "Failed to Load Libraries";
		return;
	}
	manager = factory.Create(ManAPIProgramVersion);
	if (manager == NULL) {
		cout << "Failed to create MetaTrader 4 Manager API interface";
		return;
	}
	if (manager->Connect(address.c_str()) != RET_OK) { //from pointer to member function of class
		cout << "Connection to MT4 server failed";
		return;
	}
	if (manager->Login(id, password.c_str()) != RET_OK) {
		cout << "Login Failed";
		return;
	}
	else
		cout << "log in successful" << endl;

	int totalSymbols = 0;
	ConSymbol* sym = manager->CfgRequestSymbol(&totalSymbols);
	/*if (sym)
	{
		for (int i = 0; i < totalSymbols; i++)
		{
			cout << "Symbol: " << sym[i].symbol << "\nSwap long: " <<sym[i].swap_long << "\nSwap short: " << sym[i].swap_short << endl;
		}
	}
	else
	{
		cerr << "SymbolsGetAll failed. Error code: " << endl;
	}*/
	cout << "Number of symbols in MT4 demo server: " << totalSymbols << endl;

	int successCount = 0; //declare values to count the success and fail cases
	int failCount = 0;

	// Iterate through the swap data
	cout << "Number of symbols in swapDataList: " << swapDataList.size() << endl;
	for (size_t i = 0; i < swapDataList.size(); i++) {
		string symbolWithSuffix = swapDataList[i].symbol + ".k";  // Add .k suffix
		cout << "Attempting to update symbol: " << symbolWithSuffix << endl;

		// Refresh symbols to ensure latest list
		manager->SymbolsRefresh();

		// Check if the symbol exists in MT4 admin
		ConSymbol symbolData; //create an object of class ConSymbol
		int symbolStatus = manager->SymbolGet(symbolWithSuffix.c_str(), &symbolData); //pointer manager to function symbolget 

		if (symbolStatus != RET_OK) {
			cerr << "Symbol " << symbolWithSuffix << " not found. That symbol is not in Market Watch...No adding and continue" << endl;
			//manager->SymbolAdd(symbolWithSuffix.c_str());  // Add symbol to Market Watch
			//manager->SymbolsRefresh();  // Refresh symbol list

			//// Retry to get symbol after adding
			//symbolStatus = manager->SymbolGet(symbolWithSuffix.c_str(), &symbolData);
		}

		// If symbol found, proceed to update
		if (symbolStatus == RET_OK) {
			cout << "Symbol " << symbolWithSuffix << " retrieved successfully!" << endl;

			// Update swap values from swapDataList
			symbolData.swap_long = swapDataList[i].swap_long;
			symbolData.swap_short = swapDataList[i].swap_short;

			// Update symbol in MT4
			int updateStatus = manager->CfgUpdateSymbol(&symbolData); //this method will check thether the symbol alreay exists, if yes, will update, otherwise a new entry is added

			// Check update status
			if (updateStatus == RET_OK) {
				cout << "Successfully updated " << symbolWithSuffix << endl;
				successCount++;
			}
			else {
				cerr << "Failed to update " << symbolWithSuffix
					<< " with error code: " << updateStatus << endl;
				failCount++;
			}
		}
		else {
			cerr << "Failed to find symbol " << symbolWithSuffix
				<< " cuz it is not existed (Error code: " << symbolStatus << ")." << endl;
			failCount++;
		}

		// Separator for readability
		cout << "---------------------------------" << endl;
	}
	// After processing all symbols, print the success and failure counts
	cout << "Successfully updated " << successCount << " symbols." << endl;
	cout << "Failed to update " << failCount << " symbols." << endl;

	// Release the connection to MT4 after all operations are done
	manager->Release();

}


int main()
{
		cout << "Start connecting to server";
		string address = "43.157.39.63";
		int id = 1;
		string password = "kjp0812!";
	 //connectMT4(address, id, password);

	string jsonFile = "symbol.json"; // Path to your JSON file

	// Read swap data from the JSON file
	vector<SwapData> swapDataList = readSwapData(jsonFile);

	// Step 2: Update the swap values in MT4 admin
	//updateSwapInMT4Admin(swapDataList);
	connectMT4(address,id,password,swapDataList);

	return 0;
}

