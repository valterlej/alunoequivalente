import streamlit as st
import pandas as pd
import datetime
from funcoes_2024 import filtrar_cursos
from funcoes_2024 import filtrar_tipos_cursos
from funcoes_2024 import obter_parametros_curso

dados = pd.read_excel('assets/relacao_cursos.xlsx', index_col=0)

tab_cursos, tab_ciclos, tab_simulacao = st.tabs(["Parâmetros de Curso", "Parâmetros de Ciclo", "Simulação"])

with tab_cursos:
    tipos = filtrar_tipos_cursos(dados)
    tipo_selecionado = st.selectbox("Selecione um tipo de curso",tipos,)

    cursos = filtrar_cursos(dados, tipo_selecionado)
    curso_selecionado = st.selectbox("Selecione um curso",cursos,)

    peso, esforco, carga_horaria, agro = obter_parametros_curso(curso_selecionado, tipo_selecionado, dados)
    bonus = 0.5 if agro else 0.0

    CHC = int(st.number_input("Carga horária do curso", value=int(carga_horaria), min_value=0, max_value=5000))
    PC = float(st.number_input("Peso do curso", value=peso, step=0.5, min_value=0.0, max_value=2.5))
    B = float(st.number_input("Bônus agropecuária", value=bonus, step=0.5, min_value=0.0, max_value=0.5))

with tab_ciclos:
    DIC = st.date_input("Início do ciclo", datetime.date(2027,1,1), format='DD/MM/YYYY')
    DPFC = st.date_input("Final do ciclo", datetime.date(2029,12,31), format='DD/MM/YYYY')
    MAT_INI = int(st.number_input("Matrículas iniciais do ciclo", value=40, min_value=0, max_value=200))

with tab_simulacao:
    ANOS_REF = st.slider("Selecione os anos de referência", 2020, 2040, (2027, 2031))
    EVS = float(st.number_input("Fator de evasão anual", value=0.125, step=0.05, min_value=0.0, max_value=1.0))

