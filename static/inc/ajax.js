var b_version = navigator.appVersion || '';
var b_agent = navigator.userAgent || '';

var b_android = (b_version.toLowerCase().indexOf('android') !== -1) || (trim(b_agent.toLowerCase()).indexOf('mobile') !== -1);

var tbs_android_key = null;
function utf8UrlEncode(v)
{
 	return escape(encodeURIComponent(v)) ;
}
function utf8UrlDecode(v)
{
	return decodeURIComponent(unescape(v));
}


Array.prototype.removeIdx=function(dx)
{
	if(isNaN(dx)||dx>this.length){return null;}
	var r = this[dx] ;
	for(var i=0,n=0;i<this.length;i++)
	{
		if(this[i]!=this[dx])
		{
			this[n++]=this[i];
		}
	}
	this.length-=1;
	return r ;
}

Array.prototype.addTail=function(o)
{
	this[this.length]=o ;
}

Array.prototype.pushAll=function(ss)
{
	if(ss==null||ss.length<=0)
		return ;
	for(var s of ss)
		this.push(s) ;
}

Array.prototype.remove = function(val)
{ 
	var index = this.indexOf(val); 
	if (index > -1)
		this.splice(index, 1);
}

//var on_grid_value_show_end=null; 	
var r_cb__ = null ;
var r_b_debug = false;

function trim(n)
{
if(n==null)
	return null ;

	n = n + "";
return n.replace(/(^\s+)|\s+$/g,'');
}

var __sending=false;

var send_cur_url_ajax=null ;

function on_resp_error(errinf)
{
	if(!r_cb__)
		return ;

	if(r_cb__.callback)
		r_cb__.callback(false,errinf);
	else
		r_cb__(false,errinf) ;
}

function on_resp_succ(res_ss)
{
	if(!r_cb__)
		return ;

	//try
	//{
		if(r_cb__.callback)
			r_cb__.callback(true,res_ss) ;
		else
			r_cb__(true,res_ss) ;
		if(res_ss!=null&&res_ss!='')
		{
    		var ep = res_ss.lastIndexOf('</script>') ;
			if(ep>0)
			{
				var sp = res_ss.lastIndexOf('<script>') ;
				if(sp>0)
				{
					var runsptxt = res_ss.substring(sp+8,ep) ;
					var oScript = document.createElement("script"); 
			        oScript.language = "javascript";
			        oScript.type = "text/javascript"; 
			        //oScript.id = sId; 
			        oScript.defer = true;
			        oScript.text = runsptxt;
					document.body.appendChild(oScript);
				}
			}
		}
	//}
	//catch(EE)
	//{
	//	on_resp_error("ajax callback error:"+EE.message+" ln="+EE.lineNumber);
	//}
}

function SendResCallback()
{
  try
  {
    if (req.readyState == 4)
    {
        if (req.status == 200)
        {
            var res_ss = trim(req.responseText) ;
			on_resp_succ(res_ss);
        }
        else
        {
            //var divp = document.getElementById(curViewId+"_content");
            //divp.innerHTML="Problem with server response:\n "+ req.statusText+"\n"+req.responseText;
            //alert("Problem with server response:\n "+ req.statusText+"\n"+);
            if(r_b_debug)
            {
	            var winExk1=window.open();
	            winExk1.document.write(req.responseText);
	            winExk1.document.close();
            }
            on_resp_error('req.status'+req.status+" @ "+send_cur_url_ajax);
            return ;
        }
    }
  }
  catch(E)
  {
        on_resp_error(E);
  }
  finally
  {
  	//__sending=false;
  }
}



function sendWithResCallback(url,sendstr,cb_f,bdebug,bfile)
{
	//__sending = true;
	send_cur_url_ajax = url ;
	r_cb__ = cb_f ;
	if(bdebug)
		r_b_debug = true ;
	else
		r_b_debug = false;
	
	r_b_debug = false;
	//_tbs_client_auth_
	if(b_android)
	{
		var sessionid=''
		//if(typeof(tbs_call.tt)!='undefined')
		//	tbs_call.tt() ;
		//if(tbs_call.t)
		//	tbs_call.t("send_ajax-->") ;
		if(typeof(tbs_call)!='undefined' && typeof(tbs_call.getSessionId)!='undefined')
			sessionid = tbs_call.getSessionId() ;

		//alert(createAuthLine());
		if(url.indexOf("?") > 0)
			url += "&_tbs_client_auth_=" + createAuthLine()+"&tbs_auth="+sessionid;
		else
			url += "?_tbs_client_auth_=" + createAuthLine()+"&tbs_auth="+sessionid;
	}
	//if(sendstr!=null && sendstr!='')
    //	url=url+"&"+sendstr;
    
    if (window.XMLHttpRequest)
    {
        //not IE
        req = new XMLHttpRequest();
        req.withCredentials = true;
        req.onreadystatechange = SendResCallback;
        try
        {
            req.open("POST", url, true);
            if(bfile)
            	req.setRequestHeader('Content-Type', 'multipart/form-data');
            else
            	req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        }
        catch (e)
        {
            alert("Server Communication Problem\n"+e);
        }
        req.send(sendstr) ;
    }
    else if (window.ActiveXObject)
    {
        // IE
        req = new ActiveXObject("Microsoft.XMLHTTP");
        if (req)
        {
        	req.onreadystatechange=SendResCallback;
        	req.open("POST", url, true);
        	if(bfile)
            	req.setRequestHeader('Content-Type', 'multipart/form-data');
            else
            	req.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

        }
        req.send(sendstr);
    }
}


var __send_start=false;

var __send_cur = null ;
var __send_que=[] ;

try
{
(function(a){var b=a({});a.subscribe=function(){b.on.apply(b,arguments)},a.unsubscribe=function(){b.off.apply(b,arguments)},a.publish=function(){b.trigger.apply(b,arguments)}})(jQuery)
}
catch(E)
{}

