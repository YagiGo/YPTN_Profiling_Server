# -*- coding: utf-8 -*-
# get all urls of a webpage
import db.config
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ABWPR.accessManager import DBInteract

class WebpageExtract(DBInteract):
    def __init__(self, url):
        super(WebpageExtract, self).__init__()
        self.url = url
        self.THRESHOLD = 7

    def generatePath(self):
        pass

    def predict(self):
        parsedSoup = BeautifulSoup(open('../news.yahoo.co.jp.html', 'r'), 'html.parser')
        allUrls = self.findAndParseURLs(parsedSoup)
        RUCValueDB = self.client[self.RUC_VALUE_DB]
        RUCValueCollection = RUCValueDB.collection_names()
        allLinkCount = len(allUrls)
        cacheLinkCount = 0
        uncacheLinkCount = 0
        for urlInfo in allUrls:

            domain =  urlInfo["netloc"]
            if domain in RUCValueCollection:
                # get the newest ruc value
                newestRUC = RUCValueDB[domain].find().sort([('timestamp', -1)]).limit(1)[0]
                if self.THRESHOLD < newestRUC["RUCValue"]:
                    # print "will cache {}".format(urlInfo["originalUrl"])
                    cacheLinkCount += 1
                else:
                    print("will not cache {}".format(urlInfo["originalUrl"]))
                    uncacheLinkCount += 1
        print("All link count {}, cache link count   {}, uncache link count {}, cache rate {}".format(allLinkCount, cacheLinkCount, uncacheLinkCount, str(cacheLinkCount / allLinkCount)))
        # TODO Send the result to ESM with websocket, asking it to cache related URLs

    def findAndParseURLs(self, soup):
        allUrls = []
        for link in soup.find_all('a'):
            urlFound = link.get('href')
            urlParseResult = urlparse(urlFound)

            urlInfo = dict()
            urlInfo['scheme'] = urlParseResult.scheme
            urlInfo['netloc'] = urlParseResult.netlocloa
            urlInfo['path'] = urlParseResult.path
            urlInfo['param'] = urlParseResult.params
            urlInfo['query'] = urlParseResult.query
            urlInfo['fragment'] = urlParseResult.fragment
            urlInfo['originalUrl'] = urlFound
            allUrls.append(urlInfo)
        return allUrls

    def extractDomain(self, soup):
        pass


if __name__ == '__main__':
    testExt = WebpageExtract('news.yahoo.co.jp')
    testExt.predict()
    testExt.predict()
