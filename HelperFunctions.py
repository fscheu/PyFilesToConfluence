import json
import getpass
import keyring
import requests


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


def read_template(config,auth):
    url = '{base}template/{page_id}'.format(base=config["CONFLUENCE"]["BASE_URL"], page_id=config["CONFLUENCE"]["PAG_TEMPLATE"])
    r = requests.get(
        url,
        auth=auth,
        headers={'Content-Type': 'application/json', 'USER-AGENT': config["CONFLUENCE"]["USER_AGENT"]}
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


def get_page_info(config, auth, pageid):

    url = '{base}/{pageid}'.format(
        base=config["CONFLUENCE"]["BASE_URL"],
        pageid=pageid)

    r = requests.get(url, auth = auth)

    r.raise_for_status()

    return r.json()


def search_page(config, auth, concepto):
    # Busca si existe la página del concepto

    url = '{base}?spaceKey={space}&title=Concepto%20{con}'.format(
        base=config["CONFLUENCE"]["BASE_URL"],
        space=config["CONFLUENCE"]["SPACE_CONF"],
        con=concepto)

    r = requests.get(url, auth=auth)
    r.raise_for_status()
    r = r.json()
    if r['size'] == 0:
        return None
    else:
        # Del json con el resultado de la busqueda me quedo con el primer resultado
        return r['results'][0]


def add_page(config, auth, idConcepto, textoConcepto):
    data = {
        'type': 'page',
        'title': str('Concepto ' + idConcepto),
        'ancestors': [{"type": "page", "id": str(config["CONFLUENCE"]["PAG_PADRE_CONF"])}],
        'space': {'key': config["CONFLUENCE"]["SPACE_CONF"]},
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

    url = '{base}'.format(base=config["CONFLUENCE"]["BASE_URL"])

    r = requests.post(
        url,
        data=data,
        auth=auth,
        headers={'Content-Type': 'application/json'}
    )

    r.raise_for_status()

    print("Se agregó la página '%s' para el concepto %s" % (str('Concepto ' + idConcepto), str(idConcepto)))


def upd_page(config, auth, result, textoConcepto):

    info = get_page_info(config, auth, result['id'])

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

    url = '{base}/{pageid}'.format(base=config["CONFLUENCE"]["BASE_URL"], pageid=result['id'])

    r = requests.put(
        url,
        data=data,
        auth=auth,
        headers={'Content-Type': 'application/json'}
    )

    r.raise_for_status()

    print("Se actualizó la página '%s'" % (result['title']))
    print("URL: %s%s" % (config["CONFLUENCE"]["VIEW_URL"], result['id']))
