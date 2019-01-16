import requests
import time
import mimetypes
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from decimal import Decimal

from .exceptions import (
  PageError, DisambiguationError, RedirectError, HTTPTimeoutError,
  WikiaException, ODD_ERROR_MESSAGE)
from .util import cache, stdout_encode, debug

# Generate all extensions from the OS
mimetypes.init()
API_URL = 'http://{lang}{sub_wikia}.wikia.com/api/v1/{action}'
# URL used when browsing the wikia proper
STANDARD_URL = 'http://{lang}{sub_wikia}.wikia.com/wiki/{page}'
LANG = ""
RATE_LIMIT = False
RATE_LIMIT_MIN_WAIT = None
RATE_LIMIT_LAST_CALL = None
USER_AGENT = 'wikia (https://github.com/NotThatSiri/DLD-Bot/wikia)'
def set_lang(language):
  '''
  Sets the global language variable, which is sent in the params
  '''
  global LANG
  LANG = language.lower() + '.' if language else ''

  for cached_func in (search, summary):
    cached_func.clear_cache()


def set_user_agent(user_agent_string):
  '''
  Set the User-Agent string to be used for all requests.
  Arguments:
  * user_agent_string - (string) a string specifying the User-Agent header
  '''
  global USER_AGENT
  USER_AGENT = user_agent_string


def set_rate_limiting(rate_limit, min_wait=timedelta(milliseconds=50)):
  '''
  Enable or disable rate limiting on requests to the wikia servers.
  If rate limiting is not enabled, under some circumstances (depending on
  load on Wikia, the number of requests you and other `wikia` users
  are making, and other factors), Wikia may return an HTTP timeout error.
  Enabling rate limiting generally prevents that issue, but please note that
  HTTPTimeoutError still might be raised.
  Arguments:
  * rate_limit - (Boolean) whether to enable rate limiting or not
  Keyword arguments:
  * min_wait - if rate limiting is enabled, `min_wait` is a timedelta describing the minimum time to wait before requests.
         Defaults to timedelta(milliseconds=50)
  '''
  global RATE_LIMIT
  global RATE_LIMIT_MIN_WAIT
  global RATE_LIMIT_LAST_CALL

  RATE_LIMIT = rate_limit
  if not rate_limit:
    RATE_LIMIT_MIN_WAIT = None
  else:
    RATE_LIMIT_MIN_WAIT = min_wait

  RATE_LIMIT_LAST_CALL = None


@cache
def search(sub_wikia, query, results=10):
  '''
  Do a Wikia search for `query`.
  Keyword arguments:
  * sub_wikia - the sub wikia to search in (i.e: "runescape", "elderscrolls")
  * results - the maxmimum number of results returned
  '''
  global LANG

  search_params = {
    'action': 'Search/List?/',
    'sub_wikia': sub_wikia,
    'lang': LANG,
    'limit': results,
    'query': query
  }

  raw_results = _wiki_request(search_params)

  try:
      search_results = (d['title'] for d in raw_results['items'])
  except KeyError as e:
      raise WikiaError("Could not locate page \"{}\" in subwikia \"{}\"".format(query,
                                                                            sub_wikia))
  return list(search_results)


def random(pages=1):
  '''
  Get a list of random Wikia article titles.
  .. note:: Random only gets articles from namespace 0, meaning no Category, U
  Keyword arguments:
  * pages - the number of random pages returned (max of 10)
  '''
  #http://en.wikia.org/w/api.php?action=query&list=random&rnlimit=5000&format=
  query_params = {
    'lang': LANG
  }

  request = _wiki_request(query_params)
  titles = [page['title'] for page in request['query']['random']]

  if len(titles) == 1:
    return titles[0]

  return titles


