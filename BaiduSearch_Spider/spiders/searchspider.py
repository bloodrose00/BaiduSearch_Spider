# -*- coding: utf-8 -*-
import scrapy
from BaiduSearch_Spider.items import BaidusearchSpiderItem

from time import sleep
from BaiduSearch_Spider.body_path import *
import traceback

import csv
import os


class BaiduspiderSpider(scrapy.Spider):
    name = 'searchspider'
    count=0
    start_urls = ['http://baidu.com/']

    def __init__(self, keyword=None, search=None, *args, **kwargs):
        super(BaiduspiderSpider, self).__init__(*args, **kwargs)
        self.keyword = keyword
        self.search = search
        if self.keyword == None: # 如果没有指定关键词，那么从文件中读取
            self.ReadKeyword()

    def ReadKeyword(self): # 设置要包含要搜索关键词的csv文件
        #关键词csv文件的位置
        # filename = "高校学生自杀搜索关键词.csv"
        filename = "keywords.csv"
        path1 = os.path.dirname(__file__)# 获取当前文件所在文件夹
        path2 = os.path.dirname(path1) + '\\keyword\\'+filename# 获取当前文件所在文件夹的父文件夹
        #打开(创建)文件
        file = open(path2,'r',newline='',encoding='utf-8-sig') # 不带newline的话输出总会有一个空行 加入encoding='utf-8-sig'就不会乱码了
        #csv读取
        reader = csv.reader(file) # 建立csv文件句柄
        self.keywords=[]
        for row in reader:
            self.keywords.append(row)
        self.keywords=self.keywords[1:]# 去掉第一项    

    def start_requests(self):
        # keyword="双鸭山"
        if self.keyword == None or self.keyword == "":
            for line in self.keywords:
                line=(line[0]).split()
                keyword="|".join(line)
                begin_page = 0
                end_page = 76
                start_urls1 = "http://www.baidu.com/s?wd={}&pn={}&rn=10&ie=utf-8"
                for page in range(begin_page,end_page):# 一页链接数量由参数&rn=决定
                    U = start_urls1.format(keyword,page*10)
                    yield scrapy.Request(url = U,meta = {'keyword':" ".join(line)},callback = self.parse,dont_filter=True)
                sleep(1)  #设置一个时间间隔，太快了不好
        else:
            #begin_page = 0
            #end_page = 76
            start_urls1 = "http://www.baidu.com/s?wd={}&pn={}&rn=10&ie=utf-8"
            #for page in range(begin_page,end_page):# 一页链接数量由参数&rn=决定
            U = start_urls1.format(self.keyword,0)  
            sleep(0.5)  #设置一个翻页的时间，太快了不好
            yield scrapy.Request(url = U,meta = {'keyword':self.keyword.replace("|"," ")},callback = self.parse,dont_filter=True)



    def parse(self,response):
        #处理百度verify重定向问题  百度会限制单ip的爬取速率，所以遇到重定向到verify就延时一段时间再重新请求
        if response.status in [301,302] and "verify" in response.url:
            sleep(1) # 延时一段时间再重新请求
            yield scrapy.Request(url = response.request.url,meta = {'keyword':response.meta['keyword']},callback = self.parse,dont_filter=True)

        list1 = response.xpath('//div[@class="result-op c-container xpath-log"]')
        list2 = response.xpath('//div[@class="result c-container "]')
        #print(list1)
        #print(list2)


        for section in list2:
            item = BaidusearchSpiderItem()
            item['keyword']=response.meta['keyword'] # 标注关键词
            item['number']=self.count
            self.count+=1
            try:
                info = section.xpath('.//a')[0]
                item['link'] = info.xpath('@href').extract()[0]
            except:
                #traceback.print_exc()
                item['link']=""

            try:
                res_title=section.xpath('.//h3/a')
                item['title']=(res_title[0].xpath('string(.)').extract_first()).strip('\n\t \'')
            except:
                #traceback.print_exc()
                item['title']=""
 
            try:
                b=section.xpath('.//div[@class="c-abstract" ]')
                if len(b)==0:
                    b=section.xpath('.//div[@class="c-summary c-row c-gap-top-small"]')
                S=b.xpath('string(.)').extract()[0]
                S=S.replace("\n"," ").replace("\t"," ").replace("\xa0"," ") # 用空格隔开方便下一步进行split
                List = S.split()
                List.pop() #去除百度快照
                if (List[0][0]).isdigit(): # 判断第一个是不是时间
                    item['time'] = List[0]
                    item['brief'] = ("".join(List[1:])).lstrip("= -")
                else:
                    item['time'] = ""
                    item['brief'] = ("".join(List[:])).lstrip("= -")
            except:
                #traceback.print_exc()
                item['time']=""
                item['brief']=""
            yield item
            # yield scrapy.Request(url = item['link'],meta = {'item':item},callback = self.parse_next,dont_filter=True)

        for section in list1:
            
            item = BaidusearchSpiderItem()
            item['number']=self.count
            self.count+=1
            item['keyword']=response.meta['keyword'] # 标注关键词
            try:
                info = section.xpath('.//h3/a')[0]
                item['link'] = info.xpath('@href').extract()[0]
            except:
                #traceback.print_exc()
                item['link']=""

            try:
                res_title=section.xpath('.//h3/a')
                item['title']=(res_title[0].xpath('string(.)').extract_first()).strip('\n\t \'')
            except:
                #traceback.print_exc()
                item['title']=""
            try:
                b=section.xpath('.//div[@class="c-row"]')
                S=b.xpath('string(.)').extract()[0]
                S=S.replace("\n"," ").replace("\t"," ").replace("\xa0"," ") # 用空格隔开方便下一步进行split
                List = S.split()
                List.pop() #去除更多
                item['time']="" # 这种讯息一般没有时间
                item['brief'] = ("".join(List[:])).lstrip("= ")
            except:
                #traceback.print_exc()
                item['time']=""
                item['brief']=""
            yield item

                # 解析出下一页的url继续请求
        #print("\n\n\n")
        #print(response.body)
        #print("\n\n\n")
        next_pageURL = response.xpath('//div[@id="page"]/a[@class="n"]')
        #print(next_pageURL)
        # 因为 上一页和下一页的标签都是class=n 如果页面只有一个 class=n 出现要单独讨论，否则可能死循环
        if len(next_pageURL)==0 or(len(next_pageURL)==1 and "上一页" in next_pageURL[0].xpath('./text()').extract()[0]):
            #print(next_pageURL[0].xpath('./text()').extract()[0])
            pass
        else:
            next_pageURL = next_pageURL[-1].xpath('@href').extract()[0]
            # sleep(0.02) # 放慢翻页请求速度，否则可能爬下来一个空的html
            #print("\n\n\n翻页中     http://www.baidu.com"+next_pageURL+"\n\n\n")
            yield scrapy.Request(url = "http://www.baidu.com"+next_pageURL,meta = {'keyword':response.meta['keyword']},callback = self.parse,dont_filter=True)
