from app.db.base import Base
import app.db.models.transacao
from app.core.database import sync_engine

def main():
    Base.metadata.create_all(bind=sync_engine)
    print('Tabelas Criadas')

if __name__ == '__main__':
    main()