from lxml import etree as ET
import lxml
from StringIO import StringIO
xml_file_path = "SR_US_100572652.svg"
def test_1():
    try:
        doc = ET.parse(xml_file_path)
    except:
        info = 'error : %s\n' % xml_file_path
        # write to log

'''lxml learn'''
#http://wenku.it168.com/d_000783427.shtml
def test_1_1():
    root = ET.Element('root')
    print root.tag # root

    root.append(ET.Element("child1"))
    child2 = ET.SubElement(root, "child2")
    child3 = ET.SubElement(root, "child3")
    child4 = ET.SubElement(child2, "child4")
    
    #print ET.tostring(root, pretty_print = True)
    print [child.tag for child in root]
    # elem is list
    print "=====elem list====="
    child = root[0]
    print child.tag
    print len(root)
    print root.index(root[0]) # 0, if child2:1; root[5]:error; lxml.etree only
    children = list(root)
    print [child.tag for child in root]
#    for child in root:
#        print child.tag
    print root
    print children

    # can insert elem with insert()
    root.insert(0, ET.Element("child0"))
#    print ET.tostring(root, pretty_print = True)
    print [child.tag for child in root]
    # del elem
    print "=====delete elem====="
    print [child.tag for child in root]
    root[0] = root[-1] # this moves the element
    print [child.tag for child in root]
#    for child in root:
#    print child.tag

    # deep copy
    print "=====deep copy====="
    from copy import deepcopy
    element = ET.Element("neu")
    element.append(deepcopy(root[1]))
    print (element[0].tag)
    print ([c.tag for c in root])
    print ([ne.tag for ne in element])

    # getparent return parent node
    print "=====getparent return parent node====="
    if root is root[0].getparent():  # lxml.etree only
        print "YES"

    # access sibling (or neighbours)
    print "=====access sibling (or neighbours)====="
    if root[0] is root[1].getprevious(): print "YES" # lxml.etree only
    if root[1] is root[0].getnext(): print "YES" # lxml.etree only

def test_1_2():
    # elem with attribute
    print "=====elem with attribute====="
    root = ET.Element("root", interesting = "totally")
    print ET.tostring(root)

    # set get attribute
    print root.get("interesting")
    root .set("interesting", "somewhat")
    print root.get("interesting")

    # Dic. api of attribute
    attributes = root.attrib
    print (attributes["interesting"])
    print attributes.get("hello")
    attributes["hello"] = "Guten Tag"
    print attributes.get("hello")
    print root.get("hello")
    print root.attrib # {'interesting': 'somewhat', 'hello': 'Guten Tag'}
    
    # elem have content
    root = ET.Element("root")
    root.text = "TEXT"
    print root.text
    print ET.tostring(root, pretty_print = True)

    html = ET.Element("html")
    body = ET.SubElement(html, "body")
    body.text = "TEXT"
    print ET.tostring(html)
    br = ET.SubElement(body, "br")
    print ET.tostring(html)
    br.tail = "TAIL"
    print ET.tostring(html)
    # ???
    print html.xpath("string()") # lxml.etree only
    print html.xpath("//text()") # lxml.etree only

    # create fun ???
    build_text_list = ET.XPath("//text()") # lxml.etree only!
    print(build_text_list(html))
    # through getparent to get parent node
    texts = build_text_list(html)
    print(texts[0])   #TEXT
    parent = texts[0].getparent()
    print(parent.tag) #body
    print(texts[1])   # TAIL
    print(texts[1].getparent().tag) # br
    print(texts[0].is_text)# True
    print(texts[1].is_text)# False
    print(texts[1].is_tail)#True

def test_1_3():
    # tree iteration
    root = ET.Element("root")
    ET.SubElement(root, "child").text = "Child 1"
    ET.SubElement(root, "child").text = "Child 2"
    ET.SubElement(root, "another").text = "Child 3"
#    print(ET.tostring(root, pretty_print=True))
    print ET.tostring(root)

    for elem in root.iter():
        print "%s-[%s]" % (elem.tag, elem.text)
    # filter
    print "=====after filter====="
    for elem in root.iter("child"):
        print "%s-[%s]" % (elem.tag, elem.text)

    root.append(ET.Entity("#234"))
    root.append(ET.Comment("some comment"))
    for elem in root.iter():
        if isinstance(elem.tag, basestring):
            print "%s - %s" % (elem.tag, elem.text)
        else:
            print "SPECIAL: %s - %s" % (elem, elem.text)

    for elem in root.iter(tag = ET.Element):
        print "%s-[%s]" % (elem.tag, elem.text)

# lxml learn note 3
def test_1_4():
    # Serialization
    root = ET.XML("<root><a><b/></a></root>")
    print ET.tostring(root)
    print ET.tostring(root, xml_declaration=True)
    print ET.tostring(root, encoding="iso-8859-1")
    #print ET.tostring(root, pretty_print=True)
    # appends a newline at the end 
    print "dfd"

    root = ET.XML("<html><head/><body><p>Hello<br/>World</p></body></html>")
    print ET.tostring(root) # default: method = 'xml'
    print ET.tostring(root, method="html")
    #print etree.tostring(root, method="html", pretty_print=True)
    print ET.tostring(root, method="text")

    # default acsII
    br = root.find(".//br")  # find from all doc
    br.tail = u"W\xf6rld"
    #ET.tostring(root, method="text")  # error
    print ET.tostring(root, method="text", encoding="UTF-8")
    # print ET.tostring(root, method="text", encoding=unicode)  # error ?

    # Element
    # 1 
    tree = ET.parse(StringIO(r' <!DOCTYPE root SYSTEM "test" [ <!ENTITY tasty     "eggs"> ]>     <root><a>&tasty;</a></root>     '))
    print "====="
    print  tree.docinfo.doctype
    print "====="
    print ET.tostring(tree)
    print "====="
    print ET.tostring(tree.getroot())

    # 2
    tree_string = r' <!DOCTYPE root SYSTEM "test" [ <!ENTITY tasty     "eggs"> ]>     <root>     <a>&tasty;</a>     </root>     '
    some_xml_data = "<root>data</root>"
    tree = ET.fromstring(tree_string)
    # 3
    root = ET.XML("<root>data</root>")
    # 4
    some_file_like = StringIO("<root>data</root>")
    tree = ET.parse(some_file_like)

    # parse return a object, not string ,so
    print ET.tostring(tree)

# parse engin
# lxml learn note 4
def test_1_5():
    parser = ET.XMLParser(remove_blank_text=True) # lxml.etree only!
    root = ET.XML("<root> <a/> <b> </b> </root>", parser)
    print ET.tostring(root)

    # increase parse
    # way one through file object, call times read funcation
    class DataSource:
        data = [ b"<roo", b"t><", b"a/", b"><", b"/root>" ]
        def read(self, requested_size):
            try:
                return self.data.pop(0)
            except IndexError:
                return b''

    tree = ET.parse(DataSource())
    print ET.tostring(tree)

    # way two through feed close
    parser = ET.XMLParser()
    parser.feed("<roo")
    parser.feed("t><")
    parser.feed("a/")
    parser.feed("><")
    parser.feed("/root>")
    root = parser.close()
    print ET.tostring(root)
if __name__ == "__main__":
    test_1_4()
