#encoding:utf-8
from socket import *
import struct
import json
import os,sys,time
import threading
class Config:
    IP='0.0.0.0'
    PORT=7000
    BUFFSIZE=int(1024*1)
    LINK_NUM=2#最大链接数
    FILE_DIR=os.getcwd()+'\\FILE_DIR'
def process_bar(precent,width,maxs,cur,speed):
    use_num = int(precent*width)
    space_num = int(width-use_num)
    precent = precent*100
    if speed>0:
        yt=(maxs-cur)*1024.0/speed
    else:
        yt=99999
    if speed>1024.0:
        speed/=1024.0
        st="%10.2fmb/s"%(speed)
    else:
        st="%10.2fkb/s"%(speed)
    print('[%s%s][%.2fmb/%.2fmb]%.2f%%(%s)[预计剩余时间:%.2f秒]%s'%(use_num*'#', space_num*' ',cur,maxs,precent,st,yt,"    "),file=sys.stdout, end='\r')

class Server:
    def __init__(self,config):
        self.socket=socket(AF_INET, SOCK_STREAM)
        self.socket.bind((config.IP,config.PORT))
        self.linkList=[]
        self.config=config
        if not os.path.exists(self.config.FILE_DIR):
            os.mkdir(self.config.FILE_DIR)
    def start(self,command=False):
        self.socket.listen(self.config.LINK_NUM)
        self.listen=threading.Thread(target=self.listen,args=())
        # self.listen.setDaemon(True)
        self.listen.start()
        print("客户端连接监听已开启")
        if command:
            self.command=threading.Thread(target=self.command,args=())
            self.command.setDaemon(True)
            self.command.start()
            print("接受命令输入已开启")
    def listen(self):
        while True:
            socket,addr=self.socket.accept()
            print("%s进行了连接"%(str(addr)))
            thr=threading.Thread(target=self.clientListen,args=(socket,))
            # thr.setDaemon(True)
            self.linkList.append((socket,thr))
            thr.start()
    def removeSocket(self,socket):
        for i in self.linkList:
            if socket in i:
                self.linkList.remove(i)
                break
    def clientListen(self,socket):
        while True:
            try:
                data =socket.recv(self.config.BUFFSIZE).decode("utf-8")
                data=json.loads(data)
            except Exception as e:
                print('连接中断',socket,e)
                socket.close()
                self.removeSocket(socket)
                break
            else:
                print("接收到来自客户端的指令信息：",data)
                if data['type']=='ls':
                    filelist=os.listdir(self.config.FILE_DIR)
                    filedir=[]
                    for i in filelist:
                        filedir.append((i,os.path.getsize(self.config.FILE_DIR+'\\'+i)))
                    print("当前文件夹内的可下载文件：",filedir)
                    sendData=json.dumps({'type':'dir','data':filedir}).encode('utf-8')
                    socket.send(struct.pack('i',len(sendData)))
                    socket.send(sendData)
                elif data['type']=='download':
                    print('尝试发送请求的文件给客户端：',data['filename'])
                    self.sendFile(socket,data['filename'])
                elif data['type']=='upload':
                    print('尝试接收来自客户端的文件：')
                    self.download(socket)
    def sendFile(self,socket,file):
        filemesg = self.config.FILE_DIR+"\\"+file.strip()
        if not os.path.exists(filemesg):
            print('尝试发送的文件不存在',filemesg)
            socket.send(json.dumps({'type':'fail'}).encode('utf-8'))
        else:
            print('尝试发送的文件存在',filemesg)
            socket.send(json.dumps({'type':'success'}).encode('utf-8'))
            filesize_bytes = os.path.getsize(filemesg) # 得到文件的大小,字节
            nowTime=time.localtime()
            filename ='%s_%s_%s_'%(nowTime.tm_mon,nowTime.tm_mday,nowTime.tm_hour)+file.strip()
            dirc = {
                'filename': filename,
                'filesize_bytes': filesize_bytes,
            }
            head_info = json.dumps(dirc)  # 将字典转换成字符串
            head_info_len = struct.pack('i',len(head_info)) #  将字符串的长度打包
            print("长度打包结果：")
            print(head_info_len,type(head_info_len),len(head_info))
            #   先将报头转换成字符串(json.dumps), 再将字符串的长度打包
            #   发送报头长度,发送报头内容,最后放真是内容
            #   报头内容包括文件名,文件信息,报头
            #   接收时:先接收4个字节的报头长度,
            #   将报头长度解压,得到头部信息的大小,在接收头部信息, 反序列化(json.loads)
            #   最后接收真实文件
            socket.send(struct.pack('i',20))
            socket.send(json.dumps({'type':'fileHead'}).encode('utf-8'))
            print('尝试发送文件的基础信息：')
            print('基础新的长度:',head_info_len)
            socket.send(head_info_len)  # 发送head_info的长度
            print('基础信息:',head_info)
            socket.send(head_info.encode('utf-8'))
            print('完毕')
            #   发送真是信息
            with open(filemesg, 'rb') as f:
                data = f.read()
                try:
                    socket.sendall(data)
                except Exception as e:
                    print('发送失败',e)
                    self.removeSocket(socket)
                else:
                    print('发送成功')
    def download(self,socket):
        print('准备下载请求的文件...')
        head_struct = socket.recv(4)  # 接收报头的长度,
        if head_struct:
            print('等待接收数据...')
        head_len = struct.unpack('i', head_struct)[0]  # 解析出报头的字符串大小
        data = socket.recv(head_len)  # 接收长度为head_len的报头内容的信息 (包含文件大小,文件名的内容)
        head_dir = json.loads(data.decode('utf-8'))
        filesize_b = head_dir['filesize_bytes']
        filename = head_dir['filename']
        #   接受真的文件内容
        recv_len = 0
        recv_mesg = b''
        old = time.time()
        f = open(self.config.FILE_DIR+"\\"+filename, 'wb')
        count=0
        scount=0
        time1=time.time()
        time2=0
        speed=0
        flag_end=False
        while recv_len < filesize_b:
            if filesize_b - recv_len > self.config.BUFFSIZE:
                recv_mesg = socket.recv(self.config.BUFFSIZE)
                f.write(recv_mesg)
                recv_len += len(recv_mesg)
            else:
                recv_mesg = socket.recv(filesize_b - recv_len)
                recv_len += len(recv_mesg)
                f.write(recv_mesg)
                flag_end=True
            count+=1
            scount+=len(recv_mesg)
            time2=time.time()
            dt=time2-time1
            if dt>0.5:
                speed=scount/1024.0/dt
                time1=time2
                count=0
                scount=0
            percent = recv_len / filesize_b
            process_bar(percent,50,filesize_b/1048576.0,recv_len/1048576.0,speed)
        now = time.time()
        stamp = now - old
        print('[总共用时%.5fs]' % stamp)
        f.close()
    def command(self):
        while True:
            command=str(input("输入命令:"))
            print("接受的命令：%s"%command)
server=Server(Config())
server.start()