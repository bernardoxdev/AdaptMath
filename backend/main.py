import os

from datetime import datetime, timezone
from passlib.context import CryptContext
from functools import wraps
from jose import jwt, JWTError, ExpiredSignatureError

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session

from backend.core.jwt import SECRET_KEY, ALGORITHM, renovar_tokens
from backend.redis.redis import RedisManager
from backend.utils.user_utils import registrar_usuario, realizar_login, export_data, get_nivel, get_estatistica_questoes, get_relatorio_evolucao, get_dashboard_atividades, get_relatorio_resumo
from backend.utils.questoes_utils import gerar_teste, get_materias, get_modelos, favoritar_questao, get_questao_by_id, responder_questao_teste, questoes_favoritadas, responder_questao, reportar_questao, get_questao_by_infos, get_questao_favoritada, remover_questao_favoritada
from backend.utils.conversas_utils import criar_nova_conversa, get_conversas, get_conversa
from backend.utils.ia_utils import gerar_dica, get_relatorio_insights, gerar_analise_relatorio, responder_chat

from backend.database.connection import SessionLocal
from backend.database.models.testes_aptidao import TesteAptidao
from backend.database.models.respostas_questoes import RespostaQuestao
from backend.database.models.refresh_token import RefreshToken

"""
CONFIG
"""
app = Flask(__name__, template_folder="../frontend/templates")

app.static_folder = '../frontend/src'
app.static_url_path = '/static'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-secret")
app.config['SESSION_TYPE'] = 'filesystem'

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False
)

Session(app)

