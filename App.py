import streamlit as st
import pandas as pd
from datetime import datetimeimport streamlit as st
import pandas as pd
from datetime import datetime, date
import hashlib
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA AVANÇADO
# ==========================================
st.set_page_config(
    layout="wide", 
    page_title="Enterprise ERP Cloud Pro", 
    page_icon="⚡"
)

st.markdown("""
<style>
    /* Estilização Geral Moderna */
    .main { background-color: #f8fafc; padding: 25px; }
    .title-text { 
        color: #0f172a; 
        font-weight: 800; 
        font-size: 2.4rem; 
        margin-bottom: 25px; 
        text-align: center; 
        letter-spacing: -0.025em;
    }
    .stExpander, .stTabs { 
        border: 1px solid #e2e8f0; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); 
        background-color: #ffffff; 
        margin-bottom: 20px; 
        padding: 15px; 
    }
    .stButton>button { 
        background-color: #6366f1; 
        color: white; 
        border-radius: 8px; 
        font-weight: 600; 
        border: none; 
        padding: 10px 24px; 
        transition: all 0.2s ease-in-out; 
    }
    .stButton>button:hover { 
        background-color: #4f46e5; 
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }
    .dataframe { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXÃO COM O SUPABASE (CACHED)
# ==========================================
@st.cache_resource
def init_connection() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro crítico nas credenciais do Supabase: {e}")
        st.stop()

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase. Verifique se as secrets estão configuradas. Detalhes: {e}")
    st.stop()

# ==========================================
# SISTEMA DE SEGURANÇA E AUTENTICAÇÃO HASH
# ==========================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_ativo' not in st.session_state:
    st.session_state.usuario_ativo = ""
if 'role' not in st.session_state:
    st.session_state.role = ""

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<p class="title-text">🔐 Enterprise ERP Login</p>', unsafe_allow_html=True)
        with st.form("form_login"):
            usuario = st.text_input("Usuário do Sistema")
            senha = st.text_input("Senha de Acesso", type="password")
            botao_login = st.form_submit_button("Acessar Plataforma", use_container_width=True)
            
            if botao_login:
                # Verificação contra o Supabase (tabela 'usuarios') ou fallback seguro
                try:
                    res = supabase.table("usuarios").select("*").eq("username", usuario).execute()
                    if res.data:
                        user_record = res.data[0]
                        if user_record['password_hash'] == hash_password(senha):
                            st.session_state.autenticado = True
                            st.session_state.usuario_ativo = user_record['username']
                            st.session_state.role = user_record.get('role', 'Operador')
                            st.success("Autenticação realizada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas.")
                    else:
                        # Fallback padrão se tabela estiver vazia
                        if usuario == "admin" and senha == "admin123":
                            st.session_state.autenticado = True
                            st.session_state.usuario_ativo = "admin"
                            st.session_state.role = "Administrador"
                            st.success("Login Master efetuado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Usuário não encontrado ou senha incorreta.")
                except Exception as ex:
                    # Fallback de emergência caso a tabela 'usuarios' não exista na nuvem
                    if usuario == "admin" and senha == "admin123":
                        st.session_state.autenticado = True
                        st.session_state.usuario_ativo = "admin"
                        st.session_state.role = "Administrador"
                        st.success("Login de emergência efetuado!")
                        st.rerun()
                    else:
                        st.error(f"Erro na verificação de login: {ex}")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# ==========================================
# BARRA LATERAL (SIDEBAR) & CONTROLE DE SESSÃO
# ==========================================
with st.sidebar:
    st.markdown(f"### Bem-vindo, **{st.session_state.usuario_ativo}**")
    st.caption(f"Perfil: 🛡️ {st.session_state.role}")
    if st.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state.autenticado = False
        st.session_state.usuario_ativo = ""
        st.session_state.role = ""
        st.rerun()
    st.markdown("---")
    st.success("🟢 Sincronizado com Supabase Cloud")

st.markdown('<p class="title-text">⚡ Sistema ERP Integrado em Nuvem Pro</p>', unsafe_allow_html=True)

# ==========================================
# CACHE DE DADOS OTIMIZADO COM TTL
# ==========================================
@st.cache_data(ttl=30)
def carregar_dados_tabela(nome_tabela):
    try:
        resposta = supabase.table(nome_tabela).select("*").execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        return pd.DataFrame()

# Carregamento de todas as tabelas essenciais
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")
df_fornecedores = carregar_dados_tabela("fornecedores")
df_clientes = carregar_dados_tabela("clientes")

# Normalização de schemas e colunas vazias
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'produto', 'categoria', 'quantidade', 'limite_minimo', 'valor_unitario'])
if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'data', 'produto', 'quantidade', 'valor_total', 'cliente'])
if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'data', 'descricao', 'tipo', 'valor', 'categoria'])
if df_fornecedores.empty:
    df_fornecedores = pd.DataFrame(columns=['id', 'nome', 'contato', 'categoria_produto', 'email'])
if df_clientes.empty:
    df_clientes = pd.DataFrame(columns=['id', 'nome', 'telefone', 'email', 'endereco'])

# Renomeações para padronização visual em português capitalizado
rename_map_estoque = {'produto': 'Produto', 'categoria': 'Categoria', 'quantidade': 'Quantidade', 'limite_minimo': 'Limite Mínimo', 'valor_unitario': 'Valor Unitário'}
df_estoque = df_estoque.rename(columns={k: v for k, v in rename_map_estoque.items() if k in df_estoque.columns})

rename_map_vendas = {'data': 'Data', 'produto': 'Produto', 'quantidade': 'Quantidade', 'valor_total': 'Valor Total', 'cliente': 'Cliente'}
df_vendas = df_vendas.rename(columns={k: v for k, v in rename_map_vendas.items() if k in df_vendas.columns})

rename_map_fin = {'data': 'Data', 'descricao': 'Descrição', 'tipo': 'Tipo', 'valor': 'Valor', 'categoria': 'Categoria'}
df_financeiro = df_financeiro.rename(columns={k: v for k, v in rename_map_fin.items() if k in df_financeiro.columns})

rename_map_forn = {'nome': 'Nome', 'contato': 'Contato', 'categoria_produto': 'Categoria de Produto', 'email': 'E-mail'}
df_fornecedores = df_fornecedores.rename(columns={k: v for k, v in rename_map_forn.items() if k in df_fornecedores.columns})

rename_map_cli = {'nome': 'Nome', 'telefone': 'Telefone', 'email': 'E-mail', 'endereco': 'Endereço'}
df_clientes = df_clientes.rename(columns={k: v for k, v in rename_map_cli.items() if k in df_clientes.columns})

# ==========================================
# NAVEGAÇÃO POR ABAS COMPLETA
# ==========================================
tab_estoque, tab_vendas, tab_financeiro, tab_fornecedores, tab_clientes, tab_relatorios = st.tabs([
    "📦 Estoque", 
    "🛒 Vendas & PDV", 
    "💰 Financeiro", 
    "🤝 Fornecedores",
    "👥 Clientes (CRM)",
    "📊 Relatórios & BI"
])

# ==========================================
# ABA 1: ESTOQUE
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão Avançada de Estoque")
    
    col_busca, col_filtro = st.columns([2, 1])
    with col_busca:
        termo_busca = st.text_input("🔍 Pesquisar produto no estoque por nome:", "")
    with col_filtro:
        categorias_disponiveis = ["Todas"] + list(df_estoque['Categoria'].unique()) if not df_estoque.empty and 'Categoria' in df_estoque.columns else ["Todas"]
        filtro_cat = st.selectbox("Filtrar por Categoria", categorias_disponiveis)

    with st.expander("➕ Adicionar Novo Produto"):
        with st.form("form_produto_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Produto *")
                categoria = st.selectbox("Categoria", ["Grãos", "Massas", "Óleos e Condimentos", "Bebidas", "Limpeza", "Eletrônicos", "Outros"])
                preco = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01, format="%.2f")
            with col2:
                qtd = st.number_input("Quantidade Inicial", min_value=0, step=1)
                limite = st.number_input("Limite Mínimo de Alerta", min_value=0, step=1, value=5)
            
            btn_adicionar = st.form_submit_button("Cadastrar Produto na Nuvem")
            
            if btn_adicionar:
                if not nome.strip():
                    st.error("O nome do produto é obrigatório.")
                else:
                    produto_existe = False
                    if not df_estoque.empty and 'Produto' in df_estoque.columns:
                        produto_existe = df_estoque['Produto'].str.lower().eq(nome.strip().lower()).any()
                    
                    if produto_existe:
                        st.error(f"⚠️ O produto '{nome}' já se encontra cadastrado!")
                    else:
                        try:
                            supabase.table("estoque").insert({
                                "produto": nome.strip(),
                                "categoria": categoria,
                                "quantidade": int(qtd),
                                "limite_minimo": int(limite),
                                "valor_unitario": float(preco)
                            }).execute()
                            st.success("✅ Produto cadastrado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao inserir no banco: {e}")

    with st.expander("🔄 Atualizar Estoque e Preço"):
        if not df_estoque.empty and 'Produto' in df_estoque.columns:
            produtos_disponiveis = df_estoque['Produto'].tolist()
            produto_selecionado = st.selectbox("Selecione o produto para alterar:", produtos_disponiveis)
            
            item_atual = df_estoque[df_estoque['Produto'] == produto_selecionado].iloc[0]
            item_id = item_atual['id']
            quantidade_atual = int(item_atual['Quantidade'])
            preco_atual = float(item_atual['Valor Unitário'])
            
            col_u1, col_u2 = st.columns(2)
            nova_quantidade = col_u1.number_input("Nova Quantidade Total", value=quantidade_atual, min_value=0, step=1)
            novo_preco = col_u2.number_input("Novo Valor Unitário (R$)", value=preco_atual, min_value=0.0, step=0.01, format="%.2f")
            
            if st.button("Confirmar Atualização"):
                try:
                    supabase.table("estoque").update({
                        "quantidade": int(nova_quantidade),
                        "valor_unitario": float(novo_preco)
                    }).eq("id", item_id).execute()
                    st.success("Registro de estoque atualizado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.info("Nenhum produto disponível para atualização.")

    with st.expander("🗑️ Excluir Produto"):
        if not df_estoque.empty and 'Produto' in df_estoque.columns:
            produto_remover = st.selectbox("Selecione o produto para exclusão:", df_estoque['Produto'].tolist(), key="del_prod")
            if st.button("Excluir Permanentemente"):
                try:
                    item_id = df_estoque[df_estoque['Produto'] == produto_remover].iloc[0]['id']
                    supabase.table("estoque").delete().eq("id", item_id).execute()
                    st.success(f"Produto '{produto_remover}' removido com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir: {e}")
        else:
            st.info("Nenhum produto cadastrado para remoção.")

    # Exibição e filtros aplicados
    dados_est = df_estoque.copy()
    if not dados_est.empty:
        if termo_busca:
            dados_est = dados_est[dados_est['Produto'].str.contains(termo_busca, case=False, na=False)]
        if filtro_cat != "Todas":
            dados_est = dados_est[dados_est['Categoria'] == filtro_cat]

        produtos_em_alerta = dados_est[dados_est['Quantidade'] <= dados_est['Limite Mínimo']]
        if not produtos_em_alerta.empty:
            st.warning("⚠️ **Atenção: Os seguintes itens atingiram ou estão abaixo do limite mínimo de segurança!**")
            for _, row in produtos_em_alerta.iterrows():
                st.error(f"📉 **{row['Produto']}**: Restam apenas **{row['Quantidade']}** unidades (Mínimo recomendado: {row['Limite Mínimo']})")
        
        dados_est['Valor Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
        st.subheader("Tabela de Inventário Atual")
        st.dataframe(
            dados_est[['Produto', 'Categoria', 'Quantidade', 'Limite Mínimo', 'Valor Unitário', 'Valor Total']].style.format({
                'Valor Unitário': 'R$ {:.2f}', 
                'Valor Total': 'R$ {:.2f}'
            }), 
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("O inventário de estoque está vazio.")

# ==========================================
# ABA 2: VENDAS & PDV
# ==========================================
with tab_vendas:
    st.subheader("🛒 Frente de Caixa & Registro de Vendas")
    
    with st.form("form_venda_pdv"):
        if not df_estoque.empty and 'Produto' in df_estoque.columns:
            prod_venda = st.selectbox("Produto Disponível", df_estoque['Produto'].tolist())
            
            # Seleção opcional de cliente vinculado
            clientes_lista = ["Consumidor Final (Não Identificado)"]
            if not df_clientes.empty and 'Nome' in df_clientes.columns:
                clientes_lista += df_clientes['Nome'].tolist()
            cliente_venda = st.selectbox("Cliente Vinculado à Venda", clientes_lista)
            
            qtd_venda = st.number_input("Quantidade Vendida", min_value=1, step=1, value=1)
            btn_venda = st.form_submit_button("Concluir e Registrar Venda")
            
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
                        # 1. Atualiza estoque
                        supabase.table("estoque").update({"quantidade": novo_estoque}).eq("id", item_id).execute()
                        
                        # 2. Registra na tabela de vendas
                        venda_payload = {
                            "data": data_str,
                            "produto": prod_venda,
                            "quantidade": int(qtd_venda),
                            "valor_total": float(vlr_total),
                            "cliente": cliente_venda
                        }
                        supabase.table("vendas").insert(venda_payload).execute()
                        
                        # 3. Registra entrada automática no financeiro
                        supabase.table("financeiro").insert({
                            "data": data_str,
                            "descricao": f"Venda: {prod_venda} (Client: {cliente_venda})",
                            "tipo": "Entrada",
                            "valor": float(vlr_total),
                            "categoria": "Receita de Vendas"
                        }).execute()
                        
                        st.success("🎉 Venda registrada com sucesso! Estoque e livro caixa atualizados.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar transação de venda: {e}")
                else:
                    st.error(f"Estoque insuficiente! Estoque atual disponível: {estoque_atual} unidades.")
        else:
            st.info("Cadastre produtos no estoque antes de realizar operações de vendas.")
            st.form_submit_button("Concluir Venda", disabled=True)

    with st.expander("✏️ Editar ou Cancelar Venda Existente"):
        if not df_vendas.empty and 'id' in df_vendas.columns:
            opcoes_venda = []
            for _, row in df_vendas.iterrows():
                cli_info = f" | Cli: {row.get('Cliente', 'N/A')}" if 'Cliente' in row else ""
                texto = f"ID: {row['id']} | {row['Data']} | {row['Produto']} | Qtd: {row['Quantidade']} | R$ {row['Valor Total']:.2f}{cli_info}"
                opcoes_venda.append(texto)
                
            venda_selecionada = st.selectbox("Selecione a transação de venda:", opcoes_venda)
            venda_id_str = venda_selecionada.split("|")[0].replace("ID:", "").strip()
            
            venda_atual = df_vendas[df_vendas['id'].astype(str) == venda_id_str].iloc[0]
            old_prod = venda_atual['Produto']
            old_qtd = int(venda_atual['Quantidade'])
            old_total = float(venda_atual['Valor Total'])
            
            col_ev1, col_ev2 = st.columns(2)
            if col_ev1.button("🗑️ Cancelar Venda e Estornar Estoque"):
                try:
                    # Devolve quantidade ao estoque
                    if not df_estoque.empty and old_prod in df_estoque['Produto'].values:
                        est_item = df_estoque[df_estoque['Produto'] == old_prod].iloc[0]
                        novo_qtd_est = int(est_item['Quantidade']) + old_qtd
                        supabase.table("estoque").update({"quantidade": novo_qtd_est}).eq("id", est_item['id']).execute()
                    
                    # Remove venda
                    supabase.table("vendas").delete().eq("id", venda_atual['id']).execute()
                    
                    # Remove do financeiro correspondente
                    fin_match = df_financeiro[(df_financeiro['Descrição'].str.contains(old_prod, na=False)) & (df_financeiro['Valor'] == old_total)]
                    if not fin_match.empty:
                        supabase.table("financeiro").delete().eq("id", fin_match.iloc[0]['id']).execute()
                    
                    st.success("Venda cancelada, estoque estornado e financeiro corrigido com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cancelar venda: {e}")
        else:
            st.info("Nenhuma venda registrada para edição.")

    st.subheader("📜 Histórico Geral de Vendas")
    if not df_vendas.empty:
        cols_venda_exibir = [c for c in ['Data', 'Cliente', 'Produto', 'Quantidade', 'Valor Total'] if c in df_vendas.columns]
        st.dataframe(df_vendas[cols_venda_exibir].style.format({'Valor Total': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
    else:
        st.info("Nenhuma venda registrada até o momento.")

# ==========================================
# ABA 3: FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("💰 Gestão Financeira & Caixa")
    
    with st.expander("📝 Registrar Movimentação Manual (Despesa / Entrada)"):
        with st.form("form_financeiro_manual", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                desc = st.text_input("Descrição da Transação (Ex: Conta de Luz, Aluguel, Insumos)")
                tipo = st.selectbox("Tipo de Movimento", ["Saída", "Entrada"])
            with col_f2:
                valor = st.number_input("Valor Monetário (R$)", min_value=0.01, step=0.01, format="%.2f")
                categoria_fin = st.selectbox("Categoria Financeira", ["Operacional", "Despesas Fixas", "Impostos", "Fornecedores", "Investimentos", "Outros"])
            
            btn_fin = st.form_submit_button("Salvar Transação no Livro Caixa")
            
            if btn_fin:
                if not desc.strip():
                    st.error("A descrição é obrigatória.")
                else:
                    try:
                        supabase.table("financeiro").insert({
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "descricao": desc.strip(),
                            "tipo": tipo,
                            "valor": float(valor),
                            "categoria": categoria_fin
                        }).execute()
                        st.success("✅ Transação financeira registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar transação: {e}")

    with st.expander("🗑️ Excluir Lançamento Financeiro Manual"):
        st.warning("Nota: Vendas geram lançamentos automáticos. Para estorná-las, utilize a aba de Vendas.")
        if not df_financeiro.empty and 'id' in df_financeiro.columns:
            opcoes_exclusao = []
            for _, row in df_financeiro.iterrows():
                opcoes_exclusao.append(f"ID: {row['id']} | {row['Data']} | {row['Tipo']} | {row['Descrição']} | R$ {row['Valor']:.2f}")
                
            transacao_excluir = st.selectbox("Selecione o registro a apagar:", opcoes_exclusao)
            if st.button("Apagar Registro Selecionado"):
                id_excluir = transacao_excluir.split("|")[0].replace("ID:", "").strip()
                try:
                    supabase.table("financeiro").delete().eq("id", id_excluir).execute()
                    st.success("Registro financeiro apagado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao apagar registro: {e}")
        else:
            st.info("Nenhum registro financeiro disponível.")

    dados_fin = df_financeiro.copy()
    if not dados_fin.empty:
        entradas = dados_fin[dados_fin['Tipo'] == 'Entrada']['Valor'].sum()
        saidas = dados_fin[dados_fin['Tipo'] == 'Saída']['Valor'].sum()
        saldo = entradas - saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:.2f}", delta="Receitas")
        c2.metric("Total Saídas", f"R$ {saidas:.2f}", delta="- Despesas", delta_color="inverse")
        c3.metric("Saldo Líquido Atual", f"R$ {saldo:.2f}", delta="Resultado Caixa")
        
        st.subheader("Extrato Consolidado")
        cols_fin_exibir = [c for c in ['Data', 'Descrição', 'Tipo', 'Categoria', 'Valor'] if c in dados_fin.columns]
        st.dataframe(dados_fin[cols_fin_exibir].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True, use_container_width=True)
    else:
        st.info("Nenhuma movimentação financeira registrada.")

# ==========================================
# ABA 4: FORNECEDORES
# ==========================================
with tab_fornecedores:
    st.subheader("🤝 Cadastro & Gestão de Fornecedores")
    
    with st.expander("➕ Adicionar Novo Fornecedor"):
        with st.form("form_forn_novo", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nome_forn = st.text_input("Nome / Razão Social *")
                contato_forn = st.text_input("Telefone / WhatsApp")
            with col_f2:
                email_forn = st.text_input("E-mail Comercial")
                cat_forn = st.text_input("Categoria de Produtos Fornecidos")
            
            btn_forn = st.form_submit_button("Cadastrar Fornecedor")
            
            if btn_forn:
                if not nome_forn.strip():
                    st.error("O nome do fornecedor é obrigatório.")
                else:
                    try:
                        supabase.table("fornecedores").insert({
                            "nome": nome_forn.strip(),
                            "contato": contato_forn,
                            "email": email_forn,
                            "categoria_produto": cat_forn
                        }).execute()
                        st.success("✅ Fornecedor cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {e}")

    if not df_fornecedores.empty:
        st.subheader("Lista de Fornecedores Ativos")
        cols_forn_exibir = [c for c in ['Nome', 'Contato', 'E-mail', 'Categoria de Produto'] if c in df_fornecedores.columns]
        st.dataframe(df_fornecedores[cols_forn_exibir], hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum fornecedor cadastrado na nuvem.")

# ==========================================
# ABA 5: CLIENTES (CRM)
# ==========================================
with tab_clientes:
    st.subheader("👥 Gestão de Relacionamento com Clientes (CRM)")
    
    with st.expander("➕ Cadastrar Novo Cliente"):
        with st.form("form_cliente_novo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome_cli = st.text_input("Nome Completo *")
                tel_cli = st.text_input("Telefone de Contato")
            with col2:
                email_cli = st.text_input("E-mail do Cliente")
                end_cli = st.text_input("Endereço Completo")
            
            btn_cad_cli = st.form_submit_button("Salvar Registro de Cliente")
            
            if btn_cad_cli:
                if not nome_cli.strip():
                    st.error("O nome do cliente é obrigatório.")
                else:
                    try:
                        supabase.table("clientes").insert({
                            "nome": nome_cli.strip(),
                            "telefone": tel_cli,
                            "email": email_cli,
                            "endereco": end_cli
                        }).execute()
                        st.success("✅ Cliente cadastrado com sucesso no CRM!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar cliente: {e}")

    if not df_clientes.empty:
        st.subheader("Base de Clientes Cadastrados")
        cols_cli_exibir = [c for c in ['Nome', 'Telefone', 'E-mail', 'Endereço'] if c in df_clientes.columns]
        st.dataframe(df_clientes[cols_cli_exibir], hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum cliente cadastrado no momento.")

# ==========================================
# ABA 6: RELATÓRIOS & BI (BUSINESS INTELLIGENCE)
# ==========================================
with tab_relatorios:
    st.subheader("📊 Business Intelligence & Indicadores de Desempenho")
    
    if not df_vendas.empty or not df_estoque.empty or not df_financeiro.empty:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        total_vendas_val = df_vendas['Valor Total'].sum() if not df_vendas.empty and 'Valor Total' in df_vendas.columns else 0.0
        total_produtos_est = df_estoque['Quantidade'].sum() if not df_estoque.empty and 'Quantidade' in df_estoque.columns else 0
        total_cadastros_cli = len(df_clientes) if not df_clientes.empty else 0
        lucro_liquido = 0.0
        if not df_financeiro.empty and 'Tipo' in df_financeiro.columns and 'Valor' in df_financeiro.columns:
            ent = df_financeiro[df_financeiro['Tipo'] == 'Entrada']['Valor'].sum()
            sai = df_financeiro[df_financeiro['Tipo'] == 'Saída']['Valor'].sum()
            lucro_liquido = ent - sai
        
        col_m1.metric("Faturamento Bruto", f"R$ {total_vendas_val:.2f}")
        col_m2.metric("Saldo Líquido em Caixa", f"R$ {lucro_liquido:.2f}")
        col_m3.metric("Volume em Estoque", f"{total_produtos_est} un.")
        col_m4.metric("Base de Clientes", f"{total_cadastros_cli}")
        
        st.markdown("---")
        st.markdown("### 📈 Desempenho de Vendas por Produto")
        if not df_vendas.empty and 'Produto' in df_vendas.columns and 'Valor Total' in df_vendas.columns:
            vendas_por_produto = df_vendas.groupby('Produto')['Valor Total'].sum().reset_index()
            st.bar_chart(vendas_por_produto.set_index('Produto'))
        else:
            st.info("Dados insuficientes para gerar gráficos de vendas.")
            
        st.markdown("---")
        st.markdown("### 📦 Valoração do Estoque por Categoria")
        if not df_estoque.empty and 'Categoria' in df_estoque.columns:
            df_estoque['Valor_Total_Item'] = df_estoque['Quantidade'] * df_estoque['Valor Unitário']
            est_por_cat = df_estoque.groupby('Categoria')['Valor_Total_Item'].sum().reset_index()
            st.bar_chart(est_por_cat.set_index('Categoria'))
        else:
            st.info("Dados insuficientes para gerar gráficos de estoque.")
    else:
        st.info("Cadastre dados no sistema para gerar relatórios e gráficos analíticos.")
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
