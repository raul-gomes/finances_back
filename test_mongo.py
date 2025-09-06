from datetime import datetime, timedelta
from pymongo import MongoClient

client = MongoClient('mongodb://admin:password@localhost:27017/finances-db?authSource=admin&replicaSet=rs0')
db = client['finances-db']
collection = db.categorias

# calcula data-limite: 30 dias atrás
cutoff = datetime.utcnow() - timedelta(days=30)

# remove documentos com updated_at anterior ao cutoff
result = collection.delete_many({ })
print(f"Documentos removidos: {result.deleted_count}")
