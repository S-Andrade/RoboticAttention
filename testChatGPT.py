# -*- coding: utf-8 -*-
import json
import openai 
  
def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

api_key = load_api_key()
openai.api_key = api_key


def getPrompt(pistas):
    return f"""
        Tu és um elemento de uma equipa de investigação criminal. 
        O teu objetivo é relacionar as varias pistas enquanto falas com outros investigadores. Sendo que não deves resolver o caso. 
        Entre ``` estão as pistas que deves relacionar.
        És um cominador natural e consegues explicar qualquer tipo de informação de uma forma simples e rapida.
        Lembra-te que deves usar português europeu. Deves de usar um tom simpatico e informal.
        A tua resposta deve de ser sumarizada e deves extrair a informação mais importante e escreve-la numa versão simples, curta, simpatica e informal. 
        Deves de escrever tudo numa frase com no maximo 10 palavras.
        Deves de só responder ao que te foi perguntado, não des informação a mais!
        Só podes usar portugues europeu!
        Pistas: ```{pistas}```
    """


def chatGPT(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


with open('graph.json', encoding="utf8") as f:
    data = json.load(f)

nodes = ['SR.GAIA', 'ASSASINATO', 'OFICINA GAIA', 'MARIA', 'MIGUEL', 'MAUTO', 'EDUARDO', 'BRUNO', 'CARLA', 'CAFÉ', 'SARA', 'PÉ-DE-CABRA', 'CAMPO DE GOLF', 'RICARDO', 'CARTEIRA', 'CARRO', 'POSTO DE GASOLINA']


messages = []

while True: 
    message = input("User : ") 
    res = [ele for ele in nodes if(ele in message.upper())]

    if len(res) == 0:
        messages += [{"role": "user", "content": message}]
        response = chatGPT(messages)
        print(response)

    else:
        pistas = ""
        for d in data:
            if d['node_1']in res or d['node_2']in res:
                pistas += d['edge']

        messages = [{"role": "user", "content": getPrompt(pistas)},
                    {"role": "user", "content": message}]
        response = chatGPT(messages)
        print(response)
