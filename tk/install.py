import os
import shutil

def copy_file():
    file_path = os.path.join(os.getcwd(), 'tk.py')
    if not os.path.isfile(file_path):
        print("Error: tk.py file not found!")
        return
    dest_path = os.path.join(os.path.expanduser('~'), 'bin', 'tk')
    shutil.copy2(file_path, dest_path)
    os.chmod(dest_path, 0o755)

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

def kt_install():
    copy_file()
    export_path()
    print("DONE")
