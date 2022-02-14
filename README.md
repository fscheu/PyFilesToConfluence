# PyFilesToConfluence
Python script to parse files and generate or update Confluence pages

## Badges


[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)
[![Coverage](https://img.shields.io/gitlab/coverage/fscheu/PyFilesToConfluence/master)](https://opensource.org/licenses/)

## How To Use

First, you have to configurate your settings file

DIR: Defines the local route to read the files to parse

BAS_URL: This is the URL of the Confluence contents API
CONVERT_URL: This is the URL to convert contents formats 
VIEW_URL: URL to query for a page

SPACE_CONF: Confluence space where the pages are going to be uploaded
USER: Connection user
FATHER_PAGE: ID of the father page where the uploaded pages are going to be uploaded
TEMPLATE_PAGE: ID of the Template page used in the generation of new pages