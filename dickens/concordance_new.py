import os
import re

from cheshire3.document import StringDocument
from cheshire3.internal import cheshire3Root
from cheshire3.server import SimpleServer
from cheshire3.baseObjects import Session

from lxml import etree

class Concordancer(object):
    
    def __init__(self):
        self.session = Session()
        self.session.database = 'db_dickens'
        self.serv = SimpleServer(self.session, 
                                 os.path.join(cheshire3Root, 'configs', 'serverConfig.xml')
                                 )
        self.db = self.serv.get_object(self.session, self.session.database)
        self.qf = self.db.get_object(self.session, 'defaultQueryFactory')
        self.resultSetStore = self.db.get_object(self.session, 'resultSetStore')        
        self.idxStore = self.db.get_object(self.session, 'indexStore')
        ## self.logger = self.db.get_object(self.session, 'concordanceLogger') ## TODO: add to dbs/dickens/config
        
#     def search(self, req):        
#         ## get search id and identify the relevant records
#         args = request.args
        
    def create_concordance(self, terms, idxName): #, Materials): 
        ## create a list of lists containing each three contexts, and a list within those contexts containing each word
        session = self.session
        db = self.db
        qf = self.qf
        
        query = qf.get_query(session, 'c3.%s-idx = "%s"' % (idxName, terms))
        rs = db.search(session, query)
        if len(rs) > 0:
            for i in rs:
                rec = i.fetch_record(session)
                tree = rec.get_dom(session).getroottree() 
                print tree.xpath('//div')[0].get('id')
                
                for m in i.proxInfo:                    
               
                    if idxName in ['quote', 'non-quote', 'longsus', 'shortsus']:  
                        elems = [0] 
                        (e_q, w_q) = (m[0][0], m[0][1])     
                        print e_q, w_q   
                        
                        ## locate search term in xml
                        search_term = tree.xpath('//div/descendant::w[%d+1]' % w_q)                  

                        sentence_tree = tree.xpath('//*[@eid="%d"]/following::w[%d+1]/ancestor-or-self::s' % (e_q, w_q))[0]                     
                        chapter_tree = tree.xpath('//*[@eid="%d"]/following::w[%d+1]/ancestor-or-self::div' % (e_q, w_q))[0]  
                        
                        print sentence_tree.get('id')
                        
                        ## count number of words in chapter_tree until (first) target word
                        
                        #count = chapter_tree.xpath('count(//s)')
                        
                        count = 0
#                         for word in chapter_tree.xpath('//w'):
#                             count = count + int(word.get('o'))
#                         
#                         print count
                        prec_s_tree = chapter_tree.xpath('//div/descendant::s[@sid="3"]/preceding-sibling::s/descendant::w')
                        print len(prec_s_tree)
                            
                        #//div/descendant::s[@sid="3"]/preceding-sibling::s/descendant::w
                        
#                         count_words = 0
#                         for word in chapter_tree.xpath('//div/descendant::w'):
#                             #if word.xpath('//w/ancestor::s[@id=%s]' % sentence_tree.get('id')):
#                             if not word.xpath('//w/ancestor::s')[0].get('id') == sentence_tree.get('id'):
#                             #if word.xpath('//w/ancestor::s[@sid="1"]'):
#                                 count_words += 1
#                             else:
#                                 break
#                         print count_words
                                  
                             
#                         c_walker = chapter_tree.getiterator()
#                         count = 0
#                         print terms.split(' ')[0]
#                         for c in c_walker:
#                               
#                             if c.tag == 'w' and not c.text.lower() == terms.split(' ')[0]:
#                                 count += 1
#                             elif c.tag == 'w' and c.text.lower() == terms.split(' ')[0]: 
#                                 ## verify sentence match
#                                 if not sentence_tree == chapter_tree.xpath('//div/descendant-or-self::w[%d+1]/ancestor-or-self::s' % count)[0] :
#                                     count += 1 ##?
#                                     continue  
#                                 elif sentence_tree == chapter_tree.xpath('//div/descendant-or-self::w[%d+1]/ancestor-or-self::s' % count)[0] :
#                                     ## verify word match
#                                     print c.get('o'), search_term[0].get('o')
#                                     if not c.get('o') == search_term[0].get('o'):
#                                         count += 1 ##?
#                                         continue
#                                     else:
#                                         break
#                                       
#                         w = count
#                         (e, w) = (0, w) 
#                         print 'word number: ', w
#                         
#                         ## for quotes I want the chapter tree 
#                         if idxName == 'quote': 
#                                                       
#                             #for x in chapter_tree.xpath('//div/descendant-or-self::w[%d+1]' % w):
#                             #for x in chapter_tree.xpath('//div/descendant::w[%d+1]' % w):
#                             for x in chapter_tree.xpath('//div/descendant::w[3927]'):
#                                 print x.text
#                                 
#                             print len(chapter_tree.xpath('//div/descendant::w'))
#                                 
                break

                            
            




        
        
        
