#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

from typing import Callable, Tuple

from qiling import Qiling
from qiling.os.windows.api import *
from qiling.os.windows.const import *
from qiling.os.windows.fncc import *
from qiling.os.windows.structs import *

def __RegOpenKey(ql: Qiling, address: int, params):
    hKey = params["hKey"]
    lpSubKey = params["lpSubKey"]
    phkResult = params["phkResult"]

    handle = ql.os.handle_manager.get(hKey)

    if handle is None or not handle.name.startswith('HKEY'):
        return ERROR_FILE_NOT_FOUND

    params["hKey"] = handle.name

    if lpSubKey:
        key = f'{handle.name}\\{lpSubKey}'

        # Keys in the profile are saved as KEY\PARAM = VALUE, so i just want to check that the key is the same
        keys_profile = [entry.casefold() for entry in ql.os.profile["REGISTRY"].keys()]

        if key.casefold() in keys_profile:
            ql.log.debug("Using profile for key of  %s" % key)
            ql.os.registry_manager.access(key)

        else:
            if not ql.os.registry_manager.exists(key):
                ql.log.debug("Value key %s not present" % key)
                return ERROR_FILE_NOT_FOUND

        # new handle
        handle = Handle(obj=key)
        ql.os.handle_manager.append(handle)

    if phkResult:
        ql.mem.write_ptr(phkResult, handle.id)

    return ERROR_SUCCESS

def __RegQueryValue(ql: Qiling, address: int, params, wstring: bool):
    ret = ERROR_SUCCESS

    hKey = params["hKey"]
    lpValueName = params["lpValueName"]
    lpType = params["lpType"]
    lpData = params["lpData"]
    lpcbData = params["lpcbData"]
    s_hKey = ql.os.handle_manager.get(hKey).obj
    params["hKey"] = s_hKey
    # read reg_type
    reg_type = Registry.RegNone if lpType == 0 else ql.mem.read_ptr(lpType, 4)

    # try reading the registry key value from profile first.
    # if the key is not specified in profile, proceed to registry manager

    keyname = f'{s_hKey}\\{lpValueName}'
    value = ql.os.profile["REGISTRY"].get(keyname)

    if value is None:
        reg_type, value = ql.os.registry_manager.read(s_hKey, lpValueName, reg_type)

    else:
        ql.log.debug(f'Value for {keyname} was read from profile')

        reg_type = Registry.RegSZ
        # set that the registry has been accessed
        ql.os.registry_manager.access(s_hKey, lpValueName, reg_type, value)

    # error key
    if reg_type is None or value is None:
        ql.log.debug("Key value not found")
        return ERROR_FILE_NOT_FOUND

    # read how many bytes we are allowed to write into lpData, however this arg is optional
    if lpcbData:
        max_size = ql.mem.read_ptr(lpcbData, 4)
    else:
        max_size = 0

        # lpcbData may be null only if lpData is also null. if lpData is allocated, but lpcbData is
        # set to null, it means we have an out buffer without knowing its size
        if lpData:
            return ERROR_INVALID_PARAMETER

    # set lpData
    length = ql.os.registry_manager.write_reg_value_into_mem(reg_type, lpData, value, max_size, wstring)

    # set lpcbData
    if lpcbData:
        ql.mem.write_ptr(lpcbData, length, 4)

    if max_size < length:
        ret = ERROR_MORE_DATA

    return ret

def __RegCreateKey(ql: Qiling, address: int, params):
    hKey = params["hKey"]
    lpSubKey = params["lpSubKey"]
    phkResult = params["phkResult"]

    handle = ql.os.handle_manager.get(hKey)

    if handle is None or not handle.name.startswith('HKEY'):
        return ERROR_FILE_NOT_FOUND

    params["hKey"] = handle.name

    if lpSubKey:
        keyname = f'{handle.name}\\{lpSubKey}'

        if not ql.os.registry_manager.exists(keyname):
            ql.os.registry_manager.create(keyname)

        handle = ql.os.handle_manager.search_by_obj(keyname)

        # make sure we have a handle for this keyname
        if handle is None:
            handle = Handle(obj=keyname)
            ql.os.handle_manager.append(handle)

    if phkResult:
        ql.mem.write_ptr(phkResult, handle.id)

    return ERROR_SUCCESS

