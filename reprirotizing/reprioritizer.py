# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ABWPR.accessManager import DBInteract
import hashlib, os, sys

class Reprioritizer(DBInteract):
    def __init__(self):
        super(Reprioritizer, self).__init__()
        self.TEST_PATH = '/home/zhaoxinwu/workspace/ServerSide/output/www.softlab.cs.tsukuba.ac.jp/members.html'
        self.TEST_WRITE_PATH = '/home/zhaoxinwu/workspace/ServerSide/output/www.softlab.cs.tsukuba.ac.jp/members.html'
        self.PLACEHOLDER_PATH = 'placeholder.jpg'
        self.ROOT_PATH = "/home/zhaoxinwu/workspace/YPTN_Profiling_Server"
        self.LAZY_LOAD_PATH = '/js/lazyload.js'
        self.LAZY_LOAD_EDGE_PATH = 'assets/js/lazyload.js'
        self.LAZY_LOAD_DIGEST = '394BE70E6F7B6285BD89F6CAF89EC01A'.lower()

    def md5Hash(self, filePath):
        return hashlib.md5(open(filePath, "rb").read()).hexdigest()

    def lazylizeImage(self):


        # print(self.TEST_PATH)
        try:
            parsedSoup = BeautifulSoup(open(self.TEST_PATH, 'r'), 'html.parser')
        except UnicodeDecodeError:
            print("WARNING: This file is not UTF-8, try another encoding")
            parsedSoup = BeautifulSoup(open(self.TEST_PATH, 'r', encoding='euc-jp'), 'html.parser')
        allImages = parsedSoup.find_all('img')
        htmlHead = parsedSoup.find('head')
        # first insert the script needed to activate lazy load
        # before inserting check the checksum to make sure that the file is not modified
        calculatedHash = self.md5Hash(os.path.join(self.ROOT_PATH, self.LAZY_LOAD_EDGE_PATH))
        if(calculatedHash == self.LAZY_LOAD_DIGEST):
            print("INFO: AUTH finished, will add lazyload script to HTML file")
            lazyloadScript = parsedSoup.new_tag("script", "src='{}'".format(self.LAZY_LOAD_PATH))
            orginalHead = str(htmlHead)
            htmlHead.append(lazyloadScript)
            parsedSoup = BeautifulSoup(str(parsedSoup).replace(orginalHead, str(htmlHead)), 'html.parser')
        for image in allImages:
            oringalImage = str(image)
            if(image.has_attr('class') and 'ear' in image['class']):
                print("INFO: This website has applied EAR")
            else:
                image['class'] = 'ear' # lazylize
                image['data-src'] = image['data-srcset'] = image['src'] # add data-src and data-srcset
                image['src'] = self.PLACEHOLDER_PATH  # replace the original img src with a tiny placeholder
                # print(image)
                parsedSoup = BeautifulSoup(str(parsedSoup).replace(oringalImage, str(image)), 'html.parser')
        # print(str(parsedSoup))
        with open(self.TEST_WRITE_PATH, 'w', encoding='utf-8') as f:
            f.write(str(parsedSoup))

if(__name__ == '__main__'):
    testReprioritizer = Reprioritizer()
    testReprioritizer.lazylizeImage()

