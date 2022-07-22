import threading
import time

def excute_time(func):  # 計算執行時間 
    def run(*args,**kwargs):
        t1 = time.time()
        func(*args,**kwargs)
        t2 = time.time()
        print('excute time is : ' + str(t2-t1) + ' s .')
    return run

def writter(name,content):
    with open(name, 'w', encoding='utf_8_sig') as writter:
        writter.write(content)

class MyThreadTool:
    def __init__(self,limit=0):
        self.num = limit
        if self.num != 0:
            self.Limit = threading.Semaphore(self.num)

    def run(self, function, *args):
        self.thread = threading.Thread(target=function, args=args)
        if self.num != 0 : 
            self.Limit.acquire()
        self.thread.start()

    def end(self):
        if self.num != 0 : 
            self.Limit.release()

    def join(self):
        self.thread.join()