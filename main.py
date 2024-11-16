import os, sys
import time
import psutil

class Proc:

    @staticmethod
    def pidis():
        return psutil.pids()

    @staticmethod
    def proccess(pid):
        return psutil.Process(pid)

    @staticmethod
    def coresCount():
        return psutil.cpu_count()

    @staticmethod
    def threads(p):
        if isinstance(p, int):
            p = psutil.Process(p)
        count = p.num_threads()
        threads = p.threads()

    @staticmethod
    def processCpuTime(p):  # faster
        if isinstance(p, int):
            p = psutil.Process(p)
        sum = 0
        for thread in p.threads():
            sum += thread.system_time + thread.user_time
        return sum

    @staticmethod
    def proccessCpuTime2(p):  # slower
        if isinstance(p, int):
            p = psutil.Process(p)
        sum = 0
        for thread in p.threads():
            f = open("/proc/{pid}/task/{tid}/stat".format(pid=p.pid, tid=thread.id), 'r')
            text = f.read()
            f.close()
            last = text[text.rindex(')') + 1:].split()
            first = text[:text.rindex(')') + 1]
            arr = [first[first.index(' ') + 1:], first[:first.index(' ')]] + last
            sum += float(arr[13]) + float(arr[14])
        return sum

    @staticmethod
    def threadsStat(p):
        # https://man7.org/linux/man-pages/man5/proc.5.html
        # https://stackoverflow.com/questions/39066998/what-are-the-meaning-of-values-at-proc-pid-stat
        STATES = {
            'R': 'Running',
            'S': 'Sleeping in an interruptible wait',
            'D': 'Waiting in uninterruptible disk sleep',
            'Z': 'Zombie',
            'T': 'Stopped (in a signal)',
            't': 'Tracing stop',
            'W': 'Paging',
            'X': 'Dead',
            'x': 'Dead',
            'K': 'Wakekill',
            'P': 'Parked',
        }
        if isinstance(p, int):
            p = psutil.Process(p)
        datas = {}
        for thread in p.threads():
            tid = thread.id
            f = open("/proc/{pid}/task/{tid}/stat".format(pid=p.pid, tid=thread.id), 'r')
            text = f.read()
            f.close()
            last = text[text.rindex(')') + 1:].split()
            first = text[:text.rindex(')') + 1]

            arr = [first[first.index(' ') + 1:], first[:first.index(' ')]] + last

            datas[tid] = {
                'pid': p.pid,
                'comm': arr[1],  # The filename of the executable
                'state': (arr[2], STATES[arr[2]]),
                'ppid': int(arr[3]),  # The PID of the parent of this process.
                'pgrp': int(arr[4]),  # The process grouop ID of the proccess.
                'session': int(arr[5]),
                'tpgid': int(arr[7]),
                'utime': float(arr[13]),  # user mode time
                'stime': float(arr[14]),  # kernal time
                'cutime': float(arr[15]),  # waiting for children in user time
                'cstime': float(arr[16]),  # watining for children in kernal time
                'priority': int(arr[17]),
                'nice': int(arr[18]),  # priorirt:  the higher the value the lower the priority
                'num_threads': int(arr[19]),
                'vsize': int(arr[22]),  # virtual memory size
                'processor': int(arr[38]),  # CPU number last executed on.
                'rt_priority': int(arr[39]),  # real time scheduling priotiry
                'guest_time': float(arr[42]),
                # Guest time of the process (time spent running a vir‐tual CPU for a guest operating system), measured in clock ticks
                'cguest_time': float(arr[42]),  # Guest time of the process's children, measured in clock ticks
            }
        return datas

    @staticmethod
    def coresStat():
        # https://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux
        f = open('/proc/stat', 'r')
        data = f.read()
        f.close()
        cores = {}
        coresCount = Proc.coresCount()
        lines = data.split('\n')[:Proc.coresCount() + 1]
        core = 0
        for line in lines:
            tmp = line.split()
            cores[core] = {
                'user': int(tmp[1]),
                'nice': int(tmp[2]),
                'system': int(tmp[3]),
                'idle': int(tmp[4]),
                'iowait': int(tmp[5]),
                'irq': int(tmp[6]),
                'softirq': int(tmp[7]),
                'steal': int(tmp[8]),
                'guest': int(tmp[9]),
                'guest_nice': int(tmp[10]),
            }
            if core == coresCount:
                break
            core += 1
        return cores

    @staticmethod
    def coreUtilization(delay=0.5, callback=None, iteration=None):
        # https://www.linuxhowtos.org/System/procstat.htm
        i = 0
        first = Proc.coresStat()
        time.sleep(delay)
        coresCount = Proc.coresCount()
        print(first)
        while True:
            cores = {}
            second = Proc.coresStat()
            for i in range(coresCount + 1):
                prevIdle = first[i]['idle'] + first[i]['iowait']
                idle = second[i]['idle'] + second[i]['iowait']

                prevNonIdle = first[i]['user'] + first[i]['nice'] + first[i]['system'] + first[i]['irq'] + first[i][
                    'softirq'] + first[i]['steal']
                nonIdle = second[i]['user'] + second[i]['nice'] + second[i]['system'] + second[i]['irq'] + second[i][
                    'softirq'] + second[i]['steal']

                prevTotal = prevIdle + prevNonIdle
                total = idle + nonIdle

                totald = total - prevTotal

                idled = idle - prevIdle

                percent = (1 - idled / totald) * 100
                cores[i] = percent

            if callback != None:
                callback(cores)

            first = second
            time.sleep(delay)
            i += 1
            if i == iteration:
                break

    @staticmethod
    def loopCoreUtilization():
        if len(sys.argv) > 1:
            delay = float(sys.argv[1])
        else:
            delay = 0.8
        def callback(cores):
            os.system('clear')
            i=1
            while i < Proc.coresCount() + 1:
                print(i, ':', round(cores[i],2) ,end = '')
                i+=1
                if i < Proc.coresCount() + 1:
                    print(' - ',i, ':', round(cores[i],2), end='')
                    i+=1
                print()

        Proc.coreUtilization(delay,callback)


Proc.loopCoreUtilization()

