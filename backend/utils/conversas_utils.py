from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models.conversas import Conversas
from backend.database.models.mensagens import Mensagens

def criar_nova_conversa(user_id: int, mensagem: str) -> dict:
    db: Session = SessionLocal()
    
    try:
        conversa = Conversas(
            usuario_id=user_id,
            titulo=mensagem
        )
        
        db.add(conversa)
        db.commit()
        db.refresh(conversa)
        
        return {
            "success": True,
            "conversa_id": conversa.id
        }
    
    finally:
        db.close()
        
def get_conversas(user_id: int) -> dict:
    db: Session = SessionLocal()
    
    try:
        conversas = db.query(Conversas).filter(Conversas.usuario_id==user_id).all()
        
        if not conversas:
            return {
                "success": False,
                "message": "Não foram encontradas conversas"
            }
            
        return {
            "success": True,
            "conversas": [{"id": c.id, "titulo": c.titulo, "data": c.data} for c in conversas]
        }
    
    finally:
        db.close()

def get_conversa(conversa_id: int) -> dict:
    db: Session = SessionLocal()
    
    try:
        mensagens = db.query(Mensagens).filter(Mensagens.conversa_id==conversa_id).order_by(Mensagens.id.asc()).all()
        
        return {
            "success": True,
            "mensagens": [{"id": m.id, "tipo": m.tipo, "texto": m.texto} for m in mensagens]
        }
    
    finally:
        db.close()

if __name__ == '__main__':
    pass