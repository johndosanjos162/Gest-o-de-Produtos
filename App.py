import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA
# ==========================================
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado", page_icon="📦")

# CSS dinâmico adaptável
st.markdown("""
<style>
    .main { padding: 20px; }
    .title-text { font-weight: 700; font-size: 2.2rem; margin-bottom: 20px; text-align: center; }
    .stExpander, .stTabs { 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); 
        margin-bottom: 15px; 
        padding: 10px; 
    }
    .stButton>button { 
        background-color: #4f46e5; 
        color: white; 
        border-radius: 6px; 
        font-weight: 600; 
        border: none; 
        padding: 10px 20px; 
        transition: background-color 0.2s; 
    }
    .stButton>button:hover { 
        background-color: #4338ca; 
    }
    .dataframe { border-radius: 8px; overflow: hidden; }
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
    st.error(f"Erro ao conectar com o Supabase. Verifique as secrets. Erro: {e}")
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
        st.markdown('<p class="title-text">🔐 Acesso Restrito</p>', unsafe_allow_html=True)
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

if not st.session_state.autenticado:
    tela_login()
    st.stop()

with st.sidebar:
    st.write(f"Logado como: **Administrador**")
    if st.button("🚪 Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()
    st.markdown("---")
    st.success("🟢 Conectado ao Supabase")

st.markdown('<p class="title-text">📦 Sistema ERP Integrado (Nuvem)</p>', unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE BUSCA DO BANCO DE DADOS
# ==========================================
def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        return pd.DataFrame()

# Carregamento inicial
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_fornecedores = carregar_dados_tabela("fornecedores")
df_pedidos_compra = carregar_dados_tabela("pedidos_compra")
df_clientes = carregar_dados_tabela("clientes")
df_caixa = carregar_dados_tabela("fechamento_caixa")

# Normalizações para evitar quebras em tabelas vazias
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'produto', 'categoria', 'quantidade', 'limite_minimo', 'valor_unitario', 'preco_custo'])
if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'data', 'produto', 'quantidade', 'valor_total', 'lucro'])
if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'data', 'descricao', 'tipo', 'categoria', 'valor'])
if df_fornecedores.empty:
    df_fornecedores = pd.DataFrame(columns=['id', 'nome_empresa', 'cnpj', 'contato', 'telefone', 'email', 'observacoes'])
if df_pedidos_compra.empty:
    df_pedidos_compra = pd.DataFrame(columns=['id', 'data', 'fornecedor', 'produto', 'quantidade', 'preco_custo_unitario', 'valor_total', 'status'])
if df_clientes.empty:
    df_clientes = pd.DataFrame(columns=['id', 'nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes'])
if df_caixa.empty:
    df_caixa = pd.DataFrame(columns=['id', 'data', 'tipo_registro', 'valor', 'responsavel', 'observacao'])

# Padronizações visuais colunas
if 'Produto' not in df_estoque.columns and 'produto' in df_estoque.columns:
    df_estoque = df_estoque.rename(columns={'produto': 'Produto', 'categoria': 'Categoria', 'quantidade': 'Quantidade', 'limite_minimo': 'Limite Mínimo', 'valor_unitario': 'Valor Unitário', 'preco_custo': 'Preço de Custo'})
if 'Preço de Custo' not in df_estoque.columns:
    df_estoque['Preço de Custo'] = 0.00

# ==========================================
# ABAS PRINCIPAIS DO ERP
# ==========================================
tab_estoque, tab_vendas, tab_despesas, tab_financeiro, tab_clientes, tab_fornecedores, tab_etiquetas, tab_curva_abc, tab_caixa, tab_dashboard = st.tabs([
    "📦 Estoque", 
    "🛒 Vendas", 
    "💡 Despesas",
    "💰 Financeiro", 
    "👥 Clientes",
    "🤝 Fornecedores & Compras",
    "🏷️ Etiquetas",
    "📊 Curva ABC & Vendas",
    "💵 Caixa & Sangria",
    "📈 Dashboard"
])

# ==========================================
# 1. ESTOQUE (Com Cadastro, Edição e Exclusão)
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    sub_est_cad, sub_est_ger = st.tabs(["➕ Cadastrar Produto", "✏️ Gerenciar, Editar e Excluir"])
    
    with sub_est_cad:
        with st.form("form_produto"):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Outros"])
                preco_custo = st.number_input("Preço de Custo (R$)", min_value=0.0, step=0.01)
                preco = st.number_input("Valor Unitário / Venda (R$)", min_value=0.0, step=0.01)
            with col2:
                qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1)
            
            if st.form_submit_button("Cadastrar Produto") and nome:
                try:
                    supabase.table("estoque").insert({
                        "produto": nome.strip(), "categoria": categoria, "quantidade": int(qtd),
                        "limite_minimo": int(limite), "valor_unitario": float(preco), "preco_custo": float(preco_custo)
                    }).execute()
                    st.success("✅ Produto cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with sub_est_ger:
        if not df_estoque.empty:
            prod_sel_ed = st.selectbox("Selecione o produto para Editar ou Excluir:", df_estoque['Produto'].tolist(), key="sel_ed_est")
            item_e = df_estoque[df_estoque['Produto'] == prod_sel_ed].iloc[0]
            
            with st.form("form_edit_est"):
                e_nome = st.text_input("Nome do Produto", value=str(item_e['Produto']))
                e_cat = st.text_input("Categoria", value=str(item_e['Categoria']))
                e_qtd = st.number_input("Quantidade", value=int(item_e['Quantidade']), min_value=0, step=1)
                e_lim = st.number_input("Limite Mínimo", value=int(item_e['Limite Mínimo']), min_value=0, step=1)
                e_custo = st.number_input("Preço de Custo (R$)", value=float(item_e['Preço de Custo']), min_value=0.0, step=0.01)
                e_venda = st.number_input("Valor Unitário (R$)", value=float(item_e['Valor Unitário']), min_value=0.0, step=0.01)
                
                col_b1, col_b2 = st.columns(2)
                salvar_ed = col_b1.form_submit_button("💾 Salvar Alterações do Produto")
                excluir_prod = col_b2.form_submit_button("🗑️ Excluir Produto Definitivamente")
                
                if salvar_ed:
                    supabase.table("estoque").update({
                        "produto": e_nome, "categoria": e_cat, "quantidade": int(e_qtd),
                        "limite_minimo": int(e_lim), "preco_custo": float(e_custo), "valor_unitario": float(e_venda)
                    }).eq("id", int(item_e['id'])).execute()
                    st.success("Produto atualizado com sucesso!")
                    st.rerun()
                    
                if excluir_prod:
                    supabase.table("estoque").delete().eq("id", int(item_e['id'])).execute()
                    st.success("Produto excluído!")
                    st.rerun()
                    
            st.markdown("---")
            dados_est = df_estoque.copy()
            dados_est['Valor Custo Total'] = dados_est['Quantidade'] * dados_est['Preço de Custo']
            st.dataframe(dados_est[['Produto', 'Categoria', 'Quantidade', 'Preço de Custo', 'Valor Unitário', 'Valor Custo Total']].style.format({'Preço de Custo': 'R$ {:.2f}', 'Valor Unitário': 'R$ {:.2f}', 'Valor Custo Total': 'R$ {:.2f}'}), hide_index=True)
        else:
            st.info("Nenhum produto no estoque.")

# ==========================================
# 2. VENDAS (Com Registro e Exclusão)
# ==========================================
with tab_vendas:
    st.subheader("🛒 Registro e Gestão de Vendas")
    sub_v_reg, sub_v_ger = st.tabs(["➕ Registrar Venda", "📋 Histórico e Exclusão"])
    
    with sub_v_reg:
        with st.form("form_venda"):
            if not df_estoque.empty:
                prod_venda = st.selectbox("Produto Vendido", df_estoque['Produto'].tolist())
                qtd_venda = st.number_input("Quantidade", min_value=1, step=1)
                
                if st.form_submit_button("Registrar Venda"):
                    item_est = df_estoque[df_estoque['Produto'] == prod_venda].iloc[0]
                    estoque_atual = int(item_est['Quantidade'])
                    
                    if qtd_venda <= estoque_atual:
                        vlr_total = qtd_venda * float(item_est['Valor Unitário'])
                        lucro_venda = (float(item_est['Valor Unitário']) - float(item_est['Preço de Custo'])) * qtd_venda
                        data_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        supabase.table("estoque").update({"quantidade": estoque_atual - qtd_venda}).eq("id", item_est['id']).execute()
                        supabase.table("vendas").insert({"data": data_str, "produto": prod_venda, "quantidade": int(qtd_venda), "valor_total": float(vlr_total), "lucro": float(lucro_venda)}).execute()
                        supabase.table("financeiro").insert({"data": data_str, "descricao": f"Venda: {prod_venda} ({qtd_venda} un)", "tipo": "Entrada", "categoria": "Vendas de Produtos", "valor": float(vlr_total)}).execute()
                        
                        st.success("✅ Venda registrada com baixa automática!")
                        st.rerun()
                    else:
                        st.error("Estoque insuficiente!")
            else:
                st.warning("Cadastre produtos primeiro.")

    with sub_v_ger:
        if not df_vendas.empty:
            st.dataframe(df_vendas[['id', 'Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro']].style.format({'Valor Total': 'R$ {:.2f}', 'Lucro': 'R$ {:.2f}'}), hide_index=True)
            st.markdown("---")
            v_id_del = st.selectbox("Selecione o ID da venda para excluir:", df_vendas['id'].tolist(), key="del_venda")
            if st.button("Excluir Venda Selecionada"):
                supabase.table("vendas").delete().eq("id", int(v_id_del)).execute()
                st.success("Venda excluída com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma venda registrada.")

# ==========================================
# 3. DESPESAS (Com Cadastro e Exclusão)
# ==========================================
with tab_despesas:
    st.subheader("💡 Despesas do Comércio")
    sub_d_cad, sub_d_ger = st.tabs(["➕ Lançar Despesa", "📋 Gerenciar / Excluir Despesas"])
    
    with sub_d_cad:
        with st.form("form_desp"):
            c1, c2 = st.columns(2)
            with c1:
                cat_d = st.selectbox("Categoria", ["Energia / Luz", "Água", "Internet", "Aluguel", "Manutenção", "Impostos", "Outros"])
                desc_d = st.text_input("Descrição / Referência")
            with c2:
                vlr_d = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                data_d = st.date_input("Data", value=datetime.now())
                
            if st.form_submit_button("Lançar Despesa"):
                supabase.table("financeiro").insert({
                    "data": f"{data_d} {datetime.now().strftime('%H:%M:%S')}",
                    "descricao": desc_d, "tipo": "Saída", "categoria": f"Despesa: {cat_d}", "valor": float(vlr_d)
                }).execute()
                st.success("Despesa lançada!")
                st.rerun()

    with sub_d_ger:
        df_despesas_apenas = df_financeiro[df_financeiro['Tipo'] == 'Saída'] if not df_financeiro.empty else pd.DataFrame()
        if not df_despesas_apenas.empty:
            st.dataframe(df_despesas_apenas[['id', 'Data', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
            st.markdown("---")
            id_desp_del = st.selectbox("Selecione o ID da despesa para excluir:", df_despesas_apenas['id'].tolist(), key="del_desp")
            if st.button("Excluir Despesa"):
                supabase.table("financeiro").delete().eq("id", int(id_desp_del)).execute()
                st.success("Despesa excluída!")
                st.rerun()
        else:
            st.info("Nenhuma despesa lançada.")

# ==========================================
# 4. FINANCEIRO (Fluxo Geral)
# ==========================================
with tab_financeiro:
    st.subheader("💰 Fluxo de Caixa Completo")
    if not df_financeiro.empty:
        total_ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
        total_sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", f"R$ {total_ent:.2f}")
        c2.metric("Saídas", f"R$ {total_sai:.2f}")
        c3.metric("Saldo Líquido", f"R$ {total_ent - total_sai:.2f}")
        st.dataframe(df_financeiro[['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
    else:
        st.info("Nenhum registro financeiro.")

# ==========================================
# 5. GESTÃO DE CLIENTES (Com Cadastro, Edição e Exclusão)
# ==========================================
with tab_clientes:
    st.subheader("👥 Gestão de Clientes")
    sub_c_cad, sub_c_ger = st.tabs(["➕ Cadastrar Cliente", "✏️ Editar / Excluir Clientes"])
    
    with sub_c_cad:
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nome_cli = st.text_input("Nome Completo / Razão Social *")
                cpf_cnpj = st.text_input("CPF ou CNPJ")
                tel_cli = st.text_input("Telefone / WhatsApp")
            with c2:
                email_cli = st.text_input("E-mail")
                end_cli = st.text_input("Endereço Completo")
                obs_cli = st.text_area("Observações / Histórico")
                
            if st.form_submit_button("Salvar Cliente") and nome_cli:
                try:
                    supabase.table("clientes").insert({
                        "nome": nome_cli.strip(), "cpf_cnpj": cpf_cnpj.strip(), "telefone": tel_cli.strip(),
                        "email": email_cli.strip(), "endereco": end_cli.strip(), "observacoes": obs_cli.strip()
                    }).execute()
                    st.success(f"✅ Cliente '{nome_cli}' cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
                    
    with sub_c_ger:
        if not df_clientes.empty:
            cli_sel_ed = st.selectbox("Selecione o cliente para Editar ou Excluir:", df_clientes['nome'].tolist(), key="sel_ed_cli")
            c_item = df_clientes[df_clientes['nome'] == cli_sel_ed].iloc[0]
            
            with st.form("form_edit_cli"):
                ec_nome = st.text_input("Nome Completo", value=str(c_item['nome']))
                ec_doc = st.text_input("CPF / CNPJ", value=str(c_item['cpf_cnpj']) if c_item['cpf_cnpj'] else "")
                ec_tel = st.text_input("Telefone", value=str(c_item['telefone']) if c_item['telefone'] else "")
                ec_email = st.text_input("E-mail", value=str(c_item['email']) if c_item['email'] else "")
                ec_end = st.text_input("Endereço", value=str(c_item['endereco']) if c_item['endereco'] else "")
                ec_obs = st.text_area("Observações", value=str(c_item['observacoes']) if c_item['observacoes'] else "")
                
                col_cb1, col_cb2 = st.columns(2)
                salvar_cli_ed = col_cb1.form_submit_button("💾 Salvar Alterações do Cliente")
                excluir_cli = col_cb2.form_submit_button("🗑️️ Excluir Cliente")
                
                if salvar_cli_ed:
                    supabase.table("clientes").update({
                        "nome": ec_nome, "cpf_cnpj": ec_doc, "telefone": ec_tel,
                        "email": ec_email, "endereco": ec_end, "observacoes": ec_obs
                    }).eq("id", int(c_item['id'])).execute()
                    st.success("Cliente atualizado com sucesso!")
                    st.rerun()
                    
                if excluir_cli:
                    supabase.table("clientes").delete().eq("id", int(c_item['id'])).execute()
                    st.success("Cliente excluído!")
                    st.rerun()
                    
            st.markdown("---")
            st.dataframe(df_clientes[['nome', 'cpf_cnpj', 'telefone', 'email', 'endereco', 'observacoes']], hide_index=True)
        else:
            st.info("Nenhum cliente cadastrado.")

# ==========================================
# 6. FORNECEDORES E COMPRAS (Com Edição e Exclusão)
# ==========================================
with tab_fornecedores:
    st.subheader("🤝 Fornecedores e Pedidos de Compra")
    sub_f_cad, sub_f_ped, sub_f_ger = st.tabs(["➕ Novo Fornecedor", "📦 Registrar Pedido", "✏️ Gerenciar Fornecedores & Pedidos"])
    
    with sub_f_cad:
        with st.form("form_forn"):
            c1, c2 = st.columns(2)
            with c1:
                f_nome = st.text_input("Empresa *")
                f_cnpj = st.text_input("CNPJ")
                f_cont = st.text_input("Representante")
            with c2:
                f_tel = st.text_input("Telefone")
                f_email = st.text_input("E-mail")
                f_obs = st.text_area("Observações")
            if st.form_submit_button("Salvar Fornecedor") and f_nome:
                supabase.table("fornecedores").insert({"nome_empresa": f_nome, "cnpj": f_cnpj, "contato": f_cont, "telefone": f_tel, "email": f_email, "observacoes": f_obs}).execute()
                st.success("Fornecedor salvo!")
                st.rerun()

    with sub_f_ped:
        if not df_fornecedores.empty:
            with st.form("form_ped"):
                c1, c2 = st.columns(2)
                with c1:
                    f_sel = st.selectbox("Fornecedor", df_fornecedores['nome_empresa'].tolist())
                    p_sel = st.selectbox("Produto", df_estoque['Produto'].tolist()) if not df_estoque.empty else st.text_input("Produto")
                    qtd_comp = st.number_input("Quantidade", min_value=1, step=1)
                with c2:
                    custo_u = st.number_input("Custo Unitário (R$)", min_value=0.01, step=0.01)
                    st_ped = st.selectbox("Status", ["Pendente", "Entregue"])
                
                up_est_auto = st.checkbox("Atualizar Estoque Automaticamente?", value=True)
                lanc_cx = st.checkbox("Lançar como Saída no Financeiro?", value=True)
                
                if st.form_submit_button("Registrar Pedido de Compra"):
                    total_p = qtd_comp * custo_u
                    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    supabase.table("pedidos_compra").insert({"data": dt_str, "fornecedor": f_sel, "produto": p_sel, "quantidade": int(qtd_comp), "preco_custo_unitario": float(custo_u), "valor_total": float(total_p), "status": st_ped}).execute()
                    
                    if up_est_auto and not df_estoque.empty and p_sel in df_estoque['Produto'].values:
                        it = df_estoque[df_estoque['Produto'] == p_sel].iloc[0]
                        supabase.table("estoque").update({"quantidade": int(it['Quantidade']) + int(qtd_comp), "preco_custo": float(custo_u)}).eq("id", it['id']).execute()
                    
                    if lanc_cx:
                        supabase.table("financeiro").insert({"data": dt_str, "descricao": f"Compra ({f_sel}): {p_sel}", "tipo": "Saída", "categoria": "Compra de Mercadoria / Estoque", "valor": float(total_p)}).execute()
                        
                    st.success("Pedido de compra registrado com sucesso!")
                    st.rerun()
        else:
            st.info("Cadastre um fornecedor primeiro.")

    with sub_f_ger:
        st.write("### 🏢 Editar / Excluir Fornecedores")
        if not df_fornecedores.empty:
            forn_sel_ed = st.selectbox("Selecione o fornecedor:", df_fornecedores['nome_empresa'].tolist(), key="ed_forn_sel")
            f_item = df_fornecedores[df_fornecedores['nome_empresa'] == forn_sel_ed].iloc[0]
            
            with st.form("form_edit_forn"):
                ef_nome = st.text_input("Empresa", value=str(f_item['nome_empresa']))
                ef_cnpj = st.text_input("CNPJ", value=str(f_item['cnpj']) if f_item['cnpj'] else "")
                ef_cont = st.text_input("Representante", value=str(f_item['contato']) if f_item['contato'] else "")
                ef_tel = st.text_input("Telefone", value=str(f_item['telefone']) if f_item['telefone'] else "")
                ef_email = st.text_input("E-mail", value=str(f_item['email']) if f_item['email'] else "")
                ef_obs = st.text_area("Observações", value=str(f_item['observacoes']) if f_item['observacoes'] else "")
                
                col_fb1, col_fb2 = st.columns(2)
                if col_fb1.form_submit_button("💾 Salvar Fornecedor"):
                    supabase.table("fornecedores").update({
                        "nome_empresa": ef_nome, "cnpj": ef_cnpj, "contato": ef_cont, "telefone": ef_tel, "email": ef_email, "observacoes": ef_obs
                    }).eq("id", int(f_item['id'])).execute()
                    st.success("Fornecedor atualizado!")
                    st.rerun()
                    
                if col_fb2.form_submit_button("🗑️ Excluir Fornecedor"):
                    supabase.table("fornecedores").delete().eq("id", int(f_item['id'])).execute()
                    st.success("Fornecedor excluído!")
                    st.rerun()
        else:
            st.info("Nenhum fornecedor cadastrado.")
            
        st.markdown("---")
        st.write("### 📦 Histórico de Pedidos de Compra (Exclusão)")
        if not df_pedidos_compra.empty:
            st.dataframe(df_pedidos_compra.style.format({'preco_custo_unitario': 'R$ {:.2f}', 'valor_total': 'R$ {:.2f}'}), hide_index=True)
            id_ped_del = st.selectbox("Selecione o ID do pedido para excluir:", df_pedidos_compra['id'].tolist(), key="del_ped")
            if st.button("Excluir Pedido de Compra"):
                supabase.table("pedidos_compra").delete().eq("id", int(id_ped_del)).execute()
                st.success("Pedido excluído!")
                st.rerun()
        else:
            st.info("Nenhum pedido de compra registrado.")

# ==========================================
# 7. EMISSÃO DE ETIQUETAS DE CÓDIGO DE BARRAS
# ==========================================
with tab_etiquetas:
    st.subheader("🏷️ Emissão de Etiquetas e Código de Barras")
    st.write("Selecione um produto do estoque para gerar etiquetas de gôndola formatadas para impressão rápida.")
    
    if not df_estoque.empty:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            prod_etq = st.selectbox("Selecione o Produto", df_estoque['Produto'].tolist())
            qtd_etiquetas = st.number_input("Quantidade de Etiquetas a Gerar", min_value=1, max_value=100, value=10)
        
        item_etq = df_estoque[df_estoque['Produto'] == prod_etq].iloc[0]
        preco_etq = item_etq['Valor Unitário']
        cod_id = str(item_etq['id']).zfill(6)
        
        st.markdown("---")
        st.write("### 🖨️ Pré-visualização da Etiqueta")
        
        cols_preview = st.columns(3)
        for i in range(min(3, qtd_etiquetas)):
            with cols_preview[i]:
                st.markdown(f"""
                <div style="border: 2px dashed #333; padding: 15px; border-radius: 5px; text-align: center; background-color: #fff; color: #000;">
                    <h4 style="margin:0; font-size: 16px;">{prod_etq}</h4>
                    <p style="font-size: 12px; margin: 5px 0;">Cód: 789000{cod_id}</p>
                    <h3 style="margin:0; color: #2e7d32;">R$ {preco_etq:.2f}</h3>
                    <p style="font-size: 20px; font-family: monospace; letter-spacing: 2px; margin: 5px 0;">||| | |||| || |</p>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ Imprimir / Gerar Lote de Etiquetas"):
            st.info(f"Geradas {qtd_etiquetas} etiquetas para o produto **{prod_etq}**. Pressione Ctrl+P no seu navegador para imprimir.")
    else:
        st.info("Nenhum produto cadastrado no estoque para gerar etiquetas.")

# ==========================================
# 8. INTELIGÊNCIA DE VENDAS & CURVA ABC
# ==========================================
with tab_curva_abc:
    st.subheader("📊 Inteligência de Vendas & Relatório Curva ABC")
    st.write("Análise automatizada do faturamento por produto para classificar seu mix no padrão Curva ABC.")
    
    if not df_vendas.empty:
        curva_df = df_vendas.groupby('Produto').agg(
            Quantidade_Vendida=('Quantidade', 'sum'),
            Faturamento_Total=('Valor Total', 'sum'),
            Lucro_Total=('Lucro', 'sum')
        ).reset_index().sort_values(by='Faturamento_Total', ascending=False)
        
        faturamento_geral = curva_df['Faturamento_Total'].sum()
        if faturamento_geral > 0:
            curva_df['Participacao_%'] = (curva_df['Faturamento_Total'] / faturamento_geral) * 100
            curva_df['Acumulado_%'] = curva_df['Participacao_%'].cumsum()
            
            def classificar_abc(acum):
                if acum <= 80:
                    return 'A (Até 80%)'
                elif acum <= 95:
                    return 'B (80% - 95%)'
                else:
                    return 'C (95% - 100%)'
                    
            curva_df['Curva ABC'] = curva_df['Acumulado_%'].apply(classificar_abc)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📦 Produtos Comercializados", len(curva_df))
            c2.metric("💎 Faturamento Analisado", f"R$ {faturamento_geral:.2f}")
            c3.metric("🏆 Produtos Classe A", len(curva_df[curva_df['Curva ABC'].str.startswith('A')]))
            
            st.markdown("---")
            st.dataframe(curva_df[['Curva ABC', 'Produto', 'Quantidade_Vendida', 'Faturamento_Total', 'Lucro_Total', 'Participacao_%']].style.format({
                'Faturamento_Total': 'R$ {:.2f}', 
                'Lucro_Total': 'R$ {:.2f}', 
                'Participacao_%': '{:.2f}%'
            }), hide_index=True)
            
            st.markdown("---")
            st.altair_chart(
                alt.Chart(curva_df).mark_bar(color='#4f46e5').encode(
                    x=alt.X('Produto:N', sort='-y'),
                    y=alt.Y('Faturamento_Total:Q', title='Faturamento (R$)'),
                    color='Curva ABC:N',
                    tooltip=['Produto', 'Faturamento_Total', 'Curva ABC']
                ).properties(height=350),
                use_container_width=True
            )
        else:
            st.info("Faturamento total zerado.")
    else:
        st.info("Registre vendas no sistema para gerar a Inteligência de Vendas e Curva ABC.")

# ==========================================
# 9. FECHAMENTO DE CAIXA, SANGRIA E QUEBRA (Com Exclusão)
# ==========================================
with tab_caixa:
    st.subheader("💵 Fechamento de Caixa Diário, Sangria e Quebra")
    sub_cx_lanc, sub_cx_ger = st.tabs(["➕ Operações de Caixa", "📋 Histórico e Exclusão de Caixa"])
    
    with sub_cx_lanc:
        with st.form("form_operacao_caixa"):
            c1, c2 = st.columns(2)
            with c1:
                tipo_op = st.selectbox("Tipo de Operação", ["Abertura de Caixa", "Sangria (Retirada de Dinheiro)", "Fechamento de Caixa com Apuração"])
                resp = st.text_input("Operador / Responsável", value="Caixa Principal")
            with c2:
                vlr_op = st.number_input("Valor Envolvido (R$)", min_value=0.0, step=0.01)
                data_op = st.date_input("Data da Operação", value=datetime.now())
                
            obs_op = st.text_area("Observações (Ex: Motivo da sangria, conferência ou quebra)")
            
            if st.form_submit_button("Registrar Operação de Caixa"):
                dt_str = f"{data_op} {datetime.now().strftime('%H:%M:%S')}"
                db_tipo = "Abertura" if "Abertura" in tipo_op else ("Sangria" if "Sangria" in tipo_op else "Fechamento")
                
                try:
                    supabase.table("fechamento_caixa").insert({
                        "data": dt_str, "tipo_registro": db_tipo, "valor": float(vlr_op),
                        "responsavel": resp, "observacao": obs_op
                    }).execute()
                    
                    if db_tipo == "Sangria":
                        supabase.table("financeiro").insert({
                            "data": dt_str, "descricao": f"Sangria de Caixa ({resp}): {obs_op}",
                            "tipo": "Saída", "categoria": "Despesas Operacionais", "valor": float(vlr_op)
                        }).execute()
                        
                    st.success(f"✅ Operação de '{db_tipo}' registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    with sub_cx_ger:
        if not df_caixa.empty:
            st.dataframe(df_caixa.style.format({'valor': 'R$ {:.2f}'}), hide_index=True)
            st.markdown("---")
            cx_del = st.selectbox("Selecione o ID do registro de caixa para excluir:", df_caixa['id'].tolist(), key="del_cx_reg")
            if st.button("Excluir Registro de Caixa"):
                supabase.table("fechamento_caixa").delete().eq("id", int(cx_del)).execute()
                st.success("Registro de caixa excluído!")
                st.rerun()
        else:
            st.info("Nenhuma operação de caixa registrada.")

# ==========================================
# 10. DASHBOARD GERAL
# ==========================================
with tab_dashboard:
    st.subheader("📊 Dashboard Geral do Sistema")
    dados_fin_dash = df_financeiro.copy()
    if not dados_fin_dash.empty:
        ent = dados_fin_dash[dados_fin_dash['Tipo'] == 'Entrada']['Valor'].sum()
        sai = dados_fin_dash[dados_fin_dash['Tipo'] == 'Saída']['Valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas Totais", f"R$ {ent:.2f}")
        c2.metric("Saídas Totais", f"R$ {sai:.2f}")
        c3.metric("Saldo Líquido", f"R$ {ent - sai:.2f}")
        
        st.markdown("---")
        st.altair_chart(
            alt.Chart(dados_fin_dash.groupby('Tipo')['Valor'].sum().reset_index()).mark_arc(innerRadius=50).encode(
                theta='Valor:Q', color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Entrada', 'Saída'], range=['#22c55e', '#ef4444'])),
                tooltip=['Tipo', 'Valor']
            ).properties(height=300),
            use_container_width=True
        )
    else:
        st.info("Sem dados para o dashboard.")
