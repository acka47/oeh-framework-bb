from lxml import etree as ET
from rdflib import Graph, Literal, Namespace, RDF, URIRef, BNode
from rdflib.namespace import SKOS, DCTERMS
from pathlib import Path
import re
import uuid
import os
from collections import Counter


subject_mapping = {
    "B-EUR": "Europabildung in der Schule",
    "B-VB": "Verbraucherbildung",
    "B-SE": "Sexualerziehung",
    "B-GES": "Gesundheitsförderung",
    "B-BSO": "Berufs- und Studienorientierung",
    "B-GEN": "Gleichstellung und Gleichberechtigung der Geschlchter",
    "B-KB": "Kulturelle Bildung",
    "B-GEW": "Gewaltprävention",
    "B-DIV": "Bildung zur Akzeptanz und Vielfalt",
    "B-MB": "Mobilitätsbildung un Verkehrserziehung",
    "B-IKB": "Interkulturelle Bildung und Erziehung",
    "B-BNE": "Nachhaltige Entwicklung/Lernen in globalen Zusammenhängen",
    "B-DEM": "Demokratiebildung",
    "B": "Fächerübergreifende Kompetenzentwicklung",
    "C": "Fächer",
    "AS": "Astronomie",
    "MA": "Mathematik",
    "DE": "Deutsch",
    "GEO": "Geografie",
    "GEWIWI": "Gesellschaftswissenschaften",
    "GEWI": "Gesellschaftswissenschaften",
    "Inf": "Informatik",
    "LER": "Lebensgestaltung-Ethik-Religionskunde",
    "La": "Latein",
    "MU": "Musik",
    "PB": "Politische Bildung",
    "Ph": "Physik",
    "Phil": "Philosophie",
    "Psy": "Psychologie",
    "Thea": "Theater",
    "AGR": "Alt-Griechisch",
    "BCM": "Medienbildung",
    "BCS": "Basiscurriculum Sprachbildung",
    "BIO": "Biologie",
    "CH": "Chemie",
    "DGS": "Deutsche Gebärdensprache",
    "EL": "Neu Griechisch",
    "EN": "Englisch",
    "ES": "Spanisch",
    "Eth": "Ethik",
    "FR": "Französisch",
    "FS": "Moderne Fremdsprachen",
    "GE": "Geschichte",
    "HE": "Hebräisch",
    "IT": "Italienisch",
    "JP": "Japanisch",
    "KU": "Kunst",
    "NW": "Naturwissenschaften",
    "NW56": "Naturwissenschaften",
    "PL": "Polnisch",
    "PT": "Portugiesisch",
    "RU": "Russisch",
    "SOWI": "Sozialwissenschaft/Wirtschaftswissenschaft",
    "SOWi": "Sozialwissenschaft/Wirtschaftswissenschaft",
    "SU": "Sachunterricht",
    "SW": "Sorbisch/Wendisch",
    "TR": "Türkisch",
    "WAT": "Wirtschaft-Arbeit-Technik",
    "ZH": "Chinesich"
}


def mapToSubject(item):
    try:
        subject_abb = item.split("-")[1]
        if subject_abb in subject_mapping.keys():
            subject = subject_mapping[subject_abb]
            return subject
    except IndexError:
        return None

class Node:
    def __init__(self, **kwargs):
        self.internal_identifier = kwargs.get("internal_identifier")
        self.identifier = kwargs.get("identifier")
        self.prefLabel = kwargs.get("prefLabel")
        self.definition = kwargs.get("definition")
        self.subject = kwargs.get("subject")
        self.niveaus = kwargs.get("niveaus")

        self.level = kwargs.get("level")
        # corresponds to "hasPart"
        self.children = []

    def __repr__(self):
        return self.identifier


def getNiveaus(prefLabel, identifier):
    if re.search("^[A-H]+$", prefLabel) is not None:
        niveaus = list(prefLabel)
    else:
        niveaus = []

    # try to get niveaus outside of prefLabel
    try:
        if re.search("[A-H]", identifier.split("-")[4]) is not None:
            niveaus += list(identifier.split("-")[4])
        if re.search("[A-H]", identifier.split("-")[5]) is not None:
            niveaus += list(identifier.split("-")[5])
    except:
        pass
    return niveaus


def writeGraph(filename, data):
    with open(filename, "w") as f:
        f.write(data)
        f.close()
    print(f"File written to: {filename}")


def writeLog(log_filename, data):
    with open(log_filename, "w") as outfile:
        outfile.write("\n".join(data))


