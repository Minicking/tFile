import logging
import platform

class Config:
    Debug = True
    # env is windows or linux
    Env_symbol = '\\' if r'Windows' in platform.platform() else '/'
    ServerHost = {
        r'tzf': r'139.196.163.240',
        r'lmh': r'47.103.200.210'
        }
    ServerPort = 7000


    LogFormat = '%(log_color)s[%(asctime)s][%(filename)s:%(lineno)d][%(levelname)s]: %(message)s'
    LogColor = {
        r'DEBUG': r'cyan',
        r'INFO': r'green',
        r'WARNING': r'yellow',
        r'ERROR': r'red',
        r'CRITICAL': r'red'
    }

    BufferSize = int(1024 * 10)