def __RegSetValue(ql: Qiling, address: int, params, wstring: bool):
    hKey = params["hKey"]
    lpSubKey = params["lpSubKey"]
    dwType = params["dwType"]
    lpData = params["lpData"]
    cbData = params["cbData"]

    s_hKey = ql.os.handle_manager.get(hKey).obj
    # this is done so the print_function would print the correct value
    params["hKey"] = s_hKey

    if not lpData:
        return ERROR_INVALID_PARAMETER

    # dwType is expected to be REG_SZ and lpData to point to a null-terminated string
    ql.os.registry_manager.write(s_hKey, lpSubKey, dwType, lpData, cbData, wstring)

    return ERROR_SUCCESS

def __RegSetValueEx(ql: Qiling, address: int, params, wstring: bool):
    hKey = params["hKey"]
    lpValueName = params["lpValueName"]
    dwType = params["dwType"]
    lpData = params["lpData"]
    cbData = params["cbData"]

    s_hKey = ql.os.handle_manager.get(hKey).obj
    # this is done so the print_function would print the correct value
    params["hKey"] = s_hKey

    if not lpData:
        return ERROR_INVALID_PARAMETER

    ql.os.registry_manager.write(s_hKey, lpValueName, dwType, lpData, cbData, wstring)

    return ERROR_SUCCESS

def __RegDeleteKey(ql: Qiling, address: int, params):
    hKey = params["hKey"]
    lpSubKey = params["lpSubKey"]

    s_hKey = ql.os.handle_manager.get(hKey).obj
    params["hKey"] = s_hKey

    ql.os.registry_manager.delete(s_hKey, lpSubKey)

    return ERROR_SUCCESS

def __RegDeleteValue(ql: Qiling, address: int, params):
    hKey = params["hKey"]
    lpValueName = params["lpValueName"]

    s_hKey = ql.os.handle_manager.get(hKey).obj
    params["hKey"] = s_hKey

    ql.os.registry_manager.delete(s_hKey, lpValueName)

    return ERROR_SUCCESS

# LSTATUS RegOpenKeyExA(
#   HKEY   hKey,
#   LPCSTR lpSubKey,
#   DWORD  ulOptions,
#   REGSAM samDesired,
#   PHKEY  phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCSTR,
    'ulOptions' : DWORD,
    'samDesired': REGSAM,
    'phkResult' : PHKEY
})
def hook_RegOpenKeyExA(ql: Qiling, address: int, params):
    return __RegOpenKey(ql, address, params)

# LSTATUS RegOpenKeyExW(
#   HKEY    hKey,
#   LPCWSTR lpSubKey,
#   DWORD   ulOptions,
#   REGSAM  samDesired,
#   PHKEY   phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCWSTR,
    'ulOptions' : DWORD,
    'samDesired': REGSAM,
    'phkResult' : PHKEY
})
def hook_RegOpenKeyExW(ql: Qiling, address: int, params):
    return __RegOpenKey(ql, address, params)

# LSTATUS RegOpenKeyW(
#   HKEY    hKey,
#   LPCWSTR lpSubKey,
#   PHKEY   phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCWSTR,
    'phkResult' : PHKEY
})
def hook_RegOpenKeyW(ql: Qiling, address: int, params):
    return __RegOpenKey(ql, address, params)

# LSTATUS RegOpenKeyA(
#   HKEY    hKey,
#   LPCSTR lpSubKey,
#   PHKEY   phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCSTR,
    'phkResult' : PHKEY
})
def hook_RegOpenKeyA(ql: Qiling, address: int, params):
    return __RegOpenKey(ql, address, params)

