# from socket import *
from socket import AF_INET, SOCK_STREAM, socket
from PyQt5.QtWidgets import QMainWindow
import struct
import json
import os
import sys
import time
from util import Util
from config import Config
from log import Log
import colorlog
import asyncio

class Client(Util, QMainWindow):
    def __init__(self, HostName):
        super().__init__()
        self.addr = (Config.ServerHost[HostName], Config.ServerPort)
        self.buffsize = Config.BufferSize
        self.init_log()
        self.init_socket()
        self.init_UI()

    def init_log(self):
        self.logger = Log()
        self.logger.info(r'初始化日志模块...')

    def init_socket(self):
        self.logger.info(r'连接服务器{}中...'.format(self.addr))
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.connect(self.addr)
        
    def init_UI(self):
        pass

    def run(self):
        while True:
            pass
            

    def download(self):
        self.logger.info('准备下载请求的文件...')
        head_struct = self.socket.recv(4)  # 接收报头的长度,
        if head_struct:
            self.logger.info('等待接收数据...')
        head_len = struct.unpack('i', head_struct)[0]  # 解析出报头的字符串大小
        # 接收长度为head_len的报头内容的信息 (包含文件大小,文件名的内容)
        data = self.socket.recv(head_len)
        head_dir = json.loads(data.decode('utf-8'))
        filesize_b = head_dir['filesize_bytes']
        filename = head_dir['filename']
        #   接受真的文件内容
        recv_len = 0
        recv_mesg = b''
        old = time.time()
        f = open(filename, 'wb')
        count = 0
        scount = 0
        time1 = time.time()
        time2 = 0
        speed = 0
        flag_end = False
        while recv_len < filesize_b:
            if filesize_b - recv_len > self.buffsize:
                recv_mesg = self.socket.recv(self.buffsize)
                f.write(recv_mesg)
                recv_len += len(recv_mesg)
            else:
                recv_mesg = self.socket.recv(filesize_b - recv_len)
                recv_len += len(recv_mesg)
                f.write(recv_mesg)
                flag_end = True
            count += 1
            scount += len(recv_mesg)
            time2 = time.time()
            dt = time2-time1
            if dt > 0.5:
                speed = scount/1024.0/dt
                time1 = time2
                count = 0
                scount = 0
            percent = recv_len / filesize_b
        now = time.time()
        stamp = now - old
        self.logger.info('[总共用时%.5fs]' % stamp)
        f.close()

    def sendFile(self, file):
        filemesg = file
        filesize_bytes = os.path.getsize(filemesg)  # 得到文件的大小,字节
        nowTime = time.localtime()
        filename = os.path.basename(file)
        dirc = {
            'filename': filename,
            'filesize_bytes': filesize_bytes,
        }
        head_info = json.dumps(dirc)  # 将字典转换成字符串
        head_info_len = struct.pack('i', len(head_info))  # 将字符串的长度打包
        #   先将报头转换成字符串(json.dumps), 再将字符串的长度打包
        #   发送报头长度,发送报头内容,最后放真是内容
        #   报头内容包括文件名,文件信息,报头
        #   接收时:先接收4个字节的报头长度,
        #   将报头长度解压,得到头部信息的大小,在接收头部信息, 反序列化(json.loads)
        #   最后接收真实文件
        try:
            self.socket.send(json.dumps({'type': 'upload'}).encode('utf-8'))
            self.socket.send(head_info_len)  # 发送head_info的长度
            self.socket.send(head_info.encode('utf-8'))
        except Exception as e:
            self.logger.error("信息头发送失败,连接强行中断！{}".format(e))
            self.socket.close()
        #   发送真是信息
        else:
            with open(filemesg, 'rb') as f:
                data = f.read()
                try:
                    self.socket.sendall(data)
                except Exception as e:
                    self.logger.info("发送失败")
                    self.socket.close()
                else:
                    self.logger.info('发送成功')


client = Client('tzf')
client.run()
