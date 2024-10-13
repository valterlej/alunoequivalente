import datetime

def txt_to_date(t, format="%d/%m/%Y"):
    return datetime.datetime.strptime(t, format)

def dias_entre(dt_fim, dt_ini):
    return (dt_fim - dt_ini).days

def adicionar_dias(data, dias):
    return data + datetime.timedelta(days = dias)