@cache
def summary(sub_wikia, title, chars=500, redirect=True):
  '''
  Plain text summary of the page from the sub-wikia.
  .. note:: This is a convenience wrapper - auto_suggest and redirect are enab
  Keyword arguments:
  * chars - if set, return only the first `chars` characters (limit is 500)
  * auto_suggest - let Wikia find a valid page title for the query
  * redirect - allow redirection without raising RedirectError
  '''

  # use auto_suggest and redirect to get the correct article
  # also, use page's error checking to raise DisambiguationError if necessary
  page_info = page(sub_wikia, title, redirect=redirect)
  title = page_info.title
  pageid = page_info.pageid

  query_params = {
    'action': 'Articles/Details?/',
    'sub_wikia': sub_wikia,
    'titles': title,
    'ids': pageid,
    'abstract': chars,
    'lang': LANG
  }

  request = _wiki_request(query_params)
  summary = request['items'][str(pageid)]['abstract']

  return summary


def page(sub_wikia, title=None, pageid=None, redirect=True, preload=False):
  '''
  Get a WikiaPage object for the page in the sub wikia with title `title` or the pageid
  `pageid` (mutually exclusive).
  Keyword arguments:
  * title - the title of the page to load
  * pageid - the numeric pageid of the page to load
  * redirect - allow redirection without raising RedirectError
  * preload - load content, summary, images, references, and links during initialization
  '''

  if title is not None:
    return WikiaPage(sub_wikia, title, redirect=redirect, preload=preload)
  elif pageid is not None:
    return WikiaPage(sub_wikia, pageid=pageid, preload=preload)
  else:
    raise ValueError("Either a title or a pageid must be specified")



