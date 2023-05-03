import network

import time
import ujson
from machine import Timer
from microWebSrv import MicroWebSrv

# ----------------------------------------------------------------------------

@MicroWebSrv.route('/test')
def _httpHandlerTestGet(httpClient, httpResponse) :
    content = """\
    <!DOCTYPE html>
    <html lang=en>
        <head>
            <meta charset="UTF-8" />
            <title>TEST GET</title>
        </head>
        <body>
            <h1>TEST GET</h1>
            Client IP address = %s
            <br />
            <form action="/test" method="post" accept-charset="ISO-8859-1">
                First name: <input type="text" name="firstname"><br />
                Last name: <input type="text" name="lastname"><br />
                <input type="submit" value="Submit">
            </form>
        </body>
    </html>
    """ % httpClient.GetIPAddr()
    httpResponse.WriteResponseOk( headers         = None,
                                  contentType     = "text/html",
                                  contentCharset = "UTF-8",
                                  content          = content )


@MicroWebSrv.route('/test', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
    formData  = httpClient.ReadRequestPostedFormData()
    firstname = formData["firstname"]
    lastname  = formData["lastname"]
    content   = """\
    <!DOCTYPE html>
    <html lang=en>
        <head>
            <meta charset="UTF-8" />
            <title>TEST POST</title>
        </head>
        <body>
            <h1>TEST POST</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
    """ % ( MicroWebSrv.HTMLEscape(firstname),
            MicroWebSrv.HTMLEscape(lastname) )
    httpResponse.WriteResponseOk( headers         = None,
                                  contentType     = "text/html",
                                  contentCharset = "UTF-8",
                                  content          = content )


@MicroWebSrv.route('/edit/<index>')             # <IP>/edit/123           ->   args['index']=123
@MicroWebSrv.route('/edit/<index>/abc/<foo>')   # <IP>/edit/123/abc/bar   ->   args['index']=123  args['foo']='bar'
@MicroWebSrv.route('/edit')                     # <IP>/edit               ->   args={}
def _httpHandlerEditWithArgs(httpClient, httpResponse, args={}) :
    content = """\
    <!DOCTYPE html>
    <html lang=en>
        <head>
            <meta charset="UTF-8" />
            <title>TEST EDIT</title>
        </head>
        <body>
    """
    content += "<h1>EDIT item with {} variable arguments</h1>"\
        .format(len(args))
    
    if 'index' in args :
        content += "<p>index = {}</p>".format(args['index'])
    
    if 'foo' in args :
        content += "<p>foo = {}</p>".format(args['foo'])
    
    content += """
        </body>
    </html>
    """
    httpResponse.WriteResponseOk( headers         = None,
                                  contentType     = "text/html",
                                  contentCharset = "UTF-8",
                                  content          = content )

# ----------------------------------------------------------------------------
runState = 0
failureState = 0
tuigandist = 50
drvtuigan = [0, 0]
usensor = [0, 1]

gSocks = []


gc.collect()
print(gc.mem_free())

def mkJsonData(cmd, data):
    data1 = {}
    data1["cmd"] = cmd
    data1["data"] = data
    return ujson.dumps(data1)

def sndAllClnts(cmdstr):
    for i in range(0, len(gSocks)):
        gSocks[i].SendText(cmdstr)

def _acceptWebSocketCallback(webSocket, httpClient) :
    global gSocks
    print("WS ACCEPT")
    webSocket.RecvTextCallback   = _recvTextCallback
    webSocket.RecvBinaryCallback = _recvBinaryCallback
    webSocket.ClosedCallback      = _closedCallback
    gSocks.append(webSocket)
    webSocket.SendText(mkJsonData("usensor", usensor))
    webSocket.SendText(mkJsonData("failureState", [failureState]))
    webSocket.SendText(mkJsonData("runState", [runState]))
    webSocket.SendText(mkJsonData("dist", [tuigandist]))

def _recvTextCallback(webSocket, msg) :
    global runState
    print("WS RECV TEXT : %s" % msg)
    try:
        cmd = ujson.loads(msg)
        print(cmd)
    except:
        print('接收的不是json格式')
        return
    if (cmd["cmd"] == "runStart"):
        runState = cmd["data"]
        sndAllClnts(mkJsonData("runState", [runState]))
        return
    if (cmd["cmd"] == "toleft"):
        drvtuigan[1] = cmd["data"]
        sndAllClnts(mkJsonData("driver", drvtuigan))
        return
    if (cmd["cmd"] == "toright"):
        drvtuigan[0] = cmd["data"]
        sndAllClnts(mkJsonData("driver", drvtuigan))
        return
    if (cmd["cmd"] == "eval"):
        sndAllClnts(mkJsonData("eval", eval(cmd["data"])))
        return
    

def _recvBinaryCallback(webSocket, data) :
    print("WS RECV DATA : %s" % data)

def _closedCallback(webSocket) :
    global gSocks
    print("WS CLOSED")
    for i in range(0, len(gSocks)):
        if (gSocks[i] == webSocket):
            del gSocks[i]
            break
    #if (tim1 != None):
        #tim1.deinit()
        #del tim1

# ----------------------------------------------------------------------------

def creaWifi():
     
    # 为开发板创建网络，模式为STA模式
    wlan = network.WLAN(network.STA_IF) # create station interface
    # 激活STA
    wlan.active(True)       # activate the interface
    # ESP32开发板扫描网络
    wlan.scan()             # scan for access points
    # 判断是否连接。没连接上返回false
    #wlan.isconnected()      # check if the station is connected to an AP
    wlan.disconnect()                                 #Disconnect the last connected WiFi
    
    # 连接网络，ssid指WIFI名字，key指密码
    wlan.connect('your router ssid', 'router password') # connect to an AP
    waitcnt = 0
    while (wlan.ifconfig()[0] == '0.0.0.0'):
        waitcnt+=1
        yield(waitcnt)

    
    # 连接后，获取ESP32开发板的MAC地址
    print(wlan.config('mac'))      # get the interface's MAC address
    # 获取开发板的IP地址，子网掩码，网关，DNS
    print(wlan.ifconfig())         # get the interface's IP/netmask/gw/DNS addresses

#routeHandlers = [
#    ( "/test",    "GET",    _httpHandlerTestGet ),
#    ( "/test",    "POST",    _httpHandlerTestPost )
#]
def startWebSvr():
    srv = MicroWebSrv(bindIP="", port=8081, webPath='www/')
    srv.MaxWebSocketRecvLen     = 256
    srv.WebSocketThreaded        = False
    srv.AcceptWebSocketCallback = _acceptWebSocketCallback
    srv.Start()

# ----------------------------------------------------------------------------
initStep = 0
def chkInitSvr():
    global initStep, corWifi
    if (initStep == 2):
        return True
    if (initStep == 0):
        corWifi = creaWifi()
        initStep = 1
    try:
        print(next(corWifi))
        return False
    except StopIteration:
        pass
    #finally:
    del corWifi
    startWebSvr()
    initStep = 2
    #tim1.period(2000)
    return True

flushcnt = 0
gccnt = 0
def memmgr():
    global gccnt
    #计算内存占比
    mfree = int((gc.mem_free()/111168)*100)
    gccnt += 1
    if (gccnt < 2):
        return [100-mfree, mfree]
    gccnt = 0
    if (mfree < 40):
        gc.collect()
    return [100-mfree, mfree]

def tmrEvt1(t):
    global flushcnt
    if (not chkInitSvr()):
        return
    flushcnt+=1
    if (flushcnt < 2):
        return
    flushcnt = 0
    diststr = mkJsonData("dist", [50])
    memstr = mkJsonData("memRate", memmgr())
    #sndAllClnts(diststr)
    sndAllClnts(memstr)

t0 = time.ticks_ms()
chkInitSvr()
print(time.ticks_ms() - t0)
tim1 = Timer(2)
tim1.init(period=1000, mode=Timer.PERIODIC, callback=tmrEvt1)


