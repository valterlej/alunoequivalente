from utils import txt_to_date
from utils import dias_entre
from utils import adicionar_dias

def filtrar_tipos_cursos(dados):
    tipos = dados["tipo de curso"]
    tipos = list(set(tipos))
    tipos = [t.replace("\\","").replace("\"","").replace("","").replace("•","").replace("“","").replace("”","") for t in tipos]
    tipos = sorted(tipos)
    tipos.remove("FORMACAO INICIAL")
    tipos.remove("FORMACAO CONTINUADA")
    tipos.remove("EDUCACAO INFANTIL")
    tipos.remove("ENSINO FUNDAMENTAL (ANOS FINAIS)")
    tipos.remove("ENSINO FUNDAMENTAL (ANOS INICIAIS)")
    tipos.remove("ENSINO FUNDAMENTAL I")
    tipos.remove("ENSINO FUNDAMENTAL II")
    tipos.remove("ENSINO MEDIO")
    return tipos

def filtrar_cursos(dados, tipo):
    dt = dados[dados["tipo de curso"] == tipo]
    cursos = dt["nome do curso"]
    cursos = list(set(cursos))
    cursos = [c.replace("\\","").replace("\"","").replace("","").replace("•","").replace("“","").replace("”","") for c in cursos]
    cursos = sorted(cursos)
    return cursos

def obter_parametros_curso(nome_curso, tipo_curso, dados):
    dt = dados[dados["nome do curso"] == nome_curso]
    dt = dt[dados["tipo de curso"] == tipo_curso]
    cdata = dt.iloc[0]
    peso = cdata["peso"]
    esforco = cdata["fator esforço curso"]
    carga_horaria = cdata["Carga horária Catálogo"]
    agro = True if cdata["Curso de Agropecuária"] == "SIM" else False
    return peso, esforco, carga_horaria, agro

def obter_periodo_analisado(ano_ref):
    DIP1P = txt_to_date("01/01/"+str(ano_ref-2))
    DFP1P = txt_to_date("31/12/"+str(ano_ref-2))
    return DIP1P, DFP1P

"""
ano_ref = ano de referência para o cálculo do aluno equivalente
DIP1P = Data de início do período analisado
DFP1P = Data de término do período analisado
DIC = data de início do ciclo
DTC = data de término do ciclo
QTDC = quantidade total de dias do ciclo
CHM = carga horária para matriz (ajustada de acordo com o catálogo)
CHMD = carga horária média diária
CHA = carga horária anualizada
FECH = fator de equalização de carga horária
 
DACP1 = ciclos que começam antes do início do período analisado e terminam 
depois do período analisado - médio e graduações na maior parte do tempo
DACP2 = ciclos que começaram dentro do período analisado e terminaram depois do final do
período analisado (ciclos com duração parcial em relação ao período analisado)
DACP3 = ciclos que começam antes do início do período analisado e terminam dentro do período analisado
e depois do início do período analisado (ciclos com duração parcial em relação ao período analisado)
DACP4 = ciclos que começaram depois do início do período analisado e terminaram antes do final 
do período analisado (ciclos com duração parcial em relação ao período analisado)
**** errado na norma --- são ciclos que ocorrem completamente dentro do período analisado
DACP5 = ciclos que começaram antes do início do período analisado e terminaram antes do 
início do período analisado (ciclos que terminaram antes do início do período, mas que ainda possuem alunos 
matriculados no ciclo)
FEDA = fator de qualização de dias ativos
FECHDA = fator de equalização de carga horária e dias ativos
MECHDA = matrículas equalizadas por carga horária e dias ativos
QTM1P = matrículas ativas no período analisado
PC = peso do curso
MP = matrículas ponderadas
B = bonificação agropecuária
E = fator de esforço do curso
"""
def calcular_aluno_equivalente(ano_ref, DIC, DTC, CHM, QTM1P, PC, B, E):
    DIP1P, DFP1P = obter_periodo_analisado(ano_ref)

    # dias totais do ciclo
    QTDC = dias_entre(DTC, DIC) + 1
    
    # carga horária média diária
    CHMD = CHM / QTDC   ### quanto menor, melhor(!)
    
    # carga horária anualizada
    CHA = CHMD * 365 if QTDC > 365 else CHM
    
    # fator de equalização de carga horária
    FECH = CHA / 800
    
    # dias ativos do ciclo no período
    DACP1 = DACP2 = DACP3 = DACP4 = DACP5 = 0
    if DTC > DFP1P and DIC < DIP1P:
        DACP1 = dias_entre(DFP1P, DIP1P) + 1        
    elif DTC > DFP1P and DIC > DIP1P: # B
        DACP2 = dias_entre(DFP1P, DIC) + 1
    elif DIC < DIP1P and (DTC > DIP1P and DTC < DFP1P): # C ---
        DACP3 = dias_entre(DTC, DIP1P) + 1
    elif DTC < DFP1P and DIC > DIP1P: # D
        DACP4 = dias_entre(DTC, DIC) + 1
    else:
        DACP5 = (dias_entre(DFP1P, DIP1P) + 1) / 2.0 ## esse cálculo pode ter sido alterado(!)
    
    # fator de equalização de dias ativos
    FEDA = (DACP1 + DACP2 + DACP3 + DACP4 + DACP5) / ((dias_entre(DFP1P, DIP1P) + 1) if (dias_entre(DTC, DIC) + 1) >= 365 else (dias_entre(DTC, DIC) + 1))
    
    # fator de equalização de carga horária e dias ativos
    FECHDA = FECH * FEDA
    
    # cálculo das matrículas equalizadas por carga horária e dias ativos
    if DACP5 == 0:
        MECHDA = FECHDA * QTM1P
    elif dias_entre(DIP1P,DTC) > 1095:
        MECHDA = 0
    else:
        MECHDA = FECHDA * QTM1P * 0.5

    # ponderação
    MP = MECHDA * PC
    
    # bonificação
    BA = MP * B # se agro vale 1/2, caso contrário, zero
    
    # totalização
    MT = MP + BA
    
    # fator de esforço? ainda não é usado
    #MT = MT * E
    return MT

