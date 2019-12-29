import ftplib

# 登录FTP服务，使用主动模式
ftp = ftplib.FTP()
ftp.connect("127.0.0.1", 21)
ftp.login("root", "root")
ftp.set_pasv(False)

# 将本地文件上传至服务器
with open("client" , 'rb') as f:
    ftp.storbinary("STOR upload_from_client", f, 1024)

# 下载服务器文件
with open("download_from_server", "wb") as f:
    ftp.retrbinary("RETR server", f.write)