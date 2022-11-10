from paramiko_connect import exception_handler
from paramiko_connect import ParamikoConnector
from common_tools import MyThreadTool
from common_tools import writter
import pandas as pd
import time
import re
from numpy import NAN
from os import makedirs
# import encodings.idna  # 包成EXE會遇到這個問題 import 就能解決

REPORT = ''  # 最後結果報告
MY_THREAD = MyThreadTool(5)
THREAD_NUMBER = 5  # 計算執行緒
threading_cnt = THREAD_NUMBER
# CISCO_ERR_MSG_LIST = ["% Invalid input detected at '^' marker.", "% Incomplete command.", ]
CISCO_ERR_MSG_I = "% Invalid input detected at '^' marker."
CISCO_ERR_MSG_II = "% Incomplete command."
CISCO_ERR_MSG_III = "syntax error:"
CISCO_ERR_MSG_IV = "% No entries found."

# make file direction
EXECUTE_DATE = time.strftime('%Y-%m-%d_%H-%M', time.localtime())
DOC_PATH = './Backup_' + EXECUTE_DATE
makedirs(DOC_PATH)

def thread_limiter(function):
    def wrapper(*args, **kwargs):
        global MY_THREAD, REPORT, threading_cnt
        tmp = function(*args, **kwargs)
        MY_THREAD.end()
        threading_cnt += 1
        REPORT += tmp
    return wrapper

@thread_limiter
@exception_handler
def show_command(ip, username, password, privilege_pass, tmp_cli, privilege_method):
    log = ''
    report = ''
    err_lst = []
    privilege_pass = str(privilege_pass)  # Empty password will be read as "float", trasfer the password into string to avoid the bug
    host = ParamikoConnector(ip, username, password, privilege_pass, privilege_method)
    host.ssh()
    device_name = host.get_device_name()

    host.send_cmd('')
    time.sleep(.2)

    for cmd in tmp_cli:
        host.send_cmd(cmd)
        tmp = host.receive()
        if CISCO_ERR_MSG_I in tmp or CISCO_ERR_MSG_II in tmp or CISCO_ERR_MSG_III in tmp or CISCO_ERR_MSG_IV in tmp:
            err_lst.append(cmd)
        log += tmp

    host.close()
    log = log.replace('\r\n', '\n')

    writter('./' + DOC_PATH + '/' + device_name + '@' + ip + '_' + str(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())) + '.txt', log)
    print(str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) + ' - Backup Process of ' + ip + ' has been done!!!')

    # making LOG information
    report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) + ' - ' + device_name + ' - ' + ip + ' : Backup Success!!!\n'
    report += ' <Command Not Support as Below>\n'
    if err_lst :
        for cmd in err_lst:
            report += '   - ' + cmd + '\n'
    report += '\n'
    return report

print('Starting Backup Process...')

host_list = pd.read_excel("host.xlsx", dtype=str)  # 讀取host.xlsx
privilege_table = pd.read_excel("host.xlsx", sheet_name='privilege_method', dtype=str)
manufac_list = host_list['model'].tolist()  # 將model欄位轉成list 內容:(廠牌/型號)

for i in range(len(manufac_list)):  # 只留下廠牌
    manufac_list[i] = re.sub('/.*', '', manufac_list[i])
manufac_set = set(manufac_list)  # 將重複廠牌的去除

raw_cli_df = pd.DataFrame()  # 指令DataFrame
manufac_cnt = {}  # 各廠牌及指令範圍
cnt = 0
for manufac in manufac_set:  # 確認廠牌後 根據backup.xlsx的Sheet尋找有沒有這個廠牌 有就讀取所有型號的指令
    read_in = pd.read_excel("backup.xlsx", sheet_name=manufac, dtype=str)
    raw_cli_df = pd.concat([raw_cli_df, read_in], axis=1, join='outer')  # 讀取後將read_in合併到raw_cli_df
    cli_dic = {manufac:(cnt, cnt+len(read_in.columns))}  # 將廠牌型號範圍第幾行到第幾行存入Dict
    cnt += len(read_in.columns)
    manufac_cnt.update(cli_dic)  # 廠牌更新到manufac_cnt

for tmp in host_list.iloc:  # 一列一列看各個設備資料 準備輸入指令
    a = tmp['model'].split('/')
    ip = tmp['IP']  
    manufacturer = a[0]  # 廠牌
    model = a[1]  # 型號
    username = tmp['username']
    password = tmp['password']
    privilege_pass = tmp['enable_pass']
    privilege_method = privilege_table[manufacturer].tolist()
    try:
        model = int(model)  # 純數字的型號在index會顯示為int 這邊如果是純數字就轉int
    except Exception:
        pass

    if manufacturer in manufac_cnt:  # 確認有該廠牌的指令
        if model in raw_cli_df.columns[manufac_cnt[manufacturer][0]:manufac_cnt[manufacturer][1]]:  # 確認該廠牌範圍內有沒有該型號的指令
            tmp_cli = list(raw_cli_df.iloc[:, manufac_cnt[manufacturer][0]:manufac_cnt[manufacturer][1]][model])  # 取出要執行的指令
        else:
            print('No Such Infra for ' + manufacturer + ' .\nPlease Check Your Model of ' + ip +' .')  
            continue
    else:
        print('No Such Commands for ' + manufacturer + ' .\nPlease Check If You Put the Manufacter in Your Backup File .')
        continue

    while NAN in tmp_cli:  # 去除空指令(DataFrame的NAN)
        tmp_cli.remove(NAN)
    while NAN in privilege_method:  # 去除空指令(DataFrame的NAN)
        privilege_method.remove(NAN)
    
    MY_THREAD.run(show_command, ip, username, password, privilege_pass, tmp_cli, privilege_method)
    threading_cnt -= 1

while True:
    if(threading_cnt==THREAD_NUMBER):  # 每0.5秒確認一次 確認5個執行緒都被釋放了才輸出REPORT
        writter(str(time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime())) + '-backup_report.log', REPORT)
        break
    else:time.sleep(.5)

input("press <ENTER> to quit...")