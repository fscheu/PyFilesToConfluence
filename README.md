# FileToConfluence Processor

FileToConfluence Processor is a Python script designed to automate the process of transferring code documentation from source files into Confluence pages. This utility is particularly useful for maintaining code documentation in Confluence, ensuring that it remains up-to-date and aligned with the codebase.
## Badges
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
[![Coverage](https://img.shields.io/gitlab/coverage/fscheu/PyFilesToConfluence/master)](https://opensource.org/licenses/)

## Table of Contents
- [FileToConfluence Processor](#filetoconfluence-processor)
  - [Badges](#badges)
  - [Table of Contents](#table-of-contents)
    - [Main Idea and Objective](#main-idea-and-objective)
    - [Configuration File](#configuration-file)
    - [Using Confluence Template](#using-confluence-template)
    - [Extension Points](#extension-points)
    - [Installation](#installation)

---

### Main Idea and Objective

The primary objective of the FileToConfluence Processor is to simplify the process of updating Confluence pages with code documentation by extracting information from source code files and formatting it to match a predefined Confluence page template. This automation ensures that your code documentation remains consistent and up-to-date with your codebase.

---

### Configuration File

The program uses a configuration file (`config.ini`) to store settings and authentication credentials. To configure the program correctly, you need to modify the following entries in the `config.ini` file:

- `[APP]`
  - `FILES_DIR`: This is the directory containing the source code files to be processed.

- `[CONFLUENCE]`
  - `BASE_URL`: The URL of your Confluence instance's REST API.
  - `CONVERT_URL`: The URL to convert content from the Confluence API.
  - `VIEW_URL`: The URL to view a page in Confluence (used for script output).
  - `SPACE_CONF`: The key of the Confluence space where the pages will be created.
  - `USER_CONF`: Your Confluence username or email.
  - `API_TOKEN`: Your Confluence API token.

Here's an example of a `config.ini` file:

```ini
[APP]
FILES_DIR = ./sample_files

[CONFLUENCE]
BASE_URL = https://your-confluence-instance.atlassian.net/wiki/rest/api/
CONVERT_URL = https://your-confluence-instance.atlassian.net/wiki/rest/api/contentbody/convert
VIEW_URL = https://your-confluence-instance.atlassian.net/wiki/pages/viewpage.action?pageId=
SPACE_CONF = YOUR_SPACE_KEY
USER_CONF = your.username@example.com
API_TOKEN = your-api-token
PAG_PADRE_CONF = 1234567
PAG_TEMPLATE = 9876543
USER_AGENT = Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.82 Safari/537.36
```

Make sure to replace the placeholders with your actual Confluence instance details and authentication credentials.

### Using Confluence Template
The program utilizes a Confluence page template to structure the code documentation within Confluence. This template provides a consistent format for all code documentation pages.

To use the template, ensure that the PAG_TEMPLATE entry in the config.ini file points to the correct page ID of your Confluence template page.

### Extension Points
The FileToConfluence Processor allows for flexibility and customization. You can adapt the program to suit your specific needs:

* Regular Expressions (Regex Patterns): The program uses regular expressions (regex) to identify and parse relevant content in your source code files. If your codebase follows a different structure, you can customize the regex patterns in the FileToConfluenceProcessor constructor within the code. Modify the const_pat, depen_pat, begin_pat, mid_pat, and end_pat patterns to match your code documentation structure.

* Custom Parsing and Formatting: If your source code files have unique documentation structures, you can rewrite the parse_file and format_concepto methods within the FileToConfluenceProcessor class to parse and format the content accordingly.

### Installation
To run the FileToConfluence Processor, follow these steps:

1. Ensure you have Python installed on your system.
2. Clone the repository to your local machine.
3. Navigate to the project directory.
4. Install the required dependencies using Pipenv:
```shell
pipenv install
```
5. Modify the config.ini file with your Confluence and file path settings.
6. Running the Script:
```shell
pipenv shell
python PyFilesToConfluence.py
```
Feel free to modify and extend the FileToConfluence Processor to meet your specific requirements. This README provides a starting point for understanding and using the program effectively.