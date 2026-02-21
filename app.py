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
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
if "history"      not in st.session_state: st.session_state.history      = []
if "last_result"  not in st.session_state: st.session_state.last_result  = None
if "last_original" not in st.session_state: st.session_state.last_original = ""

# ─── Optimizer System Prompt ───────────────────────────────────────────────────
OPTIMIZER_SYSTEM_PROMPT = """Você é um engenheiro de prompts especialista.
Sua tarefa é otimizar prompts de IA seguindo as melhores práticas do setor.

PRINCÍPIOS DE OTIMIZAÇÃO:
1. Separar claramente instruções de contexto
2. Eliminar ambiguidades sem inventar suposições
3. Definir saídas específicas e mensuráveis
4. Antecipar casos extremos relevantes ao domínio
5. Usar linguagem concisa e específica
6. Limitar a no máximo 5 regras comportamentais quando adequado
7. Priorizar clareza sobre complexidade

REGRAS ABSOLUTAS — NUNCA VIOLAR:
- Não adicionar nenhuma suposição além do que foi explicitamente solicitado
- Não perder nenhuma informação específica do prompt original
- Não presumir intenção do usuário além do que foi claramente declarado
- Eliminar redundâncias e instruções conflitantes
- Não desviar o foco do que o usuário realmente quer

ESTRUTURA DE SAÍDA OBRIGATÓRIA — use exatamente estas 4 seções em markdown:

# Goal
[Objetivo claro e específico — o que a IA deve realizar]

# Return format
[Estrutura do resultado — formato, extensão, elementos obrigatórios]

# Warnings
[Restrições importantes e coisas a evitar — máximo 5 itens]

# Context
[Background, caso de uso, domínio ou público-alvo, se fornecidos]

IMPORTANTE: Baseie-se SOMENTE nas informações do prompt original.
Se uma seção não tiver dados suficientes, escreva uma nota mínima indicando isso.

Retorne APENAS JSON válido com:
{
  "optimized_prompt": "prompt completo em markdown com as 4 seções",
  "improvements": ["melhoria 1", "melhoria 2", ..., "melhoria N"]  ← máximo 5
}"""

# ─── Core Function ─────────────────────────────────────────────────────────────
def optimize_prompt(user_prompt: str, api_key: str, model: str) -> dict:
    client = openai.OpenAI(api_key=api_key)
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


def add_to_history(original: str, result: dict):
    st.session_state.history.insert(0, {
        "id":          len(st.session_state.history) + 1,
        "time":        datetime.now().strftime("%H:%M:%S"),
        "original":    original,
        "optimized":   result["optimized_prompt"],
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

    api_key = st.text_input(
        "🔑 OpenAI API Key", type="password", placeholder="sk-...",
        help="Nunca armazenada. Usada apenas na sessão atual.",
    )
    model = st.selectbox(
        "🤖 Modelo", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        help="gpt-4o oferece os melhores resultados.",
    )
    st.info("💡 `gpt-4o-mini` é mais rápido e econômico para testes.")

    st.divider()
    st.header("📋 Histórico da Sessão")

    if st.session_state.history:
        st.caption(f"{len(st.session_state.history)} prompt(s) processado(s)")
        for item in st.session_state.history:
            preview = (item["original"][:55] + "…") if len(item["original"]) > 55 else item["original"]
            with st.expander(f"🕒 {item['time']} · {preview}"):
                st.text_area("Original", value=item["original"], height=80,
                             disabled=True, key=f"hist_orig_{item['id']}")
                if st.button("📂 Carregar resultado", key=f"load_{item['id']}"):
                    st.session_state.last_result = {
                        "optimized_prompt": item["optimized"],
                        "improvements":     item["improvements"],
                    }
                    st.session_state.last_original = item["original"]
                    st.rerun()

        if st.button("🗑️ Limpar histórico", use_container_width=True):
            st.session_state.history = []
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
    )
    st.caption(f"📊 {len(user_prompt) if user_prompt else 0} caractere(s)")

    col_opt, col_clr = st.columns([3, 1])
    with col_opt:
        optimize_btn = st.button(
            "✨ Otimizar Prompt", type="primary", use_container_width=True,
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
| **Goal** | O que a IA deve realizar |
| **Return format** | Como a resposta deve ser estruturada |
| **Warnings** | Restrições e comportamentos a evitar |
| **Context** | Background, domínio e informações de apoio |
        """)

# RIGHT ── Output
with right:
    st.subheader("🎯 Prompt Otimizado")

    if optimize_btn and user_prompt.strip() and api_key.strip():
        with st.spinner("🔄 Otimizando com IA…"):
            try:
                result = optimize_prompt(user_prompt, api_key, model)
                st.session_state.last_result   = result
                st.session_state.last_original = user_prompt
                add_to_history(user_prompt, result)
                st.success("✅ Prompt otimizado com sucesso!")
            except openai.AuthenticationError:
                st.error("❌ API Key inválida. Verifique suas credenciais.")
            except openai.RateLimitError:
                st.error("⏳ Limite de requisições atingido. Aguarde e tente novamente.")
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
            st.caption("👆 Clique no ícone de cópia no canto superior direito")
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
            '''<div class="empty-state">
                <p style="font-size:2.5rem">🚀</p>
                <p>Insira um prompt à esquerda e clique em<br>
                <strong>✨ Otimizar Prompt</strong> para começar</p>
            </div>''',
            unsafe_allow_html=True,
        )

# ─── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    """<div style="text-align:center;color:#555;font-size:0.82rem">
        ✨ Otimizador de Prompts · Powered by OpenAI &nbsp;|&nbsp;
        Sua API Key nunca é armazenada ou compartilhada
    </div>""",
    unsafe_allow_html=True,
)
