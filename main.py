import threading
import time
import bs4
import requests
import StellarPlayer
import re
import urllib.parse

zmtt_url = 'https://www.zimutiantang.com'


def concatUrl(url1, url2):
    splits = re.split(r'/+',url1)
    url = splits[0] + '//'
    if url2.startswith('/'):
        url = url + splits[1] + url2
    else:
        url = url + '/'.join(splits[1:-1]) + '/' + url2
    return url


def get_zmtt_sub_info(page_url):
    res = requests.get(page_url,verify=False)
    if res.status_code == 200:
        bs = bs4.BeautifulSoup(res.content.decode('utf-8','ignore'),'html.parser')
        downselector = bs.select('#down > a')[0]
        downurl = downselector.get('href')
        return downurl
    return ''

def parse_zmtt_page_subs(page_url):
    urls = []
    currentpage = ''
    res = requests.get(page_url,verify=False)
    if res.status_code == 200:
        bs = bs4.BeautifulSoup(res.content.decode('utf-8','ignore'),'html.parser')
        selector = bs.select('body > section > div > div > div > div > table:nth-child(2) > tbody')
        activepage =  bs.select('body > section > div > div > div > div > div > ul > li.active > span')[0].string
        currentpage = activepage
        print(activepage)
        for item in selector[0].select('.search'):
            subtype = item.select('td.nobr.center')[3]
            subtime = item.select('td.nobr.center.lasttd')[0]
            sublan = item.select('td.nobr.center')[1]
            subdownurl = item.select('td.w75pc a')[0].get('href')
            subfilename = item.select('td.w75pc a')[0].getText()
            urls.append({'title':subfilename,'language':sublan.string,'type':subtype.string,'time':subtime.string,'downurl':subdownurl})
    #print(urls)
    return urls,currentpage



class zmttplugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)  
        self.zms = []
        self.pageIndex = 0
        self.cur_page = ''
    
    def show(self):
        controls = self.makeLayout()
        self.doModal('main',800,600,'',controls)
    
    def makeLayout(self):
        list_layout = {'group':[{'type':'label','name':'title','width':0.6},
            {'type':'label','name':'language','width':0.1},
            {'type':'label','name':'type','width':0.1},
            {'type':'label','name':'time','width':0.1},
            {'type':'link','name':'下载','width':30,'@click':'onDownClick'},{'type':'space'}]}
        controls = [
            {'type':'space','height':10},
            {'group':
                [
                    {'type':'edit','name':'search_edit','label':'搜索','width':0.4},
                    {'type':'button','name':'搜字幕','@click':'onSearch'},
                    {'group':
                        [
                            {'type':'radio','name':'标题','value':False},
                            {'type':'radio','name':'全文','value':True},
                            {'type':'check','name':'模糊搜索','value':True},
                            {'type':'radio','name':'相关性','value':True},
                            {'type':'radio','name':'最新','value':False},
                            {'type':'radio','name':'最老','value':False}
                        ],
                        'width':0.5
                    }
                ]
                ,'height':30
            },
            {'group':[{'type':'label','name':'片名','width':0.59},
                {'type':'label','name':'语言','width':0.1},
                {'type':'label','name':'类型','width':0.1},
                {'type':'label','name':'上传时间','width':0.1},
                {'type':'space','width':30},
                ]
                ,'height':30
            },
            {'type':'list','name':'list','itemlayout':list_layout,'value':self.zms,'separator':True,'itemheight':40},
            {'group':
                [
                    {'type':'space'},
                    {'group':
                        [
                            {'type':'label','name':'cur_page',':value':'cur_page'},
                            {'type':'link','name':'首页','@click':'onClickFirstPage'},
                            {'type':'link','name':'上一页','@click':'onClickFormerPage'},
                            {'type':'link','name':'下一页','@click':'onClickNextPage'},
                        ]
                        ,'width':0.45
                    },
                    {'type':'space'}
                ]
                ,'height':30
            },
            {'type':'space','height':5}
        ]
        return controls
        
    
    def getSearchType(self):
        hasetitle = self.player.getControlValue('main','标题')
        haseall = self.player.getControlValue('main','全文')
        hasem = self.player.getControlValue('main','模糊搜索')
        haserelevance = self.player.getControlValue('main','相关性')
        hasenew = self.player.getControlValue('main','最新')
        haseold = self.player.getControlValue('main','最老')
        res = ''
        if hasetitle:
            res = '&f=title'
        elif haseall:
            res = '&f=_all'
        if hasem:
            res = res + '&m=yes'
        if haserelevance:
            res = res + '&s=relevance'
        elif hasenew:
            res = res + '&s=newstime_DESC'
        elif haseold:
            res = res + '&s=newstime_ASC'
        return res
    
    def onSearch(self, *args):
        self.cur_page = ''
        self.loading()
        self.zms.clear()
        self.player.updateControlValue('main','list',self.zms)
        self.search_word = self.player.getControlValue('main','search_edit')
        searchurl = zmtt_url + '/search/?q=' + urllib.parse.quote(self.search_word,encoding='utf-8') + self.getSearchType()
        print(f'url={searchurl}')
        self.zms,activepage  = parse_zmtt_page_subs(searchurl)
        self.pageIndex = int(activepage)
        self.cur_page = '第' + activepage + '页'
        self.player.updateControlValue('main','list',self.zms)
        self.loading(True)
      
    def onDownClick(self, page, control, idx, *arg):     
        downurl = self.zms[idx]['downurl']
        subdownurl = get_zmtt_sub_info(concatUrl(zmtt_url, downurl))
        self.player.callWebbrowser(subdownurl)
        
    def selectPage(self):
        self.cur_page = ''
        self.zms.clear()
        self.player.updateControlValue('main','list',self.zms)
        searchurl = zmtt_url + '/search/?q=' + urllib.parse.quote(self.search_word,encoding='utf-8') + self.getSearchType() + '&p=' +str(self.pageIndex) 
        print(f'url={searchurl}')
        self.zms,activepage = parse_zmtt_page_subs(searchurl)
        self.pageIndex = int(activepage)
        self.cur_page = '第' + activepage + '页'
        self.player.updateControlValue('main','list',self.zms)
                
    def onClickFormerPage(self, *args):
        self.search_word = self.player.getControlValue('main','search_edit')
        if self.pageIndex > 0 and len(self.search_word) > 0:
            self.pageIndex = self.pageIndex - 1
            self.loading()
            self.selectPage()
            self.loading(True)    
    
    def onClickNextPage(self, *args):
        self.search_word = self.player.getControlValue('main','search_edit')
        if len(self.search_word) > 0:
            self.pageIndex = self.pageIndex + 1
            self.loading()
            self.selectPage()
            self.loading(True)  

    def onClickFirstPage(self, *args):
        self.search_word = self.player.getControlValue('main','search_edit')
        if len(self.search_word) > 0:
            self.pageIndex = 0
            self.loading()
            self.selectPage()
            self.loading(True)    
            
    def loading(self, stopLoading = False):
        if hasattr(self.player,'loadingAnimation'):
            self.player.loadingAnimation('main', stop=stopLoading)
        
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = zmttplugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()