# LSTATUS RegQueryValueExA(
#   HKEY    hKey,
#   LPCSTR  lpValueName,
#   LPDWORD lpReserved,
#   LPDWORD lpType,
#   LPBYTE  lpData,
#   LPDWORD lpcbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCSTR,
    'lpReserved'  : LPDWORD,
    'lpType'      : LPDWORD,
    'lpData'      : LPBYTE,
    'lpcbData'    : LPDWORD
})
def hook_RegQueryValueExA(ql: Qiling, address: int, params):
    return __RegQueryValue(ql, address, params, wstring=False)

# LSTATUS RegQueryValueExW(
#   HKEY    hKey,
#   LPCWSTR lpValueName,
#   LPDWORD lpReserved,
#   LPDWORD lpType,
#   LPBYTE  lpData,
#   LPDWORD lpcbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCWSTR,
    'lpReserved'  : LPDWORD,
    'lpType'      : LPDWORD,
    'lpData'      : LPBYTE,
    'lpcbData'    : LPDWORD
})
def hook_RegQueryValueExW(ql: Qiling, address: int, params):
    return __RegQueryValue(ql, address, params, wstring=True)

# LSTATUS RegCloseKey(
#   HKEY hKey
# );
@winsdkapi(cc=STDCALL, params={
    'hKey' : HKEY
})
def hook_RegCloseKey(ql: Qiling, address: int, params):
    hKey = params["hKey"]
    ql.os.handle_manager.delete(hKey)

    return ERROR_SUCCESS

# LSTATUS RegCreateKeyA(
#   HKEY   hKey,
#   LPCSTR lpSubKey,
#   PHKEY  phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCSTR,
    'phkResult' : PHKEY
})
def hook_RegCreateKeyA(ql: Qiling, address: int, params):
    return __RegCreateKey(ql, address, params)

# LSTATUS RegCreateKeyW(
#   HKEY   hKey,
#   LPCWSTR lpSubKey,
#   PHKEY  phkResult
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'      : HKEY,
    'lpSubKey'  : LPCWSTR,
    'phkResult' : PHKEY
})
def hook_RegCreateKeyW(ql: Qiling, address: int, params):
    return __RegCreateKey(ql, address, params)

# LSTATUS RegCreateKeyExW(
#   HKEY                        hKey,
#   LPCWSTR                     lpSubKey,
#   DWORD                       Reserved,
#   LPWSTR                      lpClass,
#   DWORD                       dwOptions,
#   REGSAM                      samDesired,
#   const LPSECURITY_ATTRIBUTES lpSecurityAttributes,
#   PHKEY                       phkResult,
#   LPDWORD                     lpdwDisposition
# );
@winsdkapi(cc=STDCALL, params={ # replace_params_type={'DWORD': 'POINTER'}
    'hKey'                 : HKEY,
    'lpSubKey'             : LPCWSTR,
    'Reserved'             : DWORD,
    'lpClass'              : LPWSTR,
    'dwOptions'            : DWORD,
    'samDesired'           : REGSAM,
    'lpSecurityAttributes' : LPSECURITY_ATTRIBUTES,
    'phkResult'            : PHKEY,
    'lpdwDisposition'      : LPDWORD
})
def hook_RegCreateKeyExW(ql: Qiling, address: int, params):
    # fall back to the simple implementation
    return __RegCreateKey(ql, address, params)

# LSTATUS RegSetValueA(
#   HKEY   hKey,
#   LPCSTR lpSubKey,
#   DWORD  dwType,
#   LPCSTR lpData,
#   DWORD  cbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'     : HKEY,
    'lpSubKey' : LPCSTR,
    'dwType'   : DWORD,
    'lpData'   : LPCSTR,
    'cbData'   : DWORD
})
def hook_RegSetValueA(ql: Qiling, address: int, params):
    return __RegSetValue(ql, address, params, wstring=False)

@winsdkapi(cc=STDCALL, params={
    'hKey'     : HKEY,
    'lpSubKey' : LPCWSTR,
    'dwType'   : DWORD,
    'lpData'   : LPCWSTR,
    'cbData'   : DWORD
})
def hook_RegSetValueW(ql: Qiling, address: int, params):
    return __RegSetValue(ql, address, params, wstring=False)

