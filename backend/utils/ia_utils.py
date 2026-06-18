from sqlalchemy import func
from sqlalchemy.types import Integer
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models.questoes import Questao
from backend.database.models.questao_salva import QuestaoSalva
from backend.database.models.respostas_questoes import RespostaQuestao
from backend.database.models.testes_aptidao import TesteAptidao
from backend.database.models.conversas import Conversas
from backend.database.models.mensagens import Mensagens

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = None
model = None

def get_model():
    global tokenizer, model

    if model is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL)

        model = AutoModelForCausalLM.from_pretrained(
            MODEL,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    return tokenizer, model

def gerar_dica(questao_id: int) -> dict:
    db: Session = SessionLocal()
    tokenizer, model = get_model()

    try:
        questao = db.query(Questao).filter(Questao.id == questao_id).first()

        if not questao:
            return {
                "success": False,
                "message": "Questão não encontrada."
            }

        prompt = f"""
        Você é um professor especialista em matemática e em questões do ENEM.

        Sua função é fornecer UMA DICA para ajudar o aluno a resolver a questão.

        IMPORTANTE:
        - NÃO revele a resposta correta.
        - NÃO diga qual alternativa está correta.
        - NÃO resolva completamente a questão.
        - Apenas oriente o raciocínio do estudante.
        - Responda em português.
        - Utilize no máximo 80 palavras.

        Matéria:
        {questao.materia}

        Assunto:
        {questao.assunto}

        Título:
        {questao.titulo}

        Contexto:
        {questao.contexto or "Sem contexto"}

        Enunciado:
        {questao.texto_completo}

        Alternativa A:
        {questao.alternativa_a}

        Alternativa B:
        {questao.alternativa_b}

        Alternativa C:
        {questao.alternativa_c}

        Alternativa D:
        {questao.alternativa_d}

        Alternativa E:
        {questao.alternativa_e}
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um professor de matemática que ajuda o aluno "
                    "sem revelar respostas."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        outputs = model.generate(**inputs, max_new_tokens=120, temperature=0.5, do_sample=True, top_p=0.9, repetition_penalty=1.1)

        resposta = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

        return {
            "success": True,
            "dica": resposta
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()

def get_relatorio_insights(user_id: int) -> dict:
    db: Session = SessionLocal()
    tokenizer, model = get_model()

    try:
        respostas = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id).count()

        if respostas == 0:
            return {
                "success": True,
                "insights": [
                    {
                        "titulo": "👋 Bem-vindo",
                        "texto": "Resolva algumas questões para receber recomendações personalizadas."
                    }
                ]
            }

        materias = db.query(Questao.materia,func.count(RespostaQuestao.id).label("total"),func.sum(RespostaQuestao.acertou.cast(Integer)).label("acertos")).join(RespostaQuestao, Questao.id == RespostaQuestao.questao_id).filter(RespostaQuestao.usuario_id == user_id).group_by(Questao.materia).all()

        desempenho = []

        for materia, total, acertos in materias:
            acertos = acertos or 0

            percentual = round(acertos / total * 100, 1)

            desempenho.append({
                "materia": materia,
                "percentual": percentual,
                "total": total
            })

        desempenho.sort(key=lambda x: x["percentual"], reverse=True)

        melhor = desempenho[0]
        pior = desempenho[-1]

        media_testes = (db.query(func.avg(TesteAptidao.pontuacao)).filter(TesteAptidao.usuario_id == user_id, TesteAptidao.finalizado == True).scalar()) or 0

        salvas = db.query(QuestaoSalva).filter(QuestaoSalva.usuario_id == user_id).count()

        insights = []

        insights.append({
            "titulo": "🏆 Melhor desempenho",
            "texto":
                f"Seu melhor desempenho atualmente é em "
                f"{melhor['materia']} "
                f"({melhor['percentual']}% de acertos)."
        })

        insights.append({
            "titulo": "⚠️ Ponto de atenção",
            "texto":
                f"{pior['materia']} apresenta apenas "
                f"{pior['percentual']}% de acertos. "
                "Vale a pena revisar esse conteúdo."
        })

        if media_testes >= 80:
            insights.append({
                "titulo": "🚀 Excelente evolução",
                "texto":
                    f"Sua média nos testes é de "
                    f"{media_testes:.1f}%. Continue mantendo esse desempenho."
            })

        elif media_testes >= 60:
            insights.append({
                "titulo": "📈 Evolução constante",
                "texto":
                    f"Sua média é de {media_testes:.1f}%. "
                    "Você está evoluindo, mas ainda há espaço para melhorar."
            })

        else:
            insights.append({
                "titulo": "🎯 Recomendação",
                "texto":
                    "Priorize exercícios das matérias com menor desempenho "
                    "antes de realizar novos testes."
            })

        if salvas > 0:
            insights.append({
                "titulo": "⭐ Exercícios salvos",
                "texto":
                    f"Você possui {salvas} exercícios salvos para revisão."
            })

        return {
            "success": True,
            "insights": insights
        }

    finally:
        db.close()

def gerar_texto(prompt: str, system_prompt: str = "Você é um professor de matemática.", max_tokens: int = 500, temperature: float = 0.6) -> str:
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    texto = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    inputs = tokenizer(texto, return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=max_tokens, temperature=temperature, top_p=0.9, do_sample=True, repetition_penalty=1.1)

    resposta = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    return resposta.strip()

def gerar_analise_relatorio(user_id: int) -> dict:
    db: Session = SessionLocal()
    tokenizer, model = get_model()

    try:
        total = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id).count()

        if total == 0:
            return {
                "success": True,
                "textos": [
                    "Você ainda não respondeu questões suficientes para gerar uma análise."
                ]
            }

        acertos = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id, RespostaQuestao.acertou == True).count()

        media = (db.query(func.avg(TesteAptidao.pontuacao)).filter(TesteAptidao.usuario_id == user_id, TesteAptidao.finalizado == True).scalar()) or 0

        materias = db.query(Questao.materia,func.count(RespostaQuestao.id),func.sum(RespostaQuestao.acertou.cast(Integer))).join(RespostaQuestao, Questao.id == RespostaQuestao.questao_id).filter(RespostaQuestao.usuario_id == user_id).group_by(Questao.materia).all()

        prompt = f"""
        Você é um tutor especializado em matemática.

        Analise os dados abaixo.

        Questões respondidas:
        {total}

        Acertos:
        {acertos}

        Taxa:
        {round(acertos/total*100,1)}%

        Média nos testes:
        {round(media,1)}%

        Desempenho por matéria:
        """

        for materia, quantidade, acertos_materia in materias:

            acertos_materia = acertos_materia or 0

            percentual = round(acertos_materia / quantidade * 100, 1)

            prompt += f"""
            {materia}: {percentual}% ({acertos_materia}/{quantidade})
            """

        prompt += """

        Escreva exatamente 3 análises.

        Cada análise deve ter no máximo 2 frases.

        Não utilize markdown.

        Não faça listas numeradas.
        """

        resposta = gerar_texto(prompt)

        textos = [t.strip() for t in resposta.split("\n") if t.strip()]

        return {
            "success": True,
            "textos": textos
        }

    finally:
        db.close()

def responder_chat(usuario_id: int, conversa_id: int, mensagem_usuario: str) -> dict:
    db: Session = SessionLocal()
    tokenizer, model = get_model()

    try:
        conversa = db.query(Conversas).filter(Conversas.id == conversa_id, Conversas.usuario_id == usuario_id).first()

        if conversa is None:
            return {
                "success": False,
                "message": "Conversa não encontrada."
            }

        mensagem = Mensagens(
            conversa_id=conversa.id,
            tipo="user",
            texto=mensagem_usuario
        )

        db.add(mensagem)
        db.commit()

        historico = db.query(Mensagens).filter(Mensagens.conversa_id == conversa.id).order_by(Mensagens.id.asc()).all()

        messages = [
            {
                "role": "system",
                "content": """
                Você é o tutor oficial do AdaptMath.

                Seu objetivo é ensinar matemática.

                Nunca entregue respostas prontas de avaliações.

                Explique passo a passo.

                Sempre responda em português.
                """
            }
        ]

        for item in historico:
            messages.append({
                "role": "assistant" if item.tipo == "assistant" else "user",

                "content": item.texto
            })

        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        outputs = model.generate(**inputs, max_new_tokens=700, temperature=0.6, top_p=0.9, repetition_penalty=1.1, do_sample=True)

        resposta = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

        db.add(Mensagens(
            conversa_id=conversa.id,
            tipo="assistant",
            texto=resposta
            ))

        if conversa.titulo == "Nova Conversa":
            titulo = mensagem_usuario.strip()

            if len(titulo) > 50:
                titulo = titulo[:47] + "..."

            conversa.titulo = titulo

        db.commit()

        return {
            "success": True,
            "resposta": resposta
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