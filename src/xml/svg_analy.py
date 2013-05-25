from lxml import etree as ET

svg_path = r'SR_US_100572652.svg'
test_file = r'test_2_file.xml'
def analy_svg():
    doc = ET.parse(svg_path)
    #print ET.tostring(doc)
#    for route in doc.findall(r'{http://www.navteq.com/SaR3/1.0}routes'):
    for route in doc.findall(r'.//{http://www.navteq.com/SaR3/1.0}SVGObject'):
        print route.tag
    
if __name__ == "__main__":
    analy_svg()
