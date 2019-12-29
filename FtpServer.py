#coding=utf-8

# FtpServer.py
# 一个玩具版的Ftp服务
# by 魔笛手CTO

import socket
import os
import six


END_FLAG = "\r\n"
ASCII_MODE = "II"
BINARY_MODE = "I"


def dump(string):
    """将字符串消息dump为网络序的字节"""
    if six.PY2:
        return string
    return bytes(string, "utf-8")


def load(byte):
    """将字节消息load为字符串"""
    if six.PY2:
        return byte
    return str(byte, "utf-8")


class FtpServer():
    def __init__(self):
        self.cmd_socket = None
        self.ftp_users = {"root": "root"}  # 允许登录的ftp账号密码

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """确保服务关闭"""
        try:
            self.cmd_socket.close()
            print("socket is closed")
        except:
            pass

    def run(self):
        """启动服务，开启21端口监听"""
        print("starting server on port 21...")
        self.cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
        self.cmd_socket.bind(("0.0.0.0", 21))
        self.cmd_socket.listen(1)
        while True:
            conn, addr = self.cmd_socket.accept()
            self._handle(conn, addr)

    def _close_conn(self, conn):
        """关闭指定连接"""
        conn.close()

    def _handle(self, conn, addr):
        """一旦同客户端建立连接，将有handle负责处理交互"""
        user = None
        password = None
        authed = False
        client_data_addr = None

        self._say_hello(conn)
        while True:
            req = self._read_req(conn)
            # 返回空字符串时，关闭连接，准备响应下一个连接
            if req == "":
                return self._close_conn(conn)
            # 解析并响应客户端命令
            cmd, arg = self._parse(req)
            if cmd == "USER":
                if not authed:
                    user = arg
                    resp = "331 Please specify the password"
                else:
                    resp = "500 User has authed!"
            elif cmd == "PASS":
                if user and not authed:
                    password = arg
                    if self._auth(user, password):
                        authed = True
                        resp = "230 Login successful"
                    else:
                        resp = "500 Auth error"
                else:
                    resp = "500 User is not specified or has login"
            # binary模式和ascii模式, 当前仅支持binary模式
            elif cmd == "TYPE":
                if arg == ASCII_MODE:
                    resp = "500 Only support binary mode"
                elif arg == BINARY_MODE:
                    resp = "200 Switching to binary mode"
            # 主动模式下客户端的端口号
            elif cmd == "PORT":
                if not authed:
                    resp = "530 Not login"
                else:
                    client_data_addr = self._parse_addr(arg)
                    resp = "200 PORT command successful"
            # 上传文件
            elif cmd == "STOR":
                if not authed:
                    resp = "530 Not login"
                else:
                    resp = "150 Ok to send data"
                    self._send_resp(conn, resp)
                    self._save_file(arg, client_data_addr)
                    resp = "226 Transfer complete"
            # 下载文件
            elif cmd == "RETR":
                if not authed:
                    resp = "530 Not login"
                else:
                    if not os.path.exists(arg):
                        resp = "550 File not exist"
                    else:
                        resp = "150 Ok to send data"
                        self._send_resp(conn, resp)
                        self._send_file(arg, client_data_addr)
                        resp = "226 Transfer complete"
            else:
                print("500 Unknown command")

            # 发送响应
            self._send_resp(conn, resp)

    def _create_data_conn(self, host, port):
        """主动模式下建立数据通道"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", 20))
        sock.connect((host, port))
        return sock

    def _send_file(self, filename, client_data_add):
        """传输指定文件至客户端"""
        conn = self._create_data_conn(*client_data_add)
        with open(filename, "rb") as f:
            conn.sendall(f.read())
        conn.close()

    def _save_file(self, filename, client_data_addr):
        """保存客户端上传的文件"""
        conn = self._create_data_conn(*client_data_addr)

        with open(filename, "wb") as f:
            while True:
                body = conn.recv(1)
                if body == b'':
                    break
                f.write(body)

        conn.close()


    def _read_req(self, conn):
        """读取请求消息"""
        print("reading msg...")
        msg = ""
        while True:
            body = load(conn.recv(1))
            # 当客户端关闭连接时，body为空字符串
            if body == "":
                return body
            msg += body
            if msg.endswith(END_FLAG):
                break
        return msg

    def _send_resp(self, conn, msg):
        """发送命令响应"""
        print("ready to response:%s" % msg)
        if not msg.endswith(END_FLAG):
            msg += END_FLAG
        conn.sendall(dump(msg))

    def _auth(self, user, password):
        """登录用户认证"""
        if user and self.ftp_users.get(user) and self.ftp_users.get(user) == password:
            return True
        return False

    def _say_hello(self, conn):
        """发送欢迎语"""
        self._send_resp(conn, "220 Hello!")

    def _parse(self, msg):
        """解析客户端消息, 返回命令和参数"""
        print("receive msg:%s" % msg)
        msg = msg.strip()
        args = msg.split(" ")
        if len(args) == 2:
            cmd, arg = args
            return cmd, arg
        return None, None

    def _parse_addr(self, addr):
        """解析ip和端口号"""
        args = addr.strip().split(",")
        host = ".".join(args[:4])
        port = int(args[4]) * 256 + int(args[5])
        return host, port


if __name__ == "__main__":
    with FtpServer() as server:
        server.run()

