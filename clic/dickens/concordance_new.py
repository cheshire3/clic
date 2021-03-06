import os

from cheshire3.document import StringDocument
from cheshire3.internal import cheshire3Root
from cheshire3.server import SimpleServer
from cheshire3.baseObjects import Session

import json

wd = os.getcwd()

## get metadata: Information about chapters, word counts etc. from each individual book
booklist_r = open(''.join(wd + '/clic/dickens/booklist'), 'r')
booklist = json.load(booklist_r)

class Concordancer_New(object):
    
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
        #self.logger = self.db.get_object(self.session, 'concordanceLogger')      
       
    ## main concordance method
    ## create a list of lists containing each three contexts left - node -right, 
    ## and a list within those contexts containing each word. Add two separate lists containing metadata information:
    ## [ [left context - word 1, word 2, etc.], [node - word 1, word 2, etc], [right context - word 1, etc], 
    ##   [chapter metadata], [book metadata]
    ## ], 
    ## etc.
    def create_concordance(self, terms, idxName, Materials, selectWords): 
        ##self.logger.log(10, 'CREATING CONCORDANCE FOR RS: {0} in {1} - {2}'.format(terms, idxName, Materials)) 
        session = self.session
        db = self.db
        qf = self.qf        
        
        conc_lines = [] # return concordance lines in list
        wordWindow = 10 # wordWindow is set to 10 by default - on both sides of node
    
        books = []
        for Material in Materials:
            MatIdx = 'book-idx'
            if Material in ['dickens', 'ntc']:
                MatIdx_Vol = 'subCorpus-idx'
                books.append('c3.{0} = "{1}"'.format(MatIdx_Vol, Material))
            else:
                books.append('c3.{0} = "{1}"'.format(MatIdx, Material)) 
            
        ## search whole phrase or individual words?
        if selectWords == "whole":
            nodeLength = len(terms.split(' '))
            terms = [terms]  
        else:
            nodeLength = 1
            terms = terms.split(' ')
        
        ## define search term
        term_clauses = []
        for term in terms:
            term_clauses.append('c3.{0} = "{1}"'.format(idxName, term))      
        
        ## conduct database search
        ## note: /proxInfo needed to search individual books
        query = qf.get_query(session, ' or '.join(books) + ' and/proxInfo ' + ' or '.join(term_clauses))         
        rs = db.search(session, query) 
    
        ## get total number of hits (not yet used in interface)  
        total_count = 0        
        if len(rs) > 0:   
            for i in rs:                
                total_count = total_count + len(i.proxInfo)   
        
        ## search through each record (chapter) and identify location of search term(s)
        if len(rs) > 0:            
            count = 0 ## count hits
            for i in rs:
                 
                ## get xml record 
                rec = i.fetch_record(session)
                tree = rec.get_dom(session).getroottree()        
                  
                for m in i.proxInfo: 
                    count += 1
                      
                    if count > 1000: ## current search limit: 1000
                        break
                    else:
                       
                        if idxName in ['chapter-idx']:    
                            w = m[0][1]                                          
                       
                        elif idxName in ['quote-idx', 'non-quote-idx', 'longsus-idx', 'shortsus-idx']:  
                            (e_q, w_q) = (m[0][0], m[0][1])                    
                                
                            ## locate search term in xml
                            search_term = tree.xpath('//*[@eid="%d"]/following::w[%d+1]' % (e_q, w_q)) 
        
                            ## get xml of sentence
                            sentence_tree = tree.xpath('//*[@eid="%d"]/following::w[%d+1]/ancestor-or-self::s' % (e_q, w_q))    
                            chapter_tree = tree.xpath('//*[@eid="%d"]/following::w[%d+1]/ancestor-or-self::div' % (e_q, w_q))                         
                               
                            ## counts words preceding sentence   
                            prec_s_tree = chapter_tree[0].xpath('//div//s[@sid="%s"]/preceding::s/descendant::w' % sentence_tree[0].get('sid'))
                            prec_s_wcount = len(prec_s_tree)
        
                            ## count words within sentence
                            count_s = 0                        
                            for word in chapter_tree[0].xpath('//div//s[@sid="%s"]/descendant::w' % sentence_tree[0].get('sid')):
                                if not word.get('o') == search_term[0].get('o'):
                                    count_s += 1
                                else:
                                    break
        
                            ## word number within chapter is adding word count in preceding sentence and word count in current sentence
                            wcount = prec_s_wcount + count_s                                            
                            w = wcount                
        
                        
                    ## Define leftOnset as w - 10, then get all w and n between that and node
                    wordWindow = int(wordWindow)
                    leftOnset = max(1, w-wordWindow+1) ## we operate with word position, not list position (word 1 = 0 position in list)
                    nodeOnset = w+1
                    nodeOffset = w+nodeLength
                    try:
                        rightOnset = nodeOffset + 1
                    except:
                        rightOnset = None
                             
                    ch_words = len(tree.xpath('//div/descendant::w')) ## move to level for each record (chapter) ?                      
                    rightOffset = min(rightOnset + wordWindow, rightOnset + (ch_words - rightOnset) + 1 )
                          
                    left_text = []   
                    for l in range(leftOnset, nodeOnset):
                        try:
                            left_n_pr = tree.xpath('//div/descendant::w[%d]/preceding-sibling::n[1]' % l)[0].text
                        except:
                            left_n_pr = ''  
                        left_w = tree.xpath('//div/descendant::w[%d]' % l)[0].text
                        try: 
                            left_n_fo = tree.xpath('//div/descendant::w[%d]/following-sibling::n[1]' % l)[0].text   
                        except:
                            left_n_fo = ''                 
                        left_text.append(''.join(left_n_pr + left_w + left_n_fo))
                                
                                 
                    node_text = [] 
                    for n in range(nodeOnset, rightOnset):
                        try:
                            node_n_pr = tree.xpath('//div/descendant::w[%d]/preceding-sibling::n[1]' % n)[0].text     
                        except:
                            node_n_pr = ''             
                        node_w = tree.xpath('//div/descendant::w[%d]' % n)[0].text
                        try:
                            node_n_fo = tree.xpath('//div/descendant::w[%d]/following-sibling::n[1]' % n)[0].text
                        except:
                            node_n_fo
                        node_text.append(''.join(node_n_pr + node_w + node_n_fo))
                                              
                    right_text = [] 
                    for r in range(rightOnset, rightOffset): 
                        try:
                            right_n_pr = tree.xpath('//div/descendant::w[%d]/preceding-sibling::n[1]' % r)[0].text
                        except:
                            right_n_pr = ''                        
                        right_w = tree.xpath('//div/descendant::w[%d]' % r)[0].text
                        try:
                            right_n_fo = tree.xpath('//div/descendant::w[%d]/following-sibling::n[1]' % r)[0].text
                        except:
                            right_n_fo = ''
                        right_text.append(''.join(right_n_pr + right_w + right_n_fo))
                        
                    ### 
                    book = tree.xpath('//div')[0].get('book')
                    chapter = tree.xpath('//div')[0].get('num')
                    para_chap = tree.xpath('//div//descendant::w[%d+1]/ancestor-or-self::p' % w)[0].get('pid')
                    sent_chap = tree.xpath('//div//descendant::w[%d+1]/ancestor-or-self::s' % w)[0].get('sid')
                    word_chap = w                 
                        
                    ## count paragraph, sentence and word in whole book
                    count_para = 0
                    count_sent = 0
                    count_word = 0
                    booktitle = []
                    total_word = []
                    for b in booklist:
                        if b[0][0] == book:
                                
                            booktitle.append(b[0][1])
                            total_word.append(b[1][0][2])
                                          
                            for j, c in enumerate(b[2]):
                                while j+1 < int(chapter):
                                    count_para = count_para + int(c[0])
                                    count_sent = count_sent + int(c[1])
                                    count_word = count_word + int(c[2])
                                    j += 1
                                    break
                                    
                                ## total word in chapter
                                if j+1 == int(chapter):
                                    chapWordCount = b[2][j][2]
                        
                    book_title = booktitle[0]   ## get book title 
                    total_word = total_word[0]     
                    para_book = count_para + int(para_chap)       
                    sent_book = count_sent + int(sent_chap)  
                    word_book = count_word + int(word_chap)                     
   
                    conc_line = [left_text, node_text, right_text,
                                [book, book_title, chapter, para_chap, sent_chap, str(word_chap), str(chapWordCount)],
                                [str(para_book), str(sent_book), str(word_book), str(total_word)]]
                        
                        
                    conc_lines.append(conc_line)
    
        conc_lines.insert(0, len(conc_lines))  
        #conc_lines.insert(0, total_count)  
        return conc_lines
    
                

                            
            




        
        
        