def parseXML(xml, tree):
    data = []
    log = []
    stop_word = "\\n"

    def getLevel(elem, level=0):
        node = {
            "identifier": elem.tag,
            "description": elem.text,
            "level": level
        }
        try:
            if re.search(stop_word, elem.text):
                pass
            else:
                data.append(node)
        except:
            error_message = f"Element has error: " \
                            f"XPATH: {tree.getpath(elem)} " \
                            f"TAG: {elem.tag}, " \
                            f"TEXT: {elem.text}"
            log.append(error_message)
        for child in elem.getchildren():
            getLevel(child, level+1)

        return data

    result = getLevel(xml)
    return result, log


def sortData(data):
    sorted_data = []
    identifiers = []
    for i, item in enumerate(data):
        subject = mapToSubject(item["description"])

        if item["identifier"] == "id":
            identifiers.append(item["description"])
            node = {
                "internal_identifier": str(uuid.uuid4()),
                # "internal_identifier": item["description"],
                "identifier": item["description"],
                "prefLabel": data[i+1]["description"],
                "subject": subject,
                "level": int(item["level"])-2,
            }
            sorted_data.append(node)

    # check for duplicate identifiers
    def logDuplicate(data):
        log = []
        c = Counter(data)
        duplicates = list(Counter({k: c for k, c in c.items() if c > 1}).elements())
        [log.append(f"Identifier: {identifier} is occuring multiple times") for identifier in duplicates]
        return log

    log = logDuplicate(identifiers)
    return sorted_data, log


def addToNode(data):
    root = Node()
    try:
        for record in data:
            last = root
            for _ in range(record['level']):
                last = last.children[-1]

            niveaus = getNiveaus(record["prefLabel"], record["identifier"])

            last.children.append(Node(
                internal_identifier =record["internal_identifier"],
                identifier = record['identifier'],
                prefLabel = record['prefLabel'],
                subject = record['subject'],
                niveaus = niveaus,
                level = record['level']
            ))
    except IndexError:
        pass

    return root


def buildSkos(nodes, name_of_graph):
    print("converting data to graph...")
    g = Graph()
    name_of_graph = name_of_graph
    description_of_vocab = "Darstellung des Lehrplans von BB als kontrolliertes Vokabular"

    OCBB = Namespace("http://opencurricula/berlin-brandenburg/")
    OEH = Namespace("http://w3id.org/openeduhub/learning-resource-terms/")
    SDO = Namespace("http://schema.org/")
    base = URIRef(OCBB)

    title = Literal(name_of_graph, lang="de")
    description = Literal(description_of_vocab, lang="de")
    creator = Literal("Henry Freye", lang="de")

    g.add((base, RDF.type, SKOS.ConceptScheme))
    g.add((base, DCTERMS.title, title))
    g.add((base, DCTERMS.description, description))
    g.add((base, DCTERMS.creator, creator))

    def add_items(nodes):
        for item in nodes.children:

            node = base + URIRef(item.internal_identifier)

            g.add((node, RDF.type, SKOS.Concept))
            # g.add((node, RDF.type, SDO.Course))

            prefLabelLiteral = Literal(item.prefLabel, lang="de")
            g.add((node, SKOS.prefLabel, prefLabelLiteral))
            g.add((node, SDO.name, prefLabelLiteral))

            # add subject
            subjectLiteral = Literal(item.subject, lang="de")
            g.add((node, SDO.about, subjectLiteral))

            # add identifier as sdo:identifier and as skos:note
            identifierLiteral = Literal(item.identifier, lang="de")
            g.add((node, SDO.identifier, identifierLiteral))
            g.add((node, SKOS.note, identifierLiteral))

            # add oeh:educationalNiveau
            for niveau in item.niveaus:
                niveauLiteral = Literal(niveau, lang="de")
                niveauURL = URIRef(
                    "http://w3id.org/openeduhub/vocabs/educationalNiveau/" + niveau)
                g.add((node, OEH.educationalNiveau, niveauLiteral))
                g.add((node, OEH.educationalNiveau, niveauURL))

            # add inScheme
            g.add((node, SKOS.inScheme, base))

            if item.children != []:
                for child in item.children:
                    g.add((node, SKOS.narrower, base + URIRef(child.internal_identifier)))
                    g.add((base + URIRef(child.internal_identifier), SKOS.broader, node))

            add_items(item)

    add_items(nodes)

    for child in nodes.children:
        node = base + URIRef(child.internal_identifier)
        g.add((base, SKOS.hasTopConcept, node))
        g.add((node, SKOS.topConceptOf, base))

    # Bind a few prefix, namespace pairs for more readable output
    g.bind("dct", DCTERMS)
    g.bind("skos", SKOS)
    g.bind("ocbb", OCBB)
    g.bind("oeh", OEH)
    g.bind("sdo", SDO)

    output = g.serialize(format='turtle').decode("utf-8")
    print(f"Graph built. Length of graph: {len(g)}")

    return output
