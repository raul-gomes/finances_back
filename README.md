openssl rand -base64 756 > mongo-keyfile
chmod 400 mongo-keyfile
sudo chown 999:999 mongo-keyfile
docker compose up -d
docker exec -it mongo mongosh -u admin -p password123 --authenticationDatabase admin


# 1. Remover o diretório existente
rm -rf mongo-keyfile

# 2. Criar o keyfile como ARQUIVO
openssl rand -base64 756 > mongo-keyfile

# 3. Definir permissões corretas
chmod 600 mongo-keyfile  # Use 600 em vez de 400

# 4. Definir ownership para UID/GID do MongoDB no container
sudo chown 999:999 mongo-keyfile



uvicorn app.main:app --reload --host 0.0.0.0 --port 8000