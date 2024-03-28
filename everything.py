import queue
import re
import sys
import time

from google.cloud import speech
import pyaudio

import json
import openai

from gtts import gTTS

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS']= 'google_secret_key.json'

from playsound import playsound
import pyttsx3
from io import BytesIO



# Audio recording parameters
STREAMING_LIMIT = 240000  # 4 minutes
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)  # 100ms

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"


def load_api_key(secrets_file="secrectsChatGPT.json"):
    with open(secrets_file) as f:
        secrets = json.load(f)
    return secrets["OPENAI_API_KEY"]

def get_current_time() -> int:
    return int(round(time.time() * 1000))

class ResumableMicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(
        self: object,
        rate: int,
        chunk_size: int,
    ) -> None:
        """Creates a resumable microphone stream.

        Args:
        self: The class instance.
        rate: The audio file's sampling rate.
        chunk_size: The audio file's chunk size.

        returns: None
        """
        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self.restart_counter = 0
        self.audio_input = []
        self.last_audio_input = []
        self.result_end_time = 0
        self.is_final_end_time = 0
        self.final_request_end_time = 0
        self.bridging_offset = 0
        self.last_transcript_was_final = False
        self.new_stream = True
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
            input_device_index=0
        )

    def __enter__(self: object) -> object:
        """Opens the stream.

        Args:
        self: The class instance.

        returns: None
        """
        self.closed = False
        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> object:
        """Closes the stream and releases resources.

        Args:
        self: The class instance.
        type: The exception type.
        value: The exception value.
        traceback: The exception traceback.

        returns: None
        """
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
        self: The class instance.
        in_data: The audio data as a bytes object.
        args: Additional arguments.
        kwargs: Additional arguments.

        returns: None
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Stream Audio from microphone to API and to local buffer

        Args:
            self: The class instance.

        returns:
            The data from the audio stream.
        """
        while not self.closed:
            data = []

            if self.new_stream and self.last_audio_input:
                chunk_time = STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:
                    if self.bridging_offset < 0:
                        self.bridging_offset = 0

                    if self.bridging_offset > self.final_request_end_time:
                        self.bridging_offset = self.final_request_end_time

                    chunks_from_ms = round(
                        (self.final_request_end_time - self.bridging_offset)
                        / chunk_time
                    )

                    self.bridging_offset = round(
                        (len(self.last_audio_input) - chunks_from_ms) * chunk_time
                    )

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        data.append(self.last_audio_input[i])

                self.new_stream = False

            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            data.append(chunk)
            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)
                    self.audio_input.append(chunk)

                except queue.Empty:
                    break

            yield b"".join(data)

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
        O teu output deve de ser só uma palavra, sim ou não!
        primeiro texto: '''{newpista}'''
        segundo texto: ***{pistas}***
         
    """

def getPromptQuestion(string):
    return f"""
    Tu és um analizador de texto. O teu trabalho é perceber se uma string é uma pergunta ou não.
    Deves de dar a tua responta em boolean. True se for uma pergunta. False se não for uma pergunta.
    String: ```{string}```
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

def getPromptRelation(pista, nodes):
    return f"""You are a network graph maker who extracts the relations between terms from a given context.
    You are provided with a context chunk (delimited by ```).
    Your task is to extract the ontology of terms mentioned in the given context.
    These terms are {nodes}.
    Think about how these terms can have one on one relation with other terms. Terms that are mentioned in the same sentence or the same paragraph are typically related to each other. Terms can be related to many other terms.
    Format your output as a json. Each element contains a pair of terms and the relation between them. With  node_1, node_2 and edge as keys.
    Usa só portugues europeu!
    Chunk: ```{pista}```
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

def main() -> None:
    """start bidirectional streaming from microphone input to speech API"""
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code="pt-BR",
        enable_automatic_punctuation=True,
        max_alternatives=1,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    api_key = load_api_key()
    openai.api_key = api_key

    with open('graphR.json', encoding="utf8") as f:
        data = json.load(f)

    nodes = ['SR.GAIA', 'ASSASINATO', 'OFICINA GAIA', 'MARIA', 'MIGUEL', 'MAUTO', 'EDUARDO', 'BRUNO', 'CARLA', 'CAFÉ', 'SARA', 'PÉ-DE-CABRA', 'CAMPO DE GOLF', 'RICARDO', 'CARTEIRA', 'CARRO', 'POSTO DE GASOLINA']
 

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    print("Vamos desvendar o misterio!!")
    
    engine = pyttsx3.init('sapi5')

    voices = engine.getProperty('voices')

    voice = None
    for v in voices:
        if "Cristiano22" in v.id:
            voice = v.id

    engine.setProperty('voice', voice)

    messages = []
    historico = {'user': [], 'robot': []}

    with mic_manager as stream:
        while not stream.closed:
            
            stream.audio_input = []
            audio_generator = stream.generator()
            
            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)
            

            for r in responses:
                
                print(r.results[0].alternatives[0].transcript)
               
                if r.results[0].alternatives[0].transcript and r.results[0].is_final:

                    message = r.results[0].alternatives[0].transcript

                    historico['user'] += [message]

                    m1 = [{"role": "user", "content": getPromptQuestion(message)}]
                    question = chatGPT(m1)
                    
                    res = [ele for ele in nodes if(ele in message.upper())]
                    j = []
                    for d in data:
                        if d['node_1']in res or d['node_2']in res:
                            j.append(d)
                    
                    m3 = [{"role": "user", "content": getPromptJSON(j)}]
                    pistas = chatGPT(m3)

                    if question == "False":
                        
                        m2 = [{"role": "user", "content": getPromptNew(message,pistas)}]
                        response = chatGPT(m2)
                        print(response)
                        #time.sleep(60)

                        if 'NÃO' in response.upper():
                            m4 = [{"role": "user", "content": getPromptRelation(message,nodes)}]
                            response = chatGPT(m4)
                            print(response)
                            response = json.loads(response)
                            for r in response.keys():
                                data += response[r]
                            with open("pistas_2.json", "w") as outfile:
                                json.dump(data, outfile)
                            #time.sleep(60)
                        
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
                        
                        #time.sleep(60)
                
                    r = response 

                    if response != "Ok":
                        if any(x in response for x in historico['robot']):   
                            r = "Como eu já disse, " + response
                        if any(x in response for x in historico['user']):
                            r = "Como já disses-te, " + response
                        
                        historico['robot'] += [response]
                    print(r)
                    engine.say(r)
                    engine.runAndWait()
                
                    
            if stream.result_end_time > 0:
                stream.final_request_end_time = stream.is_final_end_time
            stream.result_end_time = 0
            stream.last_audio_input = []
            stream.last_audio_input = stream.audio_input
            stream.audio_input = []
            stream.restart_counter = stream.restart_counter + 1

            #if not stream.last_transcript_was_final:
            #    sys.stdout.write("\n")
            stream.new_stream = True


if __name__ == "__main__":
    main()

