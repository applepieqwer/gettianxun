#!/usr/bin/python
# -*- coding: UTF-8 -*-
import urllib2
import cookielib
import json
import time
from codecs import BOM_UTF8
import logging
import argparse
import datetime

#新加坡
#1 http://www.tianxun.com/intl-oneway-csha-sins.html?depdate=2015-11-02&cabin=Economy&adult=1&child=0&infant=0&direct=1
#2 var PARAMS = {"dep_flight_city_code":"CSHA","dst_flight_city_code":"SIN","depart_date":"2015-11-02","return_date":"","cabin_type":"Economy","adults":1,"children":0,"infants":0,"token":"V1QCBFoKXARJBlAFBAcHAVFRBFVRVwABAAFQA1dTDwIHA1FXA1AEBgc=","cache_key":"92a6e43a-4f34-4a91-95de-ab74301b7fd7","depCity":"\u4e0a\u6d77","depCityId":"7","dstCity":"\u65b0\u52a0\u5761","dstCityId":"3832","cabin_type_name":"\u7ecf\u6d4e\u8231","depCityCode4":"CSHA","dstCityCode4":"SIN"};
#http://www.tianxun.com/flight/ajax_intl_list.php?page=1&sort=price&order=asc&dep_flight_city_code=CSHA&dst_flight_city_code=SIN&depart_date=2015-11-02&return_date=&cabin_type=Economy&adults=1&children=0&infants=0&token=V1QCBFoKXARJBlAFBAcHAVFRBFVRVwABAAFQA1dTDwIHA1FXA1AEBgc%3D&cache_key=92a6e43a-4f34-4a91-95de-ab74301b7fd7&depCity=%E4%B8%8A%E6%B5%B7&depCityId=7&dstCity=%E6%96%B0%E5%8A%A0%E5%9D%A1&dstCityId=3832&cabin_type_name=%E7%BB%8F%E6%B5%8E%E8%88%B1&depCityCode4=CSHA&dstCityCode4=SIN&status=UpdatesPending&totken=V1QCBFoKXARJBlAFBAcHAVFRBFVRVwABAAFQA1dTDwIHA1FXA1AEBgc%3D&filter_stops=0&_=1445600593504

def lstrip_bom(str_, bom=BOM_UTF8):
	if str_.startswith(bom):
		return str_[len(bom):]
	else:
		return str_

def mk_intl_link(Org, Dst, OrgDate):
	return str('http://www.tianxun.com/intl-oneway-%s-%s.html?depdate=%s&cabin=Economy&adult=1&child=0&infant=0&direct=1'%(Org,Dst,OrgDate))
	
def download_intl_page(Org, Dst, OrgDate):
	f = urllib2.urlopen(mk_intl_link(Org,Dst,OrgDate))
	return f.read()

def find_params(html):
	logger = logging.getLogger('root')  
	logger.warning(html)
	for one_line in html.splitlines():
		if one_line.find('var PARAMS = {') != -1:
			return one_line[one_line.find('{')+1:one_line.find('}')]
	return False

def mk_params_2_ajax(params):
	ajax = 'http://www.tianxun.com/flight/ajax_intl_list.php?page=1&sort=price&order=asc&filter_stops=0'
	for p1 in params.split(','):
		v = p1.split(':')
		ajax = ajax + '&%s=%s'%(v[0].replace('"','').strip(),v[1].replace('"','').strip())
	logger = logging.getLogger('root')  
	logger.warning(ajax)
	return ajax

def download_ajax(ajax):
	f = urllib2.urlopen(ajax)
	return f.read()

def download_ajax_loop(ajax):
	status = 'UpdatesPending'
	count = 0
	while status != 'UpdatesComplete' and count < 100:
		count = count + 1
		ajax_page = download_ajax(ajax)
		if len(ajax_page) < 10:
			print 'empty ajax result. sleeping 5 secs.'
			time.sleep(5)
			continue
		logger = logging.getLogger('root')  
		logger.warning(ajax_page)
		try:
			ajax_v = json.loads(lstrip_bom(ajax_page))
		except ValueError:
			print ajax_page
			print 'Json Error'
			return False
		status = ajax_v['status']
		print '%d: Status = %s'%(count,status)
		if status == 'UpdatesComplete':
			continue
		else:
			print 'sleeping 5 secs'
			time.sleep(5)
	return ajax_v

def ajax_v_2_text(ajax_v):
	f = u'航空公司,航班号,起飞机场,起飞时间,落地机场,落地日期,落地时间,飞行时间,跨天,经停,票价,税,票务'
	for flight in ajax_v['flights']:
		flightinfo = flight['flightInfoList'][0]
		priceinfo = flight['flightPriceList'][0]
		info = flightinfo.copy()
		info.update(priceinfo)
		f = f + '\n%(flightAirlineIdsOper)s,%(flightNumber)s,%(depAirportId)s,%(depDatetime)s,%(dstAirportId)s,%(arrivalDate)s,%(arrivalDatetime)s,%(duration)s,%(nextDay)s,%(stopNum)s,%(price)s,%(tax)s,%(supplierName)s'%info
	return f

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Download info from tianxun.com')
	parser.add_argument('org',help='出发城市',type=str)
	parser.add_argument('dst',help='到达城市',type=str)
	parser.add_argument('org_date',help='出发日期（yyyy-mm-dd）',type=str)
	parser.add_argument('--output',help='保存结果信息',type=str,default='%s-%s-%s-%s-result.csv')
	parser.add_argument('--debug_file',help='保存调试信息',type=str,default='%s-debug.txt')
	args = parser.parse_args()
	
	str_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	result_filename = args.output%(str_now,args.org,args.dst,args.org_date)
	
	logger = logging.getLogger('root')  
	file_handler = logging.FileHandler(args.debug_file%str_now) 
	formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',) 
	file_handler.setFormatter(formatter)  
	logger.addHandler(file_handler)  
	
	#build cookie
	cookies = cookielib.MozillaCookieJar('cookies.txt')
	try:
		cookies.load()
	except:
		pass
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))
	urllib2.install_opener(opener)
	
	loop = True
	while loop:
		try:
			html_page = download_intl_page(args.org, args.dst, args.org_date)
			params = find_params(html_page)
			if params != False:
				ajax = mk_params_2_ajax(params)
				ajax_v = download_ajax_loop(ajax)
				if ajax_v != False:
					ajax_str = ajax_v_2_text(ajax_v)
					if ajax_str != False:
						ajax_str = ajax_str + '\ndownload datetime:%s'%str_now
						f = open(result_filename,'w')
						f.write(ajax_str.encode('utf8'))
						f.close()
						loop = False
						continue
		except urllib2.HTTPError as e:
			print 'HTTPError Maybe Captcha'
			print e.geturl()
			exit()
		print 'sleeping 10 secs'
		time.sleep(10)
	cookies.save(ignore_discard=True,ignore_expires=True)
