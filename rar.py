#!/usr/bin/python3
import yaml,json,urllib.request,urllib.parse,urllib.error,pocket,random,sys
from pocket import Pocket
from wsgiref.simple_server import make_server
from tg import MinimalApplicationConfigurator,expose,TGController,session,request
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
		x=''
	return x

def writeJSRedir(url):
	return '<script>window.location.replace("'+url+'")</script>'

class RootController(TGController):
	@expose(content_type='text/html')
	def index(self):
		file = open('./index.html','r') 
		return file.read()
	
	@expose(content_type='text/html')
	def random(self):
		at=getSessionItemOrEmpty('access_token')
		if at=='':
			return writeJSRedir('/login')

		try:
			tags=json.loads(urllib.parse.unquote(request.cookies.get('tags')))
		except:
			tags=['_untagged_']
		if len(tags)==0:
			tags=['_untagged_']
		
		try:
			pocket_instance = pocket.Pocket(rar_config['consumer_key'], at)
			articles=dict()
			#for tag in tags: #tag=tag,
			resp=pocket_instance.get(state='unread',contentType='article',detailType='complete')
			articles.update(resp[0]['list'])
		except Exception as e:
			return '<h1 style="color: red">'+str(e)

		articlesToConsider=dict()
		for key,article in articles.items():
			try:
				articleTags=article['tags']
			except:
				articleTags=['_untagged_']

			if 'norar' in articleTags:
				continue
			for articleTag in articleTags:
				for tag in tags:
					if tag==articleTag:
						articlesToConsider[key]=article
						break

		cnt=len(articlesToConsider)
		if cnt==0:
			return '<p style="font-size: 120px">No articles :(</p>'+\
				'<script>setTimeout(function(){'+\
				'  window.location.replace("/")'+\
				'}, 1500);</script>'

		f = open("/tmp/rar_last.json", "w")
		f.write(json.dumps(articlesToConsider))
		f.close()

		trgt=random.randint(0, cnt-1)
		targetArticle=articlesToConsider[list(articlesToConsider.keys())[trgt]]
		return '<script>'+\
			'localStorage.setItem("last_cnt","'+str(cnt)+'");'+\
			'localStorage.setItem("last_id","'+targetArticle['item_id']+'");'+\
			'localStorage.setItem("last_title","'+targetArticle['resolved_title']+'");'+\
		'</script>'+\
		writeJSRedir('https://app.getpocket.com/read/'+targetArticle['item_id'])

	@expose(content_type='application/json')
	def check(self,*args):
		at=getSessionItemOrEmpty('access_token')
		if at=='':
			return '{"ok":false}'
		try:
			pocket_instance = pocket.Pocket(rar_config['consumer_key'], at)
			articles=dict()
			resp=pocket_instance.get(tag='TagThatDoesNotExist')
			return '{"ok":true,"confirmation":'+str(len(resp[0]['list']))+'}'
		except:
			return '{"ok":false}'

	@expose(content_type='application/json')
	def tags(self,*args):
		at=getSessionItemOrEmpty('access_token')
		if at=='':
			return '{"error":true}'

		try:
			pocket_instance = pocket.Pocket(rar_config['consumer_key'], at)
			resp=pocket_instance.get(state='unread',detailType='complete')
		except Exception as e:
			return '<h1 style="color: red">'+str(e)
		articles=resp[0]['list']
		ai=iter(articles.items())

		tags=set()
		for k,a in ai:
			try:
				for t in list(a['tags'].items()):
					tags.add(t[0])
			except:
				pass
		txt ='{"error":false, "tags": [ '
		for t in tags:
			if t=='norar':
				continue
			txt+='"'+t+'", '
		txt+='"_untagged_" ]}'
		return txt

	@expose(content_type='text/html')
	def callback(self,*args):
		try:
			user_credentials = Pocket.get_credentials(consumer_key=rar_config['consumer_key'], code=session['request_token'])
		except Exception as e:
			return '<h1 style="color: red">'+str(e)
		access_token = user_credentials['access_token']
		session['access_token']=access_token
		session.save()
		return writeJSRedir('/index')

	@expose(content_type='text/html')
	def login(self):
		try:
			request_token = Pocket.get_request_token(consumer_key=rar_config['consumer_key'], redirect_uri=rar_config['redirect_uri'])
		except Exception as e:
			return '<h1 style="color: red">'+str(e)
		session['request_token']=request_token
		session.save()
		try:
			auth_url = Pocket.get_auth_url(code=request_token, redirect_uri=rar_config['redirect_uri'])
		except Exception as e:
			return '<h1 style="color: red">'+str(e)	
		return writeJSRedir(auth_url)

	@expose(content_type='text/html')
	def logout(self):
		session.delete()
		return writeJSRedir('/index')

config = MinimalApplicationConfigurator()
config.update_blueprint({
	'root_controller': RootController()
})
config.register(SessionConfigurationComponent)
stream = open('config.yml', 'r')
rar_config = yaml.load(stream, Loader=yaml.SafeLoader)['rar_config']
print(('Serving on port '+str(rar_config['port'])+'...'))
httpd = make_server('', rar_config['port'], config.make_wsgi_app())
httpd.serve_forever()
