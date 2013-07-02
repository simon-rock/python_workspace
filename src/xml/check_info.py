#encoding: utf-8
from lxml import etree as ET
import lxml

#检验编码方式
def encoding(s):
    cl = ['utf8', 'gb2312']
    for a in cl:
        try:
            s.decode(a)
            return a
        except UnicodeEncodeError:
            pass
        return 'unknown'

def check_info(xml_path):
    try:
        # parse 可以解析utf-8，unicode格式  内部处理成unicode和str（ascii 处理成str）
        doc = ET.parse(xml_path)
    except:
        info = 'error : %s\n' % xml_path

    # 查找所有state 信息
    res = doc.findall('.//state')
    states = {}
    #list 循环
    for r in res:
#        print r.get("name").encode('utf8')
        #if not states.has_key(r.get("name").encode('utf8')):
        if not states.has_key(r.get("name")):# 此时key 有unicode和str两种
            #states[r.get("name").encode('utf8')] = 1
            states[r.get("name")] = 1
        else:
#            print "------------------"
            #states[r.get("name").encode('utf8')] += 1
            states[r.get("name")] += 1

    print len(res), type(res)
    print len(states), type(states)

#    print states
    #dict 循环
    for k in states.iterkeys():
        if states[k] > 1:
            print k.encode('utf8'),"\t=>",states[k]
if __name__ == "__main__":
    check_info("d:/py_test/admintypes.xml")

#<config version="1.2" date="2011-05-24">
#	<countries>
#		<country id="1" abbr2="US" abbr3="USA" name="United States">
#			<adminlvls displvl="3" adminlvl="4 -1" drivingside="right" lang="ENG"/>
#			<state id="0" abbr="AL" name="ALABAMA"/>
#			<state id="1" abbr="AK" name="ALASKA"/>
#			<state id="2" abbr="AZ" name="ARIZONA"/>
#			<state id="3" abbr="AR" name="ARKANSAS"/>
#			<state id="4" abbr="CA" name="CALIFORNIA"/>
#			<state id="5" abbr="CO" name="COLORADO"/>
#           <state id="73" abbr="PR" name="PUERTO RICO">
#            <adminlvls lang="SPA" displvl="-1" adminlvl="3 4" drivingside="right"/>
#			</state>
#			<state id="74" abbr="VI" name="US VIRGIN ISLANDS">
#			    <adminlvls lang="ENG" displvl="-1" adminlvl="3 4" drivingside="left"/>			
#		    </state>
#	    </country>
#  </countries>
#</config>
