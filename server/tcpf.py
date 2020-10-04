from socket import *
import struct
import json
import os
import sys
import time
import zipfile
import os
import zipfile
 
 
def get_zip_file(input_path, result):
    """
    对目录进行深度优先遍历
    :param input_path:
    :param result:
    :return:
    """
    files = os.listdir(input_path)
    for file in files:
        if os.path.isdir(input_path + '/' + file):
            get_zip_file(input_path + '/' + file, result)
        else:
            result.append(input_path + '/' + file)
 
 
def zip_file_path(input_path, output_path, output_name):
    """
    压缩文件
    :param input_path: 压缩的文件夹路径
    :param output_path: 解压（输出）的路径
    :param output_name: 压缩包名称
    :return:
    """
    f = zipfile.ZipFile(output_path + '/' + output_name, 'w', zipfile.ZIP_DEFLATED)
    filelists = []
    get_zip_file(input_path, filelists)
    for file in filelists:
        f.write(file)
    # 调用了close方法才会保证完成压缩
    f.close()
    return output_path + r"/" + output_name
    
def process_bar(precent,width,maxs,cur,speed):
    use_num = int(precent*width)
    space_num = int(width-use_num)
    precent = precent*100
    if speed>0:
        yt=(maxs-cur)*1024.0/speed
    else:
        yt=0
    if speed>1024.0:
        speed/=1024.0
        st="%10.2fmb/s"%(speed)
    else:
        st="%10.2fkb/s"%(speed)
    print('[%s%s][%.2fmb/%.2fmb]%.2f%%(%s)[预计剩余时间:%.2f秒]%s'%(use_num*'#', space_num*' ',cur,maxs,precent,st,yt,"    "),file=sys.stdout, end='\r')

class Client:
    def __init__(self):
        self.addr=('139.196.163.240',7000)
        # self.addr=('47.103.200.210',7000)
        # self.addr=('47.103.200.210',9799)
        self.buffsize=int(1024*10)
        self.socket=socket(AF_INET, SOCK_STREAM)
    def run(self):
        self.socket.connect(self.addr)
        print('连接服务器中...',self.addr)
        while True:
            command=str(input("输入指令>>"))
            ix=command.index(':')
            waitRespons=True
            if ix!=-1:
                arg_type=command[0:ix]
                arg_data=command[ix+1:]
                data={'type':arg_type}

                if arg_type=='download':
                    data['filename']=arg_data
                    print('发送请求下载文件',data)
                    self.socket.send(json.dumps(data).encode('utf-8'))
                    try:
                        resp=json.loads(self.socket.recv(19).decode('utf-8'))
                    except Exception as e:
                        print('收到一个不符合期望的回应,连接中断！')
                        self.socket.close()
                        waitRespons=False
                    else:
                        if resp['type']=='success':
                            print('即将准备下载')
                        else:
                            print('服务器中不存在【%s】'%arg_data)
                            waitRespons=False
                elif arg_type=='ls':
                    self.socket.send(json.dumps(data).encode('utf-8'))
                elif arg_type=='upload':
                    waitRespons=False
                    arg_data=arg_data.strip('\n')
                    print(arg_data)
                    if os.path.exists(arg_data):
                        if self.isfile(arg_data):
                            self.sendFile(arg_data)
                        else:
                            print('是一个文件夹,先进行压缩')
                    else:
                        print('文件不存在')
                else:
                    waitRespons=False
                    print('无法识别的指令，请重新输入.可用指令有[ls:] [download:] [upload:]')
            else:
                waitRespons=False
                print('无法识别的指令，请重新输入.可用指令有[ls:] [download:] [upload:]')
            #以上是客户端发送数据，以下是客户端接收服务器返回的数据
            if waitRespons:
                print("等待服务器对你的指令进行回应...")
                dataLen=struct.unpack('i',self.socket.recv(4))[0]
                try:
                    data=self.socket.recv(dataLen)
                    data=data.decode('utf-8')
                    data=json.loads(data)
                except Exception as e:
                    print('接收到非法数据，连接强行中断！')
                    print('错误类型：',e)
                    print('接收到的数据:',data)
                    self.socket.close()
                    break
                else:
                    if data['type']=='dir':
                        print('服务器的可下载文件列表：')
                        ind=1
                        for i in data['data']:
                            print("%d:%10.2fMB-----%s"%(ind,i[1]/1024.0/1024.0,i[0]))
                            ind+=1
                    elif data['type']=='fileHead':
                        self.download()
    def isfile(self,path):
        if os.path.isdir(path):
            return False
        elif os.path.isfile(path):
            return True
        else:
            return False

    def download(self):
        print('准备下载请求的文件...')
        head_struct = self.socket.recv(4)  # 接收报头的长度,
        if head_struct:
            print('等待接收数据...')
        head_len = struct.unpack('i', head_struct)[0]  # 解析出报头的字符串大小
        data = self.socket.recv(head_len)  # 接收长度为head_len的报头内容的信息 (包含文件大小,文件名的内容)
        head_dir = json.loads(data.decode('utf-8'))
        filesize_b = head_dir['filesize_bytes']
        filename = head_dir['filename']
        #   接受真的文件内容
        recv_len = 0
        recv_mesg = b''
        old = time.time()
        f = open(filename, 'wb')
        count=0
        scount=0
        time1=time.time()
        time2=0
        speed=0
        flag_end=False
        while recv_len < filesize_b:
            if filesize_b - recv_len > self.buffsize:
                recv_mesg = self.socket.recv(self.buffsize)
                f.write(recv_mesg)
                recv_len += len(recv_mesg)
            else:
                recv_mesg = self.socket.recv(filesize_b - recv_len)
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
    def sendFile(self,file):
        filemesg = file
        filesize_bytes = os.path.getsize(filemesg) # 得到文件的大小,字节
        nowTime=time.localtime()
        filename =os.path.basename(file)
        dirc = {
            'filename': filename,
            'filesize_bytes': filesize_bytes,
        }
        head_info = json.dumps(dirc)  # 将字典转换成字符串
        head_info_len = struct.pack('i', len(head_info)) #  将字符串的长度打包
        #   先将报头转换成字符串(json.dumps), 再将字符串的长度打包
        #   发送报头长度,发送报头内容,最后放真是内容
        #   报头内容包括文件名,文件信息,报头
        #   接收时:先接收4个字节的报头长度,
        #   将报头长度解压,得到头部信息的大小,在接收头部信息, 反序列化(json.loads)
        #   最后接收真实文件
        try:
            self.socket.send(json.dumps({'type':'upload'}).encode('utf-8'))
            self.socket.send(head_info_len)  # 发送head_info的长度
            self.socket.send(head_info.encode('utf-8'))
        except Exception as e:
            print("信息头发送失败,连接强行中断！",e)
            self.socket.close()
        #   发送真是信息
        else:
            with open(filemesg, 'rb') as f:
                data = f.read()
                try:
                    self.socket.sendall(data)
                except Exception as e:
                    print("发送失败")
                    self.socket.close()
                else:
                    print('发送成功')
        
