from IPython.core.display import json
import scrapy
import requests
from bs4 import BeautifulSoup

class OverviewSpider(scrapy.Spider):
    name = "overview"
    allowed_domains = ["allaboutbirds.org", "cdn.download.ams.birds.cornell.edu"]
    start_urls = ["https://www.allaboutbirds.org/guide/Barred_Owl/overview"]
    descriptionSel = '#show-share > section.main-column.overview.clearfix > \
    div:nth-child(1) > div > div:nth-child(2) > p'
    backyardSel = '#show-share > section.main-column.overview.clearfix > \
    div:nth-child(3) > div > p'
    idThisSel = '#show-share > section.main-column.overview.clearfix >\
     div.narrow-content > div:nth-child(2) > p'
    coolFactsSel = '.accordion-content > ul > li'
    nameSel = '#show-share > header > h1'
    urlSel = '#show-share > header > nav > ul > li'
    lifeSel = '#show-share > header > nav > ul > li:nth-child(3) > a::attr(href)'
    mapSel = '#show-share > header > nav > ul > li:nth-child(4) > a::attr(href)'
    soundListSel = '.jp-jplayer.player-audio'
    baseUrl = 'https://www.allaboutbirds.org'


    def start_requests1(self):
      apiUrl = 'https://vl3oj3lqpf.execute-api.us-east-1.amazonaws.com/live/api/getAutocomplete/'
      
      urls = [
        self.baseUrl+'/guide/'+y['mod_name'].replace("'", '').replace(' ','_')
        for x in 'a'
        for y in requests.get(apiUrl + x).json()
      ]
        # for x in 'abcdefghijklmnopqrstuvwxyz'
      for url in urls:
          yield scrapy.Request(url=url, callback=self.parse)

    def getText(self, response, selector=None):
      elem = response
      if selector:
        elem = response.css(selector)
      ret = ''
      if elem:
        if hasattr(elem, '__iter__'):
          for subElem in elem:
            ret += BeautifulSoup(subElem.get(), 'html.parser').get_text().strip()
        else:
            ret = BeautifulSoup(elem.get(), 'html.parser').get_text().strip()

      return ret
    
    def getAttr(self, response, sel):
      elem = response.css(sel)
      if sel:
        return elem.get()
      return ''
    
    def getMaculayUrl(self, url):
      splits = url.split('/')
      if len(splits)<2:
        return 'https://example.com/'
      _id = splits[-1]
      _type = splits[-2]
      baseUrl = "https://cdn.download.ams.birds.cornell.edu/api/v2/asset/"
      
      if _type == "video":
        return baseUrl + _id + '/mp4/1280'
      else:
        return baseUrl + _id + '/1200'

    def migrationImgUrl(self, url):
      bestUrl = url.split(',')[-2]
      return bestUrl[bestUrl.index('[')+1:]

    def parse(self, response):
      overview = {
        'description': self.getText(response, self.descriptionSel),
        'backyard': self.getText(response, self.backyardSel),
        'idthis': self.getText(response, self.idThisSel),
        'coolfacts': [self.getText(x) for x in response.css(self.coolFactsSel)],
        'name': [self.getText(response ,self.nameSel)]
      }
      urls = [self.getAttr(x, 'a::attr(href)') for x in response.css(self.urlSel)]

      sound = urls[4]
      if sound is not None:
        yield response.follow(self.baseUrl+sound, 
        callback=self.parseSound, meta={"data": overview, 
          "urls": urls})
      else:
        yield overview

    def parseSound(self, response):
      data = response.meta['data']
      urls = response.meta['urls']
      life = urls[2]
      soundList = response.css(self.soundListSel)
      data["sound"]=[self.getAttr(x, '::attr(name)') for x in soundList]
      
      if life is not None:
        yield response.follow(self.baseUrl+life, 
        callback=self.parseLife, meta={"data": data, "urls":urls})
      else:
        yield data
      
    def parseLife(self, response):
      data = response.meta['data']
      urls = response.meta['urls']
      maps = urls[3]
      sections = response.css('section:not([class])')
      for x in sections:
        data[self.getAttr(x, 'h2::text')] = self.getText(x, 'p')
      
      if maps is not None:
        yield response.follow(self.baseUrl+maps, 
        callback=self.parseMap, meta={"data": data, "urls":urls})
      else:
        yield data

    def parseMap(self, response):
      data = response.meta['data']
      urls = response.meta["urls"]
      idInfo = urls[1]
      data['migration'] = self.getText(response, "#show-share > section > aside > div:nth-child(1) > p")
      data['migration-img'] = self.migrationImgUrl(
        self.getAttr(response, ".main-area>img::attr('data-interchange')"))
      if idInfo is not None:
        yield response.follow(self.baseUrl+idInfo, 
        callback=self.parseIdInfo, meta={"data": data})
      else:
        yield data
    
    def parseIdInfo(self, response):
      data = response.meta['data']
      data['img'] = [{'url':
        self.getMaculayUrl(self.getAttr(x, "div>div>a::attr('href')")), 
      'caption':self.getText(x, "a > div.annotation-txt> p")} for x in response.css('.slider.slick-3> div')]
      yield data
      
        
