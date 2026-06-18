import json
import random
import numpy as np

from typing import List
from collections import Counter
from sklearn.metrics.pairwise import cosine_similarity

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal

from backend.database.models.questoes import Questao
from backend.database.models.respostas_questoes import RespostaQuestao
from backend.database.models.testes_aptidao import TesteAptidao
from backend.database.models.teste_questao import TesteQuestao
from backend.database.models.questao_reportada import QuestaoReportada
from backend.database.models.questao_salva import QuestaoSalva

"""
TESTES
"""
def gerar_teste_aptidao(db: Session, aptidao: bool, aluno_id: int, teste: dict):
    if aptidao:
        teste_aptidao = TesteAptidao(
            usuario_id=aluno_id
        )

        db.add(teste_aptidao)

        db.commit()
        db.refresh(teste_aptidao)

        for indice, questao in teste.items():
            teste_questao = TesteQuestao(
                teste_id=teste_aptidao.id,
                questao_id=questao,
                ordem=indice
            )

            db.add(teste_questao)

        db.commit()

        return teste_aptidao

    return None

def calcular_perfil_usuario(respostas):
    embeddings = []

    for resposta in respostas:
        if not resposta.questao:
            continue

        if not resposta.questao.embedding:
            continue

        try:
            embeddings.append(np.array(json.loads(resposta.questao.embedding)))

        except Exception:
            pass

    if not embeddings:
        return None

    return np.mean(embeddings, axis=0)

def rankear_por_similaridade(questoes, perfil_usuario) -> list:
    if perfil_usuario is None:
        random.shuffle(questoes)
        return questoes

    ranking = []

    for questao in questoes:
        if not questao.embedding:
            continue

        try:
            embedding = np.array(json.loads(questao.embedding))
            score = cosine_similarity([perfil_usuario],[embedding])[0][0]
            ranking.append((score, questao))

        except Exception:
            pass

    ranking.sort(key=lambda x: x[0], reverse=True)

    return [q for _, q in ranking]

