import os
import json
import re

from sentence_transformers import SentenceTransformer

from backend.database.connection import SessionLocal
from backend.database.models.questoes import Questao

def get_model() -> SentenceTransformer:
    return SentenceTransformer("intfloat/multilingual-e5-large")

COMPETENCIAS = {
    "C1": [
        "porcentagem",
        "juros",
        "razão",
        "proporção",
        "notação científica",
        "decimal",
        "números"
    ],
    "C2": [
        "área",
        "volume",
        "círculo",
        "triângulo",
        "pirâmide",
        "geometria",
        "trapézio",
        "polígono",
        "distância"
    ],
    "C3": [
        "litros",
        "metros",
        "escala",
        "medida",
        "capacidade",
        "conversão"
    ],
    "C4": [
        "função",
        "crescimento",
        "decrescimento",
        "variação",
        "gráfico"
    ],
    "C5": [
        "equação",
        "algébrica",
        "expressão",
        "incógnita",
        "sistema"
    ],
    "C6": [
        "estatística",
        "gráfico",
        "tabela",
        "dados"
    ],
    "C7": [
        "probabilidade",
        "chance",
        "aleatório",
        "média",
        "desvio padrão",
        "amostra"
    ]
}

ASSUNTOS = {
    "Geometria": [
        "área",
        "volume",
        "triângulo",
        "círculo",
        "pirâmide",
        "polígono"
    ],
    "Funções": [
        "função",
        "gráfico",
        "crescimento",
        "decrescimento"
    ],
    "Probabilidade": [
        "probabilidade",
        "chance",
        "aleatório"
    ],
    "Estatística": [
        "estatística",
        "média",
        "desvio padrão",
        "amostra"
    ],
    "Porcentagem": [
        "porcentagem",
        "%"
    ],
    "Juros": [
        "juros"
    ],
    "Álgebra": [
        "equação",
        "algébrica",
        "expressão",
        "incógnita",
        "sistema"
    ],
    "Escala": [
        "escala"
    ],
    "Análise Combinatória": [
        "anagrama",
        "combinação",
        "arranjo",
        "permutação"
    ]
}

def classificar_competencia(texto: str):
    texto = texto.lower()

    melhor_competencia = "GERAL"
    maior_score = 0

    for competencia, palavras in COMPETENCIAS.items():
        score = 0

        for palavra in palavras:
            if palavra in texto:
                score += 1

        if score > maior_score:
            maior_score = score
            melhor_competencia = competencia

    return melhor_competencia

def classificar_assunto(texto: str):
    texto = texto.lower()

    melhor_assunto = "Geral"
    maior_score = 0

    for assunto, palavras in ASSUNTOS.items():
        score = 0

        for palavra in palavras:
            if palavra in texto:
                score += 1

        if score > maior_score:
            maior_score = score
            melhor_assunto = assunto

    return melhor_assunto

def calcular_dificuldade(texto: str):
    tamanho = len(texto)

    numeros = len(re.findall(r'\d+', texto))

    score = 1.0

    if tamanho > 500:
        score += 1

    if tamanho > 1000:
        score += 1

    if numeros > 10:
        score += 0.5

    return round(score, 1)

def gerar_texto_completo(q):
    alternativas = q.get("alternatives", [])

    texto_alternativas = ""

    for alt in alternativas:

        texto_alternativas += f"""
        {alt.get('letter', '')})
        {alt.get('text', '')}
        """

    return f"""
    {q.get("context", "")}

    {q.get("question", "")}

    {texto_alternativas}
    """

def pegar_resposta_correta(alternativas):
    for alt in alternativas:

        if alt.get("isCorrect"):
            return alt.get("letter")

    return "A"

def pegar_imagem_questao(q):
    if q.get("file"):
        return q["file"]

    arquivos = q.get("files", [])

    if arquivos:
        return arquivos[0].get("url")

    return None

def pegar_alternativa(alternativas, letra):
    for alt in alternativas:

        if alt.get("letter") == letra:
            return alt

    return {}

def pegar_texto_alternativa(alternativas, letra):
    alt = pegar_alternativa(alternativas, letra)

    return alt.get("text")

def pegar_imagem_alternativa(alternativas, letra):
    alt = pegar_alternativa(alternativas, letra)

    return alt.get("file")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "maths.json")

def questao_valida(alternativas):
    letras = ["A", "B", "C", "D", "E"]

    for letra in letras:
        alt = pegar_alternativa(alternativas, letra)

        texto = alt.get("text")
        imagem = (alt.get("file") or alt.get("imagem"))

        if not texto and not imagem:
            return False

    return True

def classificar_questao():
    db = SessionLocal()
    model = get_model()

    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            questoes = json.load(f)

        print("=" * 50)
        print(f"QUESTÕES ENCONTRADAS: {len(questoes)}")
        print("=" * 50)

        contador = 0

        for q in questoes:
            try:
                alternativas = q.get("alternatives", [])

                if len(alternativas) < 5:
                    continue

                if not questao_valida(alternativas) or not q.get("context"):
                    print(f"Questão ignorada: {q.get('question')}")
                    continue

                texto = gerar_texto_completo(q)
                competencia = classificar_competencia(texto)
                assunto = classificar_assunto(texto)
                dificuldade = calcular_dificuldade(texto)
                resposta_correta = pegar_resposta_correta(alternativas)
                embedding = json.dumps(model.encode(texto).tolist())
                nova_questao = Questao(
                    titulo=q.get("question", "Sem título"),
                    contexto=q.get("context", ""),
                    texto_completo=texto,
                    imagem_url=pegar_imagem_questao(q),
                    alternativa_a=pegar_texto_alternativa(alternativas, "A"),
                    alternativa_b=pegar_texto_alternativa(alternativas, "B"),
                    alternativa_c=pegar_texto_alternativa(alternativas, "C"),
                    alternativa_d=pegar_texto_alternativa(alternativas, "D"),
                    alternativa_e=pegar_texto_alternativa(alternativas, "E"),
                    alternativa_a_imagem=pegar_imagem_alternativa(alternativas, "A"),
                    alternativa_b_imagem=pegar_imagem_alternativa(alternativas, "B"),
                    alternativa_c_imagem=pegar_imagem_alternativa(alternativas, "C"),
                    alternativa_d_imagem=pegar_imagem_alternativa(alternativas, "D"),
                    alternativa_e_imagem=pegar_imagem_alternativa(alternativas, "E"),
                    resposta_correta=resposta_correta,
                    materia="Matemática",
                    assunto=assunto,
                    habilidade_enem=competencia,
                    dificuldade=dificuldade,
                    embedding=embedding,
                    origem="ENEM",
                    ativa=True
                )

                db.add(nova_questao)

                contador += 1

                if contador % 50 == 0:
                    db.commit()
                    
                print(f"Questão {contador} importada")

            except Exception as e:
                print("=" * 50)
                print("ERRO AO IMPORTAR QUESTÃO")
                print(e)
                print("=" * 50)

        db.commit()

        print("=" * 50)
        print("IMPORTAÇÃO FINALIZADA")
        print(f"TOTAL IMPORTADO: {contador}")
        print("=" * 50)

    finally:
        db.close()

if __name__ == "__main__":
    classificar_questao()