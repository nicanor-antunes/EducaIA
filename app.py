import os
from groq import Groq
import streamlit as st
from supabase import create_client, Client

# Configuração da página - Deve ser o primeiro comando Streamlit do script
st.set_page_config(
    page_title="EducaIA", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CONFIGURAÇÃO DO CLIENTE GROQ ----------------
@st.cache_resource
def get_groq_client():
    """Inicializa o cliente Groq buscando a chave de API nos Secrets ou Ambiente."""
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    return Groq(api_key=api_key)

# ---------------- CONFIGURAÇÃO DO SUPABASE ----------------
@st.cache_resource
def get_supabase_client():
    """Inicializa o cliente Supabase."""
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return None
    return create_client(url, key)

def carregar_progresso(nome_aluno: str) -> dict:
    """Carrega o progresso do aluno do banco. Cria registro se não existir."""
    sb = get_supabase_client()
    if sb is None:
        return None
    try:
        res = sb.table("progresso_alunos").select("*").eq("nome_aluno", nome_aluno).execute()
        if res.data:
            return res.data[0]
        # Cria novo registro para o aluno
        novo = {
            "nome_aluno": nome_aluno,
            "disciplina": st.session_state.get("disciplina", "Geografia"),
            "perguntas": 0,
            "exercicios": 0,
            "textos": 0,
            "dias_sequencia": 1,
            "ultima_data": str(datetime.date.today()),
        }
        sb.table("progresso_alunos").insert(novo).execute()
        return novo
    except Exception as e:
        st.warning(f"⚠️ Não foi possível conectar ao banco de dados: {e}")
        return None

def salvar_progresso(nome_aluno: str):
    """Salva o progresso atual do session_state no banco."""
    sb = get_supabase_client()
    if sb is None:
        return
    try:
        sb.table("progresso_alunos").upsert({
            "nome_aluno": nome_aluno,
            "disciplina": st.session_state.get("disciplina", "Geografia"),
            "perguntas": st.session_state.prog_perguntas,
            "exercicios": st.session_state.prog_exercicios,
            "textos": st.session_state.prog_textos,
            "dias_sequencia": st.session_state.prog_dias,
            "ultima_data": st.session_state.prog_ultima_data,
            "atualizado_em": "NOW()",
        }, on_conflict="nome_aluno").execute()
    except Exception:
        pass  # Falha silenciosa para não interromper a aula

def consultar_ia(prompt_formatado, mensagem_espera="Analisando conteúdo..."):
    """Envia a requisição para o modelo Llama-3.3 de forma segura."""
    client = get_groq_client()
    if client is None:
        st.error("🔑 Chave de acesso (GROQ_API_KEY) não configurada. Por favor, adicione-a nos Secrets do Streamlit.")
        return None

    with st.spinner(mensagem_espera):
        try:
            resposta = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt_formatado}],
                temperature=0.4,
                max_tokens=1800
            )
            return resposta.choices[0].message.content
        except Exception as e:
            st.error(f"⚠️ Houve uma instabilidade na conexão com o servidor. Por favor, tente novamente em instantes.")
            return None

# ---------------- ENGENHARIA DE PROMPT PEDAGÓGICO ----------------
def construir_prompt_eja(comando_estudante):
    """Garante que as respostas da IA sigam rigorosamente a metodologia didática para EJA."""
    disciplina = st.session_state.get("disciplina", "Geral")
    nivel = st.session_state.get("nivel", "EJA")
    
    return f"""
Você é o EducaIA, um tutor virtual altamente empático, especializado na Educação de Jovens e Adultos (EJA).

Contexto da Aula Atual:
- Disciplina Integrada: {disciplina}
- Nível de Ensino: {nivel}

Equipe de Mediação Pedagógica:
- Coordenadora Pedagógica: Prof.ª Ms. Andreia Crizostomo Barata
- Supervisor de Tecnologia Educacional: Prof. Dr. Nicanor Tiago Bueno Antunes

Suas regras de ouro fundamentais:
1. Comunicação Humana e Acolhedora: Responda em português fluído, sem jargões rebuscados. Lembre-se de que muitos alunos estão voltando a estudar após anos afastados.
2. Valorização da Experiência de Vida: Conecte o conhecimento científico com exemplos práticos do cotidiano de um adulto trabalhador (orçamento familiar, mercado de trabalho, ambiente urbano, saúde e esportes).
3. Estruturação Visual Clara: Use parágrafos curtos, listas com marcadores e formatação em negrito para termos importantes, facilitando a leitura na tela.
4. Linguagem Não-Infantilizada: Trate o estudante com o respeito devido a um adulto. Evite termos excessivamente infantis.

Comando ou Dúvida do Aluno:
{comando_estudante}
"""

# ---------------- INICIALIZAÇÃO DO ESTADO GLOBAL (SESSION STATE) ----------------
import datetime

if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = []

if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

if "disciplina" not in st.session_state:
    st.session_state.disciplina = "Geografia"

if "ver_cursos" not in st.session_state:
    st.session_state.ver_cursos = False

if "tamanho_fonte" not in st.session_state:
    st.session_state.tamanho_fonte = "normal"  # "normal", "grande", "extra"

if "nome_aluno" not in st.session_state:
    st.session_state.nome_aluno = ""          # identificação do aluno

if "progresso_carregado" not in st.session_state:
    st.session_state.progresso_carregado = False

# --- GAMIFICAÇÃO: contadores de progresso (valores padrão) ---
if "prog_perguntas" not in st.session_state:
    st.session_state.prog_perguntas = 0

if "prog_exercicios" not in st.session_state:
    st.session_state.prog_exercicios = 0

if "prog_textos" not in st.session_state:
    st.session_state.prog_textos = 0

if "prog_dias" not in st.session_state:
    st.session_state.prog_dias = 1

if "prog_ultima_data" not in st.session_state:
    st.session_state.prog_ultima_data = str(datetime.date.today())

logo_path = None
if os.path.exists("logo.png"):
    logo_path = "logo.png"
elif os.path.exists("logo_transparente_hd.png"):
    logo_path = "logo_transparente_hd.png"
elif os.path.exists("logo_transparente.png"):
    logo_path = "logo_transparente.png"

def _atualizar_sequencia():
    hoje = str(datetime.date.today())
    ultima = st.session_state.prog_ultima_data
    if ultima == hoje:
        return
    ontem = str(datetime.date.today() - datetime.timedelta(days=1))
    st.session_state.prog_dias = st.session_state.prog_dias + 1 if ultima == ontem else 1
    st.session_state.prog_ultima_data = hoje

def _carregar_do_banco():
    """Carrega progresso do Supabase e injeta no session_state."""
    if st.session_state.progresso_carregado:
        return
    dados = carregar_progresso(st.session_state.nome_aluno)
    if dados:
        st.session_state.prog_perguntas  = dados.get("perguntas", 0)
        st.session_state.prog_exercicios = dados.get("exercicios", 0)
        st.session_state.prog_textos     = dados.get("textos", 0)
        st.session_state.prog_dias       = dados.get("dias_sequencia", 1)
        st.session_state.prog_ultima_data = dados.get("ultima_data", str(datetime.date.today()))
        _atualizar_sequencia()
    st.session_state.progresso_carregado = True


# ---------------- IDENTIDADE VISUAL PROFISSIONAL (CSS) ----------------
_escala = {"normal": "1rem", "grande": "1.22rem", "extra": "1.48rem"}
_fonte_base = _escala.get(st.session_state.tamanho_fonte, "1rem")

