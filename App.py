import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA
# ==========================================
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado | Dashboard", page_icon="📊")

# ==========================================
# DESIGN SYSTEM / CSS AVANÇADO
# ==========================================
st.markdown("""
<style>
    /* Estilização Geral do Fundo e Fonte */
    .main { 
        background-color: #f8fafc; 
        padding: 1.5rem; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Cabeçalho do Dashboard */
    .title-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
    }
    .title-text { 
        color: #ffffff; 
        font-weight: 800; 
        font-size: 2rem; 
        margin: 0;
        letter-spacing: -0.5px;
    }
    .subtitle-text {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 5px;
    }

    /* Cartões de Expansão e Abas */
    .stExpander { 
        border: 1px solid #e2e8f0 !important; 
        border-radius: 10px !important; 
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); 
        background-color: #ffffff !important; 
        margin-bottom: 1rem; 
        padding: 5px; 
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 8px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px !important;
        font-weight: 600;
        color: #475569;
        background-color: transparent;
        padding: 10px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #2563eb !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }

    /* Botões Modernizados */
    .stButton>button { 
        background-color: #2563eb; 
        color: white; 
        border-radius: 8px; 
        font-weight: 600; 
        border: none; 
        padding: 0.5rem 1rem; 
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton>button:hover { 
        background-color: #1d4ed8; 
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }

    /* Tabelas e Dataframes */
    .dataframe { 
        border-radius: 8px; 
        overflow: hidden; 
        border: 1px solid #e2e8f0;
    }

    /* Alertas e Avisos */
    .stAlert {
        border-radius: 8px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase. Verifique se as secrets estão configuradas corretamente. Erro: {e}")
    st.stop()

# ==========================================
# CONTROLE DE SESSÃO / AUTENTICAÇÃO
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0;">
                <h2 style="text-align: center; color: #1e293b; margin-bottom: 20px;">🔐 Acesso Restrito</h2>
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

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.markdown("### 🏢 Painel de Controle")
    st.write(f"Logado como: **Administrador**")
    if st.button("🚪 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    st.success("🟢 Supabase Conectado")

# Cabeçalho Principal do Dashboard
st.markdown("""
    <div class="title-container">
        <p class="title-text">📊 Sistema ERP Integrado</p>
        <p class="subtitle-text">Gestão centralizada de Estoque, Vendas, Financeiro e Fornecedores em tempo real</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE BUSCA DO BANCO DE DADOS
# ==========================================
def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        st.error(f"Erro ao carregar dados de {nome_tabela}: {e}")
        return pd.DataFrame()

# Carregamento inicial dos dados da nuvem
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_fornecedores = carregar_dados_tabela("fornecedores")

# Normalização de colunas vazias caso o banco esteja vazio
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'produto', 'categoria', 'quantidade', 'limite_minimo', 'valor_unitario'])
if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'data', 'produto', 'quantidade', 'valor_total'])
if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'data', 'descricao', 'tipo', 'valor'])
if df_fornecedores.empty:
    df_fornecedores = pd.DataFrame(columns=['id', 'nome', 'contato', 'categoria_produto'])

# Padronizar nomes de colunas visualmente
if 'Produto' not in df_estoque.columns and 'produto' in df_estoque.columns:
    df_estoque = df_estoque.rename(columns={
        'produto': 'Produto',
        'categoria': 'Categoria',
        'quantidade': 'Quantidade',
        'limite_minimo': 'Limite Mínimo',
        'valor_unitario': 'Valor Unitário'
    })

if 'Data' not in df_vendas.columns and 'data' in df_vendas.columns:
    df_vendas = df_vendas.rename(columns={
        'data': 'Data',
        'produto': 'Produto',
        'quantidade': 'Quantidade',
        'valor_total': 'Valor Total'
    })

if 'Data' not in df_financeiro.columns and 'data' in df_financeiro.columns:
    df_financeiro = df_financeiro.rename(columns={
        'data': 'Data',
        'descricao': 'Descrição',
        'tipo': 'Tipo',
        'valor': 'Valor'
    })

if 'Nome' not in df_fornecedores.columns and 'nome' in df_fornecedores.columns:
    df_fornecedores = df_fornecedores.rename(columns={
        'nome': 'Nome',
        'contato': 'Contato',
        'categoria_produto': 'Categoria de Produto'
    })