# LSTATUS RegSetValueExA(
#   HKEY       hKey,
#   LPCSTR     lpValueName,
#   DWORD      Reserved,
#   DWORD      dwType,
#   const BYTE *lpData,
#   DWORD      cbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCSTR,
    'Reserved'    : DWORD,
    'dwType'      : DWORD,
    'lpData'      : LPBYTE,
    'cbData'      : DWORD
})
def hook_RegSetValueExA(ql: Qiling, address: int, params):
    return __RegSetValueEx(ql, address, params, wstring=False)

# LSTATUS RegSetValueExW(
#   HKEY       hKey,
#   LPCWSTR    lpValueName,
#   DWORD      Reserved,
#   DWORD      dwType,
#   const BYTE *lpData,
#   DWORD      cbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCWSTR,
    'Reserved'    : DWORD,
    'dwType'      : DWORD,
    'lpData'      : LPBYTE,
    'cbData'      : DWORD
})
def hook_RegSetValueExW(ql: Qiling, address: int, params):
    return __RegSetValueEx(ql, address, params, wstring=True)

# LSTATUS RegDeleteKeyA(
#   HKEY   hKey,
#   LPCSTR lpSubKey
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'     : HKEY,
    'lpSubKey' : LPCSTR
})
def hook_RegDeleteKeyA(ql: Qiling, address: int, params):
    return __RegDeleteKey(ql, address, params)

# LSTATUS RegDeleteKeyW(
#   HKEY   hKey,
#   LPCWSTR lpSubKey
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'     : HKEY,
    'lpSubKey' : LPCWSTR
})
def hook_RegDeleteKeyW(ql: Qiling, address: int, params):
    return __RegDeleteKey(ql, address, params)

# LSTATUS RegDeleteValueA(
#   HKEY    hKey,
#   LPCSTR lpValueName
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCSTR
})
def hook_RegDeleteValueA(ql: Qiling, address: int, params):
    return __RegDeleteValue(ql, address, params)

# LSTATUS RegDeleteValueW(
#   HKEY    hKey,
#   LPCWSTR lpValueName
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'        : HKEY,
    'lpValueName' : LPCWSTR
})
def hook_RegDeleteValueW(ql: Qiling, address: int, params):
    return __RegDeleteValue(ql, address, params)

# BOOL GetTokenInformation(
#   HANDLE                  TokenHandle,
#   TOKEN_INFORMATION_CLASS TokenInformationClass,
#   LPVOID                  TokenInformation,
#   DWORD                   TokenInformationLength,
#   PDWORD                  ReturnLength
# );
@winsdkapi(cc=STDCALL, params={
    'TokenHandle'            : HANDLE,
    'TokenInformationClass'  : TOKEN_INFORMATION_CLASS,
    'TokenInformation'       : LPVOID,
    'TokenInformationLength' : DWORD,
    'ReturnLength'           : PDWORD
})
def hook_GetTokenInformation(ql: Qiling, address: int, params):
    TokenHandle = params["TokenHandle"]
    TokenInformationClass = params["TokenInformationClass"]
    TokenInformation = params["TokenInformation"]
    TokenInformationLength = params["TokenInformationLength"]
    ReturnLength = params["ReturnLength"]

    handle = ql.os.handle_manager.get(TokenHandle)

    if handle is None:
        ql.os.last_error = ERROR_INVALID_HANDLE
        return 0

    token = handle.obj
    information_value = token.get(TokenInformationClass)

    return_size = len(information_value)
    ql.mem.write_ptr(ReturnLength, return_size, 4)

    ql.log.debug("The target is checking for its permissions")

    if return_size > TokenInformationLength:
        ql.os.last_error = ERROR_INSUFFICIENT_BUFFER
        return 0

    if TokenInformation != 0:
        ql.mem.write(TokenInformation, information_value)
        return 1
    else:
        raise QlErrorNotImplemented("API not implemented")

# PUCHAR GetSidSubAuthorityCount(
#   PSID pSid
# );
@winsdkapi(cc=STDCALL, params={
    'pSid' : PSID
})
def hook_GetSidSubAuthorityCount(ql: Qiling, address: int, params):
    pSid = params['pSid']

    # SID address is used as its handle id
    sid = ql.os.handle_manager.get(pSid).obj

    return pSid + sid.offsetof('SubAuthorityCount')

