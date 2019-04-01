import socket
import asyncio
import select
import sys
import  random
import hashlib
import struct
HOSTLEN=40
TIMEOUT=300
MAXSIZE=20480
CONNECTNUM=5
header_len = 6
client=[]
address1=""
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
async def transmit(message1,loop):
    senderData = b""
    global Connectid
    global address1
    Connectid = 0
    while 1:
        packet = await receive_packet(message1[0])
        print('New coming is %d' % (packet['code']))
        if packet['code'] == 7:
            data = packet['data']
            (Requestid, Listenport) = struct.unpack('!HH', data)
            print("The listenport is %d" % (Listenport))
            print("Start to connect slavePC %s:%d" % (local))
            reader, writer = await asyncio.open_connection(local[0],local[1] , loop=loop)
            midd=[reader,writer]
            client.append(midd)
            loop.create_task(transmit2(message1,client[len(client)-1][0],client[len(client)-1][1]))
            print("Connect slave succeed!")
            code = 8
            result = 1
            ConnectID = int(random.randint(0, 1000)) # int(input())
            print('connect id is %d'%(ConnectID))
            slave=[reader, writer]
            mid = {ConnectID: slave}
            conn_sock.update(mid)
            data_len = 6
            message_len = data_len + header_len
            pack_format = '!HHHHHH'
            packet = struct.pack(pack_format, message_len, code, data_len, Requestid, result, ConnectID)
            print("Send connect ack!")
            message1[1].write(packet)
            print("Connect ack send succeed!")
        elif packet['code'] == 10:
            print('TCP connect was broken!')
            data = packet['data']
            (connect_id,) = struct.unpack('!H', data)
            print('Close connect_id is :%d' % connect_id)
            #conn_sock[-1]=conn_sock[connect_id]
            conn_sock[connect_id][1].close()
            conn_sock.pop(connect_id)
            #conn_sock.pop(connect_id)
        elif packet['code'] == 9:
            data = packet['data']
            data_len = packet['data_len']
            (Connectid, Data) = struct.unpack('!H' + str(data_len - 2) + 's', data)
            print(Data)
            print('the coming id is:%d'%Connectid)
            senderData += Data  # 准备发给client的数据
            address1 = address
        if len(senderData) != 0:
            if Connectid in conn_sock.keys():
                conn_sock.get(Connectid)[1].write(senderData)
            else:
                print('The connectID is not exist!')
            senderData = b""


async def transmit2(message1,reader,writer):
    recvierData = b""
    verbose = False
    if '-v' in sys.argv:
        verbose = True
    connect_id = 0
    slave=[reader,writer]
    #print(slave)
    #print(conn_sock)
    while 1:
        try:
            data = b""

            data = await reader.read(20480)
            recvierData += data  # 要给8000发送的数据
            address1 = local
            for k, v in conn_sock.items():
                if v == slave:
                    print('查到了！')
                    connect_id = k
                    break
            if len(data)==0:
                print('One of the local_slave are break!')
                code = 10
                data_len = 2
                connectid = 0
                for k, v in conn_sock.items():
                    if v == slave:
                        connectid = k
                        break
                conn_sock[connectid][1].close()
                print('The connect_id is:%d' % (connectid))
                message_len = header_len + data_len
                pack_format = '!HHHH'
                packet = struct.pack(pack_format, message_len, code, data_len, connectid)
                message1[1].write(packet)
                print('已发送disconnect')
                break
            bytes = len(data)
            if verbose:
                print("Recv From %s:%d" % address1, " %d bytes" % bytes)
            if len(recvierData) != 0:
                bytes = len(recvierData)
                if verbose:
                    print("Send to %s:%d", address, " %d bytes" % bytes)
                pack_format = '!HHHH' + str(bytes) + 's'
                code = 9
                data_len = bytes + 2
                message_len = data_len + header_len
                packet = struct.pack(pack_format, message_len, code, data_len, connect_id, recvierData)
                message1[1].write(packet)  # 向slave发送Data数据包
                recvierData = b""
        except:
            break




async def slaver(message,loop):
    reader, writer = await asyncio.open_connection(message[0], message[1], loop=loop)
    request_id=0
    connect_id=0
    listen_port=0
    while True:
        packet=await receive_packet(reader)
        print("New coming is:%d"%(packet['code']))
        if packet['code']==1:
            print("Got a salt!")
            salt=str(packet['data'])
            code=2
            secrect=password+salt
            hashcode=hashlib.md5(secrect.encode()).hexdigest()
            hash_len=len(hashcode.encode())
            user_len=len(user.encode())
            data_len=hash_len+user_len+4
            message_len=data_len+header_len
            pack_format='!HHHHH'+str(hash_len)+'s'+str(user_len)+'s'
            packet=struct.pack(pack_format,message_len,code,data_len,hash_len,user_len,hashcode.encode(),user.encode())
            print("Send chap result!")
            writer.write(packet)
        elif packet['code']==3:
            print("Confirm succeed!")
            code=5
            request_id=random.randint(0,100)
            result=1
            listen_port=int(Remotelisten)
            data_len=6
            message_len=data_len+header_len
            pack_format = '!HHHHHH'
            packet = struct.pack(pack_format, message_len, code, data_len, request_id,result,listen_port)
            writer.write(packet)
        elif packet['code']==4:
            print("Confirm failed!")
            break;
        elif packet['code']==6:
            data=packet['data']
            (Requestid,Result,Listenport)=struct.unpack('!HHH',data)
            if Result==1:
                print('Bind response is back!')
                print('ListenPort is %d'%(Listenport))
            else:
                print('Deploy listenport Failed!')
            message1=[reader,writer]
            await transmit(message1,loop)
            break
def main():
    global verbose
    global conn_sock
    conn_sock = {}

    global loop,address,Remotelisten,local,user,password
    if len(sys.argv)>2:
        if sys.argv[1] == "-r" and len(sys.argv)>=3:
            s=str(sys.argv[2]).split(':')
            RemoteAddr=s[0]
            RemotePort=int(s[1])
        else:
            print("instruction error!")
            return
        if sys.argv[3]=="-u" and len(sys.argv)>=5:
            s=str(sys.argv[4]).split(':')
            user=s[0]
            password=s[1]
        else:
            print("instruction error!")
            return
        if sys.argv[5]=="-p" and len(sys.argv)>=7:
            Remotelisten=sys.argv[6]
        else:
            print("instruction error!")
            return
        if sys.argv[7]=="-l" and len(sys.argv)>=9:
            s=str(sys.argv[8]).split(':')
            LocalAddr=s[0]
            LocalPort=int(s[1])
            success=1
        else:
            print("instruction error!")
            return
    else:
        print("instruction error!")
        return
    if success==1:
        local=(LocalAddr,int(LocalPort))
        address=((RemoteAddr,int(RemotePort)))
        print('Connect to %s:%d' % (address))
        message=[RemoteAddr,int(RemotePort)]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(slaver(message,loop))
        loop.close()
if __name__ == "__main__":
     main()