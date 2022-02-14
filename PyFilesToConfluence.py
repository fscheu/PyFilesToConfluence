import codecs
import getpass
import html

import json
import keyring
import requests

import os
import re

# -----------------------------------------------------------------------------
# Globals

# DIR define el directorio desde donde se van a levantar los archivos
# DIR = 'C:\\Users\\baiscf\\Documents\\Trabajo\\PythonConfluence\\DirTesting'
DIR = 'D:\\DataSVN\\CLC\\trunk\\src\\DIRHU.CLC.Conceptos\\Concepto'
#DIR = 'D:\\dataCLC'


# BASE_URL es la url de la API de contenidos de Confluence
BASE_URL = "http://jira.dirhu.techint.net:8090/confluence/rest/api/content"
# CONVERT_URL es la url de la API de Confluence para convertir formatos de contenidos de las páginas
CONVERT_URL = "http://jira.dirhu.techint.net:8090/confluence/rest/api/contentbody/convert"

VIEW_URL = "http://jira.dirhu.techint.net:8090/confluence/pages/viewpage.action?pageId="

# Espacio de Confluence donde se van a buscar y crear las paginas
SPACE_CONF = 'CLC'
# Usuario de conexión a Confluence
USER_CONF = 'BAISCF'
# ID de página padre de Confluence de la cual se agregan las páginas de conceptos como hijas
PAG_PADRE_CONF = "21235169"
PAG_TEMPLATE = '21240001'
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36"



def pprint(data):
    '''
    Pretty prints json data.
    '''
    print (json.dumps(
        data,
        sort_keys = True,
        indent = 4,
        separators = (', ', ' : ')))


def get_login(username=None):
    '''
    Get the password for username out of the keyring.
    '''

    if username is None:
        username = getpass.getuser()

    #passwd = keyring.get_password('confluence_script', username)
    passwd = None

    if passwd is None:
        passwd = getpass.getpass()
        keyring.set_password('confluence_script', username, passwd)

    return (username, passwd)


def read_template(auth):
    url = '{base}/{page_id}?expand=body.storage'.format(base=BASE_URL, page_id=PAG_TEMPLATE)
    r = requests.get(
        url,
        auth=auth,
        headers={'Content-Type': 'application/json', 'USER-AGENT': USER_AGENT}
    )

    r.raise_for_status()
    json_text = r.text
    return json.loads(json_text)['body']['storage']['value']


def format_concepto(html_storage_txt, dictConcepto):

    # Inserto el código del concepto
    s = html_storage_txt.split('![CDATA[', maxsplit=1)
    retorno = s[0] + '![CDATA[' + ''.join(dictConcepto['textConcepto']) + s[1]

    # Armo la sección de links a dependencias
    txtDependencias = ', '.join(['<ac:link><ri:page ri:content-title="Concepto ' + str(x)
                                    + '" /><ac:plain-text-link-body><![CDATA['+ str(x)
                                    + ']]></ac:plain-text-link-body></ac:link >' for x in dictConcepto['listDepend']])

    patron = 'Conceptos que usa</th><td>'
    indexDepen = retorno.find(patron)
    if indexDepen != -1:
        retorno = retorno[0:(indexDepen+len(patron))] + txtDependencias + retorno[(indexDepen+len(patron)+6):len(retorno)]

    # Armo la sección de páginas relacionadas por labels
    patron = '<ac:parameter ac:name="labels">'
    indexDepen = retorno.find(patron)
    if indexDepen != -1:
        # se le suma 9 al inicio porque es el largo de la palabra "concepto_"
        retorno = retorno[0:(indexDepen + len(patron)+9)] + dictConcepto["idConcepto"] \
                                                    + retorno[(indexDepen + len(patron) + 9 + 4) :len(retorno)]

    # Armo la sección de campos de la base donde se guarda el concepto
    patron = 'Campos BBDD (G / A)</th><td colspan="1">'
    indexDepen = retorno.find(patron)
    if indexDepen != -1:
        try:
            retorno2 = retorno[0:(indexDepen+len(patron))] + dictConcepto['campoGrata']
        except KeyError as name:
            retorno2 = retorno[0:(indexDepen + len(patron))]

        try:
            retorno2 = retorno2 + " / " + dictConcepto['campoAumentos'] + retorno[(indexDepen+len(patron)+6):len(retorno)]
        except KeyError as name:
            retorno2 = retorno2 + retorno[(indexDepen+len(patron)+6):len(retorno)]

    return retorno2


def get_page_info(auth, pageid):

    url = '{base}/{pageid}'.format(
        base=BASE_URL,
        pageid=pageid)

    r = requests.get(url, auth = auth)

    r.raise_for_status()

    return r.json()


def search_page(auth, concepto):
    # Busca si existe la página del concepto

    url = '{base}?spaceKey={space}&title=Concepto%20{con}'.format(
        base=BASE_URL,
        space=SPACE_CONF,
        con=concepto)

    r = requests.get(url, auth=auth)
    r.raise_for_status()
    r = r.json()
    if r['size'] == 0:
        return None
    else:
        # Del json con el resultado de la busqueda me quedo con el primer resultado
        return r['results'][0]


def add_page(auth, idConcepto, textoConcepto):
    data = {
        'type': 'page',
        'title': str('Concepto ' + idConcepto),
        'ancestors': [{"type": "page", "id": str(PAG_PADRE_CONF)}],
        'space': {'key': SPACE_CONF},
        'body': {
            'storage':
                {
                    'representation': 'storage',
                    'value': str(textoConcepto),
                }
        }
    }

    data = json.dumps(data)
    pprint(data)

    url = '{base}'.format(base=BASE_URL)

    r = requests.post(
        url,
        data=data,
        auth=auth,
        headers={'Content-Type': 'application/json'}
    )

    r.raise_for_status()

    print("Se agregó la página '%s' para el concepto %s" % (str('Concepto ' + idConcepto), str(idConcepto)))


