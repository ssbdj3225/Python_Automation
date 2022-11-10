from re import search
from re import sub
import paramiko
from paramiko import ssh_exception
import time
from socket import error

def exception_handler(function):
    def wrapper(*args, **kwargs):
        report = ''
        try:
            return function(*args, **kwargs)
        except ssh_exception.NoValidConnectionsError:
            print("Unable to connect to " + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) + ' - ' + args[0] + ' : Failure - Unable to connect to ' + args[0] + '\n\n'
            return report
        except TimeoutError:
            print("Connection TIMEOUT at " + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Connection TIMEOUT at ' + args[0] + '\n\n'
            return report
        except error as e:
            print("*** Caught exception: %s: %s" % (e.__class__, e) + ' at ' + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Caught exception: %s: %s' % (e.__class__, e) + ' at ' + args[0] + '\n\n'
            return report
        except ssh_exception.AuthenticationException:
            print("Incorrect password: " + str(args[2]))
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Incorrect password: ' + str(args[2]) + '\n\n'
            return report
        except Exception as e:
            print("*** Caught exception: %s: %s" % (e.__class__, e) + ' at ' + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Caught exception: %s: %s' % (e.__class__, e) + ' at ' + args[0] + '\n\n'
            return report
    return wrapper

def excute_time(func):
    def run(*arg):
        t1 = time.time()
        func(*arg)
        t2 = time.time()
        print(t2-t1)
    return run

class ParamikoConnector:
    def __init__(self,ip,username,password,privilege_password, privilege_method):
        print('connecting...')
        self.ip = ip
        self.username = username
        self.password = password
        self.pri_pass = privilege_password
        self.pri_cmd = privilege_method
        self.TIMEOUT = 10
        self.DELAY = .2
        self.connector = paramiko.SSHClient()
        self.connector.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def ssh(self):
        self.connector.connect(self.ip, 22, self.username, self.password, timeout=self.TIMEOUT)
        self.shell = self.connector.invoke_shell()
        time.sleep(3)

        if(self.pri_pass != 'nan'):  # 如果沒有給privilege密碼就不執行
            # print(self.ip + ': enter privilege mode!!!')
            pri_tmp = self.pri_cmd.pop()
            pri_tmp = pri_tmp.replace('*', self.pri_pass)
            self.pri_cmd.append(pri_tmp)
            for cmd in self.pri_cmd:
                # print(cmd)
                self.shell.send(cmd + '\n')
                time.sleep(self.DELAY)

        self.shell.send('\n')
        time.sleep(self.DELAY)
        init_text = self.shell.recv(65535).decode()
        self.device_name = search('.*\W+$', init_text).group(0)
        # print(self.device_name)

        print('Connection at ' + self.ip + ' Success!!!')

    def send_cmd(self,cmd):
        self.shell.send(cmd + '\n')
        time.sleep(self.DELAY)
    
    def receive(self):
        tmp = ''
        log = b''
        cnt = 0
        while True:
            try:
                if not self.shell.recv_ready():
                    if self.device_name in log.decode():
                        # print(self.ip + ' : stuck ' + str(cnt) + 'times...') # For stucking debug
                        break
                    time.sleep(1)
                    cnt += 1
                log = self.shell.recv(65535)
                tmp += str(log.decode())
                
                # if self.shell.recv_ready():
                #     log = self.shell.recv(65535)  
                #     if not log:    # 如果收到b''代表收完了 可以退出
                #         break
                #     tmp += str(log.decode())
                # else:break
            except EOFError:    # 可能收到其他終止符號導致EOF問題
                pass  # 只能用pass，不能用break
        return tmp

    def get_device_name(self):
        device_name = sub('\s', '', self.device_name)
        device_name = device_name[:-1]
        return device_name

    def close(self):
        self.shell.send('exit\n')
        time.sleep(self.DELAY)
        self.shell.close()
        self.connector.close()