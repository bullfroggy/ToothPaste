// ToothPaste.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include <winsock2.h>
#include <ws2bth.h>
#include <BluetoothAPIs.h>
#include <string>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "irprops.lib")
using namespace std;

int main(){
	//Initialising winsock
	WSADATA data;
	SOCKADDR_BTH sab, sab2;
	int result;
	result = WSAStartup(MAKEWORD(2, 2), &data);//initializing winsock
	if (result!=0){
		cout << "An error occured while initialising winsock, closing.... \n";
	exit(result);
	}

	//Initialising query for device
	WSAQUERYSET queryset;
	memset(&queryset, 0, sizeof(WSAQUERYSET));
	queryset.dwSize = sizeof(WSAQUERYSET);
	queryset.dwNameSpace = NS_BTH;

	HANDLE hLookup;
	result = WSALookupServiceBegin(&queryset, LUP_CONTAINERS, &hLookup);
	if (result!=0){
		cout << "An error occured while initialising look for devices, closing.... \n";
	exit(result);
	}

	//Initialisation succeeded, start looking for devices
	BYTE buffer[4096];
	memset(buffer, 0, sizeof(buffer));
	DWORD bufferLength = sizeof(buffer);
	WSAQUERYSET *pResults = (WSAQUERYSET*)&buffer;
	while (result==0)
	{
		result = WSALookupServiceNext(hLookup, LUP_RETURN_NAME | LUP_CONTAINERS | LUP_RETURN_ADDR | LUP_FLUSHCACHE | LUP_RETURN_TYPE | LUP_RETURN_BLOB | LUP_RES_SERVICE,&bufferLength, pResults);
		if(result==0){// A device found
			//print the name of the device
			LPTSTR s = pResults->lpszServiceInstanceName;
			BTH_ADDR btAddress = ((SOCKADDR_BTH *)pResults->lpcsaBuffer->RemoteAddr.lpSockaddr)->btAddr;
			LPGUID serviceClass = pResults->lpServiceClassId;
			wcout << s << " found. \n";
			wprintf(L"Device Address is 0X%012X\n", btAddress);
			wcout << "GUID: " << serviceClass << endl;
			wcout << "Connect to this device? (y/n) \n";

			string response;
			cin >> response;
			if (response == "y" || response == "yes" || response == "Y" || response == "Yes")
			{
				SOCKET sock = socket (AF_BTH, SOCK_STREAM, BTHPROTO_RFCOMM);
				if (sock == INVALID_SOCKET)
				{
					printf ("Socket creation failed, error %d\n", WSAGetLastError());
					return 1;
				}
				else
					printf ("socket() looks fine!\n");
	
				sab.addressFamily = AF_BTH;
				sab.btAddr = 0;
				sab.serviceClassId = GUID_NULL;
				sab.port = 0;

				int bindResult = 0;
				bindResult = bind (sock, (SOCKADDR *) &sab, sizeof (sab));
				if (bindResult == SOCKET_ERROR) {
					wprintf(L"Bind failed with error %u\n", WSAGetLastError());
					closesocket(sock);
					WSACleanup();
					return 1;
				}
				else
					wprintf(L"Bind returned success\n");	

				int connectResult = 0;
				sab2.addressFamily = AF_BTH;
				sab2.btAddr = btAddress;
				sab2.port = 0;
				sab2.serviceClassId = *serviceClass;
				
				connectResult = connect(sock, (SOCKADDR *) &sab2, sizeof(sab2));
				if (connectResult == SOCKET_ERROR) {
					wprintf(L"connect function failed with error: %ld\n", WSAGetLastError());
					connectResult = closesocket(sock);
					if (connectResult == SOCKET_ERROR)
						wprintf(L"closesocket function failed with error: %ld\n", WSAGetLastError());
					WSACleanup();
					return 1;
				}
				wprintf(L"Connected!!!!!!!!!!!!.\n");
				Sleep(10000);
				WSACleanup();
				closesocket(sock);
				shutdown(sock, 2);
			}						
		}
	}
	


	WSACleanup();
	//closesocket(s);
	//shutdown(s, 2);
	
}