# ==========================================
# ABAS PRINCIPAIS DO ERP
# ==========================================
tab_estoque, tab_vendas, tab_financeiro, tab_fornecedores = st.tabs([
    "📦 Estoque", 
    "🛒 Vendas", 
    "💰 Financeiro", 
    "🤝 Fornecedores"
])

# ==========================================
# ABA 1: ESTOQUE
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    
    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
            with col2:
                qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
            
            btn_adicionar = st.form_submit_button("Cadastrar Produto")
            
            if btn_adicionar and nome:
                produto_existe = False
                if not df_estoque.empty:
                    produto_existe = df_estoque['Produto'].str.lower().eq(nome.strip().lower()).any()
                
                if produto_existe:
                    st.error(f"⚠ Erro: O produto '{nome}' já está cadastrado no estoque!")
                else:
                    try:
                        supabase.table("estoque").insert({
                            "produto": nome.strip(),
                            "categoria": categoria,
                            "quantidade": int(qtd),
                            "limite_minimo": int(limite),
                            "valor_unitario": float(preco)
                        }).execute()
                        st.success("✅ Produto cadastrado com sucesso no Supabase!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar produto: {e}")

    with st.expander("🔄 Atualizar Estoque e Preço"):
        if not df_estoque.empty:
            produtos_disponiveis = df_estoque['Produto'].tolist()
            produto_selecionado = st.selectbox("Selecione o produto para atualizar:", produtos_disponiveis, key="select_update")
            
            item_atual = df_estoque[df_estoque['Produto'] == produto_selecionado].iloc[0]
            item_id = item_atual['id']
            quantidade_atual = item_atual['Quantidade']
            preco_atual = item_atual['Valor Unitário']
            
            nova_quantidade = st.number_input("Nova Quantidade em Estoque", value=int(quantidade_atual), min_value=0, step=1)
            novo_preco = st.number_input("Novo Valor Unitário (R$)", value=float(preco_atual), min_value=0.0, step=0.01)
            
            if st.button("Atualizar Dados"):
                try:
                    supabase.table("estoque").update({
                        "quantidade": int(nova_quantidade),
                        "valor_unitario": float(novo_preco)
                    }).eq("id", item_id).execute()
                    st.success("Dados atualizados com sucesso no Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.info("Nenhum produto cadastrado para atualizar.")

    with st.expander("🗑️ Remover Produto"):
        if not df_estoque.empty:
            produtos_disponiveis_remover = df_estoque['Produto'].tolist()
            produto_remover = st.selectbox("Selecione o produto para remover:", produtos_disponiveis_remover, key="select_remove")
            if st.button("Excluir Produto"):
                try:
                    item_id = df_estoque[df_estoque['Produto'] == produto_remover].iloc[0]['id']
                    supabase.table("estoque").delete().eq("id", item_id).execute()
                    st.success(f"Produto '{produto_remover}' removido com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
        else:
            st.info("Nenhum produto cadastrado para remover.")

    dados_est = df_estoque.copy()
    if not dados_est.empty:
        produtos_em_alerta = dados_est[dados_est['Quantidade'] <= dados_est['Limite Mínimo']]
        if not produtos_em_alerta.empty:
            st.warning("⚠️ **Atenção: Os seguintes produtos estão com estoque baixo!**")
            for _, row in produtos_em_alerta.iterrows():
                st.error(f"📉 **{row['Produto']}**: Restam apenas {row['Quantidade']} unidades (Limite: {row['Limite Mínimo']})")
        
        dados_est['Valor Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
        st.markdown("### 📋 Visão Geral do Estoque")
        st.dataframe(dados_est[['Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário', 'Valor Total']].style.format({'Valor Unitário': 'R$ {:.2f}', 'Valor Total': 'R$ {:.2f}'}), use_container_width=True, hide_index=True)
    else:
        st.info("Seu estoque está vazio no momento.")

# ==========================================
# ABA 2: VENDAS
# ==========================================
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
                
                if qtd_venda <= estoque_atual:
                    novo_estoque = estoque_atual - qtd_venda
                    vlr_total = qtd_venda * valor_unit
                    data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    try:
                        supabase.table("estoque").update({"quantidade": novo_estoque}).eq("id", item_id).execute()
                        supabase.table("vendas").insert({
                            "data": data_str,
                            "produto": prod_venda,
                            "quantidade": int(qtd_venda),
                            "valor_total": float(vlr_total)
                        }).execute()
                        supabase.table("financeiro").insert({
                            "data": data_str,
                            "descricao": f"Venda: {prod_venda}",
                            "tipo": "Entrada",
                            "valor": float(vlr_total)
                        }).execute()
                        
                        st.success("Venda registrada com sucesso! Estoque e financeiro atualizados.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao registrar venda: {e}")
                else:
                    st.error(f"Quantidade em estoque insuficiente! (Disponível: {estoque_atual})")
        else:
            st.info("Cadastre produtos no estoque antes de registrar vendas.")
            btn_venda = st.form_submit_button("Registrar Venda", disabled=True)

    with st.expander("✏️ Editar ou Cancelar Venda (Corrigir Erros)"):
        if not df_vendas.empty:
            opcoes_venda = []
            for _, row in df_vendas.iterrows():
                texto = f"ID: {row['id']} | {row['Data']} | {row['Produto']} | Qtd: {row['Quantidade']} | R$ {row['Valor Total']:.2f}"
                opcoes_venda.append(texto)
                
            venda_selecionada = st.selectbox("Selecione a venda para corrigir:", opcoes_venda)
            venda_id_str = venda_selecionada.split("|")[0].replace("ID:", "").strip()
            
            venda_atual = df_vendas[df_vendas['id'].astype(str) == venda_id_str].iloc[0]
            old_prod = venda_atual['Produto']
            old_qtd = int(venda_atual['Quantidade'])
            old_total = float(venda_atual['Valor Total'])
            
            lista_produtos = df_estoque['Produto'].tolist() if not df_estoque.empty else []
            index_prod = lista_produtos.index(old_prod) if old_prod in lista_produtos else 0
            
            with st.form("form_editar_venda"):
                st.write("**Novos dados da venda:**")
                novo_prod = st.selectbox("Produto Correto", lista_produtos, index=index_prod) if lista_produtos else st.text_input("Produto", old_prod)
                nova_qtd = st.number_input("Quantidade Correta", min_value=1, step=1, value=old_qtd)
                
                col1, col2 = st.columns(2)
                btn_salvar_venda = col1.form_submit_button("Salvar Alteração")
                btn_cancelar_venda = col2.form_submit_button("Cancelar Venda (Estornar tudo)")
                
                if btn_cancelar_venda:
                    try:
                        if not df_estoque.empty and old_prod in df_estoque['Produto'].values:
                            est_item = df_estoque[df_estoque['Produto'] == old_prod].iloc[0]
                            novo_qtd_est = int(est_item['Quantidade']) + old_qtd
                            supabase.table("estoque").update({"quantidade": novo_qtd_est}).eq("id", est_item['id']).execute()
                        
                        supabase.table("vendas").delete().eq("id", venda_atual['id']).execute()
                        
                        fin_match = df_financeiro[(df_financeiro['Descrição'] == f"Venda: {old_prod}") & (df_financeiro['Valor'] == old_total)]
                        if not fin_match.empty:
                            supabase.table("financeiro").delete().eq("id", fin_match.iloc[0]['id']).execute()
                        
                        st.success("Venda cancelada! Estoque estornado e financeiro ajustado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cancelar venda: {e}")
                    
                if btn_salvar_venda:
                    try:
                        if not df_estoque.empty and old_prod in df_estoque['Produto'].values:
                            est_old = df_estoque[df_estoque['Produto'] == old_prod].iloc[0]
                            supabase.table("estoque").update({"quantidade": int(est_old['Quantidade']) + old_qtd}).eq("id", est_old['id']).execute()
                        
                        est_new = df_estoque[df_estoque['Produto'] == novo_prod].iloc[0]
                        disponivel = int(est_new['Quantidade'])
                        
                        if nova_qtd <= disponivel:
                            novo_estoque_val = disponivel - nova_qtd
                            novo_total = nova_qtd * float(est_new['Valor Unitário'])
                            
                            supabase.table("estoque").update({"quantidade": novo_estoque_val}).eq("id", est_new['id']).execute()
                            supabase.table("vendas").update({
                                "produto": novo_prod,
                                "quantidade": int(nova_qtd),
                                "valor_total": float(novo_total)
                            }).eq("id", venda_atual['id']).execute()
                            
                            fin_match = df_financeiro[(df_financeiro['Descrição'] == f"Venda: {old_prod}") & (df_financeiro['Valor'] == old_total)]
                            if not fin_match.empty:
                                supabase.table("financeiro").update({
                                    "descricao": f"Venda: {novo_prod}",
                                    "valor": float(novo_total)
                                }).eq("id", fin_match.iloc[0]['id']).execute()
                                
                            st.success("Venda atualizada com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"Estoque insuficiente para '{novo_prod}'! (Disponível: {disponivel})")
                    except Exception as e:
                        st.error(f"Erro ao atualizar venda: {e}")
        else:
            st.info("Nenhuma venda para editar.")

    st.markdown("### 📊 Histórico de Vendas")
    if not df_vendas.empty:
        st.dataframe(df_vendas[['Data', 'Produto', 'Quantidade', 'Valor Total']].style.format({'Valor Total': 'R$ {:.2f}'}), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda registrada ainda.")

# ==========================================
# ABA 3: FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("💰 Controle Financeiro")
    
    with st.expander("➕ Registrar Transação Manual (Despesas etc.)"):
        with st.form("form_fin"):
            desc = st.text_input("Descrição (Ex: Conta de Luz, Material, Fornecedor)")
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
            btn_fin = st.form_submit_button("Registrar Transação")
            
            if btn_fin and desc:
                try:
                    supabase.table("financeiro").insert({
                        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "descricao": desc,
                        "tipo": tipo,
                        "valor": float(valor)
                    }).execute()
                    st.success("Transação registrada com sucesso no Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar transação: {e}")
                
    with st.expander("🗑️ Remover Transação Manual (Corrigir Erro)"):
        st.warning("Nota: Para cancelar Vendas, use a aba de Vendas.")
        if not df_financeiro.empty:
            opcoes_exclusao = []
            for _, row in df_financeiro.iterrows():
                texto = f"ID: {row['id']} | {row['Data']} | {row['Tipo']} | {row['Descrição']} | R$ {row['Valor']:.2f}"
                opcoes_exclusao.append(texto)
                
            transacao_excluir = st.selectbox("Selecione a transação que deseja apagar:", opcoes_exclusao)
            if st.button("Apagar Registro Selecionado"):
                id_excluir = transacao_excluir.split("|")[0].replace("ID:", "").strip()
                try:
                    supabase.table("financeiro").delete().eq("id", id_excluir).execute()
                    st.success("Transação apagada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao apagar: {e}")
        else:
            st.info("Não há transações financeiras para remover.")

    dados_fin = df_financeiro.copy()
    if not dados_fin.empty:
        entradas = dados_fin[dados_fin['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = dados_fin[dados_fin['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📥 Total Entradas", f"R$ {entradas:.2f}")
        c2.metric("📤 Total Saídas", f"R$ {saidas:.2f}")
        c3.metric("💳 Saldo Atual", f"R$ {saldo:.2f}")
        
        st.markdown("### 📋 Extrato Financeiro Consolidado")
        st.dataframe(dados_fin[['Data', 'Descrição', 'Tipo', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma movimentação financeira registrada.")

# ==========================================
# ABA 4: FORNECEDORES
# ==========================================
with tab_fornecedores:
    st.subheader("🤝 Cadastro de Fornecedores")
    with st.expander("➕ Adicionar Fornecedor"):
        with st.form("form_forn"):
            nome_forn = st.text_input("Nome do Fornecedor")
            contato_forn = st.text_input("Contato (Telefone/Email)")
            cat_forn = st.text_input("Categoria de Produtos Fornecidos")
            btn_forn = st.form_submit_button("Cadastrar Fornecedor")
            
            if btn_forn and nome_forn:
                try:
                    supabase.table("fornecedores").insert({
                        "nome": nome_forn.strip(),
                        "contato": contato_forn,
                        "categoria_produto": cat_forn
                    }).execute()
                    st.success("Fornecedor cadastrado com sucesso no Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar fornecedor: {e}")

    st.markdown("### 📋 Lista de Fornecedores Ativos")
    if not df_fornecedores.empty:
        st.dataframe(df_fornecedores[['Nome', 'Contato', 'Categoria de Produto']], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum fornecedor cadastrado.")