class WikiaPage(object):
  '''
  Contains data from a Wikia page.
  Uses property methods to filter data from the raw HTML.
  '''

  def __init__(self, sub_wikia, title=None, pageid=None, redirect=True, preload=False, original_title=''):
    if title is not None:
      self.title = title
      self.original_title = original_title or title
    elif pageid is not None:
      self.pageid = pageid
    else:
      raise ValueError("Either a title or a pageid must be specified")

    self.sub_wikia = sub_wikia
    try:
        self.__load(redirect=redirect, preload=preload)
    except AttributeError as e:
        raise WikiaError("Could not locate page \"{}\" in subwikia \"{}\"".format(title or pageid,
                                                                           sub_wikia))
    if preload:
      for prop in ('content', 'summary', 'images', 'references', 'links', 'sections'):
        getattr(self, prop)

  def __repr__(self):
    return stdout_encode(u'<WikiaPage \'{}\'>'.format(self.title))

  def __eq__(self, other):
    try:
      return (
        self.pageid == other.pageid
        and self.title == other.title
        and self.url == other.url
      )
    except:
      return False

  def __load(self, redirect=True, preload=False):
    '''
    Load basic information from Wikia.
    Confirm that page exists and is not a disambiguation/redirect.
    Does not need to be called manually, should be called automatically during __init__.
    '''
    query_params = {
      'action': 'Articles/Details?/',
      'sub_wikia': self.sub_wikia,
      'lang': LANG,
    }
    if not getattr(self, 'pageid', None):
      query_params['titles'] = self.title
    else:
      query_params['ids'] = self.pageid

    try:
        request = _wiki_request(query_params)
        query = list(request['items'].values())[0]
    except (IndexError, requests.ConnectionError):
        raise WikiaError("Could not find page \"{}\" "
                         "of the sub-wikia \"{}\"".format(self.title or self.pageid,
                                                      self.sub_wikia))
    self.pageid = query['id']
    self.title = query['title']
    lang = query_params['lang']
    self.url = STANDARD_URL.format(lang=lang, sub_wikia=self.sub_wikia,
                                   page=self.title)

  def __continued_query(self, query_params):
    '''
    Based on https://www.mediawiki.org/wiki/API:Query#Continuing_queries
    '''
    query_params.update(self.__title_query_param)

    last_continue = {}
    prop = query_params.get('prop', None)

    while True:
      params = query_params.copy()
      params.update(last_continue)

      request = _wiki_request(params)

      if 'query' not in request:
        break

      pages = request['query']['pages']
      if 'generator' in query_params:
        for datum in pages.values():
          yield datum
      else:
        for datum in pages[self.pageid][prop]:
          yield datum

      if 'continue' not in request:
        break

      last_continue = request['continue']

  @property
  def __title_query_param(self):
    if getattr(self, 'title', None) is not None:
      return {'titles': self.title}
    else:
      return {'pageids': self.pageid}

  def html(self):
    '''
    Get full page HTML.
    .. warning:: This can get pretty slow on long pages.
    '''

    if not getattr(self, '_html', False):
      request = requests.get(self.url)
      self._html = request.text

    return self._html

  @property
  def content(self):
    '''
    Plain text content of each section of the page, excluding images, tables,
    and other data.
    '''
    if not getattr(self, '_content', False):
      query_params = {
        'action': "Articles/AsSimpleJson?/",
        'id': self.pageid,
        'sub_wikia': self.sub_wikia,
        'lang': LANG
      }

      request = _wiki_request(query_params)
      self._content = "\n".join(segment['text'] for section in request['sections']
                                                for segment in section['content']
                                                if segment['type'] == "paragraph")
    return self._content

  @property
  def revision_id(self):
    '''
    Revision ID of the page.
    The revision ID is a number that uniquely identifies the current
    version of the page. It can be used to create the permalink or for
    other direct API calls. See `Help:Page history
    <http://en.wikia.org/wiki/Wikia:Revision>`_ for more
    information.
    '''

    if not getattr(self, '_revid', False):
      query_params = {
        'action': "Articles/Details?/",
        'ids': self.pageid,
        'sub_wikia': self.sub_wikia,
        'lang': LANG
      }
      request = _wiki_request(query_params)
      self._revision_id = request['items'][str(self.pageid)]['revision']['id']

    return self._revision_id

  @property
  def summary(self):
    '''
    Plain text summary of the page.
    '''
    if not getattr(self, '_summary', False):
      self._summary = summary(self.sub_wikia, self.title)
    return self._summary

  @property
  def images(self):
    '''
    List of URLs of images on the page.
    '''

    if not getattr(self, '_images', False):
      # Get the first round of images
      query_params = {
        'action': "Articles/AsSimpleJson?/",
        'id': str(self.pageid),
        'sub_wikia': self.sub_wikia,
        'lang': LANG,
      }
      request = _wiki_request(query_params)
      images = [section['images'][0]['src'] for section in request["sections"]
                     if section['images']]

      # Get the second round of images
      # This time, have to use a different API call
      query_params['action'] = "Articles/Details?/"
      query_params['titles'] = self.title # This stops redirects
      request = _wiki_request(query_params)
      image_thumbnail = request["items"][str(self.pageid)]["thumbnail"]

      # Only if there are more pictures to grab
      if image_thumbnail:
        images.append(image_thumbnail)
        # A little URL manipulation is required to get the full sized version
        for index, image in enumerate(images):
          # Remove the /revision/ fluff after the image url
          image = image.partition("/revision/")[0]
          image_type = mimetypes.guess_type(image)[0]
          if image_type is not None:
            image_type = "." + image_type.split("/")[-1]
          else:
            image_type = ".png" # in case mimetypes.guess cant find it it will return None
          # JPEG has a special case, where sometimes it is written as "jpg"
          if image_type == ".jpeg" and image_type not in image:
            image_type = ".jpg"
          # Remove the filler around the image url that reduces the size
          image = "".join(image.partition(image_type)[:2])
          images[index] = image.replace("/thumb/", "/")
      self._images = images
    return self._images

  @property
  def related_pages(self):
    '''
    Lists up to 10 of the wikia URLs of pages related to this page.
    '''
    if not getattr(self, "_related_pages", False):
      query_params = {
        'action': "RelatedPages/List?/",
        'ids': self.pageid,
        'limit': 10,
        'sub_wikia': self.sub_wikia,
        'lang': LANG,
      }
      request = _wiki_request(query_params)
      self._related_pages = [request['basepath'] + url['url']
                            for url in request['items'][str(self.pageid)]]

    return self._related_pages

  @property
  def sections(self):
    '''
    List of section titles from the table of contents on the page.
    '''

    if not getattr(self, '_sections', False):
      query_params = {
        'action': 'Articles/AsSimpleJson?/',
        'id': self.pageid,
        'sub_wikia': self.sub_wikia,
        'lang': LANG,
      }

      request = _wiki_request(query_params)
      self._sections = [section['title'] for section in request['sections']]

    return self._sections

  def section(self, section_title):
    '''
    Get the plain text content of a section from `self.sections`.
    Returns None if `section_title` isn't found, otherwise returns a whitespace stripped string.
    This is a convenience method that wraps self.content.
    .. warning:: Calling `section` on a section that has subheadings will NOT return
           the full text of all of the subsections. It only gets the text between
           `section_title` and the next subheading, which is often empty.
    '''
    if section_title not in self.sections:
      return None

    query_params = {
      'action': "Articles/AsSimpleJson?/",
      'id': self.pageid,
      'sub_wikia': self.sub_wikia,
      'lang': LANG
    }

    request = _wiki_request(query_params)
    section = "\n".join(segment['text'] for section in request['sections']
                                        if section['title'] == section_title
                                        for segment in section['content']
                                        if segment['type'] == "paragraph")
    return section


  def section_lists(self, section_title):
    '''
    Get the plain text content of a section from `self.sections`.
    Returns None if `section_title` isn't found, otherwise returns a whitespace stripped string.
    This is a convenience method that wraps self.content.
    .. warning:: Calling `section` on a section that has subheadings will NOT return
           the full text of all of the subsections. It only gets the text between
           `section_title` and the next subheading, which is often empty.
    '''
    if section_title not in self.sections:
      return None

    query_params = {
      'action': "Articles/AsSimpleJson?/",
      'id': self.pageid,
      'sub_wikia': self.sub_wikia,
      'lang': LANG
    }

    request = _wiki_request(query_params)
    section = [section for section in request['sections'] if section['title'] == section_title][0]
    lists = [list['elements'] for list in section['content'] if list['type'] == 'list']
    list = [item['text'] for items in lists for item in items]
    return list


