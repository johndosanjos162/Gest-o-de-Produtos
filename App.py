import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# Configurações iniciais
st.set_page_config(layout="wide", page_title="Cyber ERP | Security & Operations", page_icon="⚡")

# Conexão com o Supabase
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar ao Supabase: {e}")
    st.stop()

# Controle de sessão
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background: #0b1120; padding: 2.5rem; border-radius: 16px; box-shadow: 0 15px 35px rgba(0,0,0,0.6); border: 1px solid rgba(56, 189, 248, 0.3);">
                <h2 style="text-align: center; color: #38bdf8; margin-bottom: 25px; font-weight: 800;">⚡ ACESSO RESTRITO</h2>
        """, unsafe_allow_html=True)
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            if botao_login:
                if usuario == "admin" and senha == "admin123":
                    st.session_state.autenticado = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.autenticado:
    tela_login()
    st.stop()

def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados de {nome_tabela}: {e}")
        return pd.DataFrame()

df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_fornecedores = carregar_dados_tabela("fornecedores")

tab_estoque, tab_vendas, tab_financeiro, tab_fornecedores = st.tabs([
    "📦 Estoque", "🛒 Vendas", "💰 Financeiro", "🤝 Fornecedores"
])

# Aba 1: Estoque
with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01)
            with col2:
                preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.01)
                qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo", min_value=0, step=1)
            
            btn_adicionar = st.form_submit_button("Cadastrar Produto")
            if btn_adicionar and nome:
                try:
                    supabase.table("estoque").insert({
                        "produto": nome.strip(),
                        "categoria": categoria,
                        "quantidade": int(qtd),
                        "limite_minimo": int(limite),
                        "valor_unitario": float(preco_venda),
                        "preco_custo": float(preco_custo)
                    }).execute()
                    st.success("✅ Produto cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar produto: {e}")

    # Exibição do estoque com margem de lucro
    dados_est = df_estoque.copy()
    if not dados_est.empty:
        dados_est['Lucro Estimado (Unit.)'] = dados_est['Valor Unitário'] - dados_est['preco_custo']
        dados_est['Margem (%)'] = ((dados_est['Valor Unitário'] - dados_est['preco_custo']) / dados_est['preco_custo']) * 100
        st.subheader("Estoque Atual")
        st.dataframe(dados_est, use_container_width=True, hide_index=True)

# Aba 2: Vendas
with tab_vendas:
    st.subheader("🛒 Registro de Vendas")
    with st.form("form_venda"):
        if not df_estoque.empty:
            prod_venda = st.selectbox("Produto Vendido", df_estoque['Produto'].tolist())
            qtd_venda = st.number_input("Quantidade Vendida", min_value=1, step=1)
            btn_venda = st.form_submit_button("Registrar Venda")
            
            if btn_venda:
                item_est = df_estoque[df_estoque['Produto'] == prod_venda].iloc[0]
                item_id = item_est['id']
                estoque_atual = int(item_est['Quantidade'])
                valor_unit = float(item_est['Valor Unitário'])
                custo_unit = float(item_est['preco_custo'])
                
                if qtd_venda <= estoque_atual:
                    novo_estoque = estoque_atual - qtd_venda
                    vlr_total = qtd_venda * valor_unit
                    lucro_venda = (valor_unit - custo_unit) * qtd_venda
                    data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    try:
                        supabase.table("estoque").update({"quantidade": novo_estoque}).eq("id", item_id).execute()
                        supabase.table("vendas").insert({
                            "data": data_str,
                            "produto": prod_venda,
                            "quantidade": int(qtd_venda),
                            "valor_total": float(vlr_total),
                            "lucro": float(lucro_venda)
                        }).execute()
                        supabase.table("financeiro").insert({
                            "data": data_str,
                            "descricao": f"Venda: {prod_venda}",
                            "tipo": "Entrada",
                            "valor": float(vlr_total)
                        }).execute()
                        st.success("Venda registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar venda: {e}")
                else:
                    st.error("Estoque insuficiente!")
        else:
            st.info("Cadastre produtos antes de registrar vendas.")

    # Histórico de vendas com lucro
    if not df_vendas.empty:
        st.subheader("Histórico de Vendas")
        st.dataframe(df_vendas[['Data', 'Produto', 'Quantidade', 'Valor Total', 'lucro']], use_container_width=True, hide_index=True)

# Aba 3: Financeiro
with tab_financeiro:
    st.subheader("💰 Controle Financeiro")
    dados_fin = df_financeiro.copy()
    if not dados_fin.empty:
        entradas = dados_fin[dados_fin['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = dados_fin[dados_fin['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📥 Total Entradas", f"R$ {entradas:.2f}")
        c2.metric("📤 Total Saídas", f"R$ {saidas:.2f}")
        c3.metric("💳 Saldo Atual", f"R$ {saldo:.2f}")
        
        # Calcular Lucro Total das Vendas registradas
        lucro_total = df_vendas['lucro'].sum() if not df_vendas.empty else 0.0
        st.metric("📈 Lucro Total Acumulado", f"R$ {lucro_total:.2f}")

# Aba 4: Fornecedores
with tab_fornecedores:
    st.subheader("🤝 Cadastro de Fornecedores")
    if not df_fornecedores.empty:
        st.dataframe(df_fornecedores, use_container_width=True, hide_index=True)
