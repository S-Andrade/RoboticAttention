import json
import openai

def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

api_key = load_api_key()
openai.api_key = api_key

with open('graphR.json', encoding="utf8") as f:
    data = json.load(f)

def getPrompt(termo1,termo2,relacao):
    return f"""
    Tu construir frases. Vais receber dois termos e uma relação que existe entre eles.
    O teu trabalho é escrever uma frase onde explica a relação entre os dois termos.
    A frase deve de ter no maximo 10 palavras.
    A frase deve de ser o mais curta possivel.
    Termo 1 : {termo1}
    Termo 2 : {termo2}
    Relação : {relacao}
    """

def getPromptJSON(json):
    return f""""
    Vais receber um json e para cada elemento deves criar uma frase. Vais usar dois termos, o "node_1" e o "node_2", e uma relação, "edge", que existe entre eles. 
    O teu trabalho é escrever uma frase onde explica a relação entre os dois termos.
    A frase deve de ter no maximo 10 palavras.
    A frase deve de ser o mais curta possivel.
    Por favor, escreve as frases sem as listares, não numeres as frases!
    JSON: {json}
    """

def chatGPT(messages, model="gpt-3.5-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

j = []
i = 0
for d in data:
    if d['node_1'] == "SARA" or d['node_2'] == "SARA":
       j.append(d)
       
print(j)    
m = [{"role": "user", "content": getPromptJSON(j)}]
r = chatGPT(m)
print(r)
i+=1