@cache
def languages():
  '''
  List all the currently supported language prefixes (usually ISO language code).
  Can be inputted to `set_lang` to change the Wikia that `wikia` requests
  results from.
  Returns: dict of <prefix>: <local_lang_name> pairs. To get just a list of prefixes,
  use `wikia.languages().keys()`.
  '''
  query_params = {
    'action': "WAM/WAMLanguages?/",
    'timestamp': time.time(), # Uses the UNIX timestamp to determine available LANGs
    'sub_wikia': '',
    'lang': LANG
  }
  request = _wiki_request(query_params)
  return response['languages']

def _wiki_request(params):
  '''
  Make a request to the Wikia API using the given search parameters.
  Returns a parsed dict of the JSON response.
  '''
  global RATE_LIMIT_LAST_CALL
  global USER_AGENT

  api_url = API_URL.format(**params)
  params['format'] = 'json'
  headers = {
    'User-Agent': USER_AGENT
  }

  if RATE_LIMIT and RATE_LIMIT_LAST_CALL and \
    RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT > datetime.now():

    # it hasn't been long enough since the last API call
    # so wait until we're in the clear to make the request

    wait_time = (RATE_LIMIT_LAST_CALL + RATE_LIMIT_MIN_WAIT) - datetime.now()
    time.sleep(int(wait_time.total_seconds()))

  r = requests.get(api_url, params=params, headers=headers)

  if RATE_LIMIT:
    RATE_LIMIT_LAST_CALL = datetime.now()

  # If getting the json representation did not work, our data is mangled
  try:
    r = r.json()
  except ValueError:
    raise WikiaError("Your request to the url \"{url}\" with the paramaters"
                     "\"{params}\" returned data in a format other than JSON."
                     "Please check your input data.".format(url=api_url,
                                                             params=params))
  # If we got a json response, then we know the format of the input was correct
  if "exception" in r:
    details, message, error_code= r['exception'].values()
    if error_code == 408:
      raise HTTPTimeoutError(query)
    raise WikiaError("{}. {} ({})".format(message, details, error_code))
  return r


class WikiaError(Exception):
    pass