# PDWORD GetSidSubAuthority(
#   PSID  pSid,
#   DWORD nSubAuthority
# );
@winsdkapi(cc=STDCALL, params={
    'pSid'          : PSID,
    'nSubAuthority' : DWORD
})
def hook_GetSidSubAuthority(ql: Qiling, address: int, params):
    pSid = params['pSid']
    nSubAuthority = params['nSubAuthority']

    # SID address is used as its handle id
    sid = ql.os.handle_manager.get(pSid).obj

    return pSid + sid.offsetof('SubAuthority') + (4 * nSubAuthority)

# LSTATUS RegEnumValueA(
#   HKEY    hKey,
#   DWORD   dwIndex,
#   LPSTR   lpValueName,
#   LPDWORD lpcchValueName,
#   LPDWORD lpReserved,
#   LPDWORD lpType,
#   LPBYTE  lpData,
#   LPDWORD lpcbData
# );
@winsdkapi(cc=STDCALL, params={
    'hKey'           : HKEY,
    'dwIndex'        : DWORD,
    'lpValueName'    : LPSTR,
    'lpcchValueName' : LPDWORD,
    'lpReserved'     : LPDWORD,
    'lpType'         : LPDWORD,
    'lpData'         : LPBYTE,
    'lpcbData'       : LPDWORD
})
def hook_RegEnumValueA(ql: Qiling, address: int, params):
    return ERROR_NO_MORE_ITEMS

# SC_HANDLE OpenSCManagerA(
#   LPCSTR lpMachineName,
#   LPCSTR lpDatabaseName,
#   DWORD  dwDesiredAccess
# );
@winsdkapi(cc=STDCALL, params={
    'lpMachineName'   : LPCSTR,
    'lpDatabaseName'  : LPCSTR,
    'dwDesiredAccess' : DWORD
})
def hook_OpenSCManagerA(ql: Qiling, address: int, params):
    lpMachineName = params["lpMachineName"]
    lpDatabaseName = params["lpDatabaseName"]

    sc_handle_name = "sc_%s_%s" % (lpMachineName, lpDatabaseName)
    new_handle = ql.os.handle_manager.search(sc_handle_name)

    if new_handle is None:
        new_handle = Handle(name=sc_handle_name)
        ql.os.handle_manager.append(new_handle)

    return new_handle.id

# SC_HANDLE CreateServiceA(
#   SC_HANDLE hSCManager,
#   LPCSTR    lpServiceName,
#   LPCSTR    lpDisplayName,
#   DWORD     dwDesiredAccess,
#   DWORD     dwServiceType,
#   DWORD     dwStartType,
#   DWORD     dwErrorControl,
#   LPCSTR    lpBinaryPathName,
#   LPCSTR    lpLoadOrderGroup,
#   LPDWORD   lpdwTagId,
#   LPCSTR    lpDependencies,
#   LPCSTR    lpServiceStartName,
#   LPCSTR    lpPassword
# );
@winsdkapi(cc=STDCALL, params={
    'hSCManager'         : SC_HANDLE,
    'lpServiceName'      : LPCSTR,
    'lpDisplayName'      : LPCSTR,
    'dwDesiredAccess'    : DWORD,
    'dwServiceType'      : DWORD,
    'dwStartType'        : DWORD,
    'dwErrorControl'     : DWORD,
    'lpBinaryPathName'   : LPCSTR,
    'lpLoadOrderGroup'   : LPCSTR,
    'lpdwTagId'          : LPDWORD,
    'lpDependencies'     : LPCSTR,
    'lpServiceStartName' : LPCSTR,
    'lpPassword'         : LPCSTR
})
def hook_CreateServiceA(ql: Qiling, address: int, params):
    hSCManager = params["hSCManager"]
    lpServiceName = params["lpServiceName"]
    lpBinaryPathName = params["lpBinaryPathName"]

    ql.os.services[lpServiceName] = lpBinaryPathName
    new_handle = Handle(obj=hSCManager, name=lpServiceName)
    ql.os.handle_manager.append(new_handle)

    return new_handle.id