function __send_que_do()
{
	if(__send_que.length==0)
		return ;
	if(__sending)
		return ;
	__sending=true;
	__send_cur = __send_que.removeIdx(0) ;
	
	//alert(__send_cur);
	var ss = (__send_cur.sendstr!=null&&__send_cur.sendstr!==undefined)?__send_cur.sendstr:'';
	sendWithResCallback(__send_cur.url,ss,function(bsucc,ret)
		{
			__send_cur.callback(bsucc,ret) ;
			
			//__send_que_do();
			__sending=false;
			//jQuery.publish("_send_q_done");
		},__send_cur.debug!==undefined?__send_cur.debug:false) ;
}
function __send_que_done()
{
	__sending=false;
}

function send_ajax_que(opts)
{//for multi send ajax in one page
	__send_que.addTail(opts) ;
	
	if(!__send_start)
	{
		__send_start=true ;
		//jQuery.subscribe("_send_q_done", __send_que_done);
		setInterval("__send_que_do()",10) ;
	}
	//if(__sending)
	//	return ;
	//__send_que_do();
}

function send_ajax(url,sendstr,cb_f,bdebug,bfile)
{

		$.ajax({
			type: 'post',
			url: url,
			data: sendstr
		}).done(function(ret){
			if(typeof(ret)=="string")
				ret = ret.trim();
			cb_f(true,ret);
		}).fail(function(req,st,err){
			cb_f(false,err);
		});
}

function ajax_get(url,sendstr,cb_f,bdebug,bfile)
{
		$.ajax({
			type: 'get',
			url: url,
			data: sendstr
		}).done(function(ret){
			if(typeof(ret)=="string")
				ret = ret.trim();
			cb_f(true,ret);
		}).fail(function(req,st,err){
			cb_f(false,err);
		});
}

function send_ajax_old11(url,sendstr,cb_f,bdebug,bfile)
{
	if(false)//(typeof($.ajax)=='function')
	{
		var jqxhr = $.ajax({
	    	url:url,
	    	//async:false,
	    	data:sendstr,
		    success:function(data,txtst,jqxhr)
		    	{
		    		var res_ss = trim(data) ;
					on_resp_succ(res_ss);
		    	}
			});//.error(function(){on_resp_error("");}) ;
	}
	else
	{
		//sendWithResCallback(url,sendstr,cb_f,bdebug,bfile) ;
		
		var opts ={};
		opts.url=url;
		opts.sendstr=sendstr;
		opts.callback=cb_f;
		opts.debug=bdebug;
		send_ajax_que(opts);
		
	}
}

//for android
function createAuthLine()
{
	//alert(tbs_call.getAuthLine());
	if(typeof(tbs_call)=='undefined')
		return '' ;
	if(typeof(tbs_call.getAuthLine)=='undefined')
		return '' ;
	return encodeHexUrl(tbs_call.getAuthLine());
}




function ToolBarBtnOpen(url,callback)
{
	
}

//
function FindFrameWin(framen)
{
	var o = FindFrameWinInner(top,framen) ;
	if(o)
		return o ;
	
	if(opener)
	{
		//alert("opener top url="+opener.top.location.href);
		return FindFrameWinInner(opener.top,framen) ;
	}
}

function FindFrame(framen)
{
	return FindFrameInner(top,framen) ;
}

function FindFrameInner(w,framen)
{
	var pfs = w.frames ;
	if(pfs==null)
		return null ;
	
	var o ;
	var i ;
	
	var ss = '';
	for(i=0 ; i < pfs.length ; i ++)
	{
		ss += pfs[i].name+',';
	}
	//alert(w.location.href+" =="+pfs.length+"  "+ss);
	for(i=0 ; i < pfs.length ; i ++)
	{
		if(pfs[i].name==framen)
			return pfs[i] ;
		o = FindFrameInner(pfs[i].window,framen) ;
		if(o!=null)
			return o ;
	}
	
	return null ;
}

function FindFrameWinInner(w,framen)
{
//alert(w.name+"  "+w.location.href+" match="+(w.name==framen));
	let w_n = "" ;
	try
	{
		w_n = w['name'] ;
	}
	catch(e){return null;}
	
	if(w_n==framen)
		return w ;
	
	//alert(w.__FOR_FIND_FRAME_NAME) ;
	if(w.__FOR_FIND_FRAME_NAME && w.__FOR_FIND_FRAME_NAME==framen)
		return w ;
	
	var pfs = w.frames ;
	if(pfs==null)
		return null ;
	
	var o ;
	var i ;
	
	for(i=0 ; i < pfs.length ; i ++)
	{
		o = FindFrameWinInner(pfs[i].window,framen) ;
		if(o!=null)
			return o ;
	}
	
	return null ;
}

//page event center

function DWEvent(eventn,eventv)
{
	this.eventName = eventn ;
	this.eventValue = eventv ;
}

function DWEventCenter()
{
	this.allEvents = new Array() ;
}

function EventCenterFire(event_name,event_v)
{
	var top_w = window.top ;
	if(top_w==null||top_w==undefined)
		top_w = window ;
	
	
	
}


/////////////////auto complete

// step1 : 
// create autocomplete container, return object and bind event to the object, and 
///create a new jsAuto instance:
// <div id="divautocomplete"></div>
// var autocomplete = new jsAuto("autocomplete","divautocomplete")
// handle event:
// autocomplete.handleEvent(value, returnObjectID)
// <input id="rautocomplete" onkeyup="autocomplete.handleEvent(this.value,"ratocomplete",event)>

// step2 :
// add autocompete item:
// autocomplete.item(string)
// string must be a string var, you can split the string by ","
// autocomplete.item("blueDestiny,never-online,csdn,blueidea")

