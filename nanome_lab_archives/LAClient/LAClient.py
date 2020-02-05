import os
from urllib.parse import quote
import requests
import xmltodict as xml
import json

from ..LAClient.Utils import epoch_time, get_signature

DEBUG = [] # ['get_entries_for_page']

class LAClient:
    instance = None
    baseurl = None

    def __init__(self, baseurl, credential_path):
        if LAClient.instance is None:
            LAClient.instance = self

        LAClient.baseurl = baseurl
        credPath = os.path.normpath(credential_path)
        with open(credential_path, 'r') as credentials:
            self.akid = credentials.readline().strip()
            self.password = credentials.readline().strip()

    @staticmethod
    def auth_params(method):
        req_time = str(epoch_time())
        akid = LAClient.instance.akid
        password = LAClient.instance.password
        sig = get_signature(akid, method, req_time, password)
        return {'akid': akid, 'expires': req_time, 'sig': sig}

    @staticmethod
    def request_route(method, route, headers={}, params={}, data=None):
        url = LAClient.baseurl + route
        action = route.split('/')[-1]
        params = {**params, **LAClient.auth_params(action)}

        if not route.startswith('/users/'):
            params['uid'] = LAClient.instance.uid

        if method == 'GET':
            req = requests.get(url, params=params)
        elif method == 'POST':
            req = requests.headers(url, headers=headers, params=params, data=data)
        else:
            raise TypeError(f'{method} not a valid request method')

        try:
            res = xml.parse(req.text)
        except:
            res = req.text

        if action in DEBUG:
            print(f'ACTION: {action}')
            print(json.dumps(res, indent=2))
            print(req.text)

        return (None, res) if req.status_code == 200 else (res, None)

    @staticmethod
    def get_route(route, params={}):
        return LAClient.request_route('GET', route, params=params)

    @staticmethod
    def post_route(route, headers={}, params={}, data=None):
        return LAClient.request_route('POST', route, headers, params)

class Users:
    @staticmethod
    def create_user_account(email, login=None, password=None, fullname=None, notebook_name=None):
        params = {
            'email': email,
            'login': login,
            'password': password,
            'fullname': fullname,
            'notebook_name': notebook_name
        }
        # TODO: this could go in request_route
        params = {k: v for k, v in params.items() if v is not None}
        return LAClient.get_route('/users/create_user_account', params)

    @staticmethod
    def user_access_info(login_or_email, password="", student_notebooks=False, hidden_notebooks=False):
        (err, res) = LAClient.get_route('/users/user_access_info', {
            'login_or_email': login_or_email,
            'password': password,
            'student_notebooks': student_notebooks,
            'hidden_note': hidden_notebooks
        })

        if err is None:
            LAClient.instance.uid = res['users']['id']

        return (err, res)

class Tree:
    @staticmethod
    def get_tree_level(nbid, level):
        return LAClient.get_route('/tree_tools/get_tree_level', {
            'nbid': nbid,
            'parent_tree_id': level
        })

    @staticmethod
    def get_entries_for_page(page_tree_id, nbid, entry_data=False, comment_data=False):
        return LAClient.get_route('/tree_tools/get_entries_for_page', {
            'page_tree_id': page_tree_id,
            'nbid': nbid,
            'entry_data': entry_data,
            'comment_data': comment_data
        })

class Entries:
    @staticmethod
    def add_attachment(filename, caption, nbid, pid, data):
        headers = { 'content-type': 'application/octet' }
        params = {
            'filename': filename,
            'caption': caption,
            'nbid': nbid,
            'pid': pid
        }
        return LAClient.post_route('/entries/add_attachment', headers, params, data)

    @staticmethod
    def entry_attachment(eid, write_location=None):
        (err, res) = LAClient.get_route('/entries/entry_attachment', { 'eid': eid })

        if err is None:
            with open(write_location or '1tyl.pdb', 'w') as f:
                f.write(res)

        return (err, res)

    @staticmethod
    def entry_info(eid, entry_data=None, comment_data=None):
        return LAClient.get_route('/entries/entry_info', {
            'eid': eid,
            'entry_data': entry_data,
            'comment_data': comment_data
        })

