#http://xsong512.iteye.com/blog/1171106
import urllib  
import hashlib  
import os  
class Spider:  
    '''crawler html'''  
    def get_html(self,url):  
        sock = urllib.urlopen(url)  
        htmlSource = sock.read()  
        sock.close()  
        return htmlSource  
    def cache_html(self,filename,htmlSource):  
        f = open(filename,'w')  
        f.write(htmlSource)  
        f.close  
    def analysis_html(self,htmlSource):  
        #from lxml import etree  
        import lxml.html.soupparser as soupparser  
        dom = soupparser.fromstring(htmlSource)  
        #doc = dom.parse(dom)  
        r = dom.xpath(".//*[@id='lh']/a[2]")  
        print len(r)  
        print r[0].tag  
        '''  
        encode('gb2312')  
????????????????  
??:http://blogold.chinaunix.net/u2/60332/showart_2109290.html  
        '''  
        print r[0].text.encode('gb2312')  
        print 'done'  
    def get_cache_html(self,filename):  
        if not os.path.isfile(filename):  
            return ''  
        f = open(filename,'r')  
        content = f.read()  
        f.close()  
        return content  
if __name__ == '__main__':  
    spider = Spider()  
    url = 'http://www.baidu.com'  
    md5_str = hashlib.md5(url).hexdigest()  
    filename = "html-"+md5_str+".html"  
    htmlSource = spider.get_cache_html(filename);  
    if not htmlSource:  
        htmlSource = spider.get_html(url)  
        spider.cache_html(filename,htmlSource)  
    spider.analysis_html(htmlSource)  
