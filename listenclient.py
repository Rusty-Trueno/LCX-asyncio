import socket
import asyncio
import select
import time
import sys
import  random,os
import hashlib
import struct
HOSTLEN=40
TIMEOUT=300
MAXSIZE=20480
CONNECTNUM=5
header_len = 6
client=[]
mark=0
flag=0
async def receive_packet(reader):
    header = await reader.read(header_len)
    if header == '':
        raise RuntimeError("socket connection broken")
    (message_len,code,data_len) = struct.unpack('!HHH', header)
    print(message_len,code,data_len)
    packet = header

    while len(packet) < message_len:
        chunk = await reader.read(message_len - len(packet))
        if chunk == '':
            raise RuntimeError("socket connection broken")
        packet = packet + chunk

    (message_len,code,data_len,data) = struct.unpack('!HHH' + str(data_len) + 's', packet)
    return {'message_len':message_len,
            'code': code,
            'data_len': data_len,
            'data': data}

async def transmit1(reader,writer):
    recvierData = b""
    global flag
    mid=[reader,writer]
    client.append(mid)
    CoNid = 0
    print('Accept Connection')
    code = 7
    data_len = 4
    pack_format = '!HHHHH'
    message_len = header_len + data_len
    packet = struct.pack(pack_format, message_len, code, data_len, request_id, listen_port)
    print("Send a co nnect request!")
    remote[1].write(packet)
    #await writer.drain()
    while 1:
        try:
            data = await reader.read(20480)
            await asyncio.sleep(0.5)
            print('有数据从client发过来了')
            print(data)
            print(mark)
            recvierData += data  # 要给8000发送的数据
            for k, v in conn_sock.items():
                if v == [reader,writer]:
                    CoNid = k
                    print(CoNid)
                    print('查到了！！！')
                    break
            if len(data)==0:
                print('One of the clients are break!')
                code = 10
                data_len = 2
                connectid = CoNid
                message_len = header_len + data_len
                pack_format = '!HHHH'
                packet = struct.pack(pack_format, message_len, code, data_len, connectid)
                remote[1].write(packet)
                print('已发送disconnect ')
                #await writer.drain()
                #
                for k, v in conn_sock.items():
                    if v == [reader,writer]:
                        conn_sock.pop(k)
                        break
                writer.close()
                break
            if len(recvierData) != 0:
                bytes = len(recvierData)
                pack_format = '!HHHH' + str(bytes) + 's'
                code = 9
                data_len = bytes + 2
                message_len = data_len + header_len
                connect_id=CoNid
                print('data connectid is %d'%(connect_id))
                packet = struct.pack(pack_format, message_len, code, data_len, connect_id, recvierData)
                remote[1].write(packet)
                #await writer.drain()
                recvierData = b""
        except:
            break
async def transmit2():
    senderData = b""
    Connectid = 0
    global mark
    global flag
    while 1:
        packet = await receive_packet(remote[0])
        print('New coming is :%d' % (packet['code']))
        if packet['code'] == 8:
            data = packet['data']
            (Requestid, Result, Connect_id) = struct.unpack('!HHH', data)
            print('connect id is %d' % (Connect_id))
            print("Get a request ack")
            mid = {Connect_id: client[mark]}
            mark+=1
            print(mid)
            conn_sock.update(mid)
            mid.clear()
            flag=1
        elif packet['code'] == 10:
            print('TCP connect was broken!')
            data = packet['data']
            (connectID,) = struct.unpack('!H', data)
            #conn_sock[-1]==conn_sock[connectID]
            conn_sock[connectID][1].close()
            conn_sock.pop(connectID)
            packet.clear()
        elif packet['code'] == 9:
            data = packet['data']
            data_len = packet['data_len']
            (Connectid, Data) = struct.unpack('!H' + str(data_len - 2) + 's', data)
            print(Data)
            print('connect id is %d' % (Connectid))
            senderData += Data  # 准备发给client的数据
        if len(senderData) != 0:
            if Connectid in conn_sock.keys():
                conn_sock.get(Connectid)[1].write(senderData)
            else:
                print('The connectID is not exist!')
            senderData = b""

async def listener(reader,writer):
    remote.clear()
    remote.append(reader)
    remote.append(writer)
    salt = str(os.urandom(8)).encode()
    code = 1
    salt_len = len(salt)
    message_len = header_len + salt_len
    pack_format = '!HHH' + str(salt_len) + 's'
    packet = struct.pack(pack_format, message_len, code, salt_len, salt)
    writer.write(packet)
    await writer.drain()
    global request_id
    request_id= 0
    global listen_port
    listen_port= 0
    connect_id = 0
    global senderData
    global Connectid
    while 1:
        packet=await receive_packet(reader)
        print('New coming is %d'%(packet['code']))
        if packet['code']==2:
            print('Hashcode is back!')
            data=packet['data']
            (hash_len,user_len,hashuser)=struct.unpack('!HH'+str(packet['data_len']-4)+'s',data)
            (hashcode,username)=struct.unpack('!'+str(hash_len)+'s'+str(user_len)+'s',hashuser)
            password=str(user.get(username.decode()))
            secrect=password+str(salt)
            my_hash=hashlib.md5(secrect.encode()).hexdigest()
            if hashcode.decode()==my_hash:
                print("Comfirm succeed!")
                code=3
                result=1
            else:
                print("Confirm failed!")
                code=4
                result=0
            data_len=2
            pack_format='!HHHH'
            message_len=2+header_len
            packet=struct.pack(pack_format,message_len,code,data_len,result)
            writer.write(packet)
            await writer.drain()
        elif packet['code']==5:
            data=packet['data']
            (request_id,result,listen_port)=struct.unpack('!HHH',data)
            if listen_port==0:
                port = random.randrange(1, 9999, 1)
                listen_port = int(port)
            code=6
            try:
                result = 1
            except:
                result=0
            data_len=6
            pack_format='!HHHHHH'
            message_len=header_len+data_len
            packet=struct.pack(pack_format,message_len,code,data_len,request_id,result,listen_port)
            writer.write(packet)
            await writer.drain()
            loop.create_task(transmit2())
            loop.create_task(asyncio.start_server(transmit1, '0.0.0.0', listen_port, loop=loop))#监听8001

            break
def main():
    RemotePort=0
    global user
    global remote
    global conn_sock
    conn_sock={}
    global task_list
    task_list={}
    remote=[]
    user={}
    success=0
    global loop
    global verbose
    if len(sys.argv)>2:
        if sys.argv[1]=="-p" and len(sys.argv)>=3:
            RemotePort=int(sys.argv[2])
        else:
            print("instruction error1!")
        if sys.argv[3]=="-u" and len(sys.argv)>=5:
            string=str(sys.argv[4]).split(',')
            for s in string:
                us=s.split(':')
                dict1={us[0]:us[1]}
                user.update(dict1)
            success=1
        else:
            print("instruction error2!")
    else:
        print("instruction error3!")
    if success==1:
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(listener, '0.0.0.0', RemotePort, loop=loop)
        server = loop.run_until_complete(coro)
        print('Serving on{}'.format(server.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
if __name__ == "__main__":
     main()

