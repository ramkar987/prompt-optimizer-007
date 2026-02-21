import streamlit as st
import openai
import json
from datetime import datetime

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="✨ Otimizador de Prompts",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0f1117; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { text-align: center; }
    .subtitle {
        text-align: center; color: #888;
        font-size: 1.05rem; margin-top: -0.8rem; margin-bottom: 1.5rem;
    }
    .empty-state {
        text-align: center; padding: 60px 20px; color: #555;
        border: 2px dashed #333; border-radius: 10px;
    }
    .improvement-box {
        background: #1a1f2e; border-left: 3px solid #4f8ef7;
        padding: 10px 14px; border-radius: 0 6px 6px 0;
        margin-bottom: 8px; font-size: 0.95rem;
    }
    div[data-testid="stTabs"] button { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
if "history"       not in st.session_state: st.session_state.history       = []
if "last_result"   not in st.session_state: st.session_state.last_result   = None
if "last_original" not in st.session_state: st.session_state.last_original = ""

# ─── Modelos disponíveis ───────────────────────────────────────────────────────
MODELS = {
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "Groq": [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ],
}

BASE_URLS = {
    "OpenAI": None,
    "Groq":   "https://api.groq.com/openai/v1",
}

# ─── Optimizer System Prompt ───────────────────────────────────────────────────
OPTIMIZER_SYSTEM_PROMPT = (
    "Você é um engenheiro de prompts especialista. Sua tarefa é otimizar "
    "prompts de IA seguindo as melhores práticas do setor.\n\n"
    "PRINCÍPIOS DE OTIMIZAÇÃO:\n"
    "1. Separar claramente instruções de contexto\n"
    "2. Eliminar ambiguidades sem inventar suposições sobre o objetivo\n"
    "3. Definir saídas específicas e mensuráveis\n"
    "4. Antecipar casos extremos relevantes ao domínio\n"
    "5. Usar linguagem concisa e específica\n"
    "6. Limitar a no máximo 5 regras comportamentais quando adequado\n"
    "7. Priorizar clareza sobre complexidade\n\n"
    "REGRAS ABSOLUTAS — NUNCA VIOLAR:\n"
    "- Não adicionar suposições sobre o OBJETIVO além do que foi explicitamente solicitado\n"
    "- Não perder nenhuma informação específica do prompt original\n"
    "- Não presumir intenção do usuário além do que foi claramente declarado\n"
    "- Eliminar redundâncias e instruções conflitantes\n"
    "- Não desviar o foco do que o usuário realmente quer\n\n"
    "ESTRUTURA DE SAÍDA OBRIGATÓRIA — use exatamente estas 4 seções em markdown:\n\n"
    "# Goal\n"
    "[Objetivo claro e específico — reformule com precisão o que o usuário quer]\n\n"
    "# Return format\n"
    "[OBRIGATÓRIO: descreva o formato esperado da entrega final. "
    "Se o usuário não especificou explicitamente, INFIRA com base no domínio da tarefa. "
    "Exemplo: se é um app → liste os componentes e comportamentos esperados. "
    "Se é um email → descreva estrutura, tom e extensão. "
    "Se é uma análise → descreva seções, profundidade e formato. "
    "NUNCA escreva 'Não especificado' — sempre forneça uma inferência útil e coerente.]\n\n"
    "# Warnings\n"
    "[Restrições importantes e coisas a evitar — máximo 5 itens. "
    "Inclua apenas o que é relevante para o domínio e contexto da tarefa.]\n\n"
    "# Context\n"
    "[Background, caso de uso, domínio, ferramentas ou público-alvo. "
    "Se não houver contexto explícito, infira o mínimo necessário a partir da natureza da tarefa.]\n\n"
    "IMPORTANTE: O objetivo (Goal) deve ser fiel ao prompt original — sem suposições. "
    "Mas Return format e Context PODEM e DEVEM ser enriquecidos com inferências razoáveis "
    "baseadas no domínio da tarefa, para tornar o prompt realmente utilizável.\n\n"
    'Retorne APENAS JSON válido com: {"optimized_prompt": "prompt completo '
    'em markdown com as 4 seções", "improvements": ["melhoria 1", ..., "melhoria N"]}'
)



# ─── Core Functions ────────────────────────────────────────────────────────────
def optimize_prompt(user_prompt: str, api_key: str, model: str, provider: str) -> dict:
    client = openai.OpenAI(
        api_key=api_key,
        base_url=BASE_URLS[provider],
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": OPTIMIZER_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Otimize este prompt:\n\n{user_prompt}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=2500,
    )
    return json.loads(response.choices[0].message.content)


def add_to_history(original: str, result: dict, provider: str, model: str):
    st.session_state.history.insert(0, {
        "id":           len(st.session_state.history) + 1,
        "time":         datetime.now().strftime("%H:%M:%S"),
        "provider":     provider,
        "model":        model,
        "original":     original,
        "optimized":    result["optimized_prompt"],
        "improvements": result["improvements"],
    })


# ─── Header ────────────────────────────────────────────────────────────────────
st.title("✨ Otimizador de Prompts")
st.markdown(
    '<p class="subtitle">Transforme instruções mal definidas em prompts '
    'estruturados e prontos para produção</p>',
    unsafe_allow_html=True,
)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    provider = st.selectbox(
        "🔌 Provedor",
        list(MODELS.keys()),
        help="OpenAI ou Groq (muito mais rápido e econômico).",
    )
    api_key = st.text_input(
        f"🔑 {provider} API Key",
        type="password",
        placeholder="sk-..." if provider == "OpenAI" else "gsk_...",
        help="Nunca armazenada. Usada apenas na sessão atual.",
    )
    model = st.selectbox(
        "🤖 Modelo",
        MODELS[provider],
        help="Modelos mais avançados produzem melhores otimizações.",
    )

    if provider == "Groq":
        st.info("⚡ **Groq** é até 10× mais rápido que OpenAI e tem tier gratuito generoso.")
    else:
        st.info("💡 `gpt-4o-mini` é mais rápido e econômico para testes.")

    st.divider()
    st.header("📋 Histórico da Sessão")

    if st.session_state.history:
        st.caption(f"{len(st.session_state.history)} prompt(s) processado(s)")
        for item in st.session_state.history:
            preview = (item["original"][:50] + "…") if len(item["original"]) > 50 else item["original"]
            label   = f"🕒 {item['time']} · {item['provider']} · {preview}"
            with st.expander(label):
                st.text_area(
                    "Original", value=item["original"], height=80,
                    disabled=True, key=f"hist_orig_{item['id']}",
                )
                st.caption(f"Modelo: `{item['model']}`")
                if st.button("📂 Carregar resultado", key=f"load_{item['id']}"):
                    st.session_state.last_result = {
                        "optimized_prompt": item["optimized"],
                        "improvements":     item["improvements"],
                    }
                    st.session_state.last_original = item["original"]
                    st.rerun()

        if st.button("🗑️ Limpar histórico", use_container_width=True):
            st.session_state.history     = []
            st.session_state.last_result = None
            st.rerun()
    else:
        st.caption("Nenhum prompt processado ainda.")

# ─── Main Layout ───────────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

# LEFT ── Input
with left:
    st.subheader("📝 Prompt Original")

    user_prompt = st.text_area(
        "Insira seu prompt inicial:",
        value=st.session_state.last_original,
        height=300,
        placeholder=(
            "Ex: Me ajuda a escrever um email pedindo aumento para meu chefe.\n\n"
            "Pode ser qualquer instrução que você queira otimizar."
        ),
        help="Cole ou escreva o prompt que deseja otimizar.",
    )
    st.caption(f"📊 {len(user_prompt) if user_prompt else 0} caractere(s)")

    col_opt, col_clr = st.columns([3, 1])
    with col_opt:
        optimize_btn = st.button(
            "✨ Otimizar Prompt",
            type="primary",
            use_container_width=True,
            disabled=not (user_prompt.strip() and api_key.strip()),
        )
    with col_clr:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.last_result   = None
            st.session_state.last_original = ""
            st.rerun()

    if not api_key:
        st.warning("⚠️ Insira sua API Key na barra lateral para continuar.")

    with st.expander("💡 Sobre as 4 seções do prompt otimizado"):
        st.markdown("""
| Seção | O que contém |
|---|---|
| **Goal** | O que a IA deve realizar — objetivo claro |
| **Return format** | Como a resposta deve ser estruturada |
| **Warnings** | Restrições e comportamentos a evitar (máx. 5) |
| **Context** | Background, domínio e informações de apoio |
        """)

# RIGHT ── Output
with right:
    st.subheader("🎯 Prompt Otimizado")

    if optimize_btn and user_prompt.strip() and api_key.strip():
        with st.spinner(f"🔄 Otimizando com {provider} · {model}…"):
            try:
                result = optimize_prompt(user_prompt, api_key, model, provider)
                st.session_state.last_result   = result
                st.session_state.last_original = user_prompt
                add_to_history(user_prompt, result, provider, model)
                st.success(f"✅ Otimizado com sucesso via {provider} · `{model}`!")
            except openai.AuthenticationError:
                st.error("❌ API Key inválida. Verifique suas credenciais.")
            except openai.RateLimitError:
                st.error("⏳ Limite de requisições atingido. Aguarde e tente novamente.")
            except openai.BadRequestError as e:
                st.error(f"❌ Requisição inválida: {e}")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {e}")

    if st.session_state.last_result:
        result = st.session_state.last_result
        tab_view, tab_copy, tab_improve = st.tabs(
            ["📋 Visualização", "📄 Copiar Texto", "📊 Melhorias"]
        )

        with tab_view:
            st.markdown(result["optimized_prompt"])

        with tab_copy:
            st.caption("👆 Clique no ícone de cópia no canto superior direito do bloco abaixo")
            st.code(result["optimized_prompt"], language="markdown")

        with tab_improve:
            st.markdown("**Melhorias aplicadas ao prompt original:**")
            for i, imp in enumerate(result["improvements"], 1):
                st.markdown(
                    f'<div class="improvement-box">✅ <strong>{i}.</strong> {imp}</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            "<div class='empty-state'>"
            "<p style='font-size:2.5rem; margin-bottom:0.5rem'>🚀</p>"
            "<p style='font-size:1.05rem'>Insira um prompt à esquerda e clique em<br>"
            "<strong>✨ Otimizar Prompt</strong> para começar</p>"
            "</div>",
            unsafe_allow_html=True,
        )

# ─── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center; color:#555; font-size:0.82rem'>"
    "✨ Otimizador de Prompts · OpenAI &amp; Groq &nbsp;|&nbsp;"
    "Sua API Key nunca é armazenada ou compartilhada"
    "</div>",
    unsafe_allow_html=True,
)
