import doctest
import os
import sys
import tempfile
import time
import unittest

import tldextract
from tldextract import extract, urlsplit, TLDExtract

class ExtractTest(unittest.TestCase):
    tldextract_with_ttl = TLDExtract(cache_ttl_sec=30)

    def assertExtract(self, expected_subdomain, expected_domain, expected_tld, url, fns=(extract, urlsplit, tldextract_with_ttl)):
        for fn in fns:
          ext = fn(url)
          self.assertEquals(expected_subdomain, ext.subdomain)
          self.assertEquals(expected_domain, ext.domain)
          self.assertEquals(expected_tld, ext.tld)
        
    def test_american(self):
        self.assertExtract('www', 'google', 'com', 'http://www.google.com')
        
    def test_british(self):
        self.assertExtract("www", "theregister", "co.uk", "http://www.theregister.co.uk")
        
    def test_no_subdomain(self):
        self.assertExtract("", "gmail", "com", "http://gmail.com")
        
    def test_nested_subdomain(self):
        self.assertExtract("media.forums", "theregister", "co.uk", "http://media.forums.theregister.co.uk")

    def test_odd_but_possible(self):
        self.assertExtract('www', 'www', 'com', 'http://www.www.com')
        self.assertExtract('', 'www', 'com', 'http://www.com')

    def test_local_host(self):
        self.assertExtract('', 'wiki', '', 'http://wiki/')
        self.assertExtract('wiki', 'bizarre', '', 'http://wiki.bizarre')

    def test_qualified_local_host(self):
        self.assertExtract('', 'wiki', 'info', 'http://wiki.info/')
        self.assertExtract('wiki', 'information', '', 'http://wiki.information/')

    def test_ip(self):
        self.assertExtract('', '216.22.0.192', '', 'http://216.22.0.192/')
        self.assertExtract('216.22', 'project', 'coop', 'http://216.22.project.coop/')

    def test_empty(self):
        self.assertExtract('', '', '', 'http://')

    def test_scheme(self):
        self.assertExtract('mail', 'google', 'com', 'https://mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', 'ssh://mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', '//mail.google.com/mail')
        self.assertExtract('mail', 'google', 'com', 'mail.google.com/mail', fns=(extract,))

    def test_port(self):
        self.assertExtract('www', 'github', 'com', 'git+ssh://www.github.com:8443/')

    def test_username(self):
        self.assertExtract('1337', 'warez', 'com', 'ftp://johndoe:5cr1p7k1dd13@1337.warez.com:2501')

    def test_regex_order(self):
        self.assertExtract('www', 'parliament', 'uk', 'http://www.parliament.uk')
        self.assertExtract('www', 'parliament', 'co.uk', 'http://www.parliament.co.uk')

    def test_unhandled_by_iana(self):
        self.assertExtract('www', 'cgs', 'act.edu.au', 'http://www.cgs.act.edu.au/')
        self.assertExtract('www', 'google', 'com.au', 'http://www.google.com.au/')

    def test_tld_is_a_website_too(self):
        self.assertExtract('www', 'metp', 'net.cn', 'http://www.metp.net.cn')
        #self.assertExtract('www', 'net', 'cn', 'http://www.net.cn') # This is unhandled by the PSL. Or is it?

class TTLTest(unittest.TestCase):
    def test_cache_file_expiry(self):
        with tempfile.NamedTemporaryFile() as tmp:
          mtime = os.path.getmtime(tmp.name)
          extract = TLDExtract(cache_file=tmp.name)

          extract.cache_ttl_sec = 0
          time.sleep(1)
          extract('www.google.com')
          mtime_after_fetch = os.path.getmtime(tmp.name)
          self.assertTrue(mtime < mtime_after_fetch, str(mtime) + ' and ' + str(mtime_after_fetch))

          extract('www.yahoo.com')
          mtime_after_second_fetch = os.path.getmtime(tmp.name)
          self.assertEquals(mtime_after_fetch, mtime_after_second_fetch)

          extract.cache_ttl_sec = 1
          time.sleep(1.1)
          extract('www.bing.com')
          mtime_after_cache_expiry = os.path.getmtime(tmp.name)
          self.assertTrue(mtime_after_second_fetch < mtime_after_cache_expiry)

    def test_make_sense(self):
        self.assertRaises(ValueError, TLDExtract, fetch=False, cache_ttl_sec=1)

def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite(tldextract.tldextract),
        unittest.TestLoader().loadTestsFromTestCase(ExtractTest),
        unittest.TestLoader().loadTestsFromTestCase(TTLTest),
    ])

def run_tests(stream=sys.stderr):
    suite = test_suite()
    unittest.TextTestRunner(stream).run(suite)

if __name__ == "__main__":
    run_tests()

