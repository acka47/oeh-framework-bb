# Lehrpläne Berlin-Brandenburg XML to SKOS

## Run converter script

- `cd oeh-framework-bb`
- make a virtual environment `python3 -m venv oeh-framework-bb`
- activate it `source oeh-framework-bb/bin/activate`
- install required packages `pip3 install -r requirements.txt`
- run script `python3 xml_to_skos.py`

This will convert the `metadata.xml` file to the data folder `curriculum_bb_skos.ttl`.

A log file showing possible errors will also be created, it 
shows info about XPATH, tag and text, where the error occured.


## View the vocabulary

There is a github action attached, which makes use of the
[Skohub-Vocabs](https://github.com/hbz/skohub-vocabs)-Tool to display the vocabulary.

To view the vocabulary locally:
- clone this repo
- clone https://github.com/hbz/skohub-vocabs
- copy the `curriculum_bb_skos.ttl`-file to the data folder of the skohub-vocabs tool
- go into skohub-vocabs folder
- run `npm i`, `cp .env.example .env`, `rm -rf .cache`, `npm run develop`.

This will start a development server and the build will be served from `http://localhost:8000/`.
