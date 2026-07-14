import xml.etree.ElementTree as ET
import re

def get_clean_tree(xmlfile):
    """
    Strips all tags of the url. 
    
    The molpro generated xml files have tag names with url appended to them,
    which makes it cumbersome to parse. This code simply strips them out
    using '}' as a delimiter.
    """
    try:
        tree = ET.parse(xmlfile)
    except ET.ParseError:
        raise ValueError("Must provide a valid XML file")
    except Exception as e:
        # Handles cases like file not found, permission error, etc.
        raise ValueError("Must provide a valid XML file") from e
    
    for elem in tree.iter():
        elem.tag = elem.tag.split("}")[1]
    return tree

def find_by_attrib(nodes, key, value):
    """
    Find all nodes that have key:value pair in their attrib

    Arguments:
        nodes : an iterable of xml elements
        key : dictionary key
        value : corresponding dict value
    """
    results = []
    for node in nodes:
        if not key in node.attrib: continue
        if value == node.attrib[key]:
            results.append(node)
        
    return results

def get_xmlener(xmlfile, command='DF-MP2-F12', enertype='total energy', verbose=False):
    """
    Get energy from a given xml file
    Can only have a single total energy, won't work on xml
    files containing energies from multiple runs (or jobs).
    """
    tree = get_clean_tree(xmlfile)
    root = tree.getroot()
    jobsteps = root.findall('.//jobstep')
    #energy_elems = root.findall(f".//property/[@name='{name}']")
    try:
        requested_jobs, = find_by_attrib(jobsteps, 'command', command)
    except ValueError as e:
        print("ERROR READING ENERGY =============================")
        print(f"{xmlfile} does not contain a single unique '{command}' method jobstep")
        print("==================================================")
        raise(e)

    try:
        requested_ener, = find_by_attrib(requested_jobs, 'name', enertype)
    except ValueError as e:
        print("ERROR READING ENERGY =============================")
        print(f"jobstep does not contain a single unique '{enertype}'")
        print("==================================================")
        raise(e)
    ener = requested_ener.attrib['value']
    method = requested_ener.attrib['method']
    name = requested_ener.attrib['name']
    if verbose:
        print(f"{method} {name}: {ener}")

    return float(ener)

