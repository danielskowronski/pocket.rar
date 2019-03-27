#!/usr/bin/python
import yaml,pocket,random
from pocket import Pocket
from wsgiref.simple_server import make_server
from tg import MinimalApplicationConfigurator,FullStackApplicationConfigurator,expose,TGController,session
from tg.configurator.components.session import SessionConfigurationComponent

def getSessionItemOrEmpty(name):
	try:
		x=session[name]
	except:
		x=""
	return x

class RootController(TGController):
	@expose(content_type='text/html')
	def index(self):
		session['a']='a'
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
		html+='<li><a href=https://github.com/danielskowronski/pocket.rar>github</a></li>'
		html+='<li><a href=/login>auth to Pocket</a></li>'
		html+='<li><a href=/logout>delete tokens from browser</a></li>'

		html+='</body>'

		return html
	
	@expose(content_type='text/html')
	def random(self):
		at=getSessionItemOrEmpty('access_token')
		if at=="":
			return '<script>window.location.replace("/index")</script>'

		pocket_instance = pocket.Pocket(rar_config['consumer_key'], session['access_token'])
		resp=pocket_instance.get(state='unread',tag='_untagged_') ##TODO: support tag
		articles=resp[0]['list']
		cnt=len(articles)
		trgt=random.randint(0, cnt)

		return '<script>window.location.href="https://getpocket.com/a/read/'+articles[articles.keys()[trgt]]['item_id']+'"</script>'

	@expose(content_type='text/html')
	def callback(self,*args):
		user_credentials = Pocket.get_credentials(consumer_key=rar_config['consumer_key'], code=session['request_token'])
		access_token = user_credentials['access_token']
		session['access_token']=access_token
		session.save()
		return '<script>window.location.replace("/index")</script>'

	@expose(content_type='text/html')
	def login(self):
		request_token = Pocket.get_request_token(consumer_key=rar_config['consumer_key'], redirect_uri=rar_config['redirect_uri'])
		session['request_token']=request_token
		session.save()
		auth_url = Pocket.get_auth_url(code=request_token, redirect_uri=rar_config['redirect_uri'])
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