def criar_ciclos_simulacao(dados_simulacao, data_inicio, anos):
    ciclos = []
    for _, curso in dados_simulacao.iterrows():
        nome = curso['Nome']
        carga_horaria = curso['Carga horária']
        ano_inicio_oferta = curso['Início da oferta']
        ano_inicio_oferta = txt_to_date(data_inicio+"/"+str(ano_inicio_oferta), format="%d/%m/%Y")
        ano_termino_oferta = curso['Término da oferta']
        ano_termino_oferta = txt_to_date(data_inicio+"/"+str(ano_termino_oferta), format="%d/%m/%Y")
        peso = curso['Peso do curso']
        bonus = curso['Bônus']
        vagas = curso['Vagas ocupadas']
        fator_evasao = curso['Fator evasão anual']
        taxa_conclusao = curso['Taxa de conclusão']
        duracao = curso['Duração']
        for ano in range(anos[0],anos[1]+1):
            if ano_inicio_oferta.year <= ano and ano_termino_oferta.year >= ano:
                inicio_ciclo = txt_to_date(data_inicio+"/"+str(ano), format="%d/%m/%Y")
                fim_ciclo = adicionar_dias(inicio_ciclo, 30 * (curso["Duração"]-1))
                ciclo = {}
                ciclo["Nome"] = nome
                ciclo["Carga horária"] = carga_horaria
                ciclo["Duração"] = duracao
                ciclo["Vagas ocupadas"] = vagas
                ciclo["Peso do curso"] = peso
                ciclo["Bonus"] = bonus
                ciclo["Fator evasão anual"] = fator_evasao
                ciclo["Taxa de conclusão"] = taxa_conclusao
                ciclo["Ano"] = ano
                ciclo["Data início"] = '{}/{}/{}'.format(inicio_ciclo.day, inicio_ciclo.month, inicio_ciclo.year)
                ciclo["Data término"] = '{}/{}/{}'.format(fim_ciclo.day, fim_ciclo.month, fim_ciclo.year)
                ciclos.append(ciclo)
    return ciclos

"""
Estima o número de matrículas de um curso 

duracao = duração do curso em meses
"""
def simular_numero_matriculas_ativas_ciclos(matriculas_iniciais, ano_ciclo, ano_ref, taxa_evasao, taxa_conclusao, duracao):
    ano_calculo = ano_ref-2
    mat = matriculas_iniciais

    if ano_calculo < ano_ciclo : return 0
    
    # diminuir evadidos por ano
    for _ in range(ano_ciclo, ano_calculo+1):
        mat = mat * (1 - taxa_evasao)

    # diminuir os formados se existirem
    if (ano_calculo - ano_ciclo) > (duracao-1)/12:
        mat = mat - matriculas_iniciais * taxa_conclusao

    return int(max(mat, 0))


"""
Essa função simula a evolução dos ciclos ao longo dos anos considerando os parâmetros 
de taxa de evasão anual e taxa de aprovação.
"""
def calcular_matriculas_totais_ano(ano, valor_MT, ciclos, simular_saidas=True):

    # filtrar os ciclos de dois até dois anos antes, ou seja, os ciclos que serão usado para calcular MT
    ciclos_selecionados = [ciclo for ciclo in ciclos if ciclo["Ano"] <= ano-2]

    ciclos_calculados = []
    for ciclo in ciclos_selecionados:
        
        if simular_saidas:
            mat_ativas = simular_numero_matriculas_ativas_ciclos(ciclo["Vagas ocupadas"], 
                                                             txt_to_date(ciclo["Data início"], format="%d/%m/%Y").year, 
                                                             ano, 
                                                             ciclo["Fator evasão anual"], 
                                                             ciclo["Taxa de conclusão"], 
                                                             ciclo["Duração"])
        else:
            mat_ativas = ciclo["Vagas ocupadas"]

        mt_ciclo = calcular_aluno_equivalente(ano, 
                                              txt_to_date(ciclo["Data início"], format="%d/%m/%Y"),
                                              txt_to_date(ciclo["Data término"], format="%d/%m/%Y"),
                                              ciclo["Carga horária"], 
                                              mat_ativas,
                                              ciclo["Peso do curso"],
                                              ciclo["Bonus"], 1)
        if mt_ciclo < 0:
            mt_ciclo = 0
        ciclo["Matrícula ativas no período"] = mat_ativas
        ciclo["Matrículas totais"] = mt_ciclo
        ciclo["R$"] = mt_ciclo * valor_MT

        if mt_ciclo != 0:
            ciclos_calculados.append(ciclo)

    return ciclos_calculados