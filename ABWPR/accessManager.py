# coding: utf-8
# Manage access count of the ESM
from pymongo import MongoClient
from db import config
from collections import Counter
from urlparse import urlparse
from datetime import datetime
import time
class DBInteract:

    def __init__(self):
        self.client = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
        self.DB_NAME = 'YPTN-Client'
        self.USER_HISTORY_COLLECTION = 'access-sites'
        self.ACCESS_COUNT_COLLECTION = 'access-counts'
        self.ACCESS_COUNT_BY_DOMAIN_COLLETCION = 'access-counts-domain'
        self.RUC_VALUE_DB = 'RUC-value'
        self.TEMP_STORAGE_DB = 'TEMP-storage'
        self.RUC_DB = 'RUC'
        self.AGING_PARAMETER = 0.85
        self.AGING = 86400 * 30

    def updateAccessCount(self):
        userHistoryCollection = self.client[self.DB_NAME][self.USER_HISTORY_COLLECTION]
        historyRecords = userHistoryCollection.find({})
        accessedUrls = []
        for record in historyRecords:
            accessedUrls.append(record['url'])
        accessCounter = Counter(accessedUrls)

        # try finding the record, if not exist, insert, if exist, update.
        accessCountCollection = self.client[self.DB_NAME][self.ACCESS_COUNT_COLLECTION]
        for url, counts in accessCounter.items():
            recordsFound = accessCountCollection.find({'url': url})
            if(len(list(recordsFound))):
                accessCountCollection.update_one(
                    {'url': url},
                    {"$set": {"counts": counts}}
                )
            else:
                accessCountCollection.insert_one(
                    {'url': url,
                     'counts': counts}
                )

    def updateAccessCountByDomain(self):
        userHistoryCollection = self.client[self.DB_NAME][self.USER_HISTORY_COLLECTION]
        historyRecords = userHistoryCollection.find({})
        accessedUrls = []
        for record in historyRecords:
            accessedDomain = urlparse(record['url']).netloc
            accessedUrls.append(accessedDomain)
        accessCounter = Counter(accessedUrls)
        accessCountByDomainCollection = self.client[self.DB_NAME][self.ACCESS_COUNT_BY_DOMAIN_COLLETCION]
        for url, counts in accessCounter.items():
            recordsFound = accessCountByDomainCollection.find({'url': url})
            if(len(list(recordsFound))):
                accessCountByDomainCollection.update_one(
                    {'url': url},
                    {"$set": {"counts": counts}}
                )
            else:
                accessCountByDomainCollection.insert_one(
                    {'url': url,
                     'counts': counts}
                )

    def getAccessCountByURL(self, url):
        accessCountCollection = self.client[self.DB_NAME][self.ACCESS_COUNT_COLLECTION]

    def getAccessCountByDomainAndTime(self, url):
        pass

    def initRUC(self):
        # store access info for init
        userHistoryCollection = self.client[self.DB_NAME][self.USER_HISTORY_COLLECTION]
        tempStore = self.client[self.TEMP_STORAGE_DB]
        accessCountCollection = self.client[self.DB_NAME][self.ACCESS_COUNT_COLLECTION]
        RUC = self.client[self.RUC_DB]
        allRecords = userHistoryCollection.find({})
        for record in allRecords:
            parsedURL = urlparse(record['url'])
            if((tempStore[parsedURL.netloc].find_one({"_id":record["_id"]})) is None):
                tempStore[parsedURL.netloc].insert_one(record)
        allDomains = tempStore.collection_names()
        for domain in allDomains:
            singleDomainAccessCollection = tempStore[domain]
            allAccessRecords = list(singleDomainAccessCollection.find({}))
            allAccessRecords = sorted(allAccessRecords, key=lambda k:k["timeStamp"])
            previousAccessDate = ""
            accessCount = 0
            for index in range(len(allAccessRecords)):
                record = allAccessRecords[index]
                accessDate = datetime.fromtimestamp(record['timeStamp']/1000)
                accessYear = accessDate.year
                accessMonth = accessDate.month
                accessDay = accessDate.day
                accessDate = str(accessYear) + "-" + str(accessMonth) + "-" + str(accessDay)
                if(previousAccessDate == ""):
                    accessCount = 1
                    previousAccessDate = accessDate
                elif(previousAccessDate != accessDate):
                    accessTimestamp = time.mktime(datetime.strptime(accessDate, "%Y-%m-%d").timetuple())
                    RUCCollection = RUC[domain]
                    if(RUCCollection.find_one({"timstamp": accessTimestamp, "url": record['url']}) is None):
                        RUCCollection.insert_one(
                            {
                                "url": record["url"],
                                "timestamp": accessTimestamp,
                                "accessDate": accessDate,
                                "accessCount": accessCount
                            }
                        )
                    accessCount = 1
                    previousAccessDate = accessDate
                else:
                    accessCount += 1

    def refreshRUC(self):
        pass


if __name__ == '__main__':
    test = DBInteract()
    # test.updateAccessCount()
    # test.updateAccessCountByDomain()
    test.initRUC()