function JsAuto(instanceName,feedback_url,objID)
{
	this._msg = [];
	if(!objID)
		objID = "div_js_auto_"+instanceName ;
	this._x = null;
	this._o = document.getElementById( objID );
	this._fix_div = false;
	if (!this._o)
	{//create auto complete div
		var dele = document.createElement("div");
		dele.id=objID ;
		dele.style.border=1 ;
		document.body.appendChild(dele) ;
		this._o = dele ;
		//return;
	}
	else
	{
		this._fix_div = true ;
	}
	this._fuzzy_match = false;
	this._seg_input_split = null ;//support input seg
	this._f = null;
	this._i = instanceName;
	this._r = null;
	this._c = 0;
	this._s = false;
	this._v = null;
	this._o.style.visibility = "hidden";
	this._o.style.position = "absolute";
	this._o.style.zIndex = "9999";
this._o.style.overflow = "auto";
this._o.style.height = "200";
	this._feedback_url = feedback_url ;
	return this;
};

var __curJsAuto = null ;

function update_input(curval)
{
	if(__curJsAuto==null)
		return ;
		
	if(__curJsAuto._feedback_url==null||__curJsAuto._feedback_url=='')
			return ;
			
	if(curval==null||curval=='')
		return ;
	
	//if(curval.length()==1)
	//	this.item_clear() ;
	//alert(__curJsAuto._feedback_url+"?in="+curval);
	sendWithResCallback(__curJsAuto._feedback_url+"?in="+curval,null,__curJsAuto) ;
};

JsAuto.prototype.callback=function(bsucc,ret)
{
	with (this)
	{
		if(!bsucc)
			return ;
		
		//ret may has fuzzy or seg_split info
		var p,q,k;
		var s,tmpv,v0;
		if(ret)
		{// [#fuzzy=true,seg_split=;#]
			p = ret.indexOf("[#") ;
			if(p>=0)
			{
				q = ret.indexOf("#]",p+1) ;
			}
			
			if(p>=0&&q>=0)
			{
				s = ret.substring(p+2,q) ;
				ret = ret.substring(0,p)+ret.substring(q+2) ;
				//alert(s+"+"+ret);
				s = s.split("|") ;
				for(k=0;k<s.length ; k ++)
				{
					tmpv = trim(s[k]) ;
					if(tmpv=="")
						continue ;
					tmpv = tmpv.split("=") ;
					v0 = trim(tmpv[0]) ;
					if("fuzzy"==v0)
					{
						if("true"==trim(tmpv[1]))
						{
							_fuzzy_match = true ;
						}
					}
					else if("seg_split"==v0)
					{
						_seg_input_split = trim(tmpv[1]) ;
					}
				}
			}
			
			
		}
		
		if(item(ret))
			process_input() ;
	}
};

JsAuto.prototype.set_obj_class_style=function(o,cn)
{
with (this)
{
	if('mouseout'==cn)
	{
		o.style.color="#000000";
		o.style.width="100%";
		o.style.backgroundColor="#ffffff";
		o.style.cursor="default";
		return ;
	}
	
	if('mouseover'==cn)
	{
		o.style.color="#ffffff";
		o.style.backgroundColor="highlight";
		o.style.width="100%";
		o.style.cursor="default";
		return ;
	}
	
	if('hiddeme'==cn)
	{
		o.style.visibility="hidden";
		if(!_fix_div)
		{
			o.style.left = 0 ;
			o.style.top = 0 ;
			o.style.width = 0 ;
		}
	}
}
}

JsAuto.prototype.directionKey=function() { with (this)
{
	var e = _e.keyCode ? _e.keyCode : _e.which;
	var l = _o.childNodes.length;
	(_c>l-1 || _c<0) ? _s=false : "";

	if( e==40 && _s )
	{
		//_o.childNodes[_c].className="mouseout";
		this.set_obj_class_style(_o.childNodes[_c],"mouseout");
		(_c >= l-1) ? _c=0 : _c ++;
		//_o.childNodes[_c].className="mouseover";
		this.set_obj_class_style(_o.childNodes[_c],"mouseover");
	}
	if( e==38 && _s )
	{
		//_o.childNodes[_c].className="mouseout";
		this.set_obj_class_style(_o.childNodes[_c],"mouseout");
		_c--<=0 ? _c = _o.childNodes.length-1 : "";
		//_o.childNodes[_c].className="mouseover";
		this.set_obj_class_style(_o.childNodes[_c],"mouseover");
	}
	if( e==13 )
	{
		if(_o.childNodes[_c] && _o.style.visibility=="visible")
		{
			//_r.value = _x[_c];
			set_or_append_val(_x[_c]) ;
			//_o.style.visibility = "hidden";
			this.set_obj_class_style(_o,"hiddeme");
		}
	}
	if( !_s )
	{
		_c = 0;
		//_o.childNodes[_c].className="mouseover";
		this.set_obj_class_style(_o.childNodes[_c],"mouseover");
		_s = true;
	}
}};

// mouseEvent.
JsAuto.prototype.domouseover=function(obj) { with (this)
{
	//_o.childNodes[_c].className = "mouseout";
	this.set_obj_class_style(_o.childNodes[_c],"mouseout");
	_c = 0;
	if(obj.tagName=="DIV")
		//obj.className="mouseover"
		this.set_obj_class_style(obj,"mouseover")
	else
		//obj.parentElement.className="mouseover";
		this.set_obj_class_style(obj.parentElement,"mouseover");
}};
JsAuto.prototype.domouseout=function(obj)
{
	if(obj.tagName=="DIV")
		//obj.className="mouseout"
		this.set_obj_class_style(obj,"mouseout")
	else
		//obj.parentElement.className="mouseout";
		this.set_obj_class_style(obj.parentElement,"mouseout");
};

