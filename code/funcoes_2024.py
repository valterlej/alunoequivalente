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
    