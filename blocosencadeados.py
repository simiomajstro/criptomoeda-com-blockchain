import json
import hashlib
import requests

from urllib.parse import urlparse as analisaURL
from time import time as tempo

class BlocosEncadeados:
    def __init__(self):
        self.transacoes_atuais = []
        self.cadeia = []
        self.elos = set()

        # Aqui é criado o primeiro bloco
        self.novo_bloco(fragmento_anterior='1', prova=100)

    def novo_bloco(self, prova, fragmento_anterior):

        # Nossa estrutura de blocos, com os 5 campos obrigatórios.
        bloco = {
            'indice': len(self.cadeia) + 1,
            'carimbo_temporal': tempo(),
            'transacoes': self.transacoes_atuais,
            'fragmento_anterior': fragmento_anterior or self.fragmento(self.cadeia[-1]),
            'prova': prova,
        }

        self.transacoes_atuais = []
        self.cadeia.append(bloco)
        return bloco  

    def nova_troca(self, remetente, recebedor, montante):
        self.transacoes_atuais.append({
            'remetente': remetente,
            'recebedor': recebedor,
            'montante': montante,
        })

        return self.ultimo_bloco['indice'] + 1  

    @property
    def ultimo_bloco(self):
        return self.cadeia[-1]    

    @staticmethod
    def fragmento(bloco):
        # É aqui que juntamos todos os dados do nosso bloco e fazemos fragmento.
        string_do_bloco = json.dumps(bloco, sort_keys=True).encode()
        return hashlib.sha256(string_do_bloco).hexdigest()

    def prova_de_trabalho(self, ultimo_bloco):
        ultima_prova = ultimo_bloco['prova']
        ultimo_fragmento = self.fragmento(ultimo_bloco)

        # Esta é a parte da força bruta. 
        # Contamos a partir de 0 e tentamos todos os números até que algo funcione.
        prova = 0
        while self.prova_valida(ultima_prova, prova, ultimo_fragmento) is False:
            prova += 1
        return prova

    @staticmethod
    def prova_valida(ultima_prova, prova, ultimo_fragmento):
        conjetura = f'{ultima_prova}{prova}{ultimo_fragmento}'.encode()
        conjetura_fragmento = hashlib.sha256(conjetura).hexdigest()

        # Ajuste sua dificuldade de mineração aqui! Quanto mais zeros, mais difícil
        # Esteja ciente de que qualquer coisa acima de 6 possivelmente irá expirar ou travar algo
        return conjetura_fragmento[:4] == "0000"     


# ----  Abaixo, aqui está o material necessário para a ideia 
#       da cadeia de blocos se tornar um "livro razão distribuído". ----   
    # Primeiro podemos adicionar URLs para outros elos.
    # Certifique-se de usar colchetes no corpo da solicitação, 
    # mesmo que seja apenas um url, como o exemplo a seguir
    # { "elos":["http://0.0.0.0:5001"] }
    def registrar_elo(self, endereco):

        endereco_analisado = analisaURL(endereco)
        if endereco_analisado.netloc:
            self.elos.add(endereco_analisado.netloc)
        elif endereco_analisado.path:
            self.elos.add(endereco_analisado.path)
        else:
            raise ValueError('URL inválida')     

    # Aqui, garantimos que nossos valores de fragmento estão corretos
    def cadeia_valida(self, cadeia):

        ultimo_bloco = cadeia[0]
        indice_atual = 1

        while indice_atual < len(cadeia):
            bloco = cadeia[indice_atual]
            print(f'{ultimo_bloco}')
            print(f'{bloco}')
            print("\n-----------\n")

            fragmento_do_ultimo_bloco = self.fragmento(ultimo_bloco)
            if bloco['fragmento_anterior'] != fragmento_do_ultimo_bloco:
                return False

            if not self.prova_valida(ultimo_bloco['prova'], bloco['prova'], fragmento_do_ultimo_bloco):
                return False

            ultimo_bloco = bloco
            indice_atual += 1

        return True

    # Aqui podemos encontrar a cadeia mais longa (válida) de todos os nossos elos registrados,
    # Se não for nosso, podemos substituir o nosso por um mais longo.
    def resolver_conflitos(self):

        todos_os_elos = self.elos
        nova_cadeia = None

        comprimento_maximo = len(self.cadeia)

        for elo in todos_os_elos:
            resposta = requests.get(f'http://{elo}/cadeia')

            if resposta.status_code == 200:
                comprimento = resposta.json()['comprimento']
                cadeia = resposta.json()['cadeia']

                if comprimento > comprimento_maximo and self.cadeia_valida(cadeia):
                    comprimento_maximo = comprimento
                    nova_cadeia = cadeia

        if nova_cadeia:
            self.cadeia = nova_cadeia
            return True

        return False
