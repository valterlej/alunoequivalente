from utils import txt_to_date
from utils import dias_entre
from utils import adicionar_dias

def filtrar_dados_v2(dados):
    dados = dados[dados["tipo de curso"] != "FORMACAO CONTINUADA"]
    dados = dados[dados["tipo de curso"] != "FORMACAO INICIAL"]
    dados = dados[dados["tipo de curso"] != "QUALIFICACAO PROFISSIONAL (FIC)"]
    dados = dados[dados["tipo de curso"] != "ESPECIALIZACAO (LATO SENSU)"]
    dados = dados[dados["tipo de curso"] != "MESTRADO"]
    dados = dados[dados["tipo de curso"] != "MESTRADO PROFISSIONAL"]
    dados = dados[dados["tipo de curso"] != "DOUTORADO"]
    return dados

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
    elif DTC < DFP1P and DIC < DIP1P: # C
        DACP3 = dias_entre(DTC, DIP1P) + 1
    elif DTC < DFP1P and DIC > DIP1P: # D
        DACP4 = dias_entre(DTC, DIC) + 1
    else:
        DACP5 = (dias_entre(DFP1P, DIP1P) + 1) / 2.0 ## esse cálculo pode ter sido alterado(!)
    
    # fator de equalização de dias ativos
    FEDA = (DACP1 + DACP2 + DACP3 + DACP4 + DACP5) / ((dias_entre(DFP1P, DIP1P) + 1) if (dias_entre(DTC, DIC) + 1) >= 365 else (dias_entre(DTC, DIC) + 1))
    print(DACP1 + DACP2 + DACP3 + DACP4 + DACP5)
    print(FEDA)
    # fator de equalização de carga horária e dias ativos
    FECHDA = FECH * FEDA
    print(FECHDA)
    # cálculo das matrículas equalizadas por carga horária e dias ativos
    if (dias_entre(DFP1P, DTC) + 1) / 365 < 3: 
        MECHDA = FECHDA * QTM1P
    else: # deveria ter se formado a mais de três anos -- na prática, até 3 anos conta 1/2 e depois 1/4
        MECHDA = FECHDA * QTM1P * 0.5
    print(MECHDA)
    # ponderação
    MP = MECHDA * PC
    print(MP)
    # bonificação
    BA = MP * B # se agro vale 1/2, caso contrário, zero
    print(BA)
    # totalização
    MT = MP + BA
    print(MT)
    # fator de esforço?
    #MT = MT * E
    #print(MT)
    return MT

def criar_ciclos_simulacao(dados_simulacao, data_inicio, data_termino, anos):
    ciclos = []
    for index, curso in dados_simulacao.iterrows():
        nome = curso['Nome']
        carga_horaria = curso['Carga horária']
        peso = curso['Peso do curso']
        bonus = curso['Bônus']
        vagas = curso['Vagas ocupadas']
        fator_evasao = curso['Fator evasão anual']
        taxa_conclusao = curso['Taxa de conclusão']
        for ano in range(anos[0],anos[1]+1):
            inicio_ciclo = txt_to_date(data_inicio+"/"+str(ano), format="%d/%m/%Y")
            #fim_ciclo = txt_to_date(data_termino+"/"+str(ano), format="%d/%m/%Y")
            fim_ciclo = adicionar_dias(inicio_ciclo, 30 * curso["Duração"])
            #mt_ciclo = calcular_aluno_equivalente(ano, inicio_ciclo, fim_ciclo, carga_horaria, vagas, peso, bonus, 1)
            ciclo = {}
            ciclo["Nome"] = nome
            ciclo["Carga horária"] = carga_horaria
            ciclo["Vagas ocupadas"] = vagas
            ciclo["Peso do curso"] = peso
            ciclo["Bonus"] = bonus
            ciclo["Fator evasão anual"] = fator_evasao
            ciclo["Taxa de conclusão"] = taxa_conclusao
            ciclo["Ano"] = ano
            ciclo["Data início"] = '{}/{}/{}'.format(inicio_ciclo.day, inicio_ciclo.month, inicio_ciclo.year)
            ciclo["Data término"] = '{}/{}/{}'.format(fim_ciclo.day, fim_ciclo.month, fim_ciclo.year)
            #ciclo["Matrículas totais"] = (0 if mt_ciclo < 0 else mt_ciclo)
            ciclos.append(ciclo)
    return ciclos

def calcular_matriculas_totais_ano(ano, valor_MT, ciclos):

    # filtrar os ciclos de dois até dois anos antes
    ciclos_selecionados = [ciclo for ciclo in ciclos if ciclo["Ano"] <= ano-2]

    for ciclo in ciclos_selecionados:
        mt_ciclo = calcular_aluno_equivalente(ano, 
                                              txt_to_date(ciclo["Data início"], format="%d/%m/%Y"),
                                              txt_to_date(ciclo["Data término"], format="%d/%m/%Y"),
                                              ciclo["Carga horária"], 
                                              ciclo["Vagas ocupadas"],
                                              ciclo["Peso do curso"],
                                              ciclo["Bonus"], 1)
        if mt_ciclo < 0:
            mt_ciclo = 0
        ciclo["Matrículas totais"] = mt_ciclo
        ciclo["R$"] = mt_ciclo * valor_MT

    # calcular as matriculas totais

    return ciclos_selecionados