# class Tree:
#     @staticmethod
#     def get_tree_level(nbid, level):
#         url = LAClient.baseurl + '/tree_tools/get_tree_level'

#         params = {'uid': LAClient.instance.uid, 'nbid': nbid, 'parent_tree_id': level }
#         params = {**params, **LAClient.auth_params('get_tree_level')}

#         r = requests.get(url, params=params)

#         print(r.text)

#         res = xml.parse(r.text)
#         if r.status_code == 200:
#             return (None, res)
#         else:
#             return (res, None)

#     @staticmethod
#     def get_entries_for_page(page_tree_id, nbid, entry_data=False, comment_data=False):
#         url = LAClient.baseurl + '/tree_tools/get_entries_for_page'

#         params = {'uid': LAClient.instance.uid, 'page_tree_id': page_tree_id, 'nbid': nbid, 'entry_data': entry_data, 'comment_data': comment_data}
#         params = {**params, **LAClient.auth_params('get_entries_for_page')}

#         r = requests.get(url, params=params)

#         print(r.text)

#         res = xml.parse(r.text)
#         if r.status_code == 200:
#             return (None, res)
#         else:
#             return (res, None)

#     @staticmethod
#     def get_entries_for_page(page_tree_id, nbid, entry_data=False, comment_data=False):
#         url = LAClient.baseurl + '/tree_tools/get_entries_for_page'

#         params = {
#             'uid': LAClient.instance.uid,
#             'page_tree_id': page_tree_id,
#             'nbid': nbid,
#             'entry_data': entry_data,
#             'comment_data': comment_data
#         }
#         params = {**params, **LAClient.auth_params('get_entries_for_page')}

#         r = requests.get(url, params=params)

#         print(r.text)

#         res = xml.parse(r.text)
#         if r.status_code == 200:
#             return (None, res)
#         else:
#             return (res, None)

# class Entries:
#     @staticmethod
#     def add_attachment(filename, caption, nbid, pid, file_content):
#         url = LAClient.baseurl + '/entries/add_attachment'

#         parameters = { 'uid': LAClient.instance.uid, 'filename': filename, 'caption': caption, 'nbid': nbid, 'pid': pid }
#         parameters = {**LAClient.auth_params('add_attachment'), **parameters}

#         r = requests.post(url, headers={'content-type':'application/octet'}, params=parameters, data=file_content)

#         print(r.text)
#         res = xml.parse(r.text)

#         if r.status_code == 200:
#             return (None, res)
#         else:
#             return (res, None)

#     @staticmethod
#     def entry_attachment(eid, write_location=None):
#         url = LAClient.baseurl + '/entries/entry_attachment'

#         params = { 'uid': LAClient.instance.uid, 'eid': eid }
#         params = {**params, **LAClient.auth_params('entry_attachment')}

#         r = requests.get(url, params=params)

#         if r.status_code == 200:
#             with open(write_location or '1tyl.pdb', 'w') as f:
#                 f.write(r.text)
#             return (None, r.text)
#         else:
#             return (r.text, None)

#     @staticmethod
#     def entry_info(eid, entry_data=None, comment_data=None):
#         url = LAClient.baseurl + '/entries/entry_info'

#         parameters = { 'uid': LAClient.instance.uid, 'eid': eid, 'entry_data': entry_data, 'comment_data': comment_data}
#         parameters = {**LAClient.auth_params('entry_info'), **parameters}

#         r = requests.get(url, params=parameters)

#         print(r.text)
#         res = xml.parse(r.text)

#         if r.status_code == 200:
#             return (None, res)
#         else:
#             return (res, None)