"""
DECORATORS
"""
def login_required(f):
    """
    Garante que a rota só possa ser acessada por usuários autenticados.

    O decorator verifica a existência de um access token armazenado
    na sessão do usuário.

    Fluxo de autenticação:

    1. Valida o access token.
    2. Caso o token esteja expirado, tenta renová-lo através do
       refresh token armazenado na sessão.
    3. Caso a renovação seja bem-sucedida, atualiza os tokens da sessão.
    4. Caso a renovação falhe ou não exista refresh token válido,
       encerra a sessão e redireciona o usuário para a tela de login.

    Attributes:
        session["user_id"]:
            Atualizado automaticamente após validação ou renovação
            do token.

    Args:
        f (Callable):
            Função Flask que será protegida pelo decorator.

    Returns:
        Callable:
            Função decorada com autenticação obrigatória.

    Raises:
        jose.exceptions.JWTError:
            Quando o token possui assinatura inválida ou está corrompido.

        jose.exceptions.ExpiredSignatureError:
            Quando o access token expirou.

    Example:
        >>> @app.route("/dashboard")
        >>> @login_required
        >>> def dashboard():
        >>>     return "Área protegida"

    Notes:
        Este decorator depende das chaves:
        - access_token
        - refresh_token

        armazenadas na sessão Flask.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        access_token = session.get("access_token")

        if not access_token:
            return redirect(
                url_for("login")
            )

        try:
            payload = jwt.decode(
                access_token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
            )

            session["user_id"] = payload["sub"]
            
            if payload.get("type") != "access":
                raise JWTError("Token inválido")

            return f(*args, **kwargs)

        except ExpiredSignatureError:
            refresh_token = session.get("refresh_token")

            if not refresh_token:
                session.clear()

                return redirect(url_for("login"))

            novos_tokens = renovar_tokens(refresh_token)

            if not novos_tokens:
                session.clear()

                return redirect(url_for("login"))

            session["access_token"] = novos_tokens["access_token"]
            session["refresh_token"] = novos_tokens["refresh_token"]
            session["user_id"] = novos_tokens["user_id"]

            return f(*args, **kwargs)

        except JWTError:
            session.clear()

            return redirect(
                url_for("login")
            )

    return wrapper

"""
ROTAS SITE
"""
# Rotas Base
@app.route("/")
def index():
    """
    Página inicial da aplicação.

    Exibe a landing page pública do AdaptMath contendo
    informações sobre a plataforma e opções de acesso.

    Returns:
        flask.Response:
            Template HTML da página inicial.

    Example:
        GET /
    """
    return render_template("index.html")

@app.route("/login")
def login():
    """
    Página de autenticação.

    Exibe o formulário utilizado para autenticação
    de usuários cadastrados.

    Returns:
        flask.Response:
            Template HTML da página de login.

    Example:
        GET /login
    """
    return render_template("login.html")

@app.route('/register')
def registro():
    """
    Renderiza a página de cadastro de novos usuários.

    Nesta página o usuário pode criar uma conta
    para acessar os recursos da plataforma.

    Returns:
        Response: Template da página de registro (registro.html).
    """
    return render_template("registro.html")

@app.route("/logout")
@login_required
def logout():
    """
    Realiza o logout do usuário autenticado.

    O refresh token armazenado na sessão é marcado como
    revogado no banco de dados, impedindo futuras renovações
    de acesso. Em seguida todos os dados da sessão são removidos.

    Returns:
        Response:
            Redireciona o usuário para a página de login.
    """
    refresh_token = session.get("refresh_token")

    if refresh_token:
        db = SessionLocal()

        try:
            refresh_db = db.query(RefreshToken).filter(RefreshToken.token == refresh_token, RefreshToken.revogado == False).first()

            if refresh_db:
                refresh_db.revogado = True

                db.commit()

        finally:
            db.close()

    session.clear()

    return redirect(url_for("login"))

# Rotas Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    """
    Exibe a página principal do dashboard.

    Carrega os dados estatísticos do usuário autenticado
    e as recomendações geradas pelo sistema de IA.

    Returns:
        Response:
            Template dashboard.html renderizado com:
            - username
            - dados de desempenho
            - recomendações
    """
    user_id = session.get('user_id')

    dados = export_data(user_id)
    recomendacoes = [] # TODO: Motor de IA para gerar recomendaçoes

    if not recomendacoes:
        recomendacoes = ['Nao existem recomendaçoes atualmente']

    return render_template("dashboard.html", username=session.get("user_name"), dados=dados, recomendacoes=recomendacoes)

@app.route('/dashboard/aptidao')
@login_required
def dashboard_aptidao():
    """
    Exibe a tela inicial do teste de aptidão.

    Caso não exista um teste armazenado no Redis para
    o usuário atual, um novo teste é gerado automaticamente.

    Returns:
        Response:
            Template dashboard_aptidao.html.

        tuple:
            Mensagem de erro e código HTTP 500 caso
            a geração do teste falhe.
    """
    user_id = session.get('user_id')
    lista_questoes = RedisManager.get(f"{user_id}_lista")

    if not lista_questoes:
        lista_questoes = gerar_teste(int(user_id), 15)

        if not lista_questoes.get("success"):
            return lista_questoes.get(
                "message",
                "Erro ao gerar teste."
            ), 500

        RedisManager.set(f"{user_id}_lista", lista_questoes)

    return render_template("dashboard_aptidao.html", quantidade=lista_questoes.get("quantidade", 0))

@app.route('/teste/aptidao')
@login_required
def teste_aptidao():
    """
    Exibe a interface de realização do teste de aptidão.

    Verifica se existe um teste ativo armazenado no Redis
    para o usuário autenticado.

    Returns:
        Response:
            Template teste_aptidao.html.

        RedirectResponse:
            Redireciona para dashboard_aptidao caso
            não exista um teste ativo.
    """
    user_id = str(session.get("user_id"))
    lista_questoes = RedisManager.get(f"{user_id}_lista")

    if not lista_questoes:
        return redirect(url_for("dashboard_aptidao"))

    return render_template("teste_aptidao.html", quantidade=lista_questoes["quantidade"])

@app.route('/dashboard/questoes')
@login_required
def dashboard_questoes():
    """
    Exibe a página de resolução de questões.

    Carrega o nível atual do usuário, os modelos
    disponíveis e as matérias cadastradas para uso
    nos filtros da página.

    Returns:
        Response:
            Template dashboard_questoes.html.
    """
    user_id = int(session.get('user_id'))

    nivel = get_nivel(user_id)
    modelos = get_modelos()
    modelos.insert(0, "Sem Filtro")
    materias = get_materias(modelos[0])
    materias.insert(0, "Sem Filtro")

    return render_template("dashboard_questoes.html", nivel=nivel, materias=materias, modelos=modelos)

@app.route('/dashboard/questoes/salvas')
@login_required
def dashboard_salvas():
    """
    Exibe a página de exercícios salvos pelo usuário.

    Returns:
        Response:
            Template dashboard_exercicios_salvos.html.
    """
    return render_template("dashboard_exercicios_salvos.html")

@app.route('/dashboard/dados')
@login_required
def dashboard_dados():
    """
    Exibe os dados pessoais e métricas de desempenho.

    Carrega estatísticas gerais e o nível atual
    do usuário autenticado.

    Returns:
        Response:
            Template dashboard_dados.html.
    """
    user_id = session.get('user_id')
    dados = export_data(user_id)
    nivel = get_nivel(user_id)

    return render_template("dashboard_dados.html", username=session.get('username'), nivel=nivel, dados=dados)

@app.route('/dashboard/relatorio')
@login_required
def dashboard_relatorio():
    """
    Exibe a página de relatórios de desempenho.

    Returns:
        Response:
            Template dashboard_relatorios.html.
    """
    return render_template("dashboard_relatorios.html")

@app.route('/dashboard/ia')
@login_required
def dashboard_ia():
    """
    Exibe a interface de conversa com a IA.

    Returns:
        Response:
            Template dashboard_conversar.html.
    """
    return render_template("dashboard_conversar.html")

"""
ROTAS API (Conexão JavaScript)
"""
# Rotas gerenciamento User
@app.route('/logar', methods=['POST'])
def logar():
    """
    Realiza a autenticação do usuário.

    Recebe email e senha através de uma requisição JSON,
    valida as credenciais e gera novos tokens de acesso.

    Body:
        {
            "email": str,
            "senha": str
        }

    Returns:
        JSON:
            {
                "success": bool,
                "message": str,
                "user": dict,
                "tokens": dict,
                "redirect": "/dashboard"
            }

        HTTP 200:
            Login realizado com sucesso.

        HTTP 401:
            Credenciais inválidas.
    """
    data = request.get_json()

    resultado = realizar_login(
        email = data.get("email"),
        senha = data.get("senha")
    )

    if resultado["success"]:
        session["access_token"] = resultado["tokens"]["access_token"]
        session["refresh_token"] = resultado["tokens"]["refresh_token"]

        session["user_id"] = resultado["user"]["id"]
        session["user_name"] = resultado["user"]["nome"]
        session["user_email"] = resultado["user"]["email"]

        return jsonify({
            **resultado,
            "redirect": "/dashboard"
        }), 200

    return jsonify(resultado), 401

@app.route('/registro', methods=['POST'])
def registrar():
    """
    Realiza o cadastro de um novo usuário.

    Recebe nome, email e senha através de JSON,
    cria o usuário e gera os tokens de autenticação.

    Body:
        {
            "nome": str,
            "email": str,
            "senha": str
        }

    Returns:
        JSON:
            {
                "success": bool,
                "message": str,
                "user": dict,
                "tokens": dict,
                "redirect": "/dashboard"
            }

        HTTP 201:
            Usuário criado com sucesso.

        HTTP 400:
            Dados inválidos ou usuário já existente.
    """
    data = request.get_json()

    resultado = registrar_usuario(
        nome=data.get("nome"),
        email=data.get("email"),
        senha=data.get("senha")
    )

    if resultado["success"]:
        session["access_token"] = resultado["tokens"]["access_token"]
        session["refresh_token"] = resultado["tokens"]["refresh_token"]

        session["user_id"] = resultado["user"]["id"]
        session["user_name"] = resultado["user"]["nome"]
        session["user_email"] = resultado["user"]["email"]

        return jsonify({
            **resultado,
            "redirect": "/dashboard"
        }), 201

    return jsonify(resultado), 400

@app.route('/start-aptidao', methods=['POST'])
def start_aptidao():
    """
    Inicia um teste de aptidão previamente gerado.

    Verifica se existe uma lista de questões
    armazenada no Redis para o usuário autenticado.

    Returns:
        JSON:
            {
                "success": bool,
                "redirect": "/teste/aptidao"
            }

        HTTP 200:
            Teste encontrado e iniciado.

        HTTP 400:
            Nenhum teste disponível para o usuário.
    """
    user_id = session.get('user_id', None)

    if not user_id or not RedisManager.get(f"{user_id}_lista"):
        return jsonify({
            "success": False,
            "message": "Nao foi encontrado seu id de usuario"
        }), 400

    return jsonify({
        "success": True,
        "redirect": "/teste/aptidao"
    }), 200

@app.route('/api/teste/questao/<int:numero>')
@login_required
def api_questao(numero):
    """
    Retorna uma questão específica do teste de aptidão em andamento.

    A questão é recuperada através da lista armazenada no Redis
    para o usuário autenticado.

    Args:
        numero (int): Número da questão dentro do teste.

    Returns:
        Response:
            200:
                Dados completos da questão.
            404:
                Teste ou questão não encontrada.
    """
    user_id = str(session.get("user_id"))
    lista = RedisManager.get(f"{user_id}_lista")

    if not lista:
        return jsonify({
            "success": False,
            "message": "Teste não encontrado."
        }), 404

    questao_id = lista["questoes"].get(str(numero)) or lista["questoes"].get(numero)

    if not questao_id:
        return jsonify({
            "success": False,
            "message": "Questão não encontrada."
        }), 404

    resultado = get_questao_by_id(questao_id)

    if not resultado["success"]:
        return jsonify(resultado), 404

    resultado["questao"]["numero"] = numero
    resultado["questao"]["total"] = lista["quantidade"]

    return jsonify(resultado)

@app.route('/api/teste/responder', methods=['POST'])
@login_required
def responder_questao_teste_route():
    """
    Registra a resposta do usuário para uma questão do teste.

    Recebe o número da questão e a alternativa escolhida,
    valida a resposta e atualiza o progresso do teste.

    Caso seja a última questão, finaliza o teste,
    calcula a pontuação final e remove os dados temporários
    armazenados no Redis.

    Body:
        {
            "numero": int,
            "alternativa": str
        }

    Returns:
        Response:
            200:
                Resposta registrada com sucesso.
            400:
                Erro ao registrar resposta.
            404:
                Teste ou questão não encontrada.
    """
    user_id = int(session.get("user_id"))

    data = request.get_json()

    numero = int(data.get("numero"))
    alternativa = data.get("alternativa")

    lista = RedisManager.get(f"{user_id}_lista")

    if not lista:
        return jsonify({
            "success": False,
            "message": "Teste não encontrado."
        }), 404

    questao_id = (
        lista["questoes"].get(str(numero))
        or lista["questoes"].get(numero)
    )

    if not questao_id:
        return jsonify({
            "success": False,
            "message": "Questão não encontrada."
        }), 404

    resultado = responder_questao_teste(
        user_id=user_id,
        questao_id=questao_id,
        teste_id=lista["teste_id"],
        alternativa=alternativa
    )

    if not resultado["success"]:
        return jsonify(resultado), 400

    acertou = resultado["acertou"]

    finalizado = numero >= lista["quantidade"]

    if finalizado:
        db = SessionLocal()

        try:
            teste = db.query(TesteAptidao).filter(TesteAptidao.id == lista["teste_id"]).first()

            if teste:
                total_acertos = db.query(RespostaQuestao).filter(RespostaQuestao.usuario_id == user_id, RespostaQuestao.teste_aptidao_id == teste.id, RespostaQuestao.acertou == True).count()

                teste.finalizado = True
                teste.pontuacao = round((total_acertos / lista["quantidade"]) * 100, 2)
                teste.finalizado_em = datetime.now(timezone.utc)

                db.commit()

            RedisManager.delete(f"{user_id}_lista")

        finally:
            db.close()

    return jsonify({
        "success": True,
        "acertou": acertou,
        "finalizado": finalizado,
        "message": resultado["message"]
    })

@app.route('/api/questoes/salvar', methods=['POST'])
@login_required
def salvar_questao():
    """
    Adiciona uma questão à lista de favoritos do usuário.

    Body:
        {
            "questao_id": int
        }

    Returns:
        Response:
            200:
                Questão favoritada com sucesso.
            400:
                Erro ao favoritar questão.
    """
    data = request.get_json()

    user_id = int(session.get("user_id"))
    questao_id = data.get("questao_id")

    return jsonify(favoritar_questao(user_id, questao_id))

@app.route('/api/questoes/salvas')
@login_required
def listar_questoes_salvas():
    """
    Lista todas as questões salvas pelo usuário autenticado.

    Returns:
        Response:
            200:
                Lista de questões favoritas do usuário.
    """
    user_id = session.get("user_id")

    return jsonify(questoes_favoritadas(user_id))

@app.route('/api/questoes/salvas/<int:questao_id>', methods=['DELETE'])
@login_required
def remover_questao_salva(questao_id):
    """
    Remove uma questão da lista de favoritos do usuário.

    Args:
        questao_id (int): Identificador da questão.

    Returns:
        Response:
            200:
                Questão removida com sucesso.
            404:
                Questão não encontrada ou não favoritada.
    """
    user_id = int(session.get("user_id"))

    resultado = remover_questao_favoritada(user_id=user_id, questao_id=questao_id)

    if not resultado["success"]:
        return jsonify(resultado), 404

    return jsonify(resultado)

@app.route('/api/questoes/proxima', methods=['POST'])
@login_required
def get_proxima_questao():
    """
    Retorna a próxima questão para o usuário.

    A seleção é realizada com base na matéria,
    dificuldade e modelo informados, podendo utilizar
    o histórico do usuário para personalizar a escolha.

    Body:
        {
            "materia": str,
            "dificuldade": str,
            "modelo": str
        }

    Returns:
        Response:
            200:
                Questão encontrada com sucesso.
            404:
                Nenhuma questão disponível para os filtros informados.
    """
    data = request.get_json()

    user_id = session.get("user_id")
    materia = data.get("materia")
    dificuldade = data.get("dificuldade")
    modelo = data.get("modelo")

    return jsonify(get_questao_by_infos(user_id, materia, dificuldade, modelo))

@app.route('/api/questoes/responder', methods=['POST'])
@login_required
def responder_questao_atividade():
    """
    Registra a resposta do usuário para uma questão avulsa.

    Verifica se a alternativa enviada está correta,
    atualiza as estatísticas do usuário e retorna
    o resultado da resposta.

    Body:
        {
            "questao_id": int,
            "alternativa": str
        }

    Returns:
        Response:
            200:
                Resposta processada com sucesso.
            400:
                Dados inválidos.
            404:
                Questão não encontrada.
    """
    data = request.get_json()

    user_id = session.get("user_id")
    questao_id = data.get("questao_id")
    alternativa = data.get("alternativa")

    return jsonify(responder_questao(user_id, questao_id, alternativa))

@app.route('/api/questoes/reportar', methods=['POST'])
@login_required
def reporte_questao():
    """
    Registra um reporte de problema em uma questão.

    Permite que o usuário informe inconsistências
    encontradas na questão, alternativas, imagens
    ou gabarito.

    Body:
        {
            "questao_id": int,
            "tipo": str,
            "descricao": str
        }

    Tipos de reporte:
        - enunciado
        - alternativa
        - imagem
        - gabarito
        - outro

    Returns:
        Response:
            200:
                Reporte enviado com sucesso.
            400:
                Dados inválidos.
            404:
                Questão não encontrada.
    """
    data = request.get_json()

    user_id = session.get("user_id")
    questao_id = data.get("questao_id")
    tipo = data.get("tipo")
    descricao = data.get("descricao")

    return jsonify(reportar_questao(user_id, questao_id, tipo, descricao))

@app.route("/api/relatorio/materias")
@login_required
def relatorio_materias():
    """
    Retorna o desempenho do usuário por matéria.

    Endpoint utilizado na tela de relatórios para exibir
    estatísticas de desempenho em cada área da matemática,
    como Probabilidade, Estatística, Geometria e Funções.

    A porcentagem de cada matéria é calculada com base
    nas questões respondidas pelo usuário e na sua taxa
    de acertos.

    Returns:
        flask.Response:
            JSON contendo a lista de matérias e seus
            respectivos percentuais de desempenho.

    Exemplo de retorno:
    {
        "success": true,
        "materias": [
            {
                "nome": "Probabilidade",
                "percentual": 92
            },
            {
                "nome": "Estatística",
                "percentual": 81
            }
        ]
    }
    """
    user_id = session.get("user_id")

    return get_estatistica_questoes(user_id)
    
@app.route("/api/relatorio/evolucao")
@login_required
def relatorio_evolucao():
    """
    Retorna a evolução mensal do desempenho do usuário.

    Endpoint responsável por alimentar o gráfico de
    evolução presente na tela de relatórios.

    Os dados são agrupados por mês utilizando as
    respostas registradas pelo usuário e calculando
    a porcentagem de acertos em cada período.

    Returns:
        flask.Response:
            JSON contendo os meses e seus respectivos
            percentuais de desempenho.

    Exemplo de retorno:
    {
        "success": true,
        "meses": [
            {
                "nome": "Jan",
                "valor": 72.5
            },
            {
                "nome": "Fev",
                "valor": 81.3
            }
        ]
    }
    """
    user_id = session.get("user_id")

    return jsonify(get_relatorio_evolucao(user_id))
    
@app.route("/api/dashboard/atividades")
@login_required
def dashboard_atividades():
    """
    Retorna as atividades recentes do usuário.

    Endpoint utilizado no dashboard para exibir um
    histórico resumido das últimas ações realizadas,
    incluindo testes de aptidão, resolução de questões
    e demais eventos relevantes da plataforma.

    As atividades são ordenadas da mais recente para
    a mais antiga.

    Returns:
        flask.Response:
            JSON contendo a lista de atividades recentes.

    Exemplo de retorno:
    {
        "success": true,
        "atividades": [
            {
                "titulo": "Teste de Aptidão",
                "descricao": "Finalizado em 17/06/2026 14:30",
                "status": "82%"
            },
            {
                "titulo": "Probabilidade",
                "descricao": "Probabilidade Condicional",
                "status": "Correta"
            }
        ]
    }
    """
    user_id = int(session.get("user_id"))

    return jsonify(get_dashboard_atividades(user_id))

@app.route("/api/relatorio/resumo")
@login_required
def relatorio_resumo():
    """
    Retorna um resumo geral do desempenho do usuário.

    O resumo inclui:
    - Média geral de acertos.
    - Quantidade de questões respondidas.
    - Matéria com melhor desempenho.
    - Matéria com pior desempenho.

    Returns:
        flask.Response:
            JSON contendo os dados resumidos do relatório.
    """
    user_id = int(session.get("user_id"))

    return jsonify(get_relatorio_resumo(user_id))

@app.route("/api/chat/conversa", methods=["POST"])
@login_required
def api_criar_conversa():
    """
    Cria uma nova conversa entre o usuário autenticado e a IA.

    Espera um JSON contendo a primeira mensagem da conversa.
    A função cria o registro da conversa, gera um título inicial
    com base na mensagem enviada e retorna o identificador da
    nova conversa.

    Body:
        {
            "mensagem": str
        }

    Returns:
        JSON:
            {
                "success": bool,
                "conversa_id": int,
                "titulo": str
            }
    """
    data = request.get_json()

    user_id = session.get("user_id")
    mensagem = data.get("mensagem")

    return jsonify(criar_nova_conversa(user_id, mensagem))


@app.route("/api/chat/conversas")
@login_required
def api_chat_conversas():
    """
    Retorna todas as conversas do usuário autenticado.

    As conversas são ordenadas da mais recente para a mais antiga,
    permitindo preencher o histórico exibido na barra lateral do chat.

    Returns:
        JSON:
            {
                "success": bool,
                "conversas": [
                    {
                        "id": int,
                        "titulo": str,
                        "data": str
                    }
                ]
            }
    """
    user_id = session.get("user_id")

    return jsonify(get_conversas(user_id))


@app.route("/api/chat/conversa/<int:conversa_id>")
@login_required
def api_carregar_conversa(conversa_id):
    """
    Retorna todas as mensagens pertencentes a uma conversa.

    Args:
        conversa_id (int):
            Identificador da conversa.

    Returns:
        JSON:
            {
                "success": bool,
                "mensagens": [
                    {
                        "tipo": str,
                        "texto": str
                    }
                ]
            }
    """
    return jsonify(get_conversa(conversa_id))


@app.route('/api/questoes/dica/<int:numero>')
@login_required
def api_gerar_dica(numero):
    """
    Gera uma dica utilizando IA para a questão atual do teste.

    A dica auxilia o usuário na resolução da questão sem revelar
    a alternativa correta ou a resposta final.

    Args:
        numero (int):
            Número da questão dentro do teste de aptidão.

    Returns:
        JSON:
            {
                "success": bool,
                "dica": str
            }
    """
    return jsonify(gerar_dica(numero))


@app.route("/api/relatorio/insights")
@login_required
def relatorio_insights():
    """
    Retorna insights automáticos sobre o desempenho do usuário.

    Os insights são gerados a partir das estatísticas de resolução
    de questões, testes realizados e desempenho por matéria.

    Returns:
        JSON:
            {
                "success": bool,
                "insights": [
                    {
                        "titulo": str,
                        "texto": str
                    }
                ]
            }
    """
    user_id = int(session.get("user_id"))

    return jsonify(get_relatorio_insights(user_id))


@app.route("/api/relatorio/analise")
@login_required
def relatorio_analise():
    """
    Gera uma análise detalhada do desempenho do usuário utilizando IA.

    A análise considera métricas como quantidade de questões
    respondidas, média dos testes, taxa de acertos e desempenho
    por matéria, produzindo recomendações personalizadas.

    Returns:
        JSON:
            {
                "success": bool,
                "textos": [
                    str,
                    ...
                ]
            }
    """
    user_id = int(session.get("user_id"))

    return jsonify(gerar_analise_relatorio(user_id))


@app.route("/api/chat/mensagem", methods=["POST"])
@login_required
def api_chat_mensagem():
    """
    Envia uma mensagem para o assistente de IA.

    A função recupera o histórico da conversa, envia o contexto
    completo ao modelo de linguagem, salva a mensagem do usuário,
    salva a resposta da IA e retorna a resposta gerada.

    Body:
        {
            "conversa_id": int,
            "mensagem": str
        }

    Returns:
        JSON:
            {
                "success": bool,
                "resposta": str
            }
    """
    data = request.get_json()

    user_id = int(session.get("user_id"))
    conversa_id = data.get("conversa_id")
    mensagem = data.get("mensagem")

    return jsonify(responder_chat(user_id, conversa_id, mensagem))

if __name__ == '__main__':
    app.run(port=5000, debug=True)