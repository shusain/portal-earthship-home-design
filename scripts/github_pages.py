"""Configure/status GitHub Pages with existing Git credentials kept in memory.
No credential is written, logged, embedded in a URL or placed on a command line.
Run after pushing main: python scripts/github_pages.py enable|status|build
"""
import subprocess,os,json,sys,urllib.request,urllib.error
REPO='shusain/portal-earthship-home-design'
def api(path='',method='GET',data=None):
    r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,env={**os.environ,'GCM_INTERACTIVE':'never'},timeout=30,check=True)
    c=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
    if not c.get('password'):raise RuntimeError('Existing GitHub credential not available')
    req=urllib.request.Request('https://api.github.com/repos/'+REPO+path,data=json.dumps(data).encode() if data is not None else None,method=method,headers={'Authorization':'Bearer '+c['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2026-03-10','Content-Type':'application/json','User-Agent':'portal-home-design-publisher'})
    with urllib.request.urlopen(req,timeout=30) as f:
        raw=f.read()
        return json.loads(raw) if raw else {}
if __name__=='__main__':
    cmd=sys.argv[1] if len(sys.argv)>1 else 'status'
    if cmd=='enable':
        try:api('/pages')
        except urllib.error.HTTPError as e:
            if e.code!=404:raise
            result=api('/pages','POST',dict(build_type='legacy',source=dict(branch='main',path='/')))
        else:result=api('/pages','PUT',dict(build_type='legacy',source=dict(branch='main',path='/')))
        print(json.dumps({k:result.get(k) for k in ['status','html_url','source','build_type']},indent=2))
    elif cmd=='build':print(json.dumps(api('/pages/builds','POST'),indent=2))
    else:
        result=api('/pages');out={k:result.get(k) for k in ['status','html_url','source','build_type','https_enforced']}
        try:
            b=api('/pages/builds/latest');out['latest_build']={k:b.get(k) for k in ['status','commit','error','updated_at']}
        except urllib.error.HTTPError as e:out['latest_build_http_status']=e.code
        print(json.dumps(out,indent=2))
