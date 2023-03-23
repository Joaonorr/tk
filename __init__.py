import os
import requests
import platform

def download_files():
    url = "https://raw.githubusercontent.com/senapk/tk/master/tk/tk.py"
    file_path = os.path.join(os.path.expanduser('~'), 'bin', 'tk')
    with open(file_path, 'wb') as f:
        response = requests.get(url)
        f.write(response.content)
    os.chmod(file_path, 0o755)

def export_path():
    file_path = os.path.join(os.path.expanduser('~'), '.bash_profile')
    new_path = os.path.join(os.path.expanduser('~'), 'bin')
    if not os.path.exists(new_path):
        os.makedirs(new_path)
    with open(file_path, 'a') as f:
        path_line = 'export PATH="$HOME/bin:$PATH"\n'
        if path_line not in f.read():
            print("Inserting ~/bin in path!")
            f.write(path_line)
    os.environ["PATH"] += os.pathsep + new_path

def linuxInstall():
    os.makedirs(os.path.join(os.path.expanduser('~'), 'bin'), exist_ok=True)
    download_files()
    export_path()
    print("DONE")

def windowsInstall():
    os.makedirs(os.path.join(os.path.expanduser('~'), 'bin'), exist_ok=True)
    download_files()
    new_path = os.path.join(os.path.expanduser('~'), 'bin')
    os.environ["PATH"] += os.pathsep + new_path
    print("DONE")

if __name__ == '__main__':
    if platform.system() == 'Linux':
        linuxInstall()
    elif platform.system() == 'Windows':
        windowsInstall()
    else:
        print("Este script só pode ser executado em sistemas Linux ou Windows!")