def gerar_teste(aluno_id: int, quantidade: int = 20, aptidao: bool = True) -> dict:
    db: Session = SessionLocal()

    try:
        respostas = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == aluno_id).all()

        if not respostas:
            questoes = db.query(Questao).filter(Questao.ativa == True).order_by(Questao.dificuldade.asc()).limit(quantidade).all()

            teste = {}

            for ordem, questao in enumerate(questoes, start=1):
                teste[ordem] = questao.id

            teste_aptidao = gerar_teste_aptidao(db, aptidao, aluno_id, teste)

            return {
                "success": True,
                "teste_id": (
                    teste_aptidao.id
                    if teste_aptidao
                    else None
                ),
                "quantidade": len(questoes),
                "questoes": teste
            }

        perfil_usuario = calcular_perfil_usuario(respostas)

        erros_assunto = Counter()
        acertos_assunto = Counter()

        questoes_respondidas = set()

        for resposta in respostas:
            questoes_respondidas.add(resposta.questao_id)

            if not resposta.questao:
                continue

            assunto = resposta.questao.assunto

            if resposta.acertou:
                acertos_assunto[assunto] += 1
            else:
                erros_assunto[assunto] += 1

        assuntos_fracos = [assunto for assunto, _ in erros_assunto.most_common(3)]
        assuntos_fortes = [assunto for assunto, _ in acertos_assunto.most_common(3)]

        qtd_fracas = int(quantidade * 0.4)
        qtd_fortes = int(quantidade * 0.3)
        qtd_novas = quantidade - qtd_fracas - qtd_fortes

        selecionadas = []

        if assuntos_fracos:
            questoes_fracas = db.query(Questao).filter(Questao.assunto.in_(assuntos_fracos), Questao.ativa == True).all()
            questoes_fracas = rankear_por_similaridade(questoes_fracas, perfil_usuario)

            selecionadas.extend(questoes_fracas[:qtd_fracas])

        if assuntos_fortes:
            questoes_fortes = db.query(Questao).filter(Questao.assunto.in_(assuntos_fortes), Questao.ativa == True).all()
            random.shuffle(questoes_fortes)

            selecionadas.extend(questoes_fortes[:qtd_fortes])

        questoes_novas = db.query(Questao).filter(Questao.ativa == True, ~Questao.id.in_(questoes_respondidas)).all()
        random.shuffle(questoes_novas)

        selecionadas.extend(questoes_novas[:qtd_novas])

        unicas = {}

        for questao in selecionadas:
            unicas[questao.id] = questao

        selecionadas = list(unicas.values())

        if len(selecionadas) < quantidade:
            ids_selecionados = [q.id for q in selecionadas]

            faltam = quantidade - len(selecionadas)

            questoes_extras = db.query(Questao).filter(Questao.ativa == True, ~Questao.id.in_(ids_selecionados)).all()

            random.shuffle(questoes_extras)

            selecionadas.extend(questoes_extras[:faltam])

        random.shuffle(selecionadas)

        selecionadas = list(unicas.values())

        random.shuffle(selecionadas)

        teste = {}

        for indice, questao in enumerate(selecionadas, start=1):
            teste[indice] = questao.id

        teste_aptidao = gerar_teste_aptidao(db, aptidao, aluno_id, teste)

        return {
            "success": True,
            "teste_id": teste_aptidao.id if teste_aptidao else None,
            "quantidade": len(
                selecionadas
            ),
            "questoes": teste
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()

"""
QUESTOES
"""
def to_dict(questao: Questao) -> dict:
    return {
            "id": questao.id,
            "titulo": questao.titulo,
            "contexto": questao.contexto,
            "imagem_url": questao.imagem_url,
            "materia": questao.materia,
            "assunto": questao.assunto,
            "habilidade_enem": questao.habilidade_enem,
            "dificuldade": questao.dificuldade,
            "origem": questao.origem,
            "alternativas": [
                {
                    "letra": "A",
                    "texto": questao.alternativa_a,
                    "imagem": questao.alternativa_a_imagem
                },
                {
                    "letra": "B",
                    "texto": questao.alternativa_b,
                    "imagem": questao.alternativa_b_imagem
                },
                {
                    "letra": "C",
                    "texto": questao.alternativa_c,
                    "imagem": questao.alternativa_c_imagem
                },
                {
                    "letra": "D",
                    "texto": questao.alternativa_d,
                    "imagem": questao.alternativa_d_imagem
                },
                {
                    "letra": "E",
                    "texto": questao.alternativa_e,
                    "imagem": questao.alternativa_e_imagem
                }
            ]
        }

def get_questao_by_id(questao_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        questao: Questao | None = db.query(Questao).filter(Questao.id == questao_id).first()

        if not questao:
            return {
                "success": False,
                "message": "Não foi encontrada questão com esse id"
            }

        return {
            "success": True,
            "questao": to_dict(questao)
        }

    finally:
        db.close()

def get_questao_by_infos(user_id: int, materia: str, dificuldade: str, modelo: str) -> dict:
    db: Session = SessionLocal()

    try:
        questoes_realizadas = [r[0] for r in db.query(RespostaQuestao.questao_id).filter(RespostaQuestao.usuario_id == user_id).all()]
        questoes_reportadas = [r[0] for r in db.query(QuestaoReportada.questao_id).filter(QuestaoReportada.usuario_id == user_id).all()]

        filtros = [~Questao.id.in_(questoes_realizadas), ~Questao.id.in_(questoes_reportadas)]

        if materia != "Sem Filtro":
            filtros.append(Questao.assunto == materia)

        if modelo != "Sem Filtro":
            filtros.append(Questao.origem == modelo)

        if dificuldade != "Sem Filtro":
            if dificuldade == "Fácil":
                min_diff = 0
                max_diff = 1.5
            elif dificuldade == "Média":
                min_diff = 1.5
                max_diff = 2.5
            else:
                min_diff = 2.5
                max_diff = 10

            filtros.append(Questao.dificuldade >= min_diff)
            filtros.append(Questao.dificuldade < max_diff)

        questao = db.query(Questao).filter(*filtros).order_by(func.random()).first()

        if not questao:
            return {
                "success": False,
                "message": "Não foi encontrada nenhuma questão com esses filtros!"
            }

        return {
            "success": True,
            "questao": to_dict(questao)
        }

    finally:
        db.close()

def get_lista_questoes(questoes_ids: List[int]) -> dict:
    db: Session = SessionLocal()

    try:
        questoes = db.query(Questao).filter(Questao.id.in_(questoes_ids)).all()

        return {
            "success": True,
            "quantidade": len(questoes),
            "questoes": {questao.id: to_dict(questao) for questao in questoes}
        }

    finally:
        db.close()

def get_materias(modelo: str) -> List[str]:
    db: Session = SessionLocal()

    try:
        return [m[0] for m in db.query(Questao.assunto).distinct().all()] if modelo == "Sem Filtro" else [m[0] for m in db.query(Questao.assunto).filter(Questao.origem == modelo).distinct().all()]

    finally:
        db.close()    

def get_modelos() -> List[str]:
    db: Session = SessionLocal()

    try:
        return [m[0] for m in db.query(Questao.origem).distinct().all()]

    finally:
        db.close()

def responder_questao(user_id: int, questao_id: int, alternativa: str) -> dict:
    db: Session = SessionLocal()

    if not alternativa:
        return {
            "success": False,
            "message": "Selecione uma alternativa"
        }

    try:
        questao: Questao = db.query(Questao).filter(Questao.id == questao_id).first()

        if not questao:
            return {
                "success": False,
                "message": "Não foi possível encontrar essa questão"
            }
        
        acertou = alternativa == questao.resposta_correta

        resposta = RespostaQuestao(
            usuario_id=user_id,
            questao_id=questao.id,
            resposta_usuario=alternativa,
            acertou=acertou
        )

        db.add(resposta)
        db.commit()

        return {
            "success": True,
            "acertou": acertou,
            "message": "Resposta correta!" if acertou else "Resposta incorreta!"
        }

    finally:
        db.close()

def reportar_questao(user_id: int, questao_id: int, tipo: str, descricao: str) -> dict:
    db: Session = SessionLocal()

    try:
        if not questao_id:
            return {
                "success": False,
                "message": "Não foi encontrado o ID da questão!"
            }
        
        if not tipo:
            return {
                "success": False,
                "message": "Não foi encontrado o tipo da questão!"
            }
        
        if not descricao:
            return {
                "success": False,
                "message": "Não foi encontrada a descrição da questão!"
            }
        
        reporte = QuestaoReportada(
            questao_id=questao_id,
            usuario_id=user_id,
            tipo=tipo,
            descricao=descricao
        )

        db.add(reporte)
        db.commit()

        return {
            "success": True,
            "message": "Questão reporta com sucesso!"
        }

    finally:
        db.close()

def questoes_reportadas(user_id: int | None) -> dict:
    db: Session = SessionLocal()

    try:
        if user_id:
            return {questao.questao_id: questao for questao in db.query(QuestaoReportada).filter(QuestaoReportada.usuario_id == user_id).all()}
        else:
            return {questao.questao_id: questao for questao in db.query(QuestaoReportada).all()}

    finally:
        db.close()

def remover_reporte(user_id: int, questao_id: int) -> dict:
    db: Session = SessionLocal()

    try:
        if not questao_id:
            return {
                "success": False,
                "message": "Não foi encontrado o id da questão!"
            }
        
        reporte = db.query(QuestaoReportada).filter(QuestaoReportada.usuario_id==user_id, QuestaoReportada.questao_id==questao_id).first()

        if not reporte:
            return {
                "success": False,
                "message": "A questão reportada não foi encontrada!"
            }
        
        db.delete(reporte)
        db.commit()

        return {
            "success": True,
            "message": "O reporte da questão foi deletado!"
        }

    finally:
        db.close()

def get_resposta_questao(questao_id: int) -> str:
    db: Session = SessionLocal()

    try:
        questao = db.query(Questao.resposta_correta).filter(Questao.id == questao_id).first()

        if not questao:
            return None
        
        return questao[0]

    finally:
        db.close()

def responder_questao_teste(user_id: int, questao_id: int, teste_id: int, alternativa: str) -> dict:
    db: Session = SessionLocal()

    try:
        if not alternativa:
            return {
                "success": False,
                "message": "Selecione uma alternativa"
            }

        questao = db.query(Questao).filter(Questao.id == questao_id).first()

        if not questao:
            return {
                "success": False,
                "message": "Questão não encontrada"
            }

        acertou = alternativa == questao.resposta_correta

        resposta = RespostaQuestao(
            usuario_id=user_id,
            questao_id=questao.id,
            teste_aptidao_id=teste_id,
            resposta_usuario=alternativa,
            acertou=acertou
        )

        db.add(resposta)
        db.commit()

        return {
            "success": True,
            "acertou": acertou,
            "message": (
                "Resposta correta!"
                if acertou
                else "Resposta incorreta."
            )
        }

    finally:
        db.close()
        
def favoritar_questao(user_id: int, questao_id: int) -> dict:
    db = SessionLocal()

    try:
        existe = db.query(QuestaoSalva).filter(QuestaoSalva.usuario_id == user_id, QuestaoSalva.questao_id == questao_id).first()

        if existe:
            return {
                "success": False,
                "message":
                "Questão já foi salva."
            }

        salva = QuestaoSalva(
            usuario_id=user_id,
            questao_id=questao_id
        )

        db.add(salva)
        db.commit()

        return {
            "success": True,
            "message": "Questão salva com sucesso."
        }

    finally:
        db.close()

def questoes_favoritadas(user_id: int) -> dict:
    db = SessionLocal()

    try:
        salvas = (
            db.query(QuestaoSalva)
            .filter(QuestaoSalva.usuario_id == user_id)
            .all()
        )

        questoes = []

        for salva in salvas:
            questao = salva.questao

            questoes.append({
                "id": questao.id,
                "titulo": questao.titulo,
                "contexto": questao.contexto,
                "assunto": questao.assunto,
                "dificuldade": questao.dificuldade,
                "origem": questao.origem
            })

        return {
            "success": True,
            "questoes": questoes
        }

    finally:
        db.close()

def get_questao_favoritada(user_id: int, questao_id: int) -> dict:
    db = SessionLocal()

    try:
        salva = db.query(QuestaoSalva).filter(QuestaoSalva.usuario_id == user_id, QuestaoSalva.questao_id == questao_id).first()

        if not salva:
            return {
                "success": False,
                "message": "Questão não está salva."
            }

        return {
            "success": True,
            "questao": to_dict(salva.questao)
        }

    finally:
        db.close()
        
def remover_questao_favoritada(user_id: int, questao_id: int) -> dict:
    db = SessionLocal()

    try:
        if not questao_id:
            return {
                "success": False,
                "message": "Questão não encontrada."
            }

        salva = db.query(QuestaoSalva).filter(QuestaoSalva.usuario_id == user_id, QuestaoSalva.questao_id == questao_id).first()

        if not salva:
            return {
                "success": False,
                "message": "Questão não está salva."
            }

        db.delete(salva)
        db.commit()

        return {
            "success": True,
            "message": "Questão removida com sucesso."
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()
        
if __name__ == '__main__':
    pass