def upd_page(auth, result, textoConcepto):

    info = get_page_info(auth, result['id'])

    ver = int(info['version']['number']) + 1

    data = {
        'id': result['id'],
        'type': 'page',
        'title': result['title'],
        'version': {'number' : ver},
        # 'ancestors': PAG_PADRE_CONF,
        'body': {
            'storage':
                {
                    'representation': 'storage',
                    'value': textoConcepto,
                }
        }
    }

    data = json.dumps(data)
    # pprint(data)

    url = '{base}/{pageid}'.format(base=BASE_URL, pageid=result['id'])

    r = requests.put(
        url,
        data=data,
        auth=auth,
        headers={'Content-Type': 'application/json'}
    )

    r.raise_for_status()

    print("Se actualizó la página '%s'" % (result['title']))
    print("URL: %s%s" % (VIEW_URL, result['id']))


def parserFile(filePath, constPat, depenPat, beginPat, midPat, endPat):

    # Vamos a parsear cada linea
    with codecs.open(filePath, encoding='utf-8') as reader:

        # Variable para indicar si tenemos que copiar las lineas porque se encontro el inicio de la sección
        copying = False
        # Variable para contar la cantidad de "regiones" que se encontraron
        # y detectar cuantos fines de region se tienen que considerar
        regionCount = 0
        # Variable para almacenar el resultado
        buffer = {}
        buffer['textConcepto'] = []
        buffer['listDepend'] = []
        buffer['idConcepto'] = ''
        buffer['campoGrata'] = ''
        buffer['campoAumentos'] = ''

        lineCount = 0

        line = reader.readline()
        while line != '':  # The EOF char is an empty string

            # Codigo para debug
            # if lineCount == 48 or lineCount == 49:
            #    print(line)
            #    print(beginPat.search(line))

            #line = line.strip()
            if constPat.search(line) is not None: # Encontro el inicio de la region de constructor

                while line.find('public') == -1:
                    line = reader.readline().strip()
                line_camposbbdd = line.split(',')
                try:
                    # HAgo un strip para sacar espacios y saco 1 caracter de cada punta para eliminar comillas dobles
                    buffer["idConcepto"] = line_camposbbdd[1].strip()[1:-1]
                    if line_camposbbdd[3].find('string.Empty') == -1:
                        buffer['campoGrata'] = re.sub('[^A-Za-z0-9_]+', '', line_camposbbdd[3])
                    if line_camposbbdd[4].find('string.Empty') == -1:
                        buffer['campoAumentos'] = re.sub('[^A-Za-z0-9_]+', '', line_camposbbdd[4])
                except IndexError:
                    pass
                continue

            elif depenPat.search(line) is not None: # Encontro el inicio de la region de dependencias

                while depenPat.search(line) is not None:
                    buffer['listDepend'].extend(re.findall('G?[0-9]+', line))
                    line = reader.readline().strip()

            elif beginPat.search(line) is not None:  # Encontro el inicio de la region del calculo
                copying = True
                line = reader.readline()
            elif (midPat.search(line) is not None) and copying:  # Encontro el inicio de otra region adentro
                regionCount = regionCount + 1  # La sumo para descartar el final y continuar
            elif endPat.search(line) is not None:
                if regionCount > 0:
                    regionCount = regionCount - 1  # Descartando el final de una region interna
                else:
                    copying = False

            # Si me encuentro en modo copia agrego la linea al buffer
            if copying:
                # buffer.append('<p>' + html.escape(line) + '</p>')
                buffer['textConcepto'].append(line)
                # print(line, end='')

            line = reader.readline()
            lineCount = lineCount + 1

    # print(buffer)
    # para retornar transformo todas las lineas en un solo string
    # buffer['textConcepto'] = ''.join(buffer['textConcepto'])
    return buffer


def main():
    # Obtenemos los datos de login
    auth = get_login(USER_CONF)

    # Obtengo el template de la página. Lo hago al principio una sola vez para todes
    html_storage_txt = read_template(auth)

    # Definimos tres patrones para buscar en cada linea. Lo hago al principio una sola vez

    # Este es el patron para detectar el constructor y extraer los campos en los que se guarda el concepto
    constPat = re.compile(r"#region Constructor", re.IGNORECASE)
    # Este es el patron para detectar la región donde se definen las dependencias
    depenPat = re.compile(r"typeof", re.IGNORECASE)
    # Este es el patrón de inicio de la zona a copiar
    beginPat = re.compile(r"#region C.+lculo", re.IGNORECASE)
    # Si aparece este patron en el medio tenemos que considerar que tenemos que encontrar más de un patron de fin
    midPat = re.compile(r"#region", re.IGNORECASE)
    # Este es el patron para cerrar la zona a copiar
    endPat = re.compile(r"#endregion", re.IGNORECASE)


    with os.scandir(DIR) as entries:
        # Para todos los archivos del directorio
        for entry in entries:

            print(entry.name)
            idConcepto = entry.name[1:-3]
            filePath = DIR + '\\' + entry.name

            # Parseo el archivo para quedarme con el texto del calculo del concepto
            textoConcepto = parserFile(filePath, constPat, depenPat, beginPat, midPat, endPat)
            htmlConcepto = format_concepto(html_storage_txt, textoConcepto)
            # print(htmlConcepto)

            # Me fijo si existe una página para ese concepto
            result = search_page(auth, idConcepto)

            if result is None:
                # Si no existe la creo
                add_page(auth, idConcepto, htmlConcepto)
            else:
                # sino la actualizo
                upd_page(auth, result, htmlConcepto)


if __name__ == "__main__": main()
