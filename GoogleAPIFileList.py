#!/usr/bin/python3

"""

  In order to run this script you need python3 and pip3 installed.

  You also need some additional python modules. Please run

    sudo pip3 install httplib2

    sudo pip3 install --upgrade google-api-python-client



  To authenticate in Google follow the instructions at

  https://developers.google.com/drive/v3/web/quickstart/python

  A client_secret.json file needs to placed in the same directory

  with this script. The link above contains the instruction on

  how to obtain this file. Once you complete these steps run

    python3 this_script.py --noauth_local_webserver

  and follow the instructions

"""

import httplib2

import os

from apiclient import discovery

from oauth2client import client

from oauth2client import tools

from oauth2client.file import Storage

try:

    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()

except ImportError:

    flags = None

import pandas as pd

# If modifying these scopes, delete your previously saved credentials

# at ~/.credentials/drive-python-quickstart.json

SCOPES = 'https://www.googleapis.com/auth/drive.metadata.readonly'

CLIENT_SECRET_FILE = 'client_secret.json'

APPLICATION_NAME = 'Drive API Python Quickstart'

folder_id = '1bpFgrL2PnnkeinEa5u3voOU147PjDo-Y' #Set to id of the parent folder you want to list
folder_list = []
all_folders = []
file_list = []



def get_credentials():
    """Gets valid user credentials from storage.



    If nothing has been stored, or if the stored credentials are invalid,

    the OAuth2 flow is completed to obtain the new credentials.



    Returns:

        Credentials, the obtained credential.

    """

    home_dir = os.path.expanduser('~')

    credential_dir = os.path.join(home_dir, '.credentials')

    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)

    credential_path = os.path.join(credential_dir,

                                   'drive-python-quickstart.json')

    store = Storage(credential_path)

    credentials = store.get()

    if not credentials or credentials.invalid:

        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)

        flow.user_agent = APPLICATION_NAME

        if flags:

            credentials = tools.run_flow(flow, store, flags)

        else:  # Needed only for compatibility with Python 2.6

            credentials = tools.run(flow, store)

        print('Storing credentials to ' + credential_path)

    return credentials


def get_root_folder(): # get's folder list from original root folder

    credentials = get_credentials()

    http = credentials.authorize(httplib2.Http())

    service = discovery.build('drive', 'v3', http=http)

    results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and '"+folder_id+"' in parents",

        pageSize=1000, fields="nextPageToken, files(id, mimeType)").execute()

    folders = results.get('files', [])

    if not folders:

        print('No folders found.')

    else:

        for folder in folders:
            id = folder.get('id')
            folder_list.append(id)


def get_all_folders(folder_list): #creates list of all sub folder under root

    for folder in folder_list:
        additional_folders = []
        credentials = get_credentials()

        http = credentials.authorize(httplib2.Http())

        service = discovery.build('drive', 'v3', http=http)
        results = service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder' and '" +folder+ "' in parents",

            pageSize=1000, fields="nextPageToken, files(id, mimeType)").execute()
        items = results.get('files', [])

        for item in items:
            id = item.get('id')
            additional_folders.append(id)
        if not additional_folders:
            pass
        else:
            all_folders.extend(additional_folders)
            folder_list = additional_folders
            get_all_folders(folder_list)

def merge(): #merges sub folder list with full list
    global full_list
    full_list = all_folders + folder_list
    full_list.append(folder_id)


def get_file_list(): #runs over each folder generating file list, for files over 1000 uses nextpagetoken to run additional requests


    for folder in full_list:
        credentials = get_credentials()

        http = credentials.authorize(httplib2.Http())

        service = discovery.build('drive', 'v3', http=http)

        page_token = None
        while True:
            results = service.files().list(
                q="'" + folder + "' in parents",

                pageSize=1000, fields="nextPageToken, files(name, md5Checksum, size, id, parents)", pageToken=page_token).execute()

            items = results.get('files', [])
            for item in items:
                name = item['name']

                checksum = item.get('md5Checksum', 'no checksum')

                size = item.get('size', '-')

                id = item.get('id')

                parents = item.get('parents')

                file_list.append([name, checksum, size, id, parents])

            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break

    files = pd.DataFrame(file_list,columns=['File_Name','Checksum','Size','ID', 'Parents'])
    print(files)
    files.to_csv('H:/test.csv')


if __name__ == '__main__':
    print('Collecting folder id list')
    get_root_folder()
    get_all_folders(folder_list)
    merge()
    print('Generating file metadata list')
    get_file_list()
