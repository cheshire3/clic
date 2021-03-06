import os
from math import log1p
import operator

from cheshire3.document import StringDocument
from cheshire3.internal import cheshire3Root
from cheshire3.server import SimpleServer
from cheshire3.baseObjects import Session

cheshirePath = os.path.join('HOME', '/home/cheshire')

class Keywords(object):
    
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
        self.logger = self.db.get_object(self.session, 'keywordLogger')
        
    def list_keywords(self, testIdxName, testMaterials, refIdxName, refMaterials, pValue):
        #self.logger.log(10, 'CREATING KEYWORDS FOR RS: {0} in {1}, compared to {2} in {3}'.format(testIdxName, testMaterials, refIdxName, refMaterials, pValue)) 
        session = self.session
        db = self.db

        clauses = []
        for testMaterial in testMaterials:
            if testMaterial in ['dickens', 'ntc']:
                testMatIdx = 'subCorpus-idx'
            else:
                testMatIdx = 'book-idx'
            clauses.append('c3.{0} = "{1}"'.format(testMatIdx, testMaterial))
            
        test_query = self.qf.get_query(session,
                                       ' or '.join(clauses)
                                       )        
        test_results = db.search(session, test_query)
        test_idx = db.get_object(session, testIdxName)
        test_facets = test_idx.facets(session, test_results)
        
        ## create dictionary containing word/cluster and number of occurrences
        test_dict = {x[0]: x[1][2] for x in test_facets}
        
        # Reference results
        clauses_ref = []
        for refMaterial in refMaterials:
            if refMaterial in ['dickens', 'ntc']:
                refMatIdx = 'subCorpus-idx'
            else:
                refMatIdx = 'book-idx'
            clauses_ref.append('c3.{0} = "{1}"'.format(refMatIdx, refMaterial))

        ref_query = self.qf.get_query(session,
                                       ' or '.join(clauses_ref)
                                       )
        ref_results = db.search(session, ref_query)
        ref_idx = db.get_object(session, refIdxName)
        ref_facets = ref_idx.facets(session, ref_results)
        ref_dict = {x[0]: x[1][2] for x in ref_facets}
        
        ## get test and ref lengths
        ## I use total counts to calculate expected values
        testLength = sum(test_dict.values())
        refLength = sum(ref_dict.values())        
       
        kw_list = []
        for term, freqTest in test_dict.iteritems():
            if freqTest > 1:
                try:
                    ## Method 1: how many observations of a given word is found in ref corpus but not in test corpus
                    ## Subtract number of occurrences in testIndex from number of occurrences in sentences
                    #freqRef = float(ref_dict[term] - freqTest)
                    ## Method 2: treat groups as mutually exclusive. NOTE: When comparing quotes with whole text the occurrences will overlap
                    freqRef = float(ref_dict[term])
                except KeyError:
                    freqRef = 5.0e-324
                else:
                    if freqRef <= 0:
                        freqRef = 5.0e-324
                
                ## following Paul Ryson formula for log likelihood (http://ucrel.lancs.ac.uk/llwizard.html)
                ## 1. Expected occurrence within corpus
                ## 1a. Expected reference value: based on sentence index
                ## - Get the total N from corpus 1 (reference corpus)
                ## - Multiply by the sum of observations found in ref corpus and those found in test corpus
                ## - Divide by the sum of total N in test corpus and reference corpus
                expectedRef = refLength*(freqTest+freqRef)/(testLength+refLength)
                ## 1b. Expected test value
                ## Equivalent steps to 1a, but multiply by test N
                expectedTest = testLength*(freqTest+freqRef)/(testLength+refLength)
                  
                ## 2. Log Likelihood
                ## Compare actual observations with expected ocurrence for both test and ref, and add these values
                ## Use log1p() (for natural logarithm - ln) instead of log()
                if freqTest*log1p(freqTest/expectedTest) >= freqRef*log1p(freqRef/expectedRef):
                    try:
                        LL = 2*((freqTest*log1p(freqTest/expectedTest)) + (freqRef*log1p(freqRef/expectedRef)))
                        LL = '%.2f' % LL
                    except:
                        LL = 909090
                else:
                    try:
                        LL = -2*((freqTest*log1p(freqTest/expectedTest)) + (freqRef*log1p(freqRef/expectedRef)))
                        LL = '%.2f' % LL
                    except:
                        LL = 909090
                
                if freqRef == 5.0e-324:
                    freqRef2 = 0
                else:
                    freqRef2 = int('%.0f' % freqRef)               
           
               
                dec_Test = '%.2f' % freqTest
                dec_Ref = '%.2f' % freqRef
                propTest = (float(dec_Test)/testLength) * 100
                propRef = (float(dec_Ref)/refLength) * 100                
              
                
                if float(pValue) == 0.000001:                     
                    if float(LL) >= 23.93:# or float(LL) <= -23.93: ## We only deal with positive LL values
                        kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                          
                else:
                    if float(pValue) == 0.0000001:
                        if float(LL) >= 28.38:
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                    if float(pValue) == 0.00000001:
                        if float(LL) >= 32.85:
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                    if float(pValue) == 0.000000001:
                        if float(LL) >= 37.33:
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                    if float(pValue) == 0.0000000001:
                        if float(LL) >= 41.83:
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                    if float(pValue) == 0.00000000001:
                        if float(LL) >= 46.33:
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])
                    
                    if float(pValue) == 0.00001:
                        if (float(LL) > 19.52):# or (float(LL) < -19.52):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])    
                    elif float(pValue) == 0.0001: 
                        if (float(LL) > 15.14):# or (float(LL) < -15.14):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue])  
                    elif float(pValue) == 0.001: 
                        if (float(LL) > 10.83):# or (float(LL) < -10.83):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue]) 
                    elif float(pValue) == 0.01: 
                        if (float(LL) > 6.64):# or (float(LL) < -6.64):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue]) 
                    elif float(pValue) == 0.05: 
                        if (float(LL) > 3.85):# or (float(LL) < -3.85):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue]) 
                    elif float(pValue) == 0.1: ## NB: returns all values
                        if (float(LL) > 2.71):# or (float(LL) < -2.71):
                            kw_list.append(['', term, str(freqTest), '%.2f' % propTest, str(freqRef2), '%.2f' % propRef, float(LL), pValue]) 

        ## sort by K value (descending)
        kw_list.sort(key=operator.itemgetter(6), reverse=True) ## reverse=TRUE for descending order

        return kw_list[0:4999]

                                            
        
        
        
        