st.markdown(f"""
<style>
/* Ocultar sidebar completamente */
[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}

/* ── TAMANHO DE FONTE GLOBAL ── */
.stApp, .stApp * {{
    font-size: {_fonte_base} !important;
}}
/* Preservar tamanhos relativos em títulos */
h1 {{ font-size: calc({_fonte_base} * 1.9) !important; }}
h2 {{ font-size: calc({_fonte_base} * 1.55) !important; }}
h3 {{ font-size: calc({_fonte_base} * 1.3) !important; }}
h4 {{ font-size: calc({_fonte_base} * 1.12) !important; }}

/* Estilização Geral do Fundo */
.stApp {{
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}}

/* Centralização Absoluta do Logotipo */
.centralizar-logo {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 20px auto;
}}

/* Subtítulos e Textos de Apoio */
.subtitulo-plataforma {{
    color: #475569;
    font-size: calc({_fonte_base} * 1.25) !important;
    font-weight: 500;
    text-align: center;
    margin-bottom: 2.5rem;
}}

.titulo-seletor {{
    color: #1e3a8a;
    font-size: calc({_fonte_base} * 1.45) !important;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1.5rem;
}}

.subtitulo-seletor {{
    color: #334155;
    font-size: calc({_fonte_base} * 1.05) !important;
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 0.8rem;
}}

.hero-shell {{
    max-width: 1040px;
    margin: 0.75rem auto 1.25rem auto;
    padding: 0 1rem;
}}

.hero-stage {{
    background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(248,250,252,0.9));
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 28px;
    padding: 1.1rem 1.25rem 1.25rem 1.25rem;
    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
}}

.logo-card {{
    max-width: 270px;
    margin: 0 auto 0.85rem auto;
    padding: 0.15rem;
}}

.welcome-panel {{
    max-width: 760px;
    margin: 0 auto;
    background: rgba(255,255,255,0.86);
    border-radius: 24px;
    border: 1px solid rgba(148, 163, 184, 0.22);
    padding: 1.25rem 1.4rem;
}}

.welcome-panel .subtitulo-plataforma {{
    margin-bottom: 0.55rem;
}}

.hero-helper {{
    max-width: 680px;
    margin: 0 auto 0.6rem auto;
    color: #475569;
    font-size: calc({_fonte_base} * 0.92) !important;
    line-height: 1.35;
    text-align: center;
}}

/* ── INPUTS: fundo branco, borda visível, texto escuro ── */
[data-testid="stTextInput"] > div > div {{
    border-radius: 14px !important;
    background-color: #ffffff !important;
    border: 2px solid #94a3b8 !important;
}}
[data-testid="stTextInput"] input {{
    color: #0f172a !important;
    font-size: {_fonte_base} !important;
    background-color: #ffffff !important;
}}
[data-testid="stTextInput"] input::placeholder {{
    color: #94a3b8 !important;
    opacity: 1 !important;
}}
[data-testid="stTextInput"] > div > div:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
}}

/* Selectbox e number_input também */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div {{
    background-color: #ffffff !important;
    border: 2px solid #94a3b8 !important;
    border-radius: 12px !important;
    color: #0f172a !important;
}}

/* Textarea (chat) */
[data-testid="stChatInput"] textarea,
textarea {{
    background-color: #ffffff !important;
    border: 2px solid #94a3b8 !important;
    color: #0f172a !important;
    font-size: {_fonte_base} !important;
}}

/* Labels dos inputs */
label, [data-testid="stWidgetLabel"] {{
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: {_fonte_base} !important;
}}

/* --- ESTILIZAÇÃO DOS BOTÕES E CARDS --- */
div.stButton > button[key^="card_"] {{
    font-weight: 700 !important;
    border-radius: 16px !important;
    padding: 25px 15px !important;
    width: 100% !important;
    min-height: 135px !important;
    font-size: calc({_fonte_base} * 1.1) !important;
    display: block !important;
    white-space: pre-line !important;
    transition: all 0.25s ease-in-out !important;
}}

div.stButton > button[key^="card_"][data-testid="stBaseButton-secondary"] {{
    background-color: #ffffff !important;
    color: #1e3a8a !important;
    border: 2px solid #cbd5e1 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
}}

div.stButton > button[key^="card_"][data-testid="stBaseButton-secondary"]:hover {{
    border-color: #10b981 !important;
    color: #10b981 !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.15) !important;
}}

div.stButton > button[key^="card_"][data-testid="stBaseButton-primary"] {{
    background-color: #1e3a8a !important;
    color: #ffffff !important;
    border: 2px solid #1e3a8a !important;
    box-shadow: 0 10px 15px -3px rgba(30, 58, 138, 0.25) !important;
    transform: translateY(-2px) !important;
}}

/* --- BOTÃO CURSOS GRATUITOS --- */
div.stButton > button[key="card_cursos"] {{
    font-weight: 700 !important;
    border-radius: 14px !important;
    font-size: {_fonte_base} !important;
    transition: all 0.25s ease-in-out !important;
    min-height: 56px !important;
}}

div.stButton > button[key="card_cursos"][data-testid="stBaseButton-secondary"] {{
    background: linear-gradient(135deg, #fffbeb, #fef9c3) !important;
    color: #78350f !important;
    border: 2px solid #fcd34d !important;
    box-shadow: 0 4px 10px rgba(251,191,36,0.15) !important;
}}

div.stButton > button[key="card_cursos"][data-testid="stBaseButton-secondary"]:hover {{
    border-color: #f59e0b !important;
    color: #92400e !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(245,158,11,0.25) !important;
}}

div.stButton > button[key="card_cursos"][data-testid="stBaseButton-primary"] {{
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: #ffffff !important;
    border: 2px solid #d97706 !important;
    box-shadow: 0 6px 16px rgba(217,119,6,0.35) !important;
    transform: translateY(-2px) !important;
}}

/* ── CORRIGIR BOTÕES PRIMARY GENÉRICOS (evitar vermelho do tema padrão) ── */
div.stButton > button[data-testid="stBaseButton-primary"] {{
    background-color: #1e3a8a !important;
    color: #ffffff !important;
    border: none !important;
}}

/* Botão de login — verde */
div.stButton > button[key="btn_login"] {{
    background-color: #10b981 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: calc({_fonte_base} * 1.1) !important;
    padding: 14px 24px !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important;
    transition: all 0.2s ease-in-out !important;
}}

div.stButton > button[key="btn_login"]:hover {{
    background-color: #059669 !important;
    transform: translateY(-2px) !important;
}}

/* --- BOTÃO VERDE DE ENTRAR --- */
div.stButton > button[key="entrar_sala"] {{
    background-color: #10b981 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: calc({_fonte_base} * 1.15) !important;
    padding: 14px 24px !important;
    border-radius: 12px !important;
    border: none !important;
    min-height: auto !important;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important;
    transition: all 0.2s ease-in-out !important;
}}

div.stButton > button[key="entrar_sala"]:hover {{
    background-color: #059669 !important;
    color: #ffffff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(16, 185, 129, 0.4) !important;
}}

/* --- BANNER HORIZONTAL DO TOPO --- */
.banner-topo {{
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    color: white;
    padding: 18px 32px;
    border-radius: 18px;
    margin-bottom: 20px;
    box-shadow: 0 8px 24px rgba(30, 58, 138, 0.18);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}}

.banner-logo-area {{
    display: flex;
    align-items: center;
    gap: 14px;
}}

.banner-logo-texto {{
    font-size: calc({_fonte_base} * 1.6) !important;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

.banner-subtitulo {{
    font-size: calc({_fonte_base} * 0.82) !important;
    opacity: 0.8;
    margin-top: 2px;
}}

.banner-info {{
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
}}

.banner-badge {{
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 10px;
    padding: 6px 16px;
    font-size: calc({_fonte_base} * 0.92) !important;
    font-weight: 600;
    white-space: nowrap;
}}

.banner-badge span {{
    opacity: 0.75;
    font-weight: 400;
    margin-right: 4px;
}}

/* Botões de menu do banner */
div.stButton > button[key^="menu_"],
div.stButton > button[key="btn_alternar"],
div.stButton > button[key="btn_sair"] {{
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    font-size: calc({_fonte_base} * 0.88) !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0 12px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: all 0.2s !important;
    width: 100% !important;
}}

div.stButton > button[key^="menu_"] {{
    background: white !important;
    color: #334155 !important;
    border: 1px solid #cbd5e1 !important;
}}

div.stButton > button[key^="menu_"]:hover {{
    border-color: #2563eb !important;
    color: #1e3a8a !important;
    box-shadow: 0 2px 8px rgba(30,58,138,0.1) !important;
}}

div.stButton > button[key^="menu_"][data-testid="stBaseButton-primary"] {{
    background: #1e3a8a !important;
    color: white !important;
    border-color: #1e3a8a !important;
    box-shadow: 0 2px 8px rgba(30,58,138,0.25) !important;
}}

div.stButton > button[key="btn_alternar"] {{
    background: white !important;
    color: #0f766e !important;
    border: 1px solid #99f6e4 !important;
}}

div.stButton > button[key="btn_alternar"]:hover {{
    background: #f0fdf4 !important;
    border-color: #10b981 !important;
}}

div.stButton > button[key="btn_sair"] {{
    background: white !important;
    color: #dc2626 !important;
    border: 1px solid #fca5a5 !important;
}}

div.stButton > button[key="btn_sair"]:hover {{
    background: #fff1f2 !important;
    border-color: #dc2626 !important;
}}

/* ── BOTÕES DE ACESSIBILIDADE ── */
div.stButton > button[key^="fonte_"] {{
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: 2px solid #cbd5e1 !important;
    background: white !important;
    color: #334155 !important;
    transition: all 0.2s !important;
}}
div.stButton > button[key^="fonte_"][data-testid="stBaseButton-primary"] {{
    background: #1e3a8a !important;
    color: white !important;
    border-color: #1e3a8a !important;
}}

/* Métricas */
.metric-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}

.metric-card {{
    background: white;
    border-radius: 14px;
    padding: 16px 24px;
    flex: 1;
    min-width: 120px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid #e2e8f0;
}}

.metric-card .valor {{
    font-size: calc({_fonte_base} * 1.7) !important;
    font-weight: 800;
    color: #1e3a8a;
}}

.metric-card .label {{
    font-size: calc({_fonte_base} * 0.78) !important;
    color: #64748b;
    margin-top: 2px;
}}

/* Rodapé */
.rodape-container {{
    text-align: center;
    color: #64748b;
    margin-top: 50px;
    font-size: calc({_fonte_base} * 0.88) !important;
    line-height: 1.6;
}}
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# TELA 0: IDENTIFICAÇÃO DO ALUNO
# ==============================================================================
if not st.session_state.nome_aluno:
    st.markdown("<br>", unsafe_allow_html=True)
    if logo_path:
        col_logo_esq, col_logo, col_logo_dir = st.columns([1.6, 1, 1.6])
        with col_logo:
            st.image(logo_path, width=300)
    else:
        st.markdown('<div style="font-size:3rem;font-weight:800;text-align:center;color:#1e3a8a;">🎓 EducaIA</div>', unsafe_allow_html=True)

    st.markdown('<div class="hero-helper">Um ambiente de aprendizagem simples, acolhedor e fácil de usar para acompanhar o progresso do estudante.</div>', unsafe_allow_html=True)

    # Controle de fonte disponível em todas as telas
    _f = st.session_state.tamanho_fonte
    _, col_fonte, _ = st.columns([2, 1, 2])
    with col_fonte:
        fa, fb, fc = st.columns(3)
        with fa:
            if st.button("A", key="fonte_normal", use_container_width=True, type="primary" if _f == "normal" else "secondary", help="Fonte normal"):
                st.session_state.tamanho_fonte = "normal"; st.rerun()
        with fb:
            if st.button("A+", key="fonte_grande", use_container_width=True, type="primary" if _f == "grande" else "secondary", help="Fonte grande"):
                st.session_state.tamanho_fonte = "grande"; st.rerun()
        with fc:
            if st.button("A++", key="fonte_extra", use_container_width=True, type="primary" if _f == "extra" else "secondary", help="Fonte extra grande"):
                st.session_state.tamanho_fonte = "extra"; st.rerun()

    _, col_id, _ = st.columns([1, 1.8, 1])
    with col_id:
        with st.container(border=True):
            st.markdown('<div class="subtitulo-plataforma" style="margin-bottom:0.5rem;">Ambiente de Aprendizagem com IA para a EJA</div>', unsafe_allow_html=True)
            st.markdown('<div class="titulo-seletor" style="font-size:1.35rem; margin-bottom:0.45rem;">👋 Olá! Como você se chama?</div>', unsafe_allow_html=True)
            st.markdown("Digite seu nome para entrar na plataforma e salvar seu progresso.")
            st.markdown("<br>", unsafe_allow_html=True)
            nome_input = st.text_input("Seu nome:", placeholder="Ex: Maria Silva", label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Entrar na plataforma", key="btn_login", type="primary", use_container_width=True):
                nome_limpo = nome_input.strip()
                if not nome_limpo:
                    st.error("Por favor, digite seu nome antes de continuar.")
                else:
                    st.session_state.nome_aluno = nome_limpo
                    st.session_state.progresso_carregado = False
                    st.rerun()
    st.stop()

# Carrega progresso do banco ao identificar o aluno
_carregar_do_banco()

# ==============================================================================
# FLUXO 1: AMBIENTE DE BOAS-VINDAS / SELEÇÃO INICIAL
# ==============================================================================
if not st.session_state.iniciado:
    st.markdown("<br>", unsafe_allow_html=True)
    if logo_path:
        col_logo_esq, col_logo, col_logo_dir = st.columns([1.6, 1, 1.6])
        with col_logo:
            st.image(logo_path, width=300)
    else:
        st.markdown('<div style="font-size:3rem; font-weight:800; text-align:center; color:#1e3a8a;">🎓 EducaIA</div>', unsafe_allow_html=True)

    st.markdown('<div class="hero-helper">Escolha a matéria, defina o ano escolar e entre na sala virtual em uma tela mais limpa e centralizada.</div>', unsafe_allow_html=True)
    margem_esq, painel_central, margem_dir = st.columns([0.5, 2.8, 0.5])
    with painel_central:
        with st.container(border=True):
            st.markdown('<div class="subtitulo-plataforma" style="margin-bottom:0.5rem;">Ambiente de Aprendizagem com Inteligência Artificial para a EJA</div>', unsafe_allow_html=True)
            st.markdown('<div class="titulo-seletor">Olá! Vamos organizar sua aula de hoje?</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="subtitulo-seletor">1. Escolha a Matéria:</div>', unsafe_allow_html=True)
            col_geo, col_hist, col_ef = st.columns(3)
            
            with col_geo:
                tipo_geo = "primary" if st.session_state.disciplina == "Geografia" else "secondary"
                if st.button("🌎\n\nGEOGRAFIA", key="card_geo", type=tipo_geo, use_container_width=True):
                    st.session_state.disciplina = "Geografia"
                    st.session_state.ver_cursos = False
                    st.rerun()
                    
            with col_hist:
                tipo_hist = "primary" if st.session_state.disciplina == "História" else "secondary"
                if st.button("🏛️\n\nHISTÓRIA", key="card_hist", type=tipo_hist, use_container_width=True):
                    st.session_state.disciplina = "História"
                    st.session_state.ver_cursos = False
                    st.rerun()
                    
            with col_ef:
                tipo_ef = "primary" if st.session_state.disciplina == "Educação Física" else "secondary"
                if st.button("🏃‍♂️\n\nEDUCAÇÃO FÍSICA", key="card_ef", type=tipo_ef, use_container_width=True):
                    st.session_state.disciplina = "Educação Física"
                    st.session_state.ver_cursos = False
                    st.rerun()

            # Botão de cursos gratuitos (largura total, separado visualmente)
            st.markdown("<div style='margin-top: 0.6rem;'></div>", unsafe_allow_html=True)
            tipo_cursos = "primary" if st.session_state.ver_cursos else "secondary"
            if st.button("🎓  CURSOS ONLINE GRATUITOS  —  Desenvolva suas habilidades para o mercado de trabalho", key="card_cursos", type=tipo_cursos, use_container_width=True):
                st.session_state.ver_cursos = not st.session_state.ver_cursos
                st.rerun()

            # Página de cursos gratuitos (exibida inline abaixo dos botões)
            if st.session_state.ver_cursos:
                import streamlit.components.v1 as components
                components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
  body { background: transparent; padding: 4px 2px 8px 2px; }
  .cursos-header {
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    border-radius: 18px;
    padding: 18px 22px;
    margin-bottom: 14px;
    color: white;
  }
  .cursos-header h3 { font-size: 1.15rem; font-weight: 800; margin-bottom: 5px; }
  .cursos-header p { font-size: 0.88rem; opacity: 0.88; line-height: 1.4; }
  .curso-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 14px;
    margin-bottom: 14px;
  }
  .curso-card {
    background: white;
    border-radius: 16px;
    border: 1.5px solid #e2e8f0;
    padding: 18px 18px 16px 18px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .curso-card:hover { transform: translateY(-3px); box-shadow: 0 8px 22px rgba(0,0,0,0.11); }
  .cc-emoji { font-size: 2rem; margin-bottom: 7px; }
  .cc-titulo { font-weight: 800; font-size: 0.98rem; color: #1e3a8a; margin-bottom: 6px; line-height: 1.3; }
  .cc-desc { font-size: 0.83rem; color: #475569; line-height: 1.45; margin-bottom: 10px; flex-grow: 1; }
  .cc-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
  .cc-tag { background: #f1f5f9; color: #334155; font-size: 0.72rem; border-radius: 20px; padding: 2px 9px; font-weight: 600; }
  .cc-link {
    display: block;
    background: #1e3a8a;
    color: white;
    text-decoration: none;
    border-radius: 10px;
    padding: 9px 14px;
    font-size: 0.85rem;
    font-weight: 700;
    text-align: center;
    transition: background 0.2s;
  }
  .cc-link:hover { background: #2563eb; color: white; }
  .dica-box {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 14px;
    padding: 13px 16px;
    font-size: 0.86rem;
    color: #166534;
    line-height: 1.5;
  }
</style>
</head>
<body>

<div class="cursos-header">
  <h3>🎓 Cursos Online Gratuitos com Certificado</h3>
  <p>Plataformas confiáveis para você desenvolver novas habilidades e se preparar para o mercado de trabalho — sem pagar nada!</p>
</div>

<div class="curso-grid">

  <div class="curso-card">
    <div class="cc-emoji">🟠</div>
    <div class="cc-titulo">Fundação Bradesco — Escola Virtual</div>
    <div class="cc-desc">Mais de 300 cursos gratuitos em tecnologia, administração, finanças e idiomas. Certificado reconhecido pelo mercado.</div>
    <div class="cc-tags">
      <span class="cc-tag">Tecnologia</span>
      <span class="cc-tag">Administração</span>
      <span class="cc-tag">Finanças</span>
      <span class="cc-tag">Idiomas</span>
    </div>
    <a class="cc-link" href="https://www.ev.org.br/cursos" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🟢</div>
    <div class="cc-titulo">Escola Virtual Gov</div>
    <div class="cc-desc">Plataforma oficial do Governo Federal com centenas de cursos em gestão pública, cidadania, direitos e tecnologia.</div>
    <div class="cc-tags">
      <span class="cc-tag">Cidadania</span>
      <span class="cc-tag">Gestão</span>
      <span class="cc-tag">Direitos</span>
      <span class="cc-tag">Governo</span>
    </div>
    <a class="cc-link" href="https://www.escolavirtual.gov.br/catalogo" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🔵</div>
    <div class="cc-titulo">Aprenda Mais — MEC</div>
    <div class="cc-desc">Portal do Ministério da Educação com cursos e recursos de aprendizagem para todas as idades, com foco na educação básica e profissional.</div>
    <div class="cc-tags">
      <span class="cc-tag">Educação</span>
      <span class="cc-tag">MEC</span>
      <span class="cc-tag">Profissionalizante</span>
    </div>
    <a class="cc-link" href="https://aprendamais.mec.gov.br/" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🟡</div>
    <div class="cc-titulo">SEBRAE — Cursos Gratuitos</div>
    <div class="cc-desc">Cursos práticos para quem quer empreender ou crescer profissionalmente: vendas, marketing digital, finanças para negócios e muito mais.</div>
    <div class="cc-tags">
      <span class="cc-tag">Empreendedorismo</span>
      <span class="cc-tag">Vendas</span>
      <span class="cc-tag">Marketing</span>
      <span class="cc-tag">Negócios</span>
    </div>
    <a class="cc-link" href="https://am.loja.sebrae.com.br/cursos/cursos-online" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🟣</div>
    <div class="cc-titulo">SENAI — EAD Gratuito</div>
    <div class="cc-desc">Cursos profissionalizantes em áreas industriais: elétrica, mecânica, soldagem, automação, saúde e segurança do trabalho.</div>
    <div class="cc-tags">
      <span class="cc-tag">Indústria</span>
      <span class="cc-tag">Elétrica</span>
      <span class="cc-tag">Segurança</span>
      <span class="cc-tag">Técnico</span>
    </div>
    <a class="cc-link" href="https://online.senai.br/cursos/gratuitos" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🔴</div>
    <div class="cc-titulo">Google Ateliê Digital</div>
    <div class="cc-desc">Aprenda marketing digital, ferramentas Google e habilidades para trabalhar ou empreender na internet. Certificado Google.</div>
    <div class="cc-tags">
      <span class="cc-tag">Marketing Digital</span>
      <span class="cc-tag">Internet</span>
      <span class="cc-tag">Tecnologia</span>
    </div>
    <a class="cc-link" href="https://learndigital.withgoogle.com/ateliedigital" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">⚫</div>
    <div class="cc-titulo">Vida e Dinheiro — Gov</div>
    <div class="cc-desc">Educação financeira acessível: como controlar o orçamento, sair das dívidas e planejar o futuro. Ideal para adultos trabalhadores.</div>
    <div class="cc-tags">
      <span class="cc-tag">Finanças</span>
      <span class="cc-tag">Orçamento</span>
      <span class="cc-tag">Planejamento</span>
    </div>
    <a class="cc-link" href="https://www.vidaedinheiro.gov.br/" target="_blank">→ Acessar cursos</a>
  </div>

  <div class="curso-card">
    <div class="cc-emoji">🌐</div>
    <div class="cc-titulo">Curso em Vídeo</div>
    <div class="cc-desc">Cursos gratuitos de informática, Python, HTML e banco de dados com linguagem simples — ideal para iniciantes na tecnologia.</div>
    <div class="cc-tags">
      <span class="cc-tag">Informática</span>
      <span class="cc-tag">Programação</span>
      <span class="cc-tag">Iniciante</span>
    </div>
    <a class="cc-link" href="https://www.cursoemvideo.com/" target="_blank">→ Acessar cursos</a>
  </div>

</div>

<div class="dica-box">
  💡 <strong>Dica do professor:</strong> Escolha 1 ou 2 cursos que combinam com sua área de trabalho ou com o emprego que você sonha. Ter um certificado faz diferença no currículo!
</div>

</body>
</html>
                """, height=780, scrolling=False)
                st.markdown("<br>", unsafe_allow_html=True)

            st.markdown('<div class="subtitulo-seletor">2. Selecione seu Ano Escolar:</div>', unsafe_allow_html=True)
            ano_selecionado = st.selectbox(
                "Ano Letivo:",
                ["EJA 6º e 7º Ano", "EJA 8º e 9º Ano"],
                label_visibility="collapsed",
                key="seletor_ano_eja"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 ENTRAR NA SALA DE AULA VIRTUAL", use_container_width=True, type="primary", key="entrar_sala"):
                st.session_state.nivel = ano_selecionado
                st.session_state.iniciado = True
                st.rerun()


# ==============================================================================
# FLUXO 2: SALA DE AULA INTERNA ATIVA
# ==============================================================================
else:
    # Recuperação rápida das variáveis de sessão
    disciplina_ativa = st.session_state.disciplina
    nivel_ativo = st.session_state.nivel

    # Inicialização do menu
    if "opcao_menu" not in st.session_state:
        st.session_state.opcao_menu = "Tirar Dúvidas (Chat)"

    # Ícone da disciplina ativa
    icones = {"Geografia": "🌎", "História": "🏛️", "Educação Física": "🏃‍♂️"}
    icone_ativo = icones.get(disciplina_ativa, "📚")

    # ---------------- BANNER HORIZONTAL DO TOPO ----------------
    nome_exibido = st.session_state.nome_aluno
    st.markdown(f"""
    <div class="banner-topo">
        <div class="banner-logo-area">
            <div style="font-size:2.2rem;">🎓</div>
            <div>
                <div class="banner-logo-texto">EducaIA</div>
                <div class="banner-subtitulo">Assistente Virtual Educacional · EJA</div>
            </div>
        </div>
        <div class="banner-info">
            <div class="banner-badge"><span>Aluno</span>👤 {nome_exibido}</div>
            <div class="banner-badge"><span>Matéria</span>{icone_ativo} {disciplina_ativa}</div>
            <div class="banner-badge"><span>Turma</span>🎯 {nivel_ativo}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- LINHA DE NAVEGAÇÃO ----------------
    nav1, nav2, nav3, nav4, nav5, nav_gap, nav_fonte, nav_limpar, nav_trocar, nav_sair = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 0.1, 1.1, 0.5, 1.1, 0.5])

    def _tipo_menu(nome):
        return "primary" if st.session_state.opcao_menu == nome else "secondary"

    with nav1:
        if st.button("💬 Professor", key="menu_chat", use_container_width=True, type=_tipo_menu("Tirar Dúvidas (Chat)")):
            st.session_state.opcao_menu = "Tirar Dúvidas (Chat)"
            st.rerun()
    with nav2:
        if st.button("📝 Exercícios", key="menu_exerc", use_container_width=True, type=_tipo_menu("Resolver Questões")):
            st.session_state.opcao_menu = "Resolver Questões"
            st.rerun()
    with nav3:
        if st.button("🎯 Simulados", key="menu_simul", use_container_width=True, type=_tipo_menu("Fazer Simulado")):
            st.session_state.opcao_menu = "Fazer Simulado"
            st.rerun()
    with nav4:
        if st.button("📚 Biblioteca", key="menu_bibli", use_container_width=True, type=_tipo_menu("Textos de Estudo")):
            st.session_state.opcao_menu = "Textos de Estudo"
            st.rerun()
    with nav5:
        if st.button("🛠️ Ferramentas", key="menu_ferr", use_container_width=True, type=_tipo_menu("Ferramentas Úteis")):
            st.session_state.opcao_menu = "Ferramentas Úteis"
            st.rerun()
    with nav_fonte:
        _f = st.session_state.tamanho_fonte
        f1, f2, f3 = st.columns(3)
        with f1:
            if st.button("A", key="fonte_normal", use_container_width=True,
                         type="primary" if _f == "normal" else "secondary",
                         help="Fonte normal"):
                st.session_state.tamanho_fonte = "normal"
                st.rerun()
        with f2:
            if st.button("A+", key="fonte_grande", use_container_width=True,
                         type="primary" if _f == "grande" else "secondary",
                         help="Fonte grande"):
                st.session_state.tamanho_fonte = "grande"
                st.rerun()
        with f3:
            if st.button("A++", key="fonte_extra", use_container_width=True,
                         type="primary" if _f == "extra" else "secondary",
                         help="Fonte extra grande"):
                st.session_state.tamanho_fonte = "extra"
                st.rerun()
    with nav_limpar:
        if st.button("🗑️", key="menu_limpar", use_container_width=True, help="Limpar conversa"):
            st.session_state.historico_chat = []
            st.rerun()
    with nav_trocar:
        if st.button("🔄 Trocar Turma", key="btn_alternar", use_container_width=True):
            st.session_state.iniciado = False
            st.session_state.historico_chat = []
            st.rerun()
    with nav_sair:
        if st.button("🚪", key="btn_sair", use_container_width=True, help="Sair da conta"):
            for key in ["nome_aluno", "iniciado", "historico_chat", "progresso_carregado",
                        "prog_perguntas", "prog_exercicios", "prog_textos", "prog_dias",
                        "prog_ultima_data", "opcao_menu"]:
                st.session_state.pop(key, None)
            st.rerun()

    opcao_menu = st.session_state.opcao_menu

    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:0.78rem; padding: 4px 0 8px 0;">
        EducaIA © 2026 &nbsp;·&nbsp; Coord. Pedagógica: Prof.ª Ms. Andreia Crizostomo Barata &nbsp;·&nbsp; Arquitetura: Prof. Dr. Nicanor Tiago Bueno Antunes
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- MÉTRICAS DE PROGRESSO (GAMIFICAÇÃO) ----------------
    _p = st.session_state.prog_perguntas
    _e = st.session_state.prog_exercicios
    _t = st.session_state.prog_textos
    _d = st.session_state.prog_dias

    # Nível baseado na soma de atividades
    _total = _p + _e + _t
    if _total < 5:
        _nivel_txt = "🌱 Iniciante"
    elif _total < 15:
        _nivel_txt = "📘 Aprendiz"
    elif _total < 30:
        _nivel_txt = "🏅 Intermediário"
    else:
        _nivel_txt = "🌟 Avançado"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="valor">{_p}</div>
            <div class="label">💬 Perguntas feitas</div>
        </div>
        <div class="metric-card">
            <div class="valor">{_e}</div>
            <div class="label">📝 Exercícios feitos</div>
        </div>
        <div class="metric-card">
            <div class="valor">{_t}</div>
            <div class="label">📚 Textos lidos</div>
        </div>
        <div class="metric-card">
            <div class="valor">{_d} {'dia' if _d == 1 else 'dias'}</div>
            <div class="label">🔥 Sequência</div>
        </div>
        <div class="metric-card">
            <div class="valor" style="font-size:1.2rem;">{_nivel_txt}</div>
            <div class="label">🎮 Seu nível</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # =====================================================
    # CONTEÚDO PRINCIPAL
    # =====================================================

    if opcao_menu == "Tirar Dúvidas (Chat)":

        st.markdown(f"### 💬 Tire suas dúvidas de {disciplina_ativa}")
        st.write(
            "Escreva sua pergunta aqui embaixo, como se estivesse conversando com o seu professor em sala de aula!"
        )

        for mensagem in st.session_state.historico_chat:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])

        entrada_aluno = st.chat_input(
            "Ex: Professor, o que é globalização e como ela afeta meu emprego?"
        )

        if entrada_aluno:

            with st.chat_message("user"):
                st.markdown(entrada_aluno)

            st.session_state.historico_chat.append(
                {
                    "role": "user",
                    "content": entrada_aluno
                }
            )
            st.session_state.prog_perguntas += 1
            salvar_progresso(st.session_state.nome_aluno)

            prompt_formatado = construir_prompt_eja(
                f"Dúvida apresentada pelo estudante: {entrada_aluno}"
            )

            resposta_ia = consultar_ia(
                prompt_formatado,
                "O tutor está elaborando uma explicação detalhada..."
            )

            if resposta_ia:

                with st.chat_message("assistant"):
                    st.markdown(resposta_ia)

                st.session_state.historico_chat.append(
                    {
                        "role": "assistant",
                        "content": resposta_ia
                    }
                )

    elif opcao_menu == "Resolver Questões":

        st.markdown("### 📝 Exercício de Fixação Inteligente")

        st.write(
            "Pratique respondendo questões criadas na hora pela Inteligência Artificial."
        )

        tema_escolhido = st.text_input(
            "Deseja praticar algum assunto específico?",
            placeholder="Ex: Relevo, Direitos Trabalhistas, Ginástica"
        )

        if st.button(
            "Gerar Nova Questão",
            type="primary",
            use_container_width=True
        ):

            comando = (
                f"Formule uma questão pedagógica de múltipla escolha sobre "
                f"'{tema_escolhido if tema_escolhido else 'assuntos gerais da ementa'}' "
                f"com alternativas de A até D. "
                f"Encerre obrigatoriamente com a tag [GABARITO] "
                f"seguida da resposta correta e justificativa."
            )

            resposta_questao = consultar_ia(
                construir_prompt_eja(comando),
                "Redigindo uma questão..."
            )

            if resposta_questao:
                st.session_state.prog_exercicios += 1
                salvar_progresso(st.session_state.nome_aluno)

                if "[GABARITO]" in resposta_questao:

                    pergunta, gabarito = resposta_questao.split("[GABARITO]")

                    st.markdown(pergunta)

                    with st.expander(
                        "👀 Verificar Resposta Correta (Gabarito)"
                    ):
                        st.markdown(gabarito)

                else:
                    st.markdown(resposta_questao)

    elif opcao_menu == "Fazer Simulado":

        st.markdown("### ⏱️ Teste de Conhecimento (Simulado)")

        st.write(
            "Monitore seu progresso respondendo a pequenos testes estruturados."
        )

        tamanho_simulado = st.selectbox(
            "Escolha a quantidade de questões do seu teste:",
            [3, 5, 10]
        )

        if st.button(
            "Montar Meu Simulado",
            type="primary",
            use_container_width=True
        ):

            comando = (
                f"Elabore um mini simulado contendo exatamente "
                f"{tamanho_simulado} questões de múltipla escolha. "
                f"No final inclua a marcação [GABARITO_SIMULADO]."
            )

            resposta_simulado = consultar_ia(
                construir_prompt_eja(comando),
                "Montando seu simulado..."
            )

            if resposta_simulado:
                st.session_state.prog_exercicios += tamanho_simulado
                salvar_progresso(st.session_state.nome_aluno)

                if "[GABARITO_SIMULADO]" in resposta_simulado:

                    perguntas, gabarito = resposta_simulado.split(
                        "[GABARITO_SIMULADO]"
                    )

                    st.markdown(perguntas)

                    with st.expander(
                        "📝 Conferir Respostas e Correções"
                    ):
                        st.markdown(gabarito)

                else:
                    st.markdown(resposta_simulado)

    # ---------------- CONTEÚDO 4: TEXTOS DE ESTUDO ----------------
    elif opcao_menu == "Textos de Estudo":

        # Abas da biblioteca
        aba_resumos, aba_busca, aba_videos, aba_glossario = st.tabs([
            "📖 Resumos", "🔍 Busca Livre", "▶️ Vídeos", "📝 Glossário"
        ])

        banco_temas = {
            "Geografia": [
                "Cartografia e Orientação no Espaço",
                "A Globalização no Nosso Dia a Dia",
                "Climas do Brasil e Mudanças Ambientais",
                "A Urbanização e a Vida nas Cidades",
                "A Dinâmica Econômica da Região Norte",
                "Biomas Brasileiros e Meio Ambiente",
                "População Brasileira e Diversidade Cultural",
            ],
            "História": [
                "O Cotidiano no Brasil Colônia",
                "O Processo de Independência e o Povo",
                "A Proclamação da República",
                "Era Vargas e a Criação das Leis Trabalhistas",
                "A Ditadura Militar no Brasil",
                "A Redemocratização e a Constituição de 1988",
                "Povos Indígenas e Africanos no Brasil",
            ],
            "Educação Física": [
                "Qualidade de Vida, Lazer e Saúde",
                "Capacidades Físicas no Trabalho Diário",
                "A Importância dos Esportes Coletivos",
                "Combate ao Sedentarismo na Vida Adulta",
                "Alimentação Saudável e Atividade Física",
                "Primeiros Socorros no Dia a Dia",
            ]
        }

        videos_por_disciplina = {
            "Geografia": [
                {"titulo": "O que é Globalização?", "url": "https://www.youtube.com/embed/cHaFaEZwtSY"},
                {"titulo": "Biomas do Brasil", "url": "https://www.youtube.com/embed/A4h5oEBSGQE"},
                {"titulo": "Urbanização Brasileira", "url": "https://www.youtube.com/embed/2JZB3V2FMQU"},
                {"titulo": "Cartografia para iniciantes", "url": "https://www.youtube.com/embed/mHnwvSnSBtQ"},
            ],
            "História": [
                {"titulo": "Brasil Colônia resumido", "url": "https://www.youtube.com/embed/KjsWCkYrGSA"},
                {"titulo": "Independência do Brasil", "url": "https://www.youtube.com/embed/LjFTy1QTVSQ"},
                {"titulo": "Era Vargas e as leis trabalhistas", "url": "https://www.youtube.com/embed/wNPPQPRRpW8"},
                {"titulo": "Ditadura Militar no Brasil", "url": "https://www.youtube.com/embed/yv3bFhi4HYs"},
            ],
            "Educação Física": [
                {"titulo": "Sedentarismo e suas consequências", "url": "https://www.youtube.com/embed/aUaInS6HIGo"},
                {"titulo": "Como calcular o IMC", "url": "https://www.youtube.com/embed/p0bPE49hCnk"},
                {"titulo": "Alongamento para iniciantes", "url": "https://www.youtube.com/embed/Eh00_rniF8E"},
                {"titulo": "Primeiros socorros básicos", "url": "https://www.youtube.com/embed/wuYEKZ5bBqI"},
            ],
        }

        termos_por_disciplina = {
            "Geografia": ["Globalização", "Urbanização", "Bioma", "Cartografia", "Migração", "PIB", "Latitude", "Longitude"],
            "História": ["Colonização", "Escravidão", "República", "Ditadura", "Constituição", "Imperialismo", "Abolição", "Democracia"],
            "Educação Física": ["Sedentarismo", "IMC", "Metabolismo", "Frequência Cardíaca", "Ergonomia", "Coordenação Motora", "Flexibilidade", "Aeróbico"],
        }

        # --- ABA 1: RESUMOS ---
        with aba_resumos:
            st.markdown("#### Selecione um tema para gerar um resumo contextualizado:")
            st.markdown("<br>", unsafe_allow_html=True)
            for tema in banco_temas[disciplina_ativa]:
                col_nome, col_acao = st.columns([3, 1])
                with col_nome:
                    st.markdown(f"📖 **{tema}**")
                with col_acao:
                    if st.button("Ler Resumo", key=f"lei_{tema}", use_container_width=True):
                        prompt_resumo = construir_prompt_eja(
                            f"Elabore um texto explicativo, introdutório e muito prático sobre o tema: {tema}."
                        )
                        texto_explicativo = consultar_ia(prompt_resumo, f"Construindo texto sobre {tema}...")
                        if texto_explicativo:
                            st.session_state.prog_textos += 1
                            salvar_progresso(st.session_state.nome_aluno)
                            st.success(f"### 📖 {tema}")
                            st.markdown(texto_explicativo)

        # --- ABA 2: BUSCA LIVRE ---
        with aba_busca:
            st.markdown("#### Pesquise qualquer tema que quiser estudar:")
            busca_tema = st.text_input(
                "Tema:",
                placeholder=f"Ex: Por que chove tanto na Amazônia?",
                label_visibility="collapsed",
                key="busca_livre_input"
            )
            if st.button("🔍 Buscar e Gerar Texto", key="btn_busca_livre", type="primary", use_container_width=False):
                if not busca_tema.strip():
                    st.warning("Digite um tema para pesquisar.")
                else:
                    prompt_busca = construir_prompt_eja(
                        f"O aluno quer aprender sobre: '{busca_tema}'. "
                        f"Explique de forma simples, prática e contextualizada para a realidade do aluno da EJA. "
                        f"Relacione com o cotidiano sempre que possível."
                    )
                    texto_busca = consultar_ia(prompt_busca, f"Pesquisando sobre '{busca_tema}'...")
                    if texto_busca:
                        st.session_state.prog_textos += 1
                        salvar_progresso(st.session_state.nome_aluno)
                        st.success(f"### 🔍 {busca_tema}")
                        st.markdown(texto_busca)

        # --- ABA 3: VÍDEOS ---
        with aba_videos:
            st.markdown("#### Vídeos educativos selecionados para sua disciplina:")
            st.markdown("<br>", unsafe_allow_html=True)
            videos = videos_por_disciplina.get(disciplina_ativa, [])
            cols = st.columns(2)
            for i, video in enumerate(videos):
                with cols[i % 2]:
                    st.markdown(f"**{video['titulo']}**")
                    st.markdown(
                        f'<iframe width="100%" height="215" src="{video["url"]}" '
                        f'frameborder="0" allowfullscreen></iframe>',
                        unsafe_allow_html=True
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

        # --- ABA 4: GLOSSÁRIO ---
        with aba_glossario:
            st.markdown("#### Clique em um termo para ver sua explicação:")
            st.markdown("<br>", unsafe_allow_html=True)
            termos = termos_por_disciplina.get(disciplina_ativa, [])
            cols_g = st.columns(4)
            for i, termo in enumerate(termos):
                with cols_g[i % 4]:
                    if st.button(f"📝 {termo}", key=f"gloss_{termo}", use_container_width=True):
                        prompt_gloss = construir_prompt_eja(
                            f"Explique o termo '{termo}' de forma simples e direta para um aluno da EJA. "
                            f"Use no máximo 5 linhas, com um exemplo do dia a dia."
                        )
                        explicacao = consultar_ia(prompt_gloss, f"Explicando '{termo}'...")
                        if explicacao:
                            st.info(f"**{termo}**\n\n{explicacao}")


    # ---------------- CONTEÚDO 5: FERRAMENTAS PEDAGÓGICAS ----------------
    elif opcao_menu == "Ferramentas Úteis":
        icone_ferr = {"Geografia": "🌎", "História": "🏛️", "Educação Física": "🏃"}.get(disciplina_ativa, "🛠️")
        st.markdown(f"### 🛠️ Ferramentas de {icone_ferr} {disciplina_ativa}")
        st.write("Use calculadoras, mapas, recursos confiáveis e ferramentas com IA para aprender de forma mais prática.")

        # Renderiza diretamente as ferramentas da disciplina ativa (sem abas para outras)
        _mostrar_geo = disciplina_ativa == "Geografia"
        _mostrar_hist = disciplina_ativa == "História"
        _mostrar_edf = disciplina_ativa == "Educação Física"

        if _mostrar_geo:
            st.markdown("#### 🗺️ Mapa interativo")
            st.markdown(
                '<iframe src="https://www.google.com/maps?q=Brasil&output=embed" '
                'width="100%" height="320" style="border:0; border-radius:16px;" '
                'allowfullscreen="" loading="lazy"></iframe>',
                unsafe_allow_html=True
            )

            st.markdown("#### 🕒 Calculadora de fuso horário")
            cidades_fuso = {
                "Manaus (UTC-4)": -4,
                "Brasília (UTC-3)": -3,
                "Rio Branco (UTC-5)": -5,
                "Lisboa (UTC+0)": 0,
                "Londres (UTC+0)": 0,
                "Nova York (UTC-5)": -5,
                "Tóquio (UTC+9)": 9,
            }
            col_fuso1, col_fuso2, col_fuso3 = st.columns([1.2, 1.2, 1])
            with col_fuso1:
                origem_fuso = st.selectbox("Cidade de origem", list(cidades_fuso.keys()), key="geo_fuso_origem")
            with col_fuso2:
                destino_fuso = st.selectbox("Cidade de destino", list(cidades_fuso.keys()), index=1, key="geo_fuso_destino")
            with col_fuso3:
                hora_origem = st.time_input("Horário na origem", value=datetime.time(8, 0), key="geo_hora_origem")

            delta_fuso = cidades_fuso[destino_fuso] - cidades_fuso[origem_fuso]
            minutos_origem = hora_origem.hour * 60 + hora_origem.minute
            minutos_destino = (minutos_origem + delta_fuso * 60) % (24 * 60)
            hora_destino = f"{minutos_destino // 60:02d}:{minutos_destino % 60:02d}"
            st.info(f"Se forem **{hora_origem.strftime('%H:%M')}** em **{origem_fuso}**, serão **{hora_destino}** em **{destino_fuso}**.")

            st.markdown("#### 🔗 Portais e exploração")
            link_geo1, link_geo2, link_geo3 = st.columns(3)
            with link_geo1:
                st.link_button("IBGE Educa", "https://educa.ibge.gov.br/", use_container_width=True)
            with link_geo2:
                st.link_button("INPE", "https://www.gov.br/inpe/pt-br", use_container_width=True)
            with link_geo3:
                st.link_button("Google Earth", "https://earth.google.com/web/", use_container_width=True)

            st.markdown("#### 🧠 Gerador de mapa mental por tema")
            tema_mapa = st.text_input(
                "Tema de Geografia",
                placeholder="Ex: Urbanização brasileira, clima da Amazônia, globalização",
                key="geo_mapa_mental_tema"
            )
            if st.button("Gerar mapa mental", key="geo_btn_mapa_mental", type="primary", use_container_width=True):
                if not tema_mapa.strip():
                    st.warning("Digite um tema para gerar o mapa mental.")
                else:
                    prompt_mapa = construir_prompt_eja(
                        f"Crie um mapa mental textual sobre '{tema_mapa}'. "
                        f"Organize em título central, 4 a 6 ramificações principais e subitens curtos. "
                        f"Use linguagem simples para EJA."
                    )
                    resposta_mapa = consultar_ia(prompt_mapa, "Montando o mapa mental...")
                    if resposta_mapa:
                        st.session_state.prog_textos += 1
                        salvar_progresso(st.session_state.nome_aluno)
                        st.success("Mapa mental gerado:")
                        st.markdown(resposta_mapa)

        if _mostrar_hist:
            st.markdown("#### 📅 O que aconteceu nessa data?")
            data_hist = st.date_input("Escolha uma data", value=datetime.date(1889, 11, 15), key="hist_data_fato")
            if st.button("Explicar essa data", key="hist_btn_data", type="primary", use_container_width=True):
                prompt_data = construir_prompt_eja(
                    f"Explique o que aconteceu na data {data_hist.strftime('%d/%m/%Y')}. "
                    f"Se não houver um fato histórico marcante exato nesse dia, explique acontecimentos próximos e o contexto do período. "
                    f"Use linguagem clara, contextualizada e adulta."
                )
                resposta_data = consultar_ia(prompt_data, "Buscando contexto histórico...")
                if resposta_data:
                    st.session_state.prog_textos += 1
                    salvar_progresso(st.session_state.nome_aluno)
                    st.markdown(resposta_data)

            st.markdown("#### ⏳ Linha do tempo interativa")
            periodo_hist = st.text_input(
                "Período histórico",
                placeholder="Ex: Ditadura Militar no Brasil, Era Vargas, Revolução Francesa",
                key="hist_periodo_linha_tempo"
            )
            if st.button("Gerar linha do tempo", key="hist_btn_linha_tempo", type="primary", use_container_width=True):
                if not periodo_hist.strip():
                    st.warning("Digite um período para gerar a linha do tempo.")
                else:
                    prompt_linha = construir_prompt_eja(
                        f"Crie uma linha do tempo sobre '{periodo_hist}' com 5 a 8 marcos cronológicos. "
                        f"Cada marco deve ter ano/data aproximada e uma explicação curta."
                    )
                    resposta_linha = consultar_ia(prompt_linha, "Organizando a linha do tempo...")
                    if resposta_linha:
                        st.session_state.prog_textos += 1
                        salvar_progresso(st.session_state.nome_aluno)
                        st.markdown(resposta_linha)

            st.markdown("#### 🏛️ Acervos e museus")
            col_hist1, col_hist2, col_hist3 = st.columns(3)
            with col_hist1:
                st.link_button("Biblioteca Nacional", "https://bndigital.bn.gov.br/", use_container_width=True)
            with col_hist2:
                st.link_button("Museu do Ipiranga", "https://museudoipiranga.org.br/", use_container_width=True)
            with col_hist3:
                st.link_button("Brasiliana USP", "https://www.brasiliana.usp.br/", use_container_width=True)

        if _mostrar_edf:
            st.markdown("#### ⚖️ Calculadora de IMC")
            col_imc1, col_imc2 = st.columns(2)
            with col_imc1:
                dado_peso = st.number_input("Peso (kg)", 30.0, 250.0, 70.0, step=0.5, key="edf_peso")
            with col_imc2:
                dado_altura = st.number_input("Altura (m)", 1.00, 2.50, 1.70, step=0.01, key="edf_altura")

            if st.button("Calcular IMC", key="edf_btn_imc", type="primary", use_container_width=True):
                valor_imc = dado_peso / (dado_altura ** 2)
                st.metric(label="Seu IMC", value=f"{valor_imc:.2f}")
                if valor_imc < 18.5:
                    st.warning("Classificação: abaixo do peso recomendado.")
                elif valor_imc < 25:
                    st.success("Classificação: peso saudável.")
                elif valor_imc < 30:
                    st.warning("Classificação: sobrepeso.")
                else:
                    st.error("Classificação: obesidade. Procure orientação profissional para uma avaliação individualizada.")

            st.markdown("#### ❤️ Frequência cardíaca máxima")
            idade_fc = st.number_input("Sua idade", 10, 100, 30, key="edf_idade_fc")
            fc_max = 220 - idade_fc
            st.info(f"Estimativa simples de frequência cardíaca máxima: **{fc_max} bpm**.")
            st.caption("Referência geral usada em contextos educativos: 220 - idade.")

            st.markdown("#### 💧 Calculadora de hidratação diária")
            peso_hid = st.number_input("Peso para hidratação (kg)", 30.0, 250.0, 70.0, step=0.5, key="edf_peso_hid")
            atividade_intensa = st.checkbox("Faço atividade física intensa ou passo muito tempo no calor", key="edf_calor")
            agua_ml = peso_hid * 35 + (500 if atividade_intensa else 0)
            st.info(f"Sugestão diária aproximada: **{agua_ml/1000:.2f} litros de água**.")

            st.markdown("#### 🏋️ Gerador de treino personalizado")
            tempo_treino = st.number_input("Tempo disponível (minutos)", 5, 180, 30, step=5, key="edf_tempo_treino")
            objetivo_treino = st.selectbox(
                "Objetivo principal",
                ["Condicionamento físico", "Emagrecimento", "Mobilidade", "Alongamento", "Saúde e disposição"],
                key="edf_objetivo_treino"
            )
            restricao_treino = st.text_input(
                "Existe alguma limitação ou cuidado?",
                placeholder="Ex: dor no joelho, sedentarismo, treino em casa",
                key="edf_restricao_treino"
            )
            if st.button("Gerar treino com IA", key="edf_btn_treino", type="primary", use_container_width=True):
                prompt_treino = construir_prompt_eja(
                    f"Monte uma rotina simples de atividade física para um aluno da EJA com {tempo_treino} minutos disponíveis. "
                    f"O objetivo é {objetivo_treino}. "
                    f"Considere estas limitações/cuidados: {restricao_treino if restricao_treino.strip() else 'nenhuma informada'}. "
                    f"Organize em aquecimento, parte principal e encerramento, com orientações seguras e linguagem acessível."
                )
                resposta_treino = consultar_ia(prompt_treino, "Montando a rotina de treino...")
                if resposta_treino:
                    st.session_state.prog_exercicios += 1
                    salvar_progresso(st.session_state.nome_aluno)
                    st.markdown(resposta_treino)

# ==============================================================================
# INFORMAÇÕES INSTITUCIONAIS: movidas para o banner de navegação
