import socket
import threading
import urllib
import urllib2


from Products.CMFCore.utils import getToolByName

from collective.logbook.config import PROP_KEY_WEBHOOK_URLS
from collective.logbook.config import WEBHOOK_HTTP_TIMEOUT

from collective.logbook.config import LOGGER as logger


class WebhookView(object):
    """
    Perform web hook HTTP POSTs.

    This view is called from events.py
    """

    def __call__(self, event):
        error = event.error
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        app = portal.getPhysicalRoot()
        urls = app.getProperty(PROP_KEY_WEBHOOK_URLS)

        if not urls:
            return

        subject = "[collective.logbook] NEW TRACEBACK: '%s'" % (
            error.get("value"))
        date = error.get("time").strftime("%Y-%m-%d %H:%M:%S"),
        traceback = "\n".join(error.get("tb_text").split("\n")[-3:])
        #error_number = error.get("id")
        error_url = error.get("url")
        logbook_url = (
            portal.absolute_url() + "/@@logbook?errornumber=%s" %
            error.get("id"))
        #req_html = error.get("req_html")

        message = "%s\n%s\n%s\n%s\n%s\n" % (
            subject, date, traceback,
            error_url, logbook_url)

        logger.info("Calling webhooks")
        logger.info("Webhook urls:\n%s" % ("\n".join(urls)))

        for url in urls:

            url = url.strip()

            # Emptry url
            if not url:
                continue

            t = UrlThread(url, {'data': message})
            t.start()


class UrlThread(threading.Thread):
    """
    A separate thread doing HTTP POST so we won't block when calling the webhook.
    """
    def __init__(self, url, data):
        threading.Thread.__init__(self)
        self.url = url
        self.data = data

    def run(self):
        orignal_timeout = socket.getdefaulttimeout()
        try:
            self.data = urllib.urlencode(self.data)
            socket.setdefaulttimeout(WEBHOOK_HTTP_TIMEOUT)
            r = urllib2.urlopen(self.url, self.data)
            r.read()
        except Exception as e:
            logger.error(e)
            logger.exception(e)
        finally:
            socket.setdefaulttimeout(orignal_timeout)
