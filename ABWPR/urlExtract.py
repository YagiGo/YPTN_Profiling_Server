# -*- coding: utf-8 -*-
# get all urls of a webpage
import db.config
from bs4 import BeautifulSoup
from urlparse import urlparse

class WebpageExtract:
    def __init__(self, url):
        self.url = url

    def generatePath(self):
        pass

    def loadPage(self):
        parsedSoup = BeautifulSoup(open('../news.yahoo.co.jp.html', 'r'), 'html.parser')
        allUrls = self.findAndParseURLs(parsedSoup)
        print allUrls


    def findAndParseURLs(self, soup):
        allUrls = []
        for link in soup.find_all('a'):
            urlFound = link.get('href')
            urlParseResult = urlparse(urlFound)

            urlInfo = dict()
            urlInfo['scheme'] = urlParseResult.scheme
            urlInfo['netloc'] = urlParseResult.netloc
            urlInfo['path'] = urlParseResult.path
            urlInfo['param'] = urlParseResult.params
            urlInfo['query'] = urlParseResult.query
            urlInfo['fragment'] = urlParseResult.fragment
            allUrls.append(urlInfo)
        return allUrls

    def extractDomain(self, soup):

        pass


if __name__ == '__main__':
    testExt = WebpageExtract('news.yahoo.co.jp')
    testExt.loadPage()