JsAuto.prototype.set_or_append_val=function(v)
{
	with(this)
	{
		if(_r.value==null||_r.value==''||_seg_input_split==null||_seg_input_split=='')
		{
			_r.value = v ;
			return ;
		}
		
		var k = 0,p = 0 ;
		var c;
		for(k = 0 ; k < _seg_input_split.length ; k ++)
		{
			c = ""+_seg_input_split.charAt(k) ;
			p = _r.value.lastIndexOf(c) ;
			if(p>0)
				break ;
		}
		
		if(p>0)
		{
			_r.value = _r.value.substring(0,p+1)+v+c ;
		}
		else
		{
			_r.value = v +_seg_input_split.charAt(0);
		}
	}
}

JsAuto.prototype.get_or_extract_cur_input_val=function(v)
{
	with(this)
	{
		if(v==null||v==''||_seg_input_split==null||_seg_input_split=='')
		{
			return v ;
		}
		
		var k = 0,p = 0 ;
		var c;
		for(k = 0 ; k < _seg_input_split.length ; k ++)
		{
			c = ""+_seg_input_split.charAt(k) ;
			p = v.lastIndexOf(c) ;
			if(p>0)
				break ;
		}
		
		if(p>0)
		{
			return v.substring(p+1) ;
		}
		else
		{
			return v ;
		}
	}
}

JsAuto.prototype.doclick=function(msg) { with (this)
{
	if(_r)
	{
		set_or_append_val(msg) ;
		//_o.style.visibility = "hidden";
		this.set_obj_class_style(_o,"hiddeme");
	}
	else
	{
		alert("javascript autocomplete ERROR :\n\n can not get return object.");
		return;
	}
}};

// object method;
JsAuto.prototype.item=function(msg)
{
	if(msg==null||msg=="")
		return false;
	
	msg = trim(msg) ;
	if(msg=='')
		return false;
	
	var tmpv;
	if( msg.indexOf(",")>0 )
	{
		var arrMsg=msg.split(",");
		for(var i=0; i<arrMsg.length; i++)
		{
			if(arrMsg[i]=='')
				continue ;
			
			tmpv = trim(arrMsg[i]) ;
			
			tmpv ? this._msg.push(tmpv) : "";
		}
	}
	else
	{
		this._msg.push(msg);
	}
	this._msg.sort();
	return true ;
};

JsAuto.prototype.item_clear=function()
{
	this._msg = null ;
	this._msg = [] ;
};

JsAuto.prototype.append=function(msg) { with (this)
{
	_i ? "" : _i = eval(_i);
	_x.push(msg);
	var div = document.createElement("DIV");

	//bind event to object.
	div.onmouseover = function(){_i.domouseover(this)};
	div.onmouseout = function(){_i.domouseout(this)};
	div.onclick = function(){_i.doclick(msg)};
	var re  = new RegExp("(" + _v + ")","i");
	div.style.lineHeight="140%";
	//div.className = "mouseout";
	this.set_obj_class_style(div,"mouseout")
	if (_v) div.innerHTML = msg.replace(re , "<strong>$1</strong>");
	div.style.fontFamily = "verdana";

	_o.appendChild(div);
}};

function getLeft(el)
{
	return el==null?0:(el.offsetLeft+getLeft(el.offsetParent));
}   
function getTop(el)
{   
	return el==null?0:(el.offsetTop+getTop(el.offsetParent));
}

function getIEPosX(elt) { return getIEPos(elt,"Left"); }
function getIEPosY(elt) { return getIEPos(elt,"Top"); }
function getIEPos(elt,which) {
 iPos = 0
 while (elt!=null) {
  iPos += elt["offset" + which]
  elt = elt.offsetParent
 }
 return iPos
}

function findXY(obj)
{
	var o=obj,x=0,y=0,w=o.offsetWidth
	while(o!=null && o.tagName.toUpperCase()!="BODY")
	{
		x+=o.offsetLeft;
		y+=o.offsetTop;
		o=o.offsetParent;
	}
	return [x,y,w]
}

JsAuto.prototype.display=function() { with(this)
{
	if(_f&&_v!="")
	{
		if(!_fix_div)
		{
		var xyw = findXY(_r) ;
	
		_o.style.height = "200";
		_o.style.left = xyw[0];//getIEPosX(_r)+'px' ;//getLeft(_r);//_r.offsetLeft;
		_o.style.width = _r.offsetWidth;
		_o.style.top = xyw[1]+_r.offsetHeight;//getTop(_r)+_r.offsetHeight;//_r.offsetTop + _r.offsetHeight;
		//alert(_o.innerHTML) ;
		}
		
		_o.style.visibility = "visible";
	}
	else
	{
		//_o.style.visibility = "hidden";
		this.set_obj_class_style(_o,"hiddeme");
		
	}
}};

JsAuto.prototype.process_input=function() { with (this)
{
	var fValue = this._curVal ;
	var fID = this._curId
	var re;
	
	_x = [];
	_f = false;
	_r = document.getElementById( fID );
	_v = fValue;
	_i = eval(_i);
	re = new RegExp("^" + fValue + "", "i");
	_o.innerHTML="";

	for(var i=0; i<_msg.length; i++)
	{
		if(_fuzzy_match)
		{
			_i.append(_msg[i]);
			_f = true;
			continue ;
		}
		
		if(re.test(_msg[i]))
		{
			_i.append(_msg[i]);
			_f = true;
		}
	}

	_i ? _i.display() : alert("can not get instance");

	if(_f)
	{
		{
			_c=0;
			var tmpo = _o.childNodes[_c] ;
	//.className = "mouseover";
	this.set_obj_class_style(tmpo,"mouseover");
			_s=true;
		}
	}
}};


