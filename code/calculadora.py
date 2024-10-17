import warnings
warnings.filterwarnings("ignore")
import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import datetime
import io
from funcoes import filtrar_cursos
from funcoes import filtrar_tipos_cursos
from funcoes import obter_parametros_curso
from funcoes import calcular_aluno_equivalente
from funcoes import criar_ciclos_simulacao
from funcoes import calcular_matriculas_totais_ano

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 160px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)
st.sidebar.image("code/assets/irati-vertical.png",width=170)
st.sidebar.header("Calculadoras", divider="green")
calculadora = st.sidebar.selectbox(
    "Selecione",
    ("Simples", "Múltiplos anos")
)
st.sidebar.header("Referências", divider="green")
st.sidebar.link_button("Portaria 646/2022","https://www.in.gov.br/en/web/dou/-/portaria-n-646-de-25-de-agosto-de-2022-*-430796902", use_container_width=True)
st.sidebar.link_button("Relação de cursos - 2024","https://docs.google.com/spreadsheets/d/12J-M2DVTdvX26cUv5O65DSJpzryeZiZC/edit?usp=sharing&ouid=101349476735007398157&rtpof=true&sd=true",use_container_width=True)
st.sidebar.header("Desenvolvedores", divider="green")
st.sidebar.link_button("Valter Estevam","mailto:valter.junior@ifpr.edu.br", use_container_width=True)
st.sidebar.link_button("João Cruz","mailto:joão.cruz@ifpr.edu.br", use_container_width=True)

dados = pd.read_excel('code/assets/relacao_cursos.xlsx', index_col=0)

if calculadora == "Simples":
    st.header("Calculadora Simples", divider="green")

    tab_cursos, tab_ciclos = st.tabs(["Parâmetros de Curso", "Parâmetros de ciclo"])

    with tab_cursos:
        tipos = filtrar_tipos_cursos(dados)
        tipo_selecionado = st.selectbox("Selecione um tipo de curso",tipos,)

        cursos = filtrar_cursos(dados, tipo_selecionado)
        curso_selecionado = st.selectbox("Selecione um curso",cursos,)

        peso, esforco, carga_horaria, agro = obter_parametros_curso(curso_selecionado, tipo_selecionado, dados)
        bonus = 0.5 if agro else 0.0

        CHM = int(st.number_input("Carga horária do curso (considerada pela matriz)", value=int(carga_horaria), min_value=0, max_value=5000))
        PC = float(st.number_input("Peso do curso", value=peso, step=0.5, min_value=0.0, max_value=5.0))
        B = float(st.number_input("Bônus agropecuária", value=bonus, step=0.5, min_value=0.0, max_value=0.5))
        E = float(st.number_input("Esforço", value=esforco, step=0.01, min_value=1.0, max_value=1.5))

    with tab_ciclos:
        DIC = st.date_input("Início do ciclo", datetime.date(2027,2,6), format='DD/MM/YYYY')
        DTC = st.date_input("Final do ciclo", datetime.date(2029,12,31), format='DD/MM/YYYY')
        MAT_INI = int(st.number_input("Matrículas ativas no período analisado", value=40, min_value=0, max_value=200))
        DIC = datetime.datetime.combine(DIC, datetime.datetime.min.time())
        DTC = datetime.datetime.combine(DTC, datetime.datetime.min.time())
        ANO_REF = int(st.number_input("Ano de referência", value=int(2025), min_value=2022, max_value=2040))
        MT = calcular_aluno_equivalente(ANO_REF, DIC, DTC, CHM, MAT_INI, PC, B, E)
        MT = 0 if MT < 0 else MT
        st.number_input("Matrículas totais", value=MT, disabled=False)


else: # múltiplos anos
    st.header("Calculadora para Múltiplos Anos e Cursos", divider="green")
    
    tab_simulacao_parametros, tab_simulacao_calculos = st.tabs(["Parâmetros de simulação","Matrículas totais e R$"])
    
    with tab_simulacao_parametros:
        DIA_MES_INICIO = st.text_input("DD/MM início de ciclos", "07/02")
        ANOS_SIMULACAO = st.slider("Selecione os anos para simular ciclos", 2018, 2045, (2018, 2030))
        
        buffer = io.BytesIO()
        df1 = pd.read_excel("code/assets/cursos_irati_modelo.xlsx")
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df1.to_excel(writer, sheet_name='Dados',index=False)
                writer.close()
                st.download_button(
                label="Baixar uma planilha de exemplo em formato MS Excel",
                data=buffer,
                file_name="cursos.xlsx",
                mime="application/vnd.ms-excel"
                )

        
        uploaded_file = st.file_uploader("Carregue um arquivo xls ou xlsx contendo os dados dos cursos.", type=".xlsx")
        
        if uploaded_file is not None:
            try:
                #read csv
                dados_cursos_simulacao = pd.read_excel(uploaded_file)
                st.write("Parâmetros dos cursos ofertados")
                st.dataframe(dados_cursos_simulacao, use_container_width=True)
            except Exception as e:
                st.write("Formato inválido. Baixe e utilize o modelo disponbilizado.") 

    with tab_simulacao_calculos:    
        if uploaded_file is not None:
            try:
                ciclos_simulacao = criar_ciclos_simulacao(dados_cursos_simulacao, DIA_MES_INICIO, ANOS_SIMULACAO)
                ano_filtrar = int(st.number_input("Ano de referência", value=int(2025), min_value=2023, max_value=2040))
                valor_MT = int(st.number_input("Valor médio por MT (é um valor estimado)", value=1134.79, min_value=800.00, max_value=2000.00))
                st.write("Ciclos ofertados e contabilizados para a matriz")
                ciclos_sel = calcular_matriculas_totais_ano(ano_filtrar, valor_MT, ciclos_simulacao)
                st.dataframe(pd.DataFrame.from_dict(ciclos_sel),use_container_width=True)
                st.number_input("Matrículas totais do campus", value=sum([c["Matrículas totais"] for c in ciclos_sel]), disabled=True)
                st.number_input("Orçamento do campus (matrículas) - R$", value=sum([c["R$"] for c in ciclos_sel]), disabled=True) 
            except Exception as e:
                st.write("Há algum parâmetro incorreto. Baixe e utilize o modelo de planilha disponbilizado.") 
