import threading
import time

# -*- coding: utf-8 -*-
import json
import openai 
import sys
import re
from threading import Thread
import random

global NOS,historico
NOS=[]
historico = {'user': [], 'robot': []}

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
        A tua resposta deve de ser Sim ou Não.

        Se a tua resposta é sim. O output deve de ser um tuplo. Com a tua resposta e a frase do segundo texto onde está exatamente a informação do primeiro texto. A frase do segundo texto que escolheres deve de dizer a mesma coisa que o primeiro texto.
        
        Se a tua resposta é não. O output deve de ser um tuplo. Com a tua resposta e um sumario do primeiro texto com um maximo de 10 palavras. Não adiciones informação. 

        O teu output deve se ser só o tuplo.

        primeiro texto: '''{newpista}'''
        segundo texto: ***{pistas}***
         
    """

def getPromptQuestion(string):
    return f"""
    Tu és um analizador de texto. O teu trabalho é perceber se uma string é uma pergunta ou não.
    Deves de dar a tua responta em boolean. True se for uma pergunta. False se não for uma pergunta.
    String: ```{string}```
    """

def getPromptAsk(string):
    return f"""
    Tu és um intrevistador. Mas há uma resposta que tu queres que o teu intervistado dê.
    Para isso vais receber uma frase(entre ```), que é essa resposta. 
    Deves de criar a pergunta, onde a resposta a essa pergunta é a frase(entre ```).
    A resposta à tua pergunta deve de ser exatamente a frase(entre ```). Não deves deixar espaço, para o intervistado responder outra coisa! Não deves perguntar por informação desnecessaria!!
    Se a frase tiver algum dos termos entre ***, deves de referir esses termos na pergunta. 
    termos: ***'SR.GAIA', 'ASSASINATO', 'OFICINA GAIA', 'MARIA', 'MIGUEL', 'MAUTO', 'EDUARDO', 'BRUNO', 'CARLA', 'CAFÉ', 'SARA', 'PÉ-DE-CABRA', 'CAMPO DE GOLF', 'RICARDO', 'CARTEIRA', 'CARRO', 'POSTO DE GASOLINA'***
    frase: ```{string}```
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

def getBigNode(data):
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

def Input(event, data, nodes):
    global NOS,historico
    while True:
        if event.isSet():
            event.wait()
        else: 
            message = input("User : ") 
            historico['user'] += [message]
            if len(NOS) == 0:
                res = [ele for ele in nodes if(ele in message.upper())]
                if len(res) == 0:
                    res = getBigNode(data)
                messages = [{"role": "user", "content": getPromptQuestion(message)}]
                question = chatGPT(messages)

            if len(NOS) > 0:
                res = NOS[0:1]
                message = NOS[2] + " " + message
                question = "False"
                NOS=[]

            pistas = ""
            for d in data:
                if d['node_1']in res or d['node_2']in res:
                    pistas += d['edge']
            
            if question == "False":
                messages = [{"role": "user", "content": getPromptNew(message,pistas)}]
                response = chatGPT(messages)
                #print(response)
                l= response.split(', ')
                anwser = re.sub("('|,|\(|\))","",l[0])
                clue = re.sub("('|,|\(|\))","",l[1])
                #print(anwser)
                if clue[-1] != ".":
                        clue = clue + "."
                print(clue) 

                if anwser.upper() == "NÃO":
                    if len(res) == 1:
                        res += res

                    di = {}
                    di['node_1'] = res[0]
                    di['node_2'] = res[1]
                    di['edge'] = clue 
                    di['confidence'] = 1
                    data.append(di)
                    with open("pistas.json", "w") as outfile:
                        json.dump(data, outfile)
                    
                    response = "Eu não sabia isso!"
                
                if anwser.upper() == "SIM":
                    
                    i = next((i for i, item in enumerate(data) if item["edge"] == clue), None)
                    #print(i)

                    if data[i]['confidence'] == 0:
                        response = "Isso é muito interessante!"
                    if data[i]['confidence'] >= 1:
                        response = "Ok"
                    data[i]['confidence'] += 1

            
            if question == "True":
                if len(res) == 0  and messages == []:
                    bignode = getBigNode(data)
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
                
                #time.sleep(60)
        
            r = response 

            if response != "Ok" and response != "Isso é muito interessante!" and response != "Eu não sabia isso!":
                if any(x in response for x in historico['robot']):   
                    r = "Como eu já disse, " + response
                if any(x in response for x in historico['user']):
                    r = "Como já disses-te, " + response
                
                historico['robot'] += [response]
            print("--" + r)            


def askquestion(event, enable,question):
    if enable:
        event.set()
        print(question)
    else:
        event.clear()
        

def main(): 
    global NOS,historico
    NOS=[]
    historico = {'user': [], 'robot': []}
    with open('hiddenprofiles.json', encoding="utf8") as f:
        data = json.load(f)
    
    nodes = ['SR.GAIA', 'ASSASINATO', 'OFICINA GAIA', 'MARIA', 'MIGUEL', 'MAUTO', 'EDUARDO', 'BRUNO', 'CARLA', 'CAFÉ', 'SARA', 'PÉ-DE-CABRA', 'CAMPO DE GOLF', 'RICARDO', 'CARTEIRA', 'CARRO', 'POSTO DE GASOLINA']
    
    with open('questions.json', encoding="utf8") as f:
        questions = json.load(f)

    event = threading.Event()
    a = threading.Thread(target=Input, args=(event, data, nodes, )).start()

    stime = time.time()
    while True:
        if time.time() - stime > 60:
            stime = time.time()
            selected_item = random.choice(questions)
            questions.remove(selected_item)
            NOS = selected_item['nodes']
            NOS += [selected_item['question']]
            b = threading.Thread(target=askquestion, args=(event, True, selected_item['question'], )).start()
            time.sleep(5)
            c = threading.Thread(target=askquestion, args=(event, False, data, )).start()
    a.start()
    a.join()



if __name__ == "__main__":
    main()




        