JsAuto.prototype.handleEvent0=function(fValue,fID,event) { with (this)
{
	var ccval = get_or_extract_cur_input_val(fValue) ;
	
	if(this._curVal!=ccval&&fValue!=null)
	{
		//if(fValue.indexOf(this._curVal)!=0)
		{
			item_clear() ;
		}
	}
	
	this._curVal = fValue ;
	this._curId = fID ;
	
	var re;
	_e = event;
	var e = _e.keyCode ? _e.keyCode : _e.which;
	_x = [];
	_f = false;
	_r = document.getElementById( fID );
	_v = fValue;
	_i = eval(_i);
	re = new RegExp("^" + fValue + "", "i");
	_o.innerHTML="";

	for(var i=0; i<_msg.length; i++)
	{
		if(re.test(_msg[i]))
		{
			_i.append(_msg[i]);
			_f = true;
		}
	}

	_i ? _i.display() : alert("can not get instance");

	if(_f)
	{
		if((e==38 || e==40 || e==13))
		{
			_i.directionKey();
		}
		else
		{
			_c=0;
			//_o.childNodes[_c].className = "mouseover";
			var tmpo = _o.childNodes[_c] ;
			this.set_obj_class_style(tmpo,"mouseover");
			_s=true;
		}
	}
	
	__curJsAuto = this ;
	if(!_f)
		setTimeout("update_input('"+utf8UrlEncode(fValue)+"')",100);
}};


JsAuto.prototype.handleEvent=function(fValue,fID,event) { with (this)
{
	var ccval = get_or_extract_cur_input_val(fValue) ;
	if(ccval==null||trim(ccval)=='')
		return ;
	
	if(this._curVal!=ccval&&ccval!=null)
	{
		//if(fValue.indexOf(this._curVal)!=0)
		{
			item_clear() ;
		}
	}
	this._curVal = ccval ;
	this._curId = fID ;
	
	var re;
	_e = event;
	var e = _e.keyCode ? _e.keyCode : _e.which;
	_x = [];
	_f = false;
	_r = document.getElementById( fID );
	_v = ccval;
	_i = eval(_i);
	//re = new RegExp("^" + fValue + "", "i");
	_o.innerHTML="";
	_fuzzy_match = true ;
	//_seg_input_split = seg_split_chrs ;

	for(var i=0; i<_msg.length; i++)
	{
		//if(re.test(_msg[i]))
		{
			_i.append(_msg[i]);
			_f = true;
		}
	}

	_i ? _i.display() : alert("can not get instance");

	if(_f)
	{
		if((e==38 || e==40 || e==13))
		{
			_i.directionKey();
		}
		else
		{
			_c=0;
			//_o.childNodes[_c].className = "mouseover";
			var tmpo = _o.childNodes[_c] ;
			this.set_obj_class_style(tmpo,"mouseover");
			_s=true;
		}
	}
	
	__curJsAuto = this ;
	if(!_f)
		setTimeout("update_input('"+utf8UrlEncode(ccval)+"')",100);
}};


//??????????????,????????????ajax??????
//????????,?????ajax??,?????????????,?????
//?,????????
function AjaxLazyShowItem(container_id,url,post_d_or_f)
{
	this.containerId = container_id ;//display container id
	this.url = url ; //ajax display url
	this.post_d_or_f = post_d_or_f ;
}


function AjaxLazyShower()
{
	this.arrayVars = new Array() ;
	this.arrayNum = 0 ;
	
	this.cur_lazy_show_item = null ;
	this.cur_lazy_show_idx = -1 ;
	
	this.on_show_start = null ;
	this.on_show_item = null ;
	this.on_show_end = null ;
	
	this.addLazyShowItem = function	(containerid,url,p_d_or_f)
	{
		this.arrayVars[this.arrayNum] = new AjaxLazyShowItem(containerid,url,p_d_or_f) ;
		this.arrayNum ++ ;
	}
	
	this.extractNextShowItem = function()
	{
		this.cur_lazy_show_idx ++ ;
		if(this.cur_lazy_show_idx>=this.arrayNum)
			return null ;
			
		this.cur_lazy_show_item = this.arrayVars[this.cur_lazy_show_idx] ;
		return this.cur_lazy_show_item;
	}

	this.show = function()
	{
		var item = this.extractNextShowItem() ;
		if(item==null)
		{
			if(this.on_show_end!=null && this.on_show_end!=undefined)
			{
				this.on_show_end() ;
			}
			
			if(typeof(on_grid_value_show_end)=='function')
				on_grid_value_show_end() ;
				
			return ;
		}
		
		//first chk
		if(this.cur_lazy_show_idx==0)
		{
			if(this.on_show_start!=null && this.on_show_start!=undefined)
			{
				this.on_show_start() ;
			}
		}
		
		var pv = '' ;
		if(item.post_d_or_f!=null)
		{
			if(typeof(item.post_d_or_f)=='function')
				pv = item.post_d_or_f() ;
			else if(item.post_d_or_f.indexOf('js:')==0)
				eval('pv='+item.post_d_or_f.substring(3)) ;
			else
				pv = item.post_d_or_f;
		}
		sendWithResCallback(item.url,pv,this);
	}
	
	this.callback = function(bsucc,ret)
	{
		if(bsucc)
		{//change container
			//ret xxx##xx=xx
			var showstr = ret ;
			var k = ret.indexOf('##') ;
			var pnvs = [] ;
			
			if(k>=0)
			{
				showstr=ret.substring(0,k) ;
				eval('pnvs='+ret.substring(k+2)) ;
			}
			
			var c = document.getElementById(this.cur_lazy_show_item.containerId) ;
			if(c!=null)
			{
				c.innerHTML = showstr ;
				for(var m=0;m<pnvs.length;m++)
					c.setAttribute(pnvs[m][0],pnvs[m][1]) ;//set attribute
				if(this.on_show_item!=null && this.on_show_item!=undefined)
				{
					this.on_show_item(c,showstr) ;
				}
			}
		}
		
		//call server again
		this.show() ;
	}
}

function decodeHexUrl(s)
{
	if(!s)
		return s ;

	if(s.indexOf("=h=") != 0 && s.indexOf("=u=") != 0)
		return s;
	
	s = s.substr(3);
	return utf8UrlDecode(s);
}

