from lxml import etree as ET

xml_path = r"\\tj-map16\simon\tools\find_impact_region\admintypes.xml"
file_impact = r"\\tj-map16\simon\tools\find_impact_region\SubRegion.out"
region_country = {}
country_piece = {}
all_reg = set()
impact_reg = set()
def load_xml(file_path):
    root = ET.parse(file_path)
    regions = root.findall('/MultiMap/Region/SubRegion')
    for elem in regions:
        if not elem.attrib.has_key("copy"):
            countrys = elem.text.split(' ')
            for c in countrys:
                if not region_country.has_key(c):
                    region_country[c] = elem.attrib['name']
                    all_reg.add(elem.attrib['name'])
                else:
                    print "repeated country -- ", c, region_country[c]
    #print region_country
    states = root.find('/regions/')
    for state in states.getchildren():
        for country in state.getchildren():
            pieces = country.text.split(' ')
            for piece in pieces:
                if not country_piece.has_key(piece):
                    country_piece[piece] = country.tag
                else:
                    print "repeated piece -- ", piece, country_piece[piece]

def get_impact_region(piece):
    if country_piece.has_key(piece):
        if region_country.has_key(country_piece[piece]):
            return region_country[country_piece[piece]]
        else:
            print "no this country ", country_piece[piece], piece
    else:
        print "no this piece [", piece,
        
if __name__ == "__main__":
    load_xml(xml_path)
    fp = open(file_impact, "r")
    for line in fp.readlines():
        impact_reg.add(get_impact_region(line[0:3]))
    print impact_reg
    print all_reg & impact_reg
    print all_reg - impact_reg
