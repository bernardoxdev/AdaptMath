from huggingface_hub import login

from backend.core.config import HF_TOKEN

from backend.database.init_db import init_db
from backend.enem.import_questao import classificar_questao
from backend.database.connection import SessionLocal
from backend.database.models.questoes import Questao

def questoes_ja_importadas():
    db = SessionLocal()

    try:
        return db.query(Questao).count() > 0

    finally:
        db.close()

def setup_database():
    try:
        if HF_TOKEN:
            print("================================")
            print("TOKEN ENCONTRADO, FAZENDO LOGIN")
            print("================================")

            login(token=HF_TOKEN)

        print("================================")
        print("CRIANDO TABELAS")
        print("================================")

        init_db()

        print("================================")
        print("IMPORTANDO QUESTÕES")
        print("================================")

        if not questoes_ja_importadas():
            classificar_questao()

        print("================================")
        print("SETUP FINALIZADO")
        print("================================")

    except Exception as e:
        print("================================")
        print("ERRO NO SETUP")
        print(e)
        print("================================")

        raise

if __name__ == "__main__":
    setup_database()