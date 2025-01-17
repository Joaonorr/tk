#!/bin/bash

function add_folder_to_path() {
    local rc_file=$1
    local folder_path=$2

    if grep -q "PATH=\$PATH:$folder_path" "$rc_file"; then
        echo "Folder $folder_path already exists in $rc_file"
    else
        echo "Adding $folder_path to $rc_file"
        printf "\nexport PATH=\$PATH:$folder_path" >> "$rc_file"
    fi
}

if [[ -f ~/.bashrc ]]; then
    add_folder_to_path ~/.bashrc ~/.tk
fi

if [[ -f ~/.zshrc ]]; then
    add_folder_to_path ~/.zshrc ~/.tk
fi


# Set the URL and destination file path
url="https://raw.githubusercontent.com/senapk/tk/master/tk.py"
update_url="https://raw.githubusercontent.com/senapk/tk/master/scripts/linux_install.sh"
update_path="$HOME/.tk/updatetk.sh"
dest_path="$HOME/.tk/tk"

# Create the destination directory if it doesn't exist
mkdir -p "$HOME/.tk"

# Download the file and save it to the destination path
curl -o "$dest_path" "$url"
curl -o "$update_path" "$update_url"

# Make the file executable
chmod +x "$dest_path"
chmod +x "$update_path"

echo "Se é a primeira vez que você está instalando o tk"
echo "você precisa reiniciar o terminal para começar a usar."
echo "Para atualizar o tk, basta executar o comando:"
echo "updatetk.sh"



