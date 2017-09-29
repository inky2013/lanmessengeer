from cefpython3 import cefpython as cef
import base64
from threading import Thread
import sys


def html_to_data_uri(html, js_callback=None):
    html = html.encode("utf-8", "replace")
    b64 = base64.b64encode(html).decode("utf-8", "replace")
    ret = "data:text/html;base64,{data}".format(data=b64)
    if not js_callback:
        return ret
    js_callback.Call(ret)


def set_javascript_bindings(browser, externals=None):
    if externals is None:
        externals = list()
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    bindings.SetFunction("html_to_data_uri", html_to_data_uri)
    for x in range(len(externals)):
        bindings.SetObject(externals[x][0], externals[x][1])
    browser.SetJavascriptBindings(bindings)


class External:
    def __init__(self, browser):
        self.browser = browser


def get_browser(window_name, html_string, handlers):
    sys.excepthook = cef.ExceptHook
    cef.Initialize(settings={})
    browser = cef.CreateBrowserSync(url=html_to_data_uri(html_string), window_title=window_name)
    set_javascript_bindings(browser, handlers)

    return browser


def get_start():
    def fn():
        cef.MessageLoop()
        cef.Shutdown()
    return fn