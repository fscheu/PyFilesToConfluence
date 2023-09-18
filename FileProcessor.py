import re
import json
import requests
import codecs
import configparser


class FileToConfluenceProcessor:
    def __init__(self):
        # Este es el patron para detectar el constructor y extraer los campos en los que se guarda el concepto
        self.const_pat = re.compile(r"#region Constructor", re.IGNORECASE)
        # Este es el patron para detectar la región donde se definen las dependencias
        self.depen_pat = re.compile(r"typeof", re.IGNORECASE)
        # Este es el patrón de inicio de la zona a copiar
        self.begin_pat = re.compile(r"#region C.+lculo", re.IGNORECASE)
        # Si aparece este patron en el medio tenemos que considerar que tenemos que encontrar más de un patron de fin
        self.mid_pat = re.compile(r"#region", re.IGNORECASE)
        # Este es el patron para cerrar la zona a copiar
        self.end_pat = re.compile(r"#endregion", re.IGNORECASE)

        self.config = configparser.ConfigParser()
        self.config.read("config.ini")

        self.auth = (
            self.config["CONFLUENCE"]["USER_CONF"],
            self.config["CONFLUENCE"]["API_TOKEN"],
        )

        self.html_storage_txt = self._read_template()

    def parse_file(self, file_path):
        """
        Parse a file to extract concept-specific information.

        Args:
            file_path (str): The path to the file to be parsed.

        Returns:
            dict: A dictionary containing concept-specific data, including text, dependencies, ID, and fields.

        Usage:
            concept_data = parse_file(file_path)
        """
        with codecs.open(file_path, encoding="utf-8") as reader:
            copying = False
            region_count = 0
            buffer = {
                "textConcepto": [],
                "listDepend": [],
                "idConcepto": "",
                "campoGrata": "",
                "campoAumentos": "",
            }

            line = reader.readline()
            while line:
                if self._parse_constructor(line, reader, buffer):
                    continue
                elif self._parse_dependencies(line, reader, buffer):
                    continue
                elif self._parse_calculation(
                    line, reader, copying, region_count, buffer
                ):
                    continue

                line = reader.readline()

            return buffer

    def _parse_constructor(self, line, reader, buffer):
        if self.const_pat.search(line):
            while line.find("public") == -1:
                line = reader.readline().strip()
            line_camposbbdd = line.split(",")
            try:
                buffer["idConcepto"] = line_camposbbdd[1].strip()[1:-1]
                if line_camposbbdd[3].find("string.Empty") == -1:
                    buffer["campoGrata"] = re.sub(
                        "[^A-Za-z0-9_]+", "", line_camposbbdd[3]
                    )
                if line_camposbbdd[4].find("string.Empty") == -1:
                    buffer["campoAumentos"] = re.sub(
                        "[^A-Za-z0-9_]+", "", line_camposbbdd[4]
                    )
            except IndexError:
                pass
            return True
        return False

    def _parse_dependencies(self, line, reader, buffer):
        if self.depen_pat.search(line):
            while self.depen_pat.search(line):
                buffer["listDepend"].extend(re.findall("G?[0-9]+", line))
                line = reader.readline().strip()
            return True
        return False

    def _parse_calculation(self, line, reader, copying, region_count, buffer):
        if self.begin_pat.search(line):
            copying = True
            line = reader.readline()
        elif self.mid_pat.search(line) and copying:
            region_count += 1
        elif self.end_pat.search(line):
            if region_count > 0:
                region_count -= 1
            else:
                copying = False

        if copying:
            buffer["textConcepto"].append(line)

        return copying

    def format_concepto(self, dict_concepto):
        # Implement the formatting logic here
        """
        Format and customize the content of a Confluence page with concept-specific information.

        Args:
            dictConcepto (dict): A dictionary containing concept-specific data.

        Returns:
            str: The formatted page content as a string.

        Usage:
            formatted_content = format_concepto(html_storage_txt, dictConcepto)
        """
        # Inserto el código del concepto
        s = self.html_storage_txt.split("</ac:structured-macro>", maxsplit=1)
        retorno = (
            s[0]
            + "<ac:plain-text-body><![CDATA["
            + "".join(dict_concepto["textConcepto"])
            + "]]></ac:plain-text-body></ac:structured-macro>"
            + s[1]
        )

        # Armo la sección de links a dependencias
        txt_dependencias = ", ".join(
            [
                '<ac:link><ri:page ri:content-title="Concepto '
                + str(x)
                + '" /><ac:plain-text-link-body><![CDATA['
                + str(x)
                + "]]></ac:plain-text-link-body></ac:link >"
                for x in dict_concepto["listDepend"]
            ]
        )

        patron = "Conceptos que usa</strong></p></th><td>"
        index_depen = retorno.find(patron)
        if index_depen != -1:
            retorno = (
                retorno[0 : (index_depen + len(patron))]
                + txt_dependencias
                + retorno[(index_depen + len(patron) + 5) : len(retorno)]
            )

        # Armo la sección de páginas relacionadas por labels
        patron = '<ac:parameter ac:name="labels">'
        index_depen = retorno.find(patron)
        if index_depen != -1:
            # se le suma 9 al inicio porque es el largo de la palabra "concepto_" que es lo que tienen todos los labels
            retorno = (
                retorno[0 : (index_depen + len(patron) + 9)]
                + dict_concepto["idConcepto"]
                + retorno[(index_depen + len(patron) + 9 + 5) : len(retorno)]
            )

        # Armo la sección de campos de la base donde se guarda el concepto
        patron = "Campos BBDD (G / A)</strong></p></th><td>"
        index_depen = retorno.find(patron)
        if index_depen != -1:
            try:
                retorno2 = (
                    retorno[0 : (index_depen + len(patron))]
                    + dict_concepto["campoGrata"]
                )
            except KeyError as name:
                retorno2 = retorno[0 : (index_depen + len(patron))]

            try:
                retorno2 = (
                    retorno2
                    + " / "
                    + dict_concepto["campoAumentos"]
                    + retorno[(index_depen + len(patron) + 5) : len(retorno)]
                )
            except KeyError as name:
                retorno2 = (
                    retorno2 + retorno[(index_depen + len(patron) + 5) : len(retorno)]
                )

        return retorno2

    def search_page(self, concepto):
        # Implement the search page logic here
        """
        Search for a Confluence page in Confluence Cloud by title.

        Args:
            concepto (str): The title of the page to search for. In my particular case I'm adding "Concepto" to the value received.

        Returns:
            dict or None: Page information as a dictionary if found, or None if not found.

        Raises:
            requests.exceptions.RequestException: If an error occurs while searching for the page.
            Exception: If an unexpected error occurs.

        Usage:
            page_info = search_page(config, auth, 'Concept Title')
        """
        try:
            base_url = self.config["CONFLUENCE"]["BASE_URL"]
            space = self.config["CONFLUENCE"]["SPACE_CONF"]
            url = f"{base_url}content?spaceKey={space}&title=Concepto%20{concepto}"

            response = requests.get(url, auth=self.auth)

            if response.status_code == 200:
                data = response.json()
                if data["size"] > 0:
                    return data["results"][0]  # Return the first result if found
                else:
                    return None  # Page not found
            elif response.status_code == 404:
                return None  # Page not found
            else:
                raise requests.exceptions.RequestException(
                    f"Error searching for the page: {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while searching for the page: {str(e)}")
            raise
        except Exception as ex:
            print(f"An unexpected error occurred: {str(ex)}")
            raise

    def add_page(self, id_concepto, texto_concepto):
        # Implement the add page logic here
        """
        Add a new Confluence page with the provided content.

        Args:
            idConcepto (str): The identifier for the concept to create the page for.
            textoConcepto (str): The content to be added to the page.

        Raises:
            Exception: If an error occurs while adding the page.

        Usage:
            add_page(config, auth, 'ConceptID', 'Page content goes here')
        """
        try:
            data = {
                "type": "page",
                "title": str("Concepto " + id_concepto),
                "ancestors": [
                    {
                        "type": "page",
                        "id": str(self.config["CONFLUENCE"]["PAG_PADRE_CONF"]),
                    }
                ],
                "space": {"key": self.config["CONFLUENCE"]["SPACE_CONF"]},
                "body": {
                    "storage": {
                        "representation": "storage",
                        "value": str(texto_concepto),
                    }
                },
            }

            data = json.dumps(data)

            url = "{base}content/".format(base=self.config["CONFLUENCE"]["BASE_URL"])

            r = requests.post(
                url,
                data=data,
                auth=self.auth,
                headers={"Content-Type": "application/json"},
            )

            r.raise_for_status()  # Raise an exception for HTTP errors

            print("Page added successfully.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while adding the page: {str(e)}")
        except Exception as ex:
            print(f"An unexpected error occurred: {str(ex)}")

    def upd_page(self, result, texto_concepto):
        # Implement the update page logic here
        """
        Update an existing Confluence page with new content.

        Args:
            result (dict): Page information obtained from get_page_info.
            texto_concepto (str): The updated content for the page.

        Raises:
            Exception: If an error occurs while updating the page.

        Usage:
            upd_page(page_info, 'Updated content goes here')
        """
        try:
            info = self._get_page_info(result["id"])

            ver = int(info["version"]["number"]) + 1

            data = {
                "id": result["id"],
                "type": "page",
                "title": result["title"],
                "version": {"number": ver},
                "body": {
                    "storage": {
                        "representation": "storage",
                        "value": texto_concepto,
                    }
                },
            }

            data = json.dumps(data)

            url = "{base}content/{pageid}".format(
                base=self.config["CONFLUENCE"]["BASE_URL"], pageid=result["id"]
            )

            r = requests.put(
                url,
                data=data,
                auth=self.auth,
                headers={
                    "Content-Type": "application/json",
                    "USER-AGENT": self.config["CONFLUENCE"]["USER_AGENT"],
                },
            )

            r.raise_for_status()  # Raise an exception for HTTP errors

            print(f"Page '{result['title']}' updated successfully.")
            print(f"URL: {self.config['CONFLUENCE']['VIEW_URL']}{result['id']}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while updating the page: {str(e)}")
        except Exception as ex:
            print(f"An unexpected error occurred: {str(ex)}")

    def _get_page_info(self, pageid):
        """
        Retrieve information about a Confluence page using its ID.

        Args:
            pageid (str): The ID of the Confluence page to retrieve information for.

        Returns:
            dict: Page information as a dictionary, including title, version, and more.

        Raises:
            requests.exceptions.RequestException: If an error occurs while fetching page information.
            Exception: If an unexpected error occurs.

        Usage:
            page_info = get_page_info('12345678')
        """
        try:
            url = "{base}content/{pageid}".format(
                base=self.config["CONFLUENCE"]["BASE_URL"], pageid=pageid
            )

            r = requests.get(url, auth=self.auth)
            r.raise_for_status()  # Raise an exception for HTTP errors

            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching page info: {str(e)}")
            return None
        except Exception as ex:
            print(f"An unexpected error occurred: {str(ex)}")
            return None

    def _read_template(self):
        """
        Read and retrieve the template content for Confluence pages.

        Returns:
            str: The template content as a string.

        Raises:
            requests.exceptions.RequestException: If an error occurs while fetching the template.
            Exception: If an unexpected error occurs.

        Usage:
            template_content = read_template(config, auth)
        """
        try:
            url = "{base}template/{page_id}".format(
                base=self.config["CONFLUENCE"]["BASE_URL"],
                page_id=self.config["CONFLUENCE"]["PAG_TEMPLATE"],
            )
            r = requests.get(
                url,
                auth=self.auth,
                headers={
                    "Content-Type": "application/json",
                    "USER-AGENT": self.config["CONFLUENCE"]["USER_AGENT"],
                },
            )

            r.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500, etc.)

            json_text = r.text
            return json.loads(json_text)["body"]["storage"]["value"]
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching the template: {str(e)}")
            return None
        except Exception as ex:
            print(f"An unexpected error occurred: {str(ex)}")
            return None
