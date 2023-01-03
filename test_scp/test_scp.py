import pexpect

def scp(source_file_path):
    username='hyx' 
    aim_ip='192.168.0.100' 
    password=' '       #?
    aim_file_path='~/Desktop/codeshere/PyCamera/resources/'
    port=8888
    password_key = '.*assword.*'
    command = f'scp -r -P {port} {source_file_path}  {username}@{aim_ip}:{aim_file_path}'

    print("执行指令: ", command)
    try:
        execute = pexpect.spawn(command)
        execute.expect(password_key)
        execute.sendline(password)
        execute.expect(pexpect.EOF)
        print("拷贝成功")
        return True
    except:
        print("拷贝失败")
        return False