function encodeHexUrl(s)
{
	if(s==null)
		return null ;
	
	if(s=='')
		return '';

	return '=u='+utf8UrlEncode(s);
}

function grid_get_prop_value(id_pn,id_pv,val_pn)
{
	var sps = document.getElementsByTagName('span') ;
	for(var i=0;i<sps.length;i++)
	{
		if(sps[i].getAttribute(id_pn)==id_pv)
			return sps[i].getAttribute(val_pn) ;
	}
	return null ;
}

function grid_get_row_col_value(row,col,pn)
{
	
}

function GridGetDataTableValueWithUrlEncode(dtvar)
{
	var prefix = dtvar + '_' ;
	var alls = document.getElementsByTagName('span');
	var i;
	var ret = '' ;
	
	for(i = 0 ; i < alls.length ; i ++)
	{//alert(alls[i].id);
		if(alls[i].id&&alls[i].id.indexOf(prefix)==0)
		{
			var r = alls[i].getAttribute('dt_row') ;
			var c = alls[i].getAttribute('dt_col') ;
			var t = alls[i].getAttribute('dt_valtype') ;
			var s = '&dt_'+r+'_'+c ;
			if(t!=null&&t!='')
				s += (':'+t) ;
			
			var v = trim(alls[i].innerHTML) ;
			ret += (s+'='+encodeHexUrl(v)) ;
		}
	}
	return ret ;
}

//export current page data table info,to excel file to download
//1,create iframe in page,with form
//2,extract data table with data table var name from this page,and set iframe form
//3,post iframe form to fixed target jsp to create excel
function exportPageDTToExcel(dtvar)
{
	
}


//call ajax url,and read prop txt,then write to map inputids
function fillInputWithAjaxPropRes(url,input_ids,prop_names,input_appends)
{
	var cb22 = new FillInputWithAjaxPropResCB(input_ids,prop_names,input_appends) ;
	sendWithResCallback(url,'',cb22,true);
}

function FillInputWithAjaxPropResCB(input_ids,prop_names,append_strs)
{
	this.inputIds = input_ids ;
	this.propNames = prop_names ;
	this.append_strs = append_strs ;
	
	this.callback = function (bsu,ret)
	{
		if(!bsu)
		{
			alert("Error:"+ret) ;
			return ;
		}
		ret = trim(ret) ;
		if(ret==null||ret=='')
			return ;
		var ls = ret.split("\n") ;
		var i;
		for(i = 0 ; i < ls.length ; i ++)
		{
			var ll = ls[i] ;
			ll = trim(ll) ;
			//alert(ll) ;
			var p = ll.indexOf("=") ;
			var n,v ;
			if(p>=0)
			{
				n = ll.substring(0,p) ;
				v = ll.substring(p+1) ;
			}
			else
			{
				n = ll;
				v = '';
			}
			var append_str = null;
			if(this.append_strs!=null&&this.append_strs!=undefined&&this.append_strs.length>i)
				append_str = this.append_strs[i] ;
			this.fillToInput(n,v,append_str) ;
		}
	}
	
	this.fillToInput = function(n,v,append_str)
	{
		if(this.propNames==null)
			return ;
		if(this.propNames.length==0)
			return ;
		
		var i = 0 ;
		for(i = 0 ; i < this.propNames.length ; i ++)
		{
			if(n==this.propNames[i])
			{
			//alert("pn="+n+' id='+input_ids[i]) ;
				var inputo = document.getElementById(input_ids[i]) ;
				//alert(inputo) ;
				if(inputo!=null)
				{
					if(append_str!=null)
						inputo.value += (append_str+v) ;
					else
						inputo.value = v ;
				}
				return ;
			}
		}
	}
}

function fillInputWithDictSelect(classn,input_ids,prop_names,append_strs)
{
	var cb11 = new fillInputWithDictSelectCB(classn,input_ids,prop_names,append_strs) ;
	dlg.open('/system/util/dlg_dd_selector.jsp?indlg=true&class_name='+classn,cb11,'fillInputWithDictSelect') ;
}

var fillInputWithDictSelectCB_u = '';
var fillInputWithDictSelectCB_i = '' ;
var fillInputWithDictSelectCB_p = '' ;
var fillInputWithDictSelectCB_a = null;

function fillInputWithDictSelectCB(ddclassn,input_ids,prop_names,append_strs)
{
	this.dd_classn = ddclassn ;
	this.input_ids = input_ids ;
	this.prop_names = prop_names ;
	this.append_strs = append_strs ;
	
	this.callback = function(ret)
	{
		if(ret==null||ret=='')
			return ;
		//window.open('/system/util/dd_read_datanode_props_ajax.jsp?class_name=company_bank_account&node_id='+ret) ;
		fillInputWithDictSelectCB_u = '/system/util/dd_read_datanode_props_ajax.jsp?class_name='+this.dd_classn+'&node_id='+ret ;
		fillInputWithDictSelectCB_i = this.input_ids ;
		fillInputWithDictSelectCB_p = this.prop_names ;
		fillInputWithDictSelectCB_a = this.append_strs ;
		
		//firefox error support
		setTimeout("fillInputWithDictSelectAjax()",500);
	}
}

function fillInputWithDictSelectAjax()
{
	fillInputWithAjaxPropRes(fillInputWithDictSelectCB_u,
			fillInputWithDictSelectCB_i,fillInputWithDictSelectCB_p,fillInputWithDictSelectCB_a);
}

//for comp action support select

function fillInputWithActSelect(search_act,detail_act,input_ids,prop_names,append_strs,input_xdstr)
{
	var cb11 = new fillInputWithActSelectCB(search_act,detail_act,input_ids,prop_names,append_strs) ;
	dlg.open('/system/util/dlg_search_list.jsp?search_act='+search_act+'&'+input_xdstr,cb11,'fillInputWithActSelect') ;
}

