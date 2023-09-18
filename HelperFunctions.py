import json
import requests


def pprint(data):
    """
    Pretty prints json data.
    """
    print(json.dumps(data, sort_keys=True, indent=4, separators=(", ", " : ")))


def read_template(config, auth):
    """
    Read and retrieve the template content for Confluence pages.

    Args:
        config (dict): Configuration settings including the Confluence API base URL and page template ID.
        auth (tuple): Authentication credentials (username, API token).

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
            base=config["CONFLUENCE"]["BASE_URL"],
            page_id=config["CONFLUENCE"]["PAG_TEMPLATE"],
        )
        r = requests.get(
            url,
            auth=auth,
            headers={
                "Content-Type": "application/json",
                "USER-AGENT": config["CONFLUENCE"]["USER_AGENT"],
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


def format_concepto(html_storage_txt, dict_concepto):
    """
    Format and customize the content of a Confluence page with concept-specific information.

    Args:
        html_storage_txt (str): The template content retrieved from Confluence.
        dictConcepto (dict): A dictionary containing concept-specific data.

    Returns:
        str: The formatted page content as a string.

    Usage:
        formatted_content = format_concepto(html_storage_txt, dictConcepto)
    """
    # Inserto el código del concepto
    s = html_storage_txt.split("</ac:structured-macro>", maxsplit=1)
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
                retorno[0 : (index_depen + len(patron))] + dict_concepto["campoGrata"]
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


def get_page_info(config, auth, pageid):
    """
    Retrieve information about a Confluence page using its ID.

    Args:
        config (dict): Configuration settings including the Confluence API base URL.
        auth (tuple): Authentication credentials (username, API token).
        pageid (str): The ID of the Confluence page to retrieve information for.

    Returns:
        dict: Page information as a dictionary, including title, version, and more.

    Raises:
        requests.exceptions.RequestException: If an error occurs while fetching page information.
        Exception: If an unexpected error occurs.

    Usage:
        page_info = get_page_info(config, auth, '12345678')
    """
    try:
        url = "{base}content/{pageid}".format(
            base=config["CONFLUENCE"]["BASE_URL"], pageid=pageid
        )

        r = requests.get(url, auth=auth)
        r.raise_for_status()  # Raise an exception for HTTP errors

        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching page info: {str(e)}")
        return None
    except Exception as ex:
        print(f"An unexpected error occurred: {str(ex)}")
        return None


def search_page(config, auth, concepto):
    """
    Search for a Confluence page in Confluence Cloud by title.

    Args:
        config (dict): Configuration settings including the Confluence API base URL.
        auth (tuple): Authentication credentials (username, API token).
        concepto (str): The title of the page to search for.

    Returns:
        dict or None: Page information as a dictionary if found, or None if not found.

    Raises:
        requests.exceptions.RequestException: If an error occurs while searching for the page.
        Exception: If an unexpected error occurs.

    Usage:
        page_info = search_page(config, auth, 'Concept Title')
    """
    try:
        base_url = config["CONFLUENCE"]["BASE_URL"]
        space = config["CONFLUENCE"]["SPACE_CONF"]
        url = f"{base_url}content?spaceKey={space}&title=Concepto%20{concepto}"

        response = requests.get(url, auth=auth)

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


def add_page(config, auth, idConcepto, textoConcepto):
    """
    Add a new Confluence page with the provided content.

    Args:
        config (dict): Configuration settings including the Confluence API base URL, space key, and more.
        auth (tuple): Authentication credentials (username, API token).
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
            "title": str("Concepto " + idConcepto),
            "ancestors": [
                {"type": "page", "id": str(config["CONFLUENCE"]["PAG_PADRE_CONF"])}
            ],
            "space": {"key": config["CONFLUENCE"]["SPACE_CONF"]},
            "body": {
                "storage": {
                    "representation": "storage",
                    "value": str(textoConcepto),
                }
            },
        }

        data = json.dumps(data)

        url = "{base}".format(base=config["CONFLUENCE"]["BASE_URL"])

        r = requests.post(
            url, data=data, auth=auth, headers={"Content-Type": "application/json"}
        )

        r.raise_for_status()  # Raise an exception for HTTP errors

        print("Page added successfully.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while adding the page: {str(e)}")
    except Exception as ex:
        print(f"An unexpected error occurred: {str(ex)}")


def upd_page(config, auth, result, textoConcepto):
    """
    Update an existing Confluence page with new content.

    Args:
        config (dict): Configuration settings including the Confluence API base URL and more.
        auth (tuple): Authentication credentials (username, API token).
        result (dict): Page information obtained from get_page_info.
        textoConcepto (str): The updated content for the page.

    Raises:
        Exception: If an error occurs while updating the page.

    Usage:
        upd_page(config, auth, page_info, 'Updated content goes here')
    """
    try:
        info = get_page_info(config, auth, result["id"])

        ver = int(info["version"]["number"]) + 1

        data = {
            "id": result["id"],
            "type": "page",
            "title": result["title"],
            "version": {"number": ver},
            "body": {
                "storage": {
                    "representation": "storage",
                    "value": textoConcepto,
                }
            },
        }

        data = json.dumps(data)

        url = "{base}/{pageid}".format(
            base=config["CONFLUENCE"]["BASE_URL"], pageid=result["id"]
        )

        r = requests.put(
            url, data=data, auth=auth, headers={"Content-Type": "application/json"}
        )

        r.raise_for_status()  # Raise an exception for HTTP errors

        print(f"Page '{result['title']}' updated successfully.")
        print(f"URL: {config['CONFLUENCE']['VIEW_URL']}{result['id']}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while updating the page: {str(e)}")
    except Exception as ex:
        print(f"An unexpected error occurred: {str(ex)}")
