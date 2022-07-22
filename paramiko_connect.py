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
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) + ' - ' + args[0] + ' : Failure - Unable to connect to ' + args[0] + '\n'
            return report
        except TimeoutError:
            print("Connection TIMEOUT at " + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Connection TIMEOUT at ' + args[0] + '\n'
            return report
        except error as e:
            print("*** Caught exception: %s: %s" % (e.__class__, e) + ' at ' + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Caught exception: %s: %s' % (e.__class__, e) + ' at ' + args[0] + '\n'
            return report
        except ssh_exception.AuthenticationException:
            print("Incorrect password: " + str(args[2]))
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Incorrect password: ' + str(args[2]) + '\n'
            return report
        except Exception as e:
            print("*** Caught exception: %s: %s" % (e.__class__, e) + ' at ' + args[0])
            report = str(time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime())) +  ' - ' + args[0] + ' : Failure - Caught exception: %s: %s' % (e.__class__, e) + ' at ' + args[0] + '\n'
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
    def __init__(self,ip,username,password):
        print('connecting...')
        self.ip = ip
        self.username = username
        self.password = password
        self.TIMEOUT = 10
        self.DELAY = .3
        self.connector = paramiko.SSHClient()
        self.connector.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def ssh(self):
        self.connector.connect(self.ip, 22, self.username, self.password, timeout=self.TIMEOUT)
        self.shell = self.connector.invoke_shell()
        time.sleep(self.DELAY)
        print('Connection at ' + self.ip + ' Success!!!')

    def send_cmd(self,cmd):
        self.shell.send(cmd + '\n')
        time.sleep(self.DELAY)
    
    def receive(self):
        tmp = ''
        while True:
            try:
                if self.shell.recv_ready():
                    log = self.shell.recv(65535)  
                    if not log:    # 如果收到b''代表收完了 可以退出
                        break
                    tmp += str(log.decode())
                else:break
            except EOFError:    # 可能收到其他終止符號導致EOF問題
                pass  # 只能用pass，不能用break
        return tmp

    def close(self):
        self.shell.send('exit\n')
        time.sleep(self.DELAY)
        self.shell.close()
        self.connector.close()