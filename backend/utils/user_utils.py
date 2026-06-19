from typing import List
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from passlib.context import CryptContext
from brutils import is_valid_email

from backend.core.jwt import create_access_token, create_refresh_token
from backend.core.config import REFRESH_TOKEN_EXPIRE_DAYS

from backend.database.connection import SessionLocal
from backend.database.models.user import User
from backend.database.models.testes_aptidao import TesteAptidao
from backend.database.models.respostas_questoes import RespostaQuestao
from backend.database.models.refresh_token import RefreshToken
from backend.database.models.questoes import Questao

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def registrar_usuario(nome: str, email: str, senha: str):
    db: Session = SessionLocal()

    try:
        if not is_valid_email(email):
            return {
                "success": False,
                "message": "Email inválido"
            }

        user_exists = db.query(User).filter(
            User.email == email
        ).first()

        if user_exists:
            return {
                "success": False,
                "message": "Usuário já cadastrado"
            }

        senha_hash = pwd_context.hash(senha)

        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha_hash
        )

        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

        access_token = create_access_token({
            "sub": str(novo_usuario.id),
            "email": novo_usuario.email
        })

        refresh_token = create_refresh_token({
            "sub": str(novo_usuario.id)
        })
        
        refresh_db = RefreshToken(
            token=refresh_token,
            user_id=novo_usuario.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        db.add(refresh_db)
        db.commit()

        return {
            "success": True,
            "message": "Usuário registrado com sucesso",
            "user": {
                "id": novo_usuario.id,
                "nome": novo_usuario.nome,
                "email": novo_usuario.email
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        }

    except IntegrityError:
        db.rollback()

        return {
            "success": False,
            "message": "Erro ao registrar usuário"
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()

def realizar_login(email: str, senha: str):
    db: Session = SessionLocal()

    try:
        usuario = db.query(User).filter(
            User.email == email
        ).first()

        if not usuario:
            return {
                "success": False,
                "message": "Email ou senha inválidos"
            }

        senha_correta = pwd_context.verify(
            senha,
            usuario.senha
        )

        if not senha_correta:
            return {
                "success": False,
                "message": "Email ou senha inválidos"
            }

        access_token = create_access_token({
            "sub": str(usuario.id),
            "email": usuario.email
        })

        refresh_token = create_refresh_token({
            "sub": str(usuario.id)
        })
        
        db.query(RefreshToken).filter(
            RefreshToken.user_id == usuario.id,
            RefreshToken.revogado == False
        ).update({
            RefreshToken.revogado: True
        })

        db.commit()
        
        refresh_db = RefreshToken(
            token=refresh_token,
            user_id=usuario.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        db.add(refresh_db)
        db.commit()

        return {
            "success": True,
            "message": "Login realizado com sucesso",
            "user": {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email
            },
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()

def export_data(user_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        dados_user: User | None = db.query(User).filter(User.id == user_id).first()

        if not dados_user:
            return {
                "success": False,
                "message": "Usuário não encontrado"
            }

        dados_testes: List[type[TesteAptidao]] = db.query(TesteAptidao).filter(TesteAptidao.usuario_id == user_id).all()

        resolvidas = (db.query(func.count()).select_from(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id).scalar() or 0)
        acertos = (db.query(func.count()).select_from(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id, RespostaQuestao.acertou == True).scalar() or 0)
        erros = (db.query(func.count()).select_from(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id, RespostaQuestao.acertou == False).scalar() or 0)
        taxa_acerto = 0

        if resolvidas > 0:
            taxa_acerto = round((acertos / resolvidas) * 100, 2)

        media_testes = 0

        if dados_testes:
            soma = sum(teste.pontuacao for teste in dados_testes)
            media_testes = round(soma / len(dados_testes), 2)

        return {
            "resolvidas": resolvidas,
            "quantidade_acertos": acertos,
            "quantidade_erros": erros,
            "taxa_acerto": taxa_acerto,
            "media_testes": media_testes
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()

def get_nivel(user_id: int) -> str:
    db: Session = SessionLocal()

    try:
        dados_user: User | None = db.query(User).filter(User.id == user_id).first()

        if not dados_user:
            return "Não Encontrado"
        
        nivel_medio = dados_user.nivel_medio

        if nivel_medio < 0.3:
            return "Básico"
        elif nivel_medio < 0.7:
            return "Intermediário"
        else:
            return "Avançado"
        
    finally:
        db.close()
        
def get_estatistica_questoes(user_id: int) -> dict:
    db: Session = SessionLocal()
    
    try:
        stmt = select(Questao.assunto, func.count(RespostaQuestao.id).label("total"), func.sum(case((RespostaQuestao.acertou == True, 1), else_=0)).label("acertos")).join(RespostaQuestao, RespostaQuestao.questao_id == Questao.id).where(RespostaQuestao.usuario_id == user_id).group_by(Questao.materia)
        resultado = db.execute(stmt)
        
        if not resultado:
            return {
                "success": False,
                "message": "Não foram encontradas respostas em matérias!"
            }

        dados = []

        for materia, total, acertos in resultado:
            percentual = round((acertos / total) * 100, 2)

            dados.append({
                "nome": materia,
                "total": total,
                "acertos": acertos,
                "percentual": percentual
            })
            
        return {
            "success": True,
            "materias": dados
        }
            
    finally:
        db.close()

def get_relatorio_evolucao(user_id: int) -> dict:
    db = SessionLocal()

    try:
        respostas = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id).order_by(RespostaQuestao.data_resposta).all()

        meses = defaultdict(lambda: {
            "total": 0,
            "acertos": 0
        })

        for resposta in respostas:
            chave = resposta.data_resposta.strftime("%Y-%m")

            meses[chave]["total"] += 1

            if resposta.acertou:
                meses[chave]["acertos"] += 1

        nomes_meses = {
            1: "Jan",
            2: "Fev",
            3: "Mar",
            4: "Abr",
            5: "Mai",
            6: "Jun",
            7: "Jul",
            8: "Ago",
            9: "Set",
            10: "Out",
            11: "Nov",
            12: "Dez"
        }

        resultado = []

        for chave, dados in sorted(meses.items()):
            ano, mes = chave.split("-")

            percentual = 0

            if dados["total"] > 0:
                percentual = round((dados["acertos"] / dados["total"]) * 100, 2)

            resultado.append({
                "nome": nomes_meses[int(mes)],
                "valor": percentual
            })

        return {
            "success": True,
            "meses": resultado
        }

    finally:
        db.close()

def get_dashboard_atividades(user_id: int) -> dict:
    db = SessionLocal()

    try:
        atividades = []

        ultimo_teste = db.query(TesteAptidao).filter(TesteAptidao.usuario_id == user_id, TesteAptidao.finalizado == True).order_by(TesteAptidao.finalizado_em.desc()).first()

        if ultimo_teste:
            atividades.append({
                "titulo": "Teste de Aptidão",
                "descricao": (
                    f"Finalizado em "
                    f"{ultimo_teste.finalizado_em.strftime('%d/%m/%Y %H:%M')}"
                ),
                "status": f"{ultimo_teste.pontuacao}%"
            })

        respostas = (
            db.query(RespostaQuestao)
            .filter(
                RespostaQuestao.usuario_id == user_id
            )
            .order_by(
                RespostaQuestao.data_resposta.desc()
            )
            .limit(5)
            .all()
        )

        for resposta in respostas:
            atividades.append({
                "titulo": resposta.questao.materia,
                "descricao": resposta.questao.assunto,
                "status": "Correta" if resposta.acertou else "Incorreta"
            })

        return {
            "success": True,
            "atividades": atividades
        }

    finally:
        db.close()
        
def get_relatorio_resumo(user_id: int) -> dict:
    db = SessionLocal()

    try:
        total_questoes = (
            db.query(RespostaQuestao)
            .filter(
                RespostaQuestao.usuario_id == user_id
            )
            .count()
        )

        total_acertos = (
            db.query(RespostaQuestao)
            .filter(
                RespostaQuestao.usuario_id == user_id,
                RespostaQuestao.acertou == True
            )
            .count()
        )

        media_geral = 0

        if total_questoes > 0:
            media_geral = round(
                (total_acertos / total_questoes) * 100,
                2
            )

        materias = get_estatistica_questoes(user_id)

        melhor = {
            "nome": "-",
            "percentual": 0
        }

        pior = {
            "nome": "-",
            "percentual": 0
        }

        if materias.get("success") and materias.get("materias"):
            lista = materias["materias"]

            melhor_materia = max(
                lista,
                key=lambda m: m["percentual"]
            )

            pior_materia = min(
                lista,
                key=lambda m: m["percentual"]
            )

            melhor = {
                "nome": melhor_materia["nome"],
                "percentual": melhor_materia["percentual"]
            }

            pior = {
                "nome": pior_materia["nome"],
                "percentual": pior_materia["percentual"]
            }

        return {
            "success": True,
            "media_geral": media_geral,
            "questoes": total_questoes,
            "melhor": melhor,
            "pior": pior
        }

    finally:
        db.close()
 
if __name__ == '__main__':
    pass