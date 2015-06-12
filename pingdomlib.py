#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, httplib, pprint, base64, datetime, time

from logni import log

try:
        import json
        log.ni( 'use python module json', DBG=1 )

except ImportError:
        import simplejson as json
        log.ni( 'use python module simplejson as json', DBG=1 )



class Pingdom:

        def __init__(self, apiKey, username, userPasswd, version='2.0'):
                """
                 * Inicializace objektu pro praci se Site24x7 API
                 *
                 * @param apiKey     	autorizacni retezec
		 * @param version	verze Pingdom API
		 * @param username	uzivatelske jmeno pro prihlaseni do administrace Pingdomu
		 * @param userPasswd	heslo pro prihlaseni
                """

                self.__apiKey        	= apiKey
                self.__apiDomain        = 'api.pingdom.com'
                self.__apiPath          = '/api/%s' % version
		self.__username		= username
		self.__userPasswd	= userPasswd



        def request( self, url='/checks', paramList={}, method='GET' ):
                """
                 * Autorizovany request na pozadovana data
                 *
                 * @param url           URL pro data
                 * @param paramList     parametry requestu
                 * @param method        POST/GET/PUT, POST pro setovani, GET pro ziskani dat, PUT pro aktualizaci dat
                 * @return              slovnik s navratovym stavem + daty
                """

                ret = {
                        'statusCode'    : 200,
                        'statusMessage' : 'OK'
                }

                parList = urllib.urlencode(paramList)

		base64str = base64.encodestring( '%s:%s' % (self.__username, self.__userPasswd) ).replace('\n', '')

                header = {
			"App-Key"	: self.__apiKey,
			"Authorization"	: "Basic %s" % base64str
		}
                
                conUrl = "%s%s" % (self.__apiPath, url)

                log.ni("Pingdom - url: %s, param: %s, header: %s", (conUrl, parList, header), INFO=3)

                connection = httplib.HTTPSConnection(self.__apiDomain)

                connection.request(method, conUrl, parList, header)

                response = connection.getresponse()

                status  = response.status
                data    = response.read()

                if status == 200:

                        data = json.loads(data)

                        log.ni("Site24x7 - response - status: %s, data: %s", (status, data), INFO=3)

                      	ret['data'] = data

              	elif data:
			data = json.loads(data)
			data = data['error']

			log.ni("Pingdom - response - code: %s, desc: %s, message: %s", ( data['statuscode'], data['statusdesc'], data['errormessage'] ), ERR=4)

			ret['statusCode']       = data['statuscode']
			ret['statusMessage']    = "%s - %s" % ( data['statusdesc'], data['errormessage'] )

                else:
                        log.ni("Pingdom - response - status: %s, data: %s", (status, data), ERR=4)

                        ret['statusCode']       = status
                        ret['statusMessage']    = data

                return ret



	def sourceList(self):
                """
                 * Vrati seznam merenych zdroju se zakladnim infem
                 *
                 * @return              slovnik s navratovym stavem + daty
                """

		ret = self.request('/checks')

                if ret['statusCode'] != 200:
                        return ret

                data = []

		# prevodnik pro nektere typy zdroju
                # vsechny typy: https://www.pingdom.com/resources/api
                sourceType = {
                        'http'       	: 'http',
                        'tcp'   	: 'socket',
                        'ping'          : 'ping'
                }

		for check in ret['data'].get( 'checks', [] ):
                        data.append({
                                'name'          	: check['name'],
                                'id'            	: int( check['id'] ),
                                'url'           	: check.get('hostname', ''),
                                'sourceType'    	: sourceType.get(check['type'], ''),
				'lastChecktime'		: int( check.get('lasttesttime', 0) ),
				'lastErrChecktime'	: int( check.get('lasterrortime', 0) )
                        })

		ret['data'] = data

                return ret



	def sourceOutputInfo(self, date, checkId):
                """
                 * Namerene hodnoty pro predany zdroj
                 *
                 * @param date          datum monitorovani, ISO format
                 * @param checkId     	ID zdroje
                 * @return              slovnik s navratovym stavem + daty
                """

		dateEnd 	= datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=1)
		dateEndTs 	= int( time.mktime( dateEnd.timetuple() ) )

                data = {
                        'sender': [],		# info o odeslanych zpravach upozornujicich na vypadky API neposkytuje
                        'output': []
                }

		# pocitam s max. merenim 2x/min, pokud nejsou vracena data prosli jsme vsechna mereni zadaneho dne, max. limit je 1000 vysledku na request
		for offset in range(0, 43000, 1000):

			# parametry nepredavame pres argument fce request, protoze se jedna o parametry GETu
			# je-li nastaven parametr 'to' berou se defaultne vysledky za jeden den do datumu 'to'
			parList = {
				'to'	: dateEndTs,
				'limit'	: 1000,
				'offset': offset
			}
			ret = self.request( '/results/%s?%s' % ( checkId, urllib.urlencode(parList) ) )

			if ret['statusCode'] != 200:
				return ret

			#pprint.pprint( ret['data'] )

			if not ret['data'].get( 'results', [] ):
				break

			for result in ret['data']['results']:
				data['output'].append({
					'checktime'     : result['time'],
					'responseTime'  : result['responsetime'] / 1000.0,
					'statusMessage' : result['statusdesclong'],
					'statusCode'    : 200 if result['statusdesc'] == 'OK' else 500	# v dokumentaci jsem nedohledal soupis vsech statusu
				})

		ret['data'] = data

                return ret




if __name__ == '__main__':

        log.mask( 'ALL' )
        log.stderr( 1 )

        pingdom = Pingdom('v06fr8n6865rtymmvm7sk42gxcxzx727', 'info@siux.cz', 'helenka99')

        #pprint.pprint( pingdom.request('/checks') )
        #pprint.pprint( pingdom.sourceList() )
        pprint.pprint( pingdom.sourceOutputInfo('2015-05-31', 1464995) )