# SC_HANDLE OpenServiceA(
#   SC_HANDLE hSCManager,
#   LPCSTR    lpServiceName,
#   DWORD     dwDesiredAccess
# );
@winsdkapi(cc=STDCALL, params={
    'hSCManager'      : SC_HANDLE,
    'lpServiceName'   : LPCSTR,
    'dwDesiredAccess' : DWORD
})
def hook_OpenServiceA(ql: Qiling, address: int, params):
    hSCManager = params["hSCManager"]
    lpServiceName = params["lpServiceName"]

    if lpServiceName in ql.os.services:
        new_handle = Handle(obj=hSCManager, name=lpServiceName)
        ql.os.handle_manager.append(new_handle)
        return new_handle.id

    return 0

# BOOL CloseServiceHandle(
#   SC_HANDLE hSCObject
# );
@winsdkapi(cc=STDCALL, params={
    'hSCObject' : SC_HANDLE
})
def hook_CloseServiceHandle(ql: Qiling, address: int, params):
    hSCObject = params["hSCObject"]
    ql.os.handle_manager.delete(hSCObject)

    return 1

# BOOL StartServiceA(
#   SC_HANDLE hService,
#   DWORD     dwNumServiceArgs,
#   LPCSTR    *lpServiceArgVectors
# );
@winsdkapi(cc=STDCALL, params={
    'hService'            : SC_HANDLE,
    'dwNumServiceArgs'    : DWORD,
    'lpServiceArgVectors' : POINTER
})
def hook_StartServiceA(ql: Qiling, address: int, params):
    return 1

# BOOL AllocateAndInitializeSid(
#   PSID_IDENTIFIER_AUTHORITY pIdentifierAuthority,
#   BYTE                      nSubAuthorityCount,
#   DWORD                     nSubAuthority0,
#   DWORD                     nSubAuthority1,
#   DWORD                     nSubAuthority2,
#   DWORD                     nSubAuthority3,
#   DWORD                     nSubAuthority4,
#   DWORD                     nSubAuthority5,
#   DWORD                     nSubAuthority6,
#   DWORD                     nSubAuthority7,
#   PSID                      *pSid
# );
@winsdkapi(cc=STDCALL, params={
    'pIdentifierAuthority' : PSID_IDENTIFIER_AUTHORITY,
    'nSubAuthorityCount'   : BYTE,
    'nSubAuthority0'       : DWORD,
    'nSubAuthority1'       : DWORD,
    'nSubAuthority2'       : DWORD,
    'nSubAuthority3'       : DWORD,
    'nSubAuthority4'       : DWORD,
    'nSubAuthority5'       : DWORD,
    'nSubAuthority6'       : DWORD,
    'nSubAuthority7'       : DWORD,
    'pSid'                 : POINTER
})
def hook_AllocateAndInitializeSid(ql: Qiling, address: int, params):
    count = params["nSubAuthorityCount"]
    subauths = tuple(params[f'nSubAuthority{i}'] for i in range(count))

    sid_struct = make_sid(auth_count=len(subauths))
    sid_addr = ql.os.heap.alloc(sid_struct.sizeof())

    sid_obj = sid_struct(
        Revision = 1,
        SubAuthorityCount = len(subauths),
        IdentifierAuthority = (5,),
        SubAuthority = subauths
    )

    sid_obj.save_to(ql.mem, sid_addr)

    handle = Handle(obj=sid_obj, id=sid_addr)
    ql.os.handle_manager.append(handle)

    dest = params["pSid"]
    ql.mem.write_ptr(dest, sid_addr)

    return 1

def __create_default_sid(ql: Qiling, subauths: Tuple[int, ...]):
    sid_struct = make_sid(auth_count=len(subauths))

    sid_obj = sid_struct(
        Revision = 1,
        SubAuthorityCount = len(subauths),
        IdentifierAuthority = (5,),
        SubAuthority = tuple(subauths)
    )

    return sid_obj

