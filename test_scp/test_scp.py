import pexpect

def scp(path):
    username='aegis' 
    aim_ip='192.168.20.119' 
    password='123456'
    source_file_path= path
    aim_file_path='/home/aegis'
    port=2222
    password_key = '.*assword.*'
    command = f'scp -P {port} {source_file_path}  {username}@{aim_ip}:{aim_file_path}'

    print("执行指令: ", command)
    try:
        execute = pexpect.spawn(command)
        execute.expect(password_key)
        execute.sendline(password)
        execute.expect(pexpect.EOF)
        print("拷贝成功")
    except:
        print("拷贝失败")
