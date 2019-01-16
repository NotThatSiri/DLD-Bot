"""
Global wikia exception and warning classes.
"""

import sys


ODD_ERROR_MESSAGE = "This shouldn't happen. Please report on GitHub: https://github.com/NotThatSiri/DLD-Bot"
class WikiaException(Exception):
  """Base Wikia exception class."""

  def __init__(self, error):
    self.error = error

  def __unicode__(self):
    return "An unknown error occured: \"{0}\". Please report it on GitHub!".format(self.error)

  if sys.version_info > (3, 0):
    def __str__(self):
      return self.__unicode__()

  else:
    def __str__(self):
      return self.__unicode__().encode('utf8')


class PageError(WikiaException):
  """Exception raised when no Wikia matched a query."""

  def __init__(self, pageid=None, *args):
    if pageid:
      self.pageid = pageid
    else:
      self.title = args[0]

  def __unicode__(self):
    if hasattr(self, 'title'):
      return u"\"{0}\" does not match any pages. Try another query!".format(self.title)
    else:
      return u"Page id \"{0}\" does not match any pages. Try another id!".format(self.pageid)


class DisambiguationError(WikiaException):
  """
  Exception raised when a page resolves to a Disambiguation page.
  The `options` property contains a list of titles
  of Wikia pages that the query may refer to.
  .. note:: `options` does not include titles that do not link to a valid Wikia page.
  """

  def __init__(self, title, may_refer_to):
    self.title = title
    self.options = may_refer_to

  def __unicode__(self):
    return u"\"{0}\" may refer to: \n{1}".format(self.title, '\n'.join(self.options))


class RedirectError(WikiaException):
  """Exception raised when a page title unexpectedly resolves to a redirect."""

  def __init__(self, title):
    self.title = title

  def __unicode__(self):
    return u"\"{0}\" resulted in a redirect. Set the redirect property to True to allow automatic redirects.".format(self.title)


class HTTPTimeoutError(WikiaException):
  """Exception raised when a request to the Mediawiki servers times out."""

  def __init__(self, query):
    self.query = query

  def __unicode__(self):
    return u"Searching for \"{0}\" resulted in a timeout. Try again in a few seconds, and make sure you have rate limiting set to True.".format(self.query)