var fillInputWithActSelectCB_u = '';
var fillInputWithActSelectCB_i = '' ;
var fillInputWithActSelectCB_p = '' ;
var fillInputWithActSelectCB_a = null ;

function fillInputWithActSelectCB(search_act,detail_act,input_ids,prop_names,append_strs)
{
	this.search_act = search_act ;
	this.detail_act = detail_act ;
	this.input_ids = input_ids ;
	this.prop_names = prop_names ;
	this.append_strs = append_strs ;
	
	this.callback = function(ret)
	{
		if(ret==null||ret=='')
			return ;
		//window.open('/system/util/dd_read_datanode_props_ajax.jsp?class_name=company_bank_account&node_id='+ret) ;
		fillInputWithActSelectCB_u = '/system/util/dlg_search_select_detail_props_ajax.jsp?search_detail_act='+this.detail_act+'&id='+ret ;
		fillInputWithActSelectCB_i = this.input_ids ;
		fillInputWithActSelectCB_p = this.prop_names ;
		fillInputWithActSelectCB_a = this.append_strs
		//firefox error support
		setTimeout("fillInputWithActSelectAjax()",500);
	}
}

function fillInputWithActSelectAjax()
{
	fillInputWithAjaxPropRes(fillInputWithActSelectCB_u,
			fillInputWithActSelectCB_i,fillInputWithActSelectCB_p,fillInputWithActSelectCB_a);
}

//return array of lines
function parseTxtToLines(txt)
{
	if(txt==null||txt=='')
		return txt ;
	var r = [] ;
	do
	{
		var i = txt.indexOf('\r\n');
		if(i>=0)
		{
			r[r.length] = txt.substring(0,i) ;
			txt = txt.substring(i+2) ;
		}
		else
		{
			r[r.length]=txt ;
			txt = null ;
		}
	}
	while(txt!=null) ;
	return r ;
}

function parseTrimTxtFirstLine(txt)
{
	var s = trim(txt) ;
	var i = s.indexOf('\r\n') ;
	if(i<0)
		return s ;
	return s.substring(0,i) ;
}


/* ???Firefox 14, Chrome 20????????????? */
/* IE9???files??????????IE9 */
function AjaxUploadX(ops){
    if(!window.FormData || !window.FileList){
        //throw('Your browser does not support ajax upload');
        throw('????????ajax upload');
    }
    this.options = ops||{};
    this._init();
}
function $id(id) 
{
	return document.getElementById(id);
}
function FileDragHover(e) 
{
	e.stopPropagation();
	e.preventDefault();
	e.target.className = (e.type == "dragover" ? "hover" : "");
}
/*function FileSelectHandler(e)
{
	FileDragHover(e);
}*/
AjaxUploadX.prototype = {
	
    _init: function ()
    {
        var THIS = this;
        var fileselect = this.options.fileselect;
        fileselect.onchange= function (e)
        {
            THIS._onchange(e);
        }
        this._input = fileselect;
        
		var tem_fileSelectHandler=function(e)
		{
			THIS._fileSelectHandler(e);
		}
		
		this.file_list=this.options.file_array;
        
        this.removedArr = new Array();
        //var fileselect = this.options.fileselect,
        //fileselect.addEventListener("change",tem_fileSelectHandler, false);
        var filedrag = this.options.filedrag;

		// is XHR2 available?
		var xhr = new XMLHttpRequest();
		if (xhr.upload) 
		{
			// file drop is important
			filedrag.addEventListener("dragover", FileDragHover, false);
			filedrag.addEventListener("dragleave", FileDragHover, false);
			filedrag.addEventListener("drop",tem_fileSelectHandler, false);
			filedrag.style.display = "block";
		}
    },
    _fileSelectHandler:function(e){
		FileDragHover(e);
		// fetch FileList object
		var files = e.target.files || e.dataTransfer.files;
		if(this.options.onselectfiles)
        {
            this.options.onselectfiles(files);
        }
	},
    _valid:function(index){
    	if(this.removedArr.length < 1)
    		return true;
    	for(var i = 0; i < this.removedArr.length; i ++){
    		if(this.removedArr[i] == index)
    			return false;
    	}
    	return true;
    },
    _destroy: function(){
        document.body.removeChild(this._input);
    },
    _onchange: function(e){
        var ops = this.options;
        if(ops.onselectfiles)
        {
            ops.onselectfiles(e.target.files);
        }
    },
    selectFiles: function()
    {
        this._input.click();
    },
    removeFile:function(index){
     	if(!this.file_list.length)
     	{//this._input.files
          this.options.onerror('No files');
          return;
      	}
      	this.removedArr.push(index);
    },
    clearFiles:function()
    {
		for(var i = 0; i < this.file_list; i ++)
		{//this._input.files
	      	this.removedArr.push(i);
		}
    },
    upload: function (){
      var xhr = new XMLHttpRequest();
      var ops = this.options;
      var v, h, evs = {loadstart:0, loadend:0, progress:0, load:0, error:0, abort:0};
      for(v in evs){
        if(h = ops['on'+v]){
            xhr.addEventListener(v, h, false);
        }
        if(h = ops['uploadHandlers']['on'+v]){
            xhr.upload.addEventListener(v, h, false);
        }
      }

      var data = new FormData();
      var files = this.file_list;//this._input.files;
      if(files.length<=0)
      {	
      	alert("No files~!");
      	return;
      }
      if(!files.length)
      {
          this.options.onerror('No files');
          return;
      }
      for(var i=0, n=files.length;i<n;i++)
      {
     	var b = this._valid(i);// remove the files
      	if(b)
      	{//alert("file name ==="+files[i].name);
       		data.append(ops.formname || "uploadedfile[]",  files[i]);
      	}
      }
      xhr.open("POST", ops.url, true);
      xhr.send(data);
    }
};

