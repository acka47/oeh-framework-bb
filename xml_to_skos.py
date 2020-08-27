from lxml import etree as ET
from rdflib import Graph, Literal, Namespace, RDF, URIRef, BNode
from rdflib.namespace import SKOS, DCTERMS
from pathlib import Path
import re
import uuid
import os



class Node:
    def __init__(self, **kwargs):
        self.internal_identifier = kwargs.get("internal_identifier")
        self.identifier = kwargs.get("identifier")
        self.prefLabel = kwargs.get("prefLabel")
        self.definition = kwargs.get("definition")

        self.level = kwargs.get("level")
        # corresponds to "hasPart"
        self.children = []

    def __repr__(self):
        return self.identifier


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
            print(error_message)
        for child in elem.getchildren():
            getLevel(child, level+1)

        return data
  
    result = getLevel(xml)
    return result


def sortData(data):
    sorted_data = []
    for i, item in enumerate(data):
        if item["identifier"] == "id":
            node = {
                "internal_identifier": str(uuid.uuid4()),
                "identifier": item["description"],
                "prefLabel": data[i+1]["description"],
                "level": int(item["level"])-2,
            }
            sorted_data.append(node)
    return sorted_data


def addToNode(data):
    root = Node()
    try:
        for record in data:
            last = root
            for _ in range(record['level']):
                last = last.children[-1]

            last.children.append(Node(
                internal_identifier =record["internal_identifier"],
                identifier = record['identifier'],
                prefLabel = record['prefLabel'],
                level = record['level']
            ))
    except IndexError:
        pass

    return root


def buildSkos(nodes):
    g = Graph()
    name_of_graph = "curriculum_bb"
    description_of_vocab = "Darstellung des Lehrplans von BB als kontrolliertes Vokabular"

    OEH = Namespace("http://w3id.org/openeduhub/vocabs/" + name_of_graph + "/")

    base = URIRef(OEH)

    title = Literal(name_of_graph, lang="de")
    description = Literal(description_of_vocab, lang="de")
    creator = Literal("Henry Freye", lang="de")

    g.add( (base, RDF.type, SKOS.ConceptScheme) )
    g.add( (base, DCTERMS.title, title) )
    g.add( (base, DCTERMS.description, description) )
    g.add( (base, DCTERMS.creator, creator) )

    def add_items(nodes):
        for item in nodes.children:
            node = base + URIRef(item.internal_identifier)

            g.add((node, RDF.type, SKOS.Concept))

            prefLabelLiteral = Literal(item.prefLabel, lang="de")
            g.add( (node, SKOS.prefLabel, prefLabelLiteral) )

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
        g.add( (base, SKOS.hasTopConcept, node))
        g.add( (node, SKOS.topConceptOf, base ))

    # Bind a few prefix, namespace pairs for more readable output
    g.bind("dct", DCTERMS)
    g.bind("skos", SKOS)

    output = g.serialize(format='turtle', base=base).decode("utf-8")
    print("Graph built.")

    return output

log = []

tree = ET.parse("metadata.xml")
xmlRoot = tree.getroot()
parsedXML = parseXML(xmlRoot, tree)

data = sortData(parsedXML)

nodes = addToNode(data)
serialized_graph = buildSkos(nodes)

# create data dir if not there
Path(Path.cwd() / "data").mkdir(exist_ok=True)

# write graph
graphname = (Path.cwd() / "data" / "curriculum_bb_skos.ttl")
writeGraph(graphname, serialized_graph)

# write error log
log_filename = (Path.cwd() / "log.txt")
writeLog(log_filename, log)


print("I'm done. Goodbye!")