client=Client()
client.run()











# tcp_client = socket(AF_INET, SOCK_STREAM)
# ip_port = (('139.196.163.240', 7000))
# # ip_port = (('127.0.0.1', 7000))
# buffsize = 1024*20
# tcp_client.connect_ex(ip_port)
# print('等待链接服务端')
# command=str(input("输入命令:"))
# if command[0:5]=='file:':
#     tcp_client.send(json.dumps({'type':'file','filename':command[5:]}).encode("utf-8"))
#     while True:
        
#         head_struct = tcp_client.recv(4)  # 接收报头的长度,
#         if head_struct:
#             print('已连接服务端,等待接收数据')
#         head_len = struct.unpack('i', head_struct)[0]  # 解析出报头的字符串大小
#         data = tcp_client.recv(head_len)  # 接收长度为head_len的报头内容的信息 (包含文件大小,文件名的内容)

#         head_dir = json.loads(data.decode('utf-8'))
#         filesize_b = head_dir['filesize_bytes']
#         filename = head_dir['filename']
#         #   接受真的文件内容
#         recv_len = 0
#         recv_mesg = b''
#         old = time.time()
#         f = open(filename, 'wb')
#         count=0
#         scount=0
#         time1=time.time()
#         time2=0
#         speed=0
#         flag_end=False
#         while recv_len < filesize_b:
            
#             if filesize_b - recv_len > buffsize:
#                 recv_mesg = tcp_client.recv(buffsize)
#                 # f.write(recv_mesg)
#                 recv_len += len(recv_mesg)
#             else:
#                 recv_mesg = tcp_client.recv(filesize_b - recv_len)
#                 recv_len += len(recv_mesg)
#                 # f.write(recv_mesg)
#                 flag_end=True
            
#             count+=1
#             scount+=len(recv_mesg)
#             if count>=20 or flag_end:
#                 time2=time.time()
#                 dt=time2-time1
#                 speed=scount/1024.0/dt
#                 time1=time2
#                 # print("结算一次：",speed,dt,scount)
#                 count=0
#                 scount=0
#             percent = recv_len / filesize_b
#             process_bar(percent,50,filesize_b/1048576.0,recv_len/1048576.0,speed)
#         now = time.time()
#         stamp = now - old
#         print('[总共用时%.5fs]' % stamp)
#         f.close()
#         tcp_client.close()
#         sys.exit()