function chk_name_nodiv(n)
{
	if(n==null||n=='')
		return false;
	var c = n.charAt(0) ;
	if(!( (c>='a'&&c<='z') || (c>='A'&&c<='A')) )
		return false;
	var s = n.length ;
	for(var i = 1 ; i < s ; i ++)
	{
		c = n.charAt(i) ;
		if(!( (c>='a'&&c<='z') || (c>='A'&&c<='A') || (c>='0'&&c<='9')))
			return false;
	}
	return true ;
}

function chk_name(n)
{
	if(n==null||n=='')
		return false;
	var c = n.charAt(0) ;
	if(!( (c>='a'&&c<='z') || (c>='A'&&c<='A')) )
		return false;
	var s = n.length ;
	for(var i = 1 ; i < s ; i ++)
	{
		c = n.charAt(i) ;
		if(!( (c>='a'&&c<='z') || (c>='A'&&c<='A') || (c>='0'&&c<='9')  || (c=='_')))
			return false;
	}
	return true ;
}
	
function combine_to_str(arrs,delmi)
{
	var n;
	if(!arrs||(n=arrs.length)<=0)
		return '';
	var ret = arrs[0];
	for(var i = 1 ; i < n ; i ++)
		ret += delmi+arrs[i];
	return ret;
}


var CHK_INT_GE0 = /^\d+$/;
var CHK_INT_GT0 = /^[0-9]*[1-9][0-9]*$/;
var CHK_INT_LE0 = /^((-\d+)|(0+))$/;
var CHK_INT_LT0 = /^-[0-9]*[1-9][0-9]*$/;
var CHK_INT = /^-?\d+$/;
var CHK_FLOAT_GE0 = /^\d+(\.\d+)?$/;
var CHK_FLOAT_GT0 = /^(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*))$/;
var CHK_FLOAT_LE0 = /^((-\d+(\.\d+)?)|(0+(\.0+)?))$/;
var CHK_FLOAT_LT0 = /^(-(([0-9]+\.[0-9]*[1-9][0-9]*)|([0-9]*[1-9][0-9]*\.[0-9]+)|([0-9]*[1-9][0-9]*)))$/;
var CHK_FLOAT = /^(-?\d+)(\.\d+)?$/;



Date.prototype.format_local = function (fmt) {
    var o = {
        "M+": this.getMonth() + 1,
        "d+": this.getDate(),
        "h+": this.getHours(), 
        "m+": this.getMinutes(),
        "s+": this.getSeconds(),
        "q+": Math.floor((this.getMonth() + 3) / 3),
        "S+": this.getMilliseconds()
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
	{
		if(k=='S+')
		{
			if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("000" + o[k]).substr(("" + o[k]).length)));
		}
		else
		{
			if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
		}
	}
    return fmt;
}

Date.prototype.format_utc = function (fmt) {
    var o = {
        "M+": this.getUTCMonth() + 1,
        "d+": this.getUTCDate(),
        "h+": this.getUTCHours(), 
        "m+": this.getUTCMinutes(),
        "s+": this.getUTCSeconds(),
        "q+": Math.floor((this.getUTCMonth() + 3) / 3),
        "S": this.getUTCMilliseconds()
    };
    if (/(y+)/.test(fmt)) fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (var k in o)
        if (new RegExp("(" + k + ")").test(fmt)) fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
}

Date.prototype.UTC_getMonthLastDay=function()
{
	let dt = new Date(this.getTime()) ;
	let m = dt.getUTCMonth()+1;
	dt.setUTCMonth(m);
	dt.setUTCDate(1);
	dt.setUTCHours(0);
	dt.setUTCMinutes(0);
	dt.setUTCSeconds(0);
	dt.setUTCMilliseconds(0);
	let ms = dt.getTime()-24*3600000 ;
	dt.setTime(ms) ;
	return dt;
}

Date.prototype.UTC_getMonthLastSunDay=function()
{//
	let dt = this.UTC_getMonthLastDay();
	let w = dt.getUTCDay() ;
	if(w==0)
		return dt;
	let d = dt.getUTCDate() ;
	dt.setUTCDate(d-w) ;
	return dt ;
}

//Determine whether it is European Daylight Saving Time(DST)
Date.prototype.check_eur_dst = function () {
    let ms = this.getTime();
    
    let tmpdt = new Date(ms);
    tmpdt.setUTCMonth(2);//mar
    tmpdt = tmpdt.UTC_getMonthLastSunDay();
    tmpdt.setUTCHours(2);

    let ms_st = tmpdt.getTime() ;
    tmpdt.setUTCMonth(9);//
    tmpdt = tmpdt.UTC_getMonthLastSunDay();
    tmpdt.setUTCHours(3);
    let ms_et = tmpdt.getTime();
    return ms>=ms_st && ms<ms_et;
}

Date.prototype.MON_ENS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];

Date.prototype.toShortGapNow=function(lang,fmt)
{//
	let inms = this.getTime() ;
	let c = new Date() ;
	c.setHours(0);
	c.setMinutes(0);
	c.setSeconds(0);
	c.setMilliseconds(0);
	let day_st = c.getTime();
	let hh = this.getHours() ;
	let mm = this.getMinutes() ;
	let hm = ((hh<10)?("0"+hh):(""+hh)) +":" +((mm<10)?("0"+mm):(""+mm));
	if(inms>=day_st)
		return hm;
	
	hm = fmt?" "+hm:"" ;
		
	let m = this.getMonth() ;
	let d =  this.getDate() ;
	
	c.setMonth(0);
	c.setDate(1);
	let y_st = c.getTime() ;
	if(inms>=y_st)
	{//in year
		if("cn"==lang)
			return (m+1)+"月" +d+"日"+hm;
		else
			return d+"th "+ this.MON_ENS[m] +hm;
	}
	
	let y = this.getFullYear() ;
	m ++ ;
	return y+"-"+((m<10)?("0"+m):(""+m))+"-"+((d<10)?("0"+d):(""+d)) +hm;
}
