# -*- coding: utf-8 -*-
import json
import openai 
import time
import sys
import re

###### Need to test, more billing #######


RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
  
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


def getPromptNew(newpista,pistas):
    return f"""
        Tu és um analizador de texto. O teu trabalho é perceber se a toda a informação de um texto está contida noutro texto.
        Deves intrepertar os dois textos e compara-los. Deves perceber se toda a informação do primeiro texto está contida no segundo texto.
        Deves de responder só com sim ou não.
        o output deve de ser um tuplo. Com a resposta e um sumario do primeiro texto com um maximo de 10 palavras. Não adiciones informação.
        primeiro texto: '''{newpista}'''
        segundo texto: ***{pistas}***
         
    """

def getPromptQuestion(string):
    return f"""
    Tu és um analizador de texto. O teu trabalho é perceber se uma string é uma pergunta ou não.
    Deves de dar a tua responta em boolean. True se for uma pergunta. False se não for uma pergunta.
    String: ```{string}```
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def getBigNode():
    dic = {}
    for d in data:
        if d['node_1'] in dic.keys():
            dic[d['node_1']] += 1
        else:
            dic[d['node_1']] = 1
        
        if d['node_2'] in dic.keys():
            dic[d['node_2']] += 1
        else:
            dic[d['node_2']] = 1

    max_value = max(dic, key=dic.get)
    return max_value


with open('pistas.json', encoding="utf8") as f:
    data = json.load(f)

nodes = ['SR.GAIA', 'ASSASINATO', 'OFICINA GAIA', 'MARIA', 'MIGUEL', 'MAUTO', 'EDUARDO', 'BRUNO', 'CARLA', 'CAFÉ', 'SARA', 'PÉ-DE-CABRA', 'CAMPO DE GOLF', 'RICARDO', 'CARTEIRA', 'CARRO', 'POSTO DE GASOLINA']

messages = []

while True:
    message = input("User : ") 

    m1 = [{"role": "user", "content": getPromptQuestion(message)}]
    question = chatGPT(m1)
    
    res = [ele for ele in nodes if(ele in message.upper())]
    pistas = ""
    for d in data:
        if d['node_1']in res or d['node_2']in res:
            pistas += d['edge']
    
    
    if question == "False":
        
        m2 = [{"role": "user", "content": getPromptNew(message,pistas)}]
        response = chatGPT(m2)
        l= response.split(', ')
        anwser = re.sub("('|,|\(|\))","",l[0])
        clue = re.sub("('|,|\(|\))","",l[1])
        
        if anwser == "Não":
            if clue[-1] != ".":
                clue = clue + "."
            if len(res) == 1:
                res += res

            di = {}
            di['node_1'] = res[0]
            di['node_2'] = res[1]
            di['edge'] = clue
            data.append(di)
            with open("pistas_2.json", "w") as outfile:
                json.dump(data, outfile)
        
        response = "Ok"

    if question == "True":   
        if len(res) == 0  and messages == []:
            bignode = getBigNode()
            pistas = ""
            for d in data:
                if d['node_1'] == bignode or d['node_2'] == bignode:
                    pistas += d['edge']

            messages = [{"role": "user", "content": getPrompt(pistas)},
                        {"role": "user", "content": message}]
            response = chatGPT(messages)
            print(response)

        elif len(res) == 0:
            messages += [{"role": "user", "content": message}]
            response = chatGPT(messages)
            

        else:
            pistas = ""
            for d in data:
                if d['node_1']in res or d['node_2']in res:
                    pistas += d['edge']

            messages = [{"role": "user", "content": getPrompt(pistas)},
                        {"role": "user", "content": message}]
            response = chatGPT(messages)
        
    print(response)
