import urllib2
import urllib
import json

test_data = {"appId":1,"uId":"0076187238364db4819db4e1b60bf3bf","xlCode":"7fe6aa8a79eb230e43ba3508e3d0aa6f","xlOpenId":""}
# test_data = {"appid":"tlznj75neOFbxcet","appsecret":"wTrBAYuBHsuEDI76","code":"31337404d0e50bbcf66cad6c1537f52f","grant_type":"authorization_code"}
# test_data_urlencode = json.dumps(test_data)
test_data_urlencode = urllib.urlencode(test_data)
requrl = "http://192.168.1.3/php_huskar/public/wx_bind_xl"
# requrl = "https://ssgw.updrips.com/oauth2/accessToken"
# for i in range(500):
req = urllib2.Request(url=requrl, data=test_data_urlencode)

res_data = urllib2.urlopen(req)
res = res_data.read()
print res
