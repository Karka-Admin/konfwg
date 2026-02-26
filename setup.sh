apt update -yq
apt upgrade -yq

apt install pipx python3 -y
pipx install ansible ansible-lint

ansible-playbook -i ansible/inventories/hosts.yml ansible/playbooks/site.yml -K