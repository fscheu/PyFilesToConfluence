import codecs
import configparser

import os
import re

import HelperFunctions as hf





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
                buffer['textConcepto'].append(line)

            line = reader.readline()
            lineCount = lineCount + 1

    # print(buffer)
    return buffer


def main():

    config = configparser.ConfigParser()
    config.read("config.ini")

    # Obtenemos los datos de login
    auth = hf.get_login(config["CONFLUENCE"]["USER_CONF"])

    # Obtengo el template de la página. Lo hago al principio una sola vez para todes
    html_storage_txt = hf.read_template(config,auth)

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


    with os.scandir(config["APP"]["FILES_DIR"]) as entries:
        # Para todos los archivos del directorio
        for entry in entries:

            print(entry.name)
            idConcepto = entry.name[1:-3]
            filePath = config["APP"]["FILES_DIR"] + '\\' + entry.name

            # Parseo el archivo para quedarme con el texto del calculo del concepto
            textoConcepto = parserFile(filePath, constPat, depenPat, beginPat, midPat, endPat)
            htmlConcepto = hf.format_concepto(html_storage_txt, textoConcepto)
            # print(htmlConcepto)

            # Me fijo si existe una página para ese concepto
            result = hf.search_page(config, auth, idConcepto)

            if result is None:
                # Si no existe la creo
                hf.add_page(config, auth, idConcepto, htmlConcepto)
            else:
                # sino la actualizo
                hf.upd_page(config, auth, result, htmlConcepto)


if __name__ == "__main__": main()