def singleton(func: Callable):
    """A decorator for functions that produce singleton objects.

    When a decorated function is called for the first time, its
    singleton object will be created. The same object will be returned
    on all consequent calls regardless of the passed arguments (if any).
    """

    __singleton = None

    def wrapper(*args, **kwargs):
        nonlocal __singleton

        if __singleton is None:
            __singleton = func(*args, **kwargs)

        return __singleton

    return wrapper

# Administrators (S-1-5-32-544)
@singleton
def __admin_sid(ql: Qiling):
    # nSubAuthority0 = SECURITY_BUILTIN_DOMAIN_RID[0x20]
    # nSubAuthority1 = DOMAIN_ALIAS_RID_ADMINS[0x220]

    return __create_default_sid(ql, (0x20, 0x220))

# All Users (S-1-5-32-545)
@singleton
def __users_sid(ql: Qiling):
    # nSubAuthority0 = SECURITY_BUILTIN_DOMAIN_RID[0x20]
    # nSubAuthority1 = DOMAIN_ALIAS_RID_USERS[0x221]

    return __create_default_sid(ql, (0x20, 0x221))

# All Users (S-1-5-32-546)
@singleton
def __guests_sid(ql: Qiling):
    # nSubAuthority0 = SECURITY_BUILTIN_DOMAIN_RID[0x20]
    # nSubAuthority1 = DOMAIN_ALIAS_RID_GUESTS[0x222]

    return __create_default_sid(ql, (0x20, 0x222))

# Power Users (S-1-5-32-547)
@singleton
def __powerusers_sid(ql: Qiling):
    # nSubAuthority0 = SECURITY_BUILTIN_DOMAIN_RID[0x20]
    # nSubAuthority1 = DOMAIN_ALIAS_RID_POWER_USERS[0x223]

    return __create_default_sid(ql, (0x20, 0x223))


# BOOL WINAPI CheckTokenMembership(
#   IN HANDLE TokenHandle,
#   IN PSID SidToCheck,
#   OUT PBOOL IsMember
# );
@winsdkapi(cc=STDCALL, params={
    'TokenHandle' : HANDLE,
    'SidToCheck'  : PSID,
    'IsMember'    : PBOOL
})
def hook_CheckTokenMembership(ql: Qiling, address: int, params):
    TokenHandle = params['TokenHandle']
    SidToCheck = params['SidToCheck']

    sid = ql.os.handle_manager.get(SidToCheck).obj
    IsMember = False

    # If TokenHandle is NULL, CheckTokenMembership uses the impersonation token of the calling thread.
    if not TokenHandle:
        # For now, treat power users as admins
        if __admin_sid(ql) == sid or __powerusers_sid(ql) == sid:
            IsMember = ql.os.profile["SYSTEM"]["permission"] == "root"

        elif __users_sid(ql) == sid:
            # FIXME: is this true for all tokens? probably not...
            IsMember = True

        elif __guests_sid(ql) == sid:
            IsMember = False

        else:
            raise NotImplementedError
    else:
        raise NotImplementedError

    ql.mem.write_ptr(params['IsMember'], int(IsMember))

    return 1


# PVOID FreeSid(
#   PSID pSid
# );
@winsdkapi(cc=STDCALL, params={
    'pSid' : PSID
})
def hook_FreeSid(ql: Qiling, address: int, params):
    # TODO: should also remove from ql.os.handle_manager ?
    ql.os.heap.free(params["pSid"])

    return 0

# BOOL EqualSid(
#   PSID pSid1,
#   PSID pSid2
# );
@winsdkapi(cc=STDCALL, params={
    'pSid1' : PSID,
    'pSid2' : PSID
})
def hook_EqualSid(ql: Qiling, address: int, params):
    # TODO once i have understood better how SID are wrote in memory. Fucking documentation
    # technically this one should be my SID that i created at the start. I said should, because when testing, it has a
    # different address. Why? No idea

    # sid1 = ql.os.handle_manager.get(params["pSid1"]).obj
    sid2 = ql.os.handle_manager.get(params["pSid2"]).obj

    # return sid1 == sid2
    return 0
