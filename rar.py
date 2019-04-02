#!/usr/bin/python
import yaml,json,urllib,pocket,random,sys
from pocket import Pocket
from wsgiref.simple_server import make_server
from tg import MinimalApplicationConfigurator,FullStackApplicationConfigurator,expose,TGController,session,request
from tg.configurator.components.session import SessionConfigurationComponent

if len(sys.argv)==3:
	_master_rt=sys.argv[1]
	_master_at=sys.argv[2]
	_master_tokens=True
else:
	_master_tokens=False

def getSessionItemOrEmpty(name):
	if _master_tokens and name=='request_token':
		return _master_rt
	if _master_tokens and name=='access_token':
		return _master_at

	try:
		x=session[name]
	except:
		x=""
	return x

class RootController(TGController):
	@expose(content_type='text/html')
	def index(self):
		rt=getSessionItemOrEmpty('request_token')
		at=getSessionItemOrEmpty('access_token')

		html='<title>Pocket.RAR</title><style>body{background: #222;color: #eee}a{color:yellow;padding:2px;}a:hover{background:yellow;color:#222}</style><body>'

		html+='<pre>'
		if rt=='':
			html+='<span style="color:red"><strike>request_token</strike></span>'
		else:
			html+='<span style="color:green">request_token='+rt+'</span>'
		html+=' '
		if at=='':
			html+='<span style="color:red"><strike>access_token</strike></span>'
		else:
			html+='<span style="color:green">access_token='+at+'</span>'
		html+='</pre>'

		html+='<h1>Pocket.RAR</h1>'
		html+='<li><a href=/random style="font-size:72px">get random article</a></li>'
		html+='<li><a href=/tags>manage tags</a></li>'
		html+='<li><a href=/login>auth to Pocket</a></li>'
		html+='<li><a href=/logout>delete tokens from browser</a></li>'
		html+='<br />'
		html+='<li><a href=https://github.com/danielskowronski/pocket.rar>github</a></li>'

		html+='</body>'

		return html
	
	@expose(content_type='text/html')
	def random(self):
		at=getSessionItemOrEmpty('access_token')
		if at=="":
			return '<script>window.location.replace("/login")</script>'

		try:
			tags=json.loads(urllib.unquote(request.cookies.get('tags')))
		except:
			tags='_untagged_'
		try:
			pocket_instance = pocket.Pocket(rar_config['consumer_key'], at)
			resp=pocket_instance.get(state='unread',tag=tags)
		except Exception,e:
			return '<h1 style="color: red">'+str(e)
		articles=resp[0]['list']
		cnt=len(articles)
		trgt=random.randint(0, cnt)

		return '<script>window.location.href="https://getpocket.com/a/read/'+articles[articles.keys()[trgt]]['item_id']+'"</script>'

	@expose(content_type='text/html')
	def tags(self,*args):
		at=getSessionItemOrEmpty('access_token')
		if at=="":
			return '<script>window.location.replace("/login")</script>'

		try:
			pocket_instance = pocket.Pocket(rar_config['consumer_key'], at)
			resp=pocket_instance.get(state='unread',detailType='complete')
		except Exception,e:
			return '<h1 style="color: red">'+str(e)
		articles=resp[0]['list']
		ai=articles.iteritems()

		tags=set()
		for k,a in ai:
			try:
				for t in a['tags'].items():
					tags.add(t[0])
			except:
				pass
		html='<body><h1>tags manager</h1>green ones are included, by default untagged ones are selected<style>li{font-size: large}</style> \n'
		html+='<script src=https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js></script> \n'
		html+='<script src=https://cdnjs.cloudflare.com/ajax/libs/jquery-cookie/1.4.1/jquery.cookie.js></script> \n'
		html+='<script>var tags;$(function() { readCookie() }); function readCookie(){ \n'
		html+='  if (!$.cookie("tags")) $.cookie("tags", "[]") \n'
		html+='  tags=JSON.parse($.cookie("tags")) \n'
		html+='  $("li").each(function(){ \n'
		html+='    t=$(this).html().split(" <")[0]; \n'
		html+='    if (tags.includes(t)) $(this).css("color","green"); else $(this).css("color","red"); \n'
		html+='  }) \n'
		html+='} \n'
		html+='function arrayRemove(arr, value) {return arr.filter(function(ele){return ele != value;});} \n'
		html+='function toggle(tag){ \n'
		html+='  if (!tags.includes(tag)) tags.push(tag); else tags=arrayRemove(tags,tag); \n'
		html+='  $.cookie("tags", JSON.stringify(tags)); readCookie(); \n'
		html+='}</script> \n'
		for t in tags:
			html+='<li>'+t+' <button onClick="toggle(\''+t+'\')">toggle</button></li> \n'
		html+='<i><li>_untagged_ <button onClick="toggle(\'_untagged_\')">toggle</button></li></i> \n'

		return html

	@expose(content_type='text/html')
	def callback(self,*args):
		try:
			user_credentials = Pocket.get_credentials(consumer_key=rar_config['consumer_key'], code=session['request_token'])
		except Exception,e:
			return '<h1 style="color: red">'+str(e)
		access_token = user_credentials['access_token']
		session['access_token']=access_token
		session.save()
		return '<script>window.location.replace("/index")</script>'

	@expose(content_type='text/html')
	def login(self):
		try:
			request_token = Pocket.get_request_token(consumer_key=rar_config['consumer_key'], redirect_uri=rar_config['redirect_uri'])
		except Exception,e:
			return '<h1 style="color: red">'+str(e)
		session['request_token']=request_token
		session.save()
		try:
			auth_url = Pocket.get_auth_url(code=request_token, redirect_uri=rar_config['redirect_uri'])
		except Exception,e:
			return '<h1 style="color: red">'+str(e)	
		return '<script>window.location.replace("'+auth_url+'")</script>'

	@expose(content_type='text/html')
	def logout(self):
		session.delete()
		return '<script>window.location.replace("/index")</script>'

config = MinimalApplicationConfigurator()
config.update_blueprint({
	'root_controller': RootController()
})
config.register(SessionConfigurationComponent)
stream = open('config.yml', 'r')
rar_config = yaml.load(stream)['rar_config']
print('Serving on port '+str(rar_config['port'])+'...')
httpd = make_server('', rar_config['port'], config.make_wsgi_app())
httpd.serve_forever()