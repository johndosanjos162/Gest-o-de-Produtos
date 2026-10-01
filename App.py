import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES INICIAIS E TEMA
# ==========================================
st.set_page_config(layout="wide", page_title="Sistema ERP Integrado", page_icon="📦")

# CSS dinâmico adaptável para Modo Claro e Modo Escuro nativo do Streamlit
st.markdown("""
<style>
    /* Estilização Geral Adaptável */
    .main { padding: 20px; }
    .title-text { font-weight: 700; font-size: 2.2rem; margin-bottom: 20px; text-align: center; }
    
    /* Ajuste para Expander e Abas manterem legibilidade em ambos os temas */
    .stExpander, .stTabs { 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); 
        margin-bottom: 15px; 
        padding: 10px; 
    }
    
    /* Botões principais mantêm destaque consistente */
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
        st.markdown('<p class="title-text">🔐 Acesso Restrito</p>', unsafe_allow_html=True)
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            botao_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if botao_login:
                if usuario == "JOHN" and senha == "fgxv4VP0":
                    st.session_state.autenticado = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

if not st.session_state.autenticado:
    tela_login()
    st.stop()

# ==========================================
# BOTÃO DE LOGOUT NA BARRA LATERAL
# ==========================================
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
        st.error(f"Erro ao carregar dados de {nome_tabela}: {e}")
        return pd.DataFrame()

# Carregamento inicial dos dados da nuvem
df_estoque = carregar_dados_tabela("estoque")
df_vendas = carregar_dados_tabela("vendas")
df_financeiro = carregar_dados_tabela("financeiro")

# Normalização de colunas vazias
if df_estoque.empty:
    df_estoque = pd.DataFrame(columns=['id', 'produto', 'categoria', 'quantidade', 'limite_minimo', 'valor_unitario', 'preco_custo'])
if df_vendas.empty:
    df_vendas = pd.DataFrame(columns=['id', 'data', 'produto', 'quantidade', 'valor_total', 'lucro'])
if df_financeiro.empty:
    df_financeiro = pd.DataFrame(columns=['id', 'data', 'descricao', 'tipo', 'categoria', 'valor'])

# Padronização de nomes de colunas visualmente
if 'Produto' not in df_estoque.columns and 'produto' in df_estoque.columns:
    df_estoque = df_estoque.rename(columns={
        'produto': 'Produto',
        'categoria': 'Categoria',
        'quantidade': 'Quantidade',
        'limite_minimo': 'Limite Mínimo',
        'valor_unitario': 'Valor Unitário',
        'preco_custo': 'Preço de Custo'
    })

if 'Preço de Custo' not in df_estoque.columns:
    df_estoque['Preço de Custo'] = 0.00

if 'Data' not in df_vendas.columns and 'data' in df_vendas.columns:
    df_vendas = df_vendas.rename(columns={
        'data': 'Data',
        'produto': 'Produto',
        'quantidade': 'Quantidade',
        'valor_total': 'Valor Total',
        'lucro': 'Lucro'
    })

if 'Lucro' not in df_vendas.columns:
    df_vendas['Lucro'] = 0.00

if 'Data' not in df_financeiro.columns and 'data' in df_financeiro.columns:
    df_financeiro = df_financeiro.rename(columns={
        'data': 'Data',
        'descricao': 'Descrição',
        'tipo': 'Tipo',
        'categoria': 'Categoria',
        'valor': 'Valor'
    })

if 'Categoria' not in df_financeiro.columns:
    df_financeiro['Categoria'] = 'Geral'

# ==========================================
# ABAS PRINCIPAIS DO ERP
# ==========================================
tab_estoque, tab_vendas, tab_despesas, tab_financeiro, tab_dashboard = st.tabs([
    "📦 Estoque", 
    "🛒 Vendas", 
    "💡 Despesas do Comércio",
    "💰 Controle Financeiro Total", 
    "📊 Dashboard & Gráficos"
])

# ==========================================
# ABA 1: ESTOQUE
# ==========================================
with tab_estoque:
    st.subheader("📦 Gestão de Estoque")
    
    with st.expander("Adicionar Novo Produto"):
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
            
            btn_adicionar = st.form_submit_button("Cadastrar Produto")
            
            if btn_adicionar and nome:
                produto_existe = False
                if not df_estoque.empty:
                    produto_existe = df_estoque['Produto'].str.lower().eq(nome.strip().lower()).any()
                
                if produto_existe:
                    st.error(f"⚠️ Erro: O produto '{nome}' já está cadastrado no estoque!")
                else:
                    try:
                        supabase.table("estoque").insert({
                            "produto": nome.strip(),
                            "categoria": categoria,
                            "quantidade": int(qtd),
                            "limite_minimo": int(limite),
                            "valor_unitario": float(preco),
                            "preco_custo": float(preco_custo)
                        }).execute()
                        st.success("✅ Produto cadastrado com sucesso no Supabase!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar produto: {e}")

    with st.expander("Atualizar Estoque, Custos e Preços"):
        if not df_estoque.empty:
            produtos_disponiveis = df_estoque['Produto'].tolist()
            produto_selecionado = st.selectbox("Selecione o produto para atualizar:", produtos_disponiveis, key="select_update")
            
            item_atual = df_estoque[df_estoque['Produto'] == produto_selecionado].iloc[0]
            item_id = item_atual['id']
            quantidade_atual = item_atual['Quantidade']
            preco_atual = item_atual['Valor Unitário']
            custo_atual = item_atual['Preço de Custo']
            
            nova_quantidade = st.number_input("Nova Quantidade em Estoque", value=int(quantidade_atual), min_value=0, step=1)
            novo_custo = st.number_input("Novo Preço de Custo (R$)", value=float(custo_atual), min_value=0.0, step=0.01)
            novo_preco = st.number_input("Novo Valor Unitário / Venda (R$)", value=float(preco_atual), min_value=0.0, step=0.01)
            
            if st.button("Atualizar Dados"):
                try:
                    supabase.table("estoque").update({
                        "quantidade": int(nova_quantidade),
                        "preco_custo": float(novo_custo),
                        "valor_unitario": float(novo_preco)
                    }).eq("id", item_id).execute()
                    st.success("Dados atualizados com sucesso no Supabase!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.info("Nenhum produto cadastrado para atualizar.")

    with st.expander("Remover Produto"):
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
            st.warning("⚠ **Atenção: Os seguintes produtos estão com estoque baixo!**")
            for _, row in produtos_em_alerta.iterrows():
                st.error(f"📉 **{row['Produto']}**: Restam apenas {row['Quantidade']} unidades (Limite: {row['Limite Mínimo']})")
        
        dados_est['Valor Custo Total'] = dados_est['Quantidade'] * dados_est['Preço de Custo']
        dados_est['Valor Venda Total'] = dados_est['Quantidade'] * dados_est['Valor Unitário']
        
        total_investido = dados_est['Valor Custo Total'].sum()
        total_projetado = dados_est['Valor Venda Total'].sum()
        lucro_potencial = total_projetado - total_investido
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("💵 Dinheiro Investido (Custo)", f"R$ {total_investido:.2f}")
        c_m2.metric("🏷️ Valor Total de Venda", f"R$ {total_projetado:.2f}")
        c_m3.metric("📈 Lucro Potencial (Estoque)", f"R$ {lucro_potencial:.2f}")
        
        st.subheader("Estoque Atual")
        st.dataframe(dados_est[['Produto', 'Categoria', 'Quantidade', 'Preço de Custo', 'Valor Unitário', 'Valor Custo Total', 'Valor Venda Total']].style.format({'Preço de Custo': 'R$ {:.2f}', 'Valor Unitário': 'R$ {:.2f}', 'Valor Custo Total': 'R$ {:.2f}', 'Valor Venda Total': 'R$ {:.2f}'}), hide_index=True)
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
                custo_unit = float(item_est['Preço de Custo'])
                
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
                            "descricao": f"Venda automática: {prod_venda} ({qtd_venda} un)",
                            "tipo": "Entrada",
                            "categoria": "Vendas de Produtos",
                            "valor": float(vlr_total)
                        }).execute()
                        
                        st.success("✅ Venda registrada! Estoque baixado e entrada financeira lançada automaticamente.")
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
                        
                        fin_match = df_financeiro[(df_financeiro['Descrição'].str.contains(old_prod)) & (df_financeiro['Valor'] == old_total)]
                        if not fin_match.empty:
                            supabase.table("financeiro").delete().eq("id", fin_match.iloc[0]['id']).execute()
                        
                        st.success("Venda cancelada! Estoque estornado e lançamento financeiro removido.")
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
                            novo_lucro = (float(est_new['Valor Unitário']) - float(est_new['Preço de Custo'])) * nova_qtd
                            
                            supabase.table("estoque").update({"quantidade": novo_estoque_val}).eq("id", est_new['id']).execute()
                            supabase.table("vendas").update({
                                "produto": novo_prod,
                                "quantidade": int(nova_qtd),
                                "valor_total": float(novo_total),
                                "lucro": float(novo_lucro)
                            }).eq("id", venda_atual['id']).execute()
                            
                            fin_match = df_financeiro[(df_financeiro['Descrição'].str.contains(old_prod)) & (df_financeiro['Valor'] == old_total)]
                            if not fin_match.empty:
                                supabase.table("financeiro").update({
                                    "descricao": f"Venda automática: {novo_prod} ({nova_qtd} un)",
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

    st.subheader("Histórico de Vendas")
    if not df_vendas.empty:
        st.dataframe(df_vendas[['Data', 'Produto', 'Quantidade', 'Valor Total', 'Lucro']].style.format({'Valor Total': 'R$ {:.2f}', 'Lucro': 'R$ {:.2f}'}), hide_index=True)
    else:
        st.info("Nenhuma venda registrada ainda.")

# ==========================================
# ABA 3: DESPESAS DO COMÉRCIO
# ==========================================
with tab_despesas:
    st.subheader("💡 Controle de Despesas Operacionais do Comércio")
    st.write("Registre rapidamente contas como **Água, Energia/Luz, Internet, Aluguel** e gerencie os lançamentos incorretos.")
    
    sub_aba_cadastro, sub_aba_gerenciar = st.tabs(["➕ Nova Despesa", "✏️ Gerenciar, Editar ou Excluir Despesas"])
    
    with sub_aba_cadastro:
        with st.form("form_despesas_comercio"):
            c1, c2 = st.columns(2)
            with c1:
                categoria_despesa = st.selectbox(
                    "Categoria da Despesa", 
                    ["Energia / Luz", "Água", "Internet / Telefone", "Aluguel", "Manutenção", "Impostos e Taxas", "Outros"]
                )
                descricao_despesa = st.text_input("Descrição / Referência (Ex: Conta de Luz - Mês Referência)")
            with c2:
                valor_despesa = st.number_input("Valor da Despesa (R$)", min_value=0.01, step=0.01)
                data_despesa = st.date_input("Data do Vencimento / Pagamento", value=datetime.now())
                
            btn_salvar_despesa = st.form_submit_button("Lançar Despesa do Comércio", use_container_width=True)
            
            if btn_salvar_despesa and descricao_despesa:
                try:
                    data_str = f"{data_despesa} {datetime.now().strftime('%H:%M:%S')}"
                    supabase.table("financeiro").insert({
                        "data": data_str,
                        "descricao": descricao_despesa.strip(),
                        "tipo": "Saída",
                        "categoria": f"Despesa: {categoria_despesa}",
                        "valor": float(valor_despesa)
                    }).execute()
                    st.success(f"✅ Despesa de '{categoria_despesa}' lançada com sucesso no fluxo de caixa!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao registrar despesa: {e}")

    with sub_aba_gerenciar:
        st.write("### 📋 Histórico e Gestão de Despesas Cadastradas")
        dados_fin_gasto = df_financeiro.copy()
        
        if not dados_fin_gasto.empty:
            despesas_apenas = dados_fin_gasto[dados_fin_gasto['Tipo'] == 'Saída'].copy()
            
            if not despesas_apenas.empty:
                despesas_comercio = despesas_apenas[despesas_apenas['Categoria'].str.startswith('Despesa:')].copy()
                
                if not despesas_comercio.empty:
                    st.dataframe(despesas_comercio[['id', 'Data', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
                    
                    st.markdown("---")
                    st.write("#### 🛠️ Escolha uma Despesa para Excluir ou Editar")
                    
                    opcoes_despesas = []
                    for _, row in despesas_comercio.iterrows():
                        texto_op = f"ID: {row['id']} | {row['Data']} | {row['Categoria']} - {row['Descrição']} | R$ {row['Valor']:.2f}"
                        opcoes_despesas.append(texto_op)
                        
                    despesa_selecionada = st.selectbox("Selecione o registro da despesa:", opcoes_despesas)
                    id_selecionado = despesa_selecionada.split("|")[0].replace("ID:", "").strip()
                    
                    item_despesa_atual = despesas_comercio[despesas_comercio['id'].astype(str) == id_selecionado].iloc[0]
                    
                    cat_atual_limpa = item_despesa_atual['Categoria'].replace("Despesa: ", "").strip()
                    categorias_possiveis = ["Energia / Luz", "Água", "Internet / Telefone", "Aluguel", "Manutenção", "Impostos e Taxas", "Outros"]
                    idx_cat = categorias_possiveis.index(cat_atual_limpa) if cat_atual_limpa in categorias_possiveis else 0
                    
                    col_b1, col_b2 = st.columns(2)
                    
                    with col_b1:
                        if st.button("🗑️ Excluir Despesa Selecionada", use_container_width=True):
                            try:
                                supabase.table("financeiro").delete().eq("id", id_selecionado).execute()
                                st.success("Despesa excluída com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir despesa: {e}")
                                
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.form("form_editar_despesa"):
                        st.write("#### ✏️ Modificar Dados da Despesa")
                        nova_cat = st.selectbox("Nova Categoria", categorias_possiveis, index=idx_cat)
                        nova_desc = st.text_input("Nova Descrição", value=item_despesa_atual['Descrição'])
                        novo_vlr = st.number_input("Novo Valor (R$)", value=float(item_despesa_atual['Valor']), min_value=0.01, step=0.01)
                        
                        btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações da Despesa", use_container_width=True)
                        
                        if btn_salvar_edicao:
                            try:
                                supabase.table("financeiro").update({
                                    "descricao": nova_desc.strip(),
                                    "categoria": f"Despesa: {nova_cat}",
                                    "valor": float(novo_vlr)
                                }).eq("id", id_selecionado).execute()
                                st.success("Despesa atualizada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar despesa: {e}")
                else:
                    st.info("Nenhuma despesa do comércio cadastrada ainda.")
            else:
                st.info("Nenhuma saída registrada no sistema.")
        else:
            st.info("Nenhum dado financeiro registrado.")

# ==========================================
# ABA 4: CONTROLE FINANCEIRO TOTAL
# ==========================================
with tab_financeiro:
    st.subheader("💰 Gestão Financeira Completa (Fluxo de Caixa)")
    
    fin_tab_lancamento, fin_tab_extrato, fin_tab_analise = st.tabs(["➕ Novo Lançamento Manual", "📋 Extrato e Gestão", "📊 Relatórios e Indicadores"])
    
    with fin_tab_lancamento:
        st.write("### Registrar Outras Entradas ou Saídas Manuais")
        with st.form("form_fin_total"):
            c1, c2 = st.columns(2)
            with c1:
                tipo = st.selectbox("Tipo de Movimentação", ["Entrada", "Saída"])
                desc = st.text_input("Descrição / Histórico (Ex: Aporte, Venda Avulsa)")
            with c2:
                if tipo == "Entrada":
                    cat_fin = st.selectbox("Categoria", ["Serviços Prestados", "Aporte de Capital", "Rendimentos / Juros", "Outras Entradas"])
                else:
                    cat_fin = st.selectbox("Categoria", ["Compra de Mercadoria / Estoque", "Despesas Operacionais", "Salários / Pró-labore", "Outras Saídas"])
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
                
            data_lancamento = st.date_input("Data da Movimentação", value=datetime.now())
            
            btn_salvar_fin = st.form_submit_button("Salvar Lançamento Manual", use_container_width=True)
            
            if btn_salvar_fin and desc:
                try:
                    data_str = f"{data_lancamento} {datetime.now().strftime('%H:%M:%S')}"
                    supabase.table("financeiro").insert({
                        "data": data_str,
                        "descricao": desc.strip(),
                        "tipo": tipo,
                        "categoria": cat_fin,
                        "valor": float(valor)
                    }).execute()
                    st.success("✅ Transação financeira manual registrada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar transação: {e}")

    with fin_tab_extrato:
        st.write("### Histórico Unificado de Caixa (Vendas + Despesas + Manuais)")
        dados_fin = df_financeiro.copy()
        
        if not dados_fin.empty:
            col_f1, col_f2 = st.columns(2)
            filtro_tipo = col_f1.selectbox("Filtrar por Tipo", ["Todos", "Entrada", "Saída"])
            if filtro_tipo != "Todos":
                dados_fin = dados_fin[dados_fin['Tipo'] == filtro_tipo]
                
            categorias_disponiveis = ["Todas"] + list(dados_fin['Categoria'].unique()) if 'Categoria' in dados_fin.columns else ["Todas"]
            filtro_cat = col_f2.selectbox("Filtrar por Categoria", categorias_disponiveis)
            if filtro_cat != "Todas":
                dados_fin = dados_fin[dados_fin['Categoria'] == filtro_cat]

            st.dataframe(dados_fin[['id', 'Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
            
            st.markdown("---")
            st.write("#### Excluir Lançamento Financeiro")
            opcoes_exclusao = []
            for _, row in dados_fin.iterrows():
                texto = f"ID: {row['id']} | {row['Data']} | [{row['Tipo']}] {row['Categoria']} - {row['Descrição']} | R$ {row['Valor']:.2f}"
                opcoes_exclusao.append(texto)
                
            if opcoes_exclusao:
                transacao_excluir = st.selectbox("Selecione o lançamento para apagar:", opcoes_exclusao)
                if st.button("🗑️ Apagar Lançamento Selecionado"):
                    id_excluir = transacao_excluir.split("|")[0].replace("ID:", "").strip()
                    try:
                        supabase.table("financeiro").delete().eq("id", id_excluir).execute()
                        st.success("Transação apagada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao apagar: {e}")
        else:
            st.info("Nenhuma movimentação financeira registrada.")

    with fin_tab_analise:
        st.write("### 📊 Indicadores e Resumo de Caixa")
        dados_fin_completo = df_financeiro.copy()
        
        if not dados_fin_completo.empty:
            total_entradas = dados_fin_completo[dados_fin_completo['Tipo'] == 'Entrada']['Valor'].sum()
            total_saidas = dados_fin_completo[dados_fin_completo['Tipo'] == 'Saída']['Valor'].sum()
            saldo_caixa = total_entradas - total_saidas
            
            lucro_vendas = df_vendas['Lucro'].sum() if not df_vendas.empty else 0.0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🟢 Total de Entradas (Vendas + Outras)", f"R$ {total_entradas:.2f}")
            c2.metric("🔴 Total de Saídas (Despesas)", f"R$ {total_saidas:.2f}")
            c3.metric("💰 Saldo Líquido em Caixa", f"R$ {saldo_caixa:.2f}", delta=f"R$ {saldo_caixa:.2f}")
            c4.metric("📈 Lucro Bruto (Vendas)", f"R$ {lucro_vendas:.2f}")
            
            st.markdown("---")
            st.write("#### Despesas por Categoria")
            saidas_df = dados_fin_completo[dados_fin_completo['Tipo'] == 'Saída']
            if not saidas_df.empty:
                gasto_por_cat = saidas_df.groupby('Categoria')['Valor'].sum().reset_index()
                st.dataframe(gasto_por_cat.style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
            else:
                st.info("Nenhuma saída/despesa registrada para detalhar por categoria.")
        else:
            st.info("Cadastre movimentações financeiras para visualizar os relatórios.")

# ==========================================
# ABA 5: DASHBOARD & GRÁFICOS
# ==========================================
with tab_dashboard:
    st.subheader("📊 Dashboard Analítico e Monitoramento do Comércio")
    
    dados_fin_dash = df_financeiro.copy()
    
    if not dados_fin_dash.empty:
        total_entradas_dash = dados_fin_dash[dados_fin_dash['Tipo'] == 'Entrada']['Valor'].sum()
        total_saidas_dash = dados_fin_dash[dados_fin_dash['Tipo'] == 'Saída']['Valor'].sum()
        resultado_liquido = total_entradas_dash - total_saidas_dash
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("🟢 Total de Ganhos (Entradas)", f"R$ {total_entradas_dash:.2f}")
        col_m2.metric("🔴 Total de Perdas/Despesas", f"R$ {total_saidas_dash:.2f}")
        col_m3.metric("💼 Resultado Líquido", f"R$ {resultado_liquido:.2f}", delta=f"R$ {resultado_liquido:.2f}")
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.write("### 🥧 Distribuição de Entradas e Saídas (Gráfico de Pizza)")
            resumo_tipo = dados_fin_dash.groupby('Tipo')['Valor'].sum()
            if not resumo_tipo.empty:
                st.altair_chart(
                    alt.Chart(resumo_tipo.reset_index()).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="Valor", type="quantitative"),
                        color=alt.Color(field="Tipo", type="nominal", scale=alt.Scale(domain=['Entrada', 'Saída'], range=['#22c55e', '#ef4444'])),
                        tooltip=['Tipo', 'Valor']
                    ).properties(height=300),
                    use_container_width=True
                )
            else:
                st.info("Dados insuficientes para o gráfico de pizza.")

        with col_g2:
            st.write("### 🏷️ Despesas e Custos por Categoria")
            saidas_dash = dados_fin_dash[dados_fin_dash['Tipo'] == 'Saída']
            if not saidas_dash.empty:
                resumo_cat = saidas_dash.groupby('Categoria')['Valor'].sum().reset_index()
                st.altair_chart(
                    alt.Chart(resumo_cat).mark_bar(color='#f97316').encode(
                        x=alt.X('Categoria:N', sort='-y'),
                        y=alt.Y('Valor:Q'),
                        tooltip=['Categoria', 'Valor']
                    ).properties(height=300),
                    use_container_width=True
                )
            else:
                st.info("Nenhuma despesa cadastrada para exibir o gráfico de categorias.")
        
        st.markdown("---")
        st.write("### 📈 Histórico Geral de Transações Monitoradas")
        st.dataframe(dados_fin_dash[['Data', 'Tipo', 'Categoria', 'Descrição', 'Valor']].style.format({'Valor': 'R$ {:.2f}'}), hide_index=True)
        
    else:
        st.info("Nenhum dado financeiro ou de vendas registrado ainda para gerar o dashboard analítico.")
