import codecs

import os
import re

from FileProcessor import FileToConfluenceProcessor


def main():
    file_processor = FileToConfluenceProcessor

    with os.scandir(file_processor.config["APP"]["FILES_DIR"]) as entries:
        # Para todos los archivos del directorio
        for entry in entries:
            print(entry.name)
            id_concepto = entry.name[1:-3]
            file_path = file_processor.config["APP"]["FILES_DIR"] + "\\" + entry.name

            # Parseo el archivo para quedarme con el texto del calculo del concepto
            texto_concepto = file_processor.parse_file(file_path)
            html_concepto = file_processor.format_concepto(texto_concepto)

            # Me fijo si existe una página para ese concepto
            result = file_processor.search_page(id_concepto)

            if result is None:
                # Si no existe la creo
                file_processor.add_page(id_concepto, html_concepto)
            else:
                # sino la actualizo
                file_processor.upd_page(result, html_concepto)


if __name__ == "__main__":
    main()
