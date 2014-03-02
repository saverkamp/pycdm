#!/usr/bin/python

"""
Pycdm - Library for working with CONTENTdm item and collection metadata.

Copyright 2012 Shawn Averkamp  <shawnaverkamp@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import urllib2
import json
import csv
import cStringIO
import codecs
import collections as colls
from HTMLParser import HTMLParser

base = 'http://yourbaseurl.edu'
port = ':81'
collections = {}

def item(alias, id, pageinfo='off'):
    """Factory for creating Item subclass instances."""
    call = Api()
    info = call.dmGetItemInfo(alias, id)
    objinfo = call.dmGetCompoundObjectInfo(alias, id)
    parent = call.dmGetParent(alias, id)
    #initialize Collection object for alias and store in collections
    if alias not in collections:
        collections[alias] = Collection(alias)
    if ('code' in objinfo):
        if (str(parent) != '-1'):
            raise RuntimeError('ID entered is not an item')
        else:
            return SinglePageItem(alias, id, info, pageinfo)
    elif ('type' in objinfo):
        if (objinfo['type'] == 'Document' or objinfo['type'] == 'Document-PDF'):
            return Document(alias, id, info, objinfo, pageinfo)
        elif (objinfo['type'] == 'Monograph'):
            return Monograph(alias, id, info, objinfo, pageinfo)
        else:
            raise RuntimeError('error')


class Collection:
    """A CONTENTdm collection

    Attributes:
        name    The name of the digital collection
        alias   The CDM alias of the digital collection
        url     The URL for the digital collection
        fields  A dict of the collection's Field objects with field nickname as key
        dcmap   A dict of the collection field mapping to Qualified Dublin Core
        items   A list of ids for all items in the collection
    """
    def __init__(self, alias):
        call = Api()
        params = call.dmGetCollectionParameters(alias)
        fields = call.dmGetCollectionFields(alias)
        self.name = params['name']
        self.alias = alias
        urlparts = [base, alias]
        self.url = '/'.join(urlparts)
        # fields are structured as a dictionary of objects with nickname as key (nick:Field)
        self.fields = {}
        for f in fields:
            field = Field(alias, f)
            self.fields[field.nick] = field
        self.dcmap = {}
        # map field nicknames to dc nicknames, '' if no map
        for key, value in self.fields.items():
            if value.dc == '':
                self.dcmap[key] = ''
            else:
                self.dcmap[key] = value.dc

    def getItems(self, startnum='0', items=[]):
        """Get all item ids in a Collection."""
        call = Api()
        items = items
        itemscount = 0
        alias = self.alias
        itemsQuery = call.dmQuery('0', alias=alias, sortby='dmrecord', maxrecs='10000', start=startnum)
        itemscount = len(itemsQuery)
        for i in itemsQuery:
            items.append(i[1])
        if itemscount == 10000:
            startnum = str(itemscount + 1)
            self.getItems(startnum=startnum, items=items)
        self.items = items

class Field:
    """A Collection field

    Attributes:
        alias   The alias of the collection
        name    The full name of the field
        nick    The CDM nickname of the field
        dc      The Dublin Core mapping of the field
        req     Obligation of the field, required=1
        hide    Field is hidden, hidden=1
        search  Field is indexed, search=1
        vocab   Field has controlled vocabulary, vocab=1
        vocabterms  List of controlled vocabulary terms
    """
    def __init__(self, alias, fieldinfo):
        self.alias = alias
        self.name = fieldinfo['name']
        self.nick = fieldinfo['nick']
        self.dc = fieldinfo['dc']
        self.req = fieldinfo['req']
        self.hide = fieldinfo['hide']
        self.search = fieldinfo['search']
        self.vocab = fieldinfo['vocab']
        if self.vocab == 1:
            call = Api()
            terms = call.dmGetCollectionFieldVocabulary(alias, self.nick)
            if len(terms) >= 1:
                self.vocabterms = htmlunescape(terms)
            else:
                self.vocabterms = None
        else:
            self.vocabterms = None


class Item:
    """Abstract superclass for items"""
    def __init__(self, alias, id, info):
        pass

    def pages(self):
        pass
    def pageinfo(self):
        """Get page metadata (dmGetItemInfo) for all pages in an Item."""
        for p in self.pages:
            p.pageinfo()


class Singlepage:
    """Abstract superclass for single page objects."""
    def __init__(self):
        pass
    
    def getfileurl(self, alias, find):
        """Calls dmGetItemUrl to get resource url for .url files"""
        call = Api()
        if (find[-3:] == 'url'):
            url = call.dmGetItemUrl(alias, find)
            return url.replace('\r\n', '')
        else:
            return call.GetFile(alias, self.id, find)

    def GetImage(self, action='2', scale='scale', width='width', height='height', x='x', y='y', text='text', degrees='degrees'):
        """Builds url for retrieving downloadable version of image."""
        url = (base + '/utils/ajaxhelper/?CISOROOT=' + self.alias + '&CISOPTR=' + self.id + '&action=' + action + '&DMSCALE=' +
        scale + '&DMWIDTH=' + width + '&DMHEIGHT=' + height + '&DMX=' + x + '&DMY=' + y + '&DMTEXT=' + text + '&DMROTATE=' + degrees)
        self.imageurl = url
        return url

    def defaultimageurl(self):
        """Builds GetImage url using defaults"""
        call = Api()
        self.imageurl = call.GetImage(self.alias, self.id)


# abstract class Subitem
class Subitem:
    """Abstract superclass for constituent parts of items."""
    def __init__(self):
        pass


class SinglePageItem(Item, Singlepage):
    """Item, Singlepage subclass for single page items.

    Attributes:
        alias       The collection alias
        id          The CDM generated identifer of the item
        collection  The Collection object the item is part of 
        info        Dict of descriptive metadata for the item, where key=field nickname
        dcinfo      Dict of descriptive metadata for the item, where key=DC field name
        label       The label for the page
        file        The filename of the page file
        parentnodetitle     The title of the parent node (will always be empty for SinglePageItem)
        refurl      The CDM reference URL for the item
        fileurl     URL for the stored file for the page
        imageurl    URL for the default scaled/cropped JPEG image of a page image. Use GetImage() to 
                    set URL with different parameters 
        thumburl    URL for the page thumbnail
        pages       List of the item's consitutent page objects
    """
    def __init__(self, alias, id, info, pageinfo):
        self.alias = alias
        self.id = id
        #If not in collections dict, initialize Collection object for alias and store in collections
        if alias in collections:
            self.collection = collections[alias]
        else:
            collections[alias] = Collection(alias)
            self.collection = collections[alias]
        self.info = htmlunescape(info)
        self.dcinfo = dcinfo(alias, self.info)
        self.label = HTMLParser().unescape(info['title'])
        self.file = info['find']
        self.parentnodetitle = ''
        refurlparts = [base, 'cdm', 'ref', 'collection', alias, 'id', self.id]
        self.refurl = '/'.join(refurlparts)
        self.fileurl = self.getfileurl(alias, info['find'])
        self.imageurl = self.GetImage()
        thumburlparts = [base, 'utils/getthumbnail/collection', self.alias, 'id', self.id]
        self.thumburl = '/'.join(thumburlparts)
        self.pages = self.getPages()
    def getPages(self):
        """Return a list of page objects."""
        pages = []
        pages.append(self)
        return pages


class Document(Item):
    """Item subclass for CDM document compound objects.

    A Document is composed of a series of Pages.

    Attributes:
    alias       The collection alias
    id          The CDM generated identifer of the item
    collection  The Collection object the item is part of 
    info        Dict of descriptive metadata for the item, where key=field nickname
    dcinfo      Dict of descriptive metadata for the item, where key=DC field name
    refurl      The CDM reference URL for the item
    structure   The page structure of the Document object
    pages       List of the item's consitutent page objects
    """
    def __init__(self, alias, id, info, objinfo, pageinfo):
        self.alias = alias
        self.id = id
        self.info = htmlunescape(info)
        self.dcinfo = dcinfo(alias, self.info)
        #If not in collections dict, initialize Collection object for alias and store in collections
        if alias in collections:
            self.collection = collections[alias]
        else:
            collections[alias] = Collection(alias)
        refurlparts = [base, 'cdm', 'ref', 'collection', alias, 'id', self.id]
        self.refurl = '/'.join(refurlparts)
        self.structure = []
        for key, value in objinfo.items():
            if key == 'page':
                if type(value) == list:
                    for v in value:
                        page = Page(v, alias, self.id, self.info['title'], pageinfo)
                        self.structure.append(page)
                else:
                    page = Page(value, alias, self.id, self.info['title'], pageinfo)
                    self.structure.append(page)

        self.pages = self.getPages()
    def getPages(self):
        """Return a list of constituent page objects."""
        return self.structure


class Monograph(Item):
    """Item subclass for CDM Monograph compound objects.

    A Monograph is composed of any combination of Nodes and Pages

    Attributes:
    alias       The collection alias
    id          The CDM generated identifer of the item
    collection  The Collection object the item is part of 
    info        Dict of descriptive metadata for the item, where key=field nickname
    dcinfo      Dict of descriptive metadata for the item, where key=DC field name
    refurl      The CDM reference URL for the item
    structure   The node/page structure of the Monograph object
    pages       List of the item's consitutent page objects
    """
    def __init__(self, alias, id, info, objinfo, pageinfo):
        self.alias = alias
        self.id = id
        #If not in collections dict, initialize Collection object for alias and store in collections
        if alias in collections:
            self.collection = collections[alias]
        else:
            collections[alias] = Collection(alias)
        self.info = htmlunescape(info)
        self.dcinfo = dcinfo(alias, self.info)
        refurlparts = [base, 'cdm', 'ref', 'collection', alias, 'id', self.id]
        self.refurl = '/'.join(refurlparts)
        self.structure = []
        for key, value in objinfo.items():
            if key == 'node':
                subitem = Node(colls.OrderedDict(value), alias, self.id, pageinfo, self.info['title'])
                self.structure.append(subitem)
            elif key == 'page':
                subitem = Page(value, alias, self.id, pageinfo)
                self.structure.append(subitem)
        self.pages = self.getPages()
    def getPages(self):
        """Return a list of constituent page objects."""
        pages = []
        for s in self.structure:
            if isinstance(s, Page):
                pages.append(s)
            elif isinstance(s, Node):
                nodepages = s.getPages()
                pages.extend(nodepages)
            else:
                print 'none'
        return pages


class Node(Subitem):
    """Subitem subclass for aggregations of other Nodes and/or Pages.

        Attributes:
        alias       The collection alias
        structure   The node/page structure of the node
        nodetitle   The title of the node
        parentnodetitle     The title of the parent node
        parentId    The CDM generated identifier of the parent item
        pages       List of the node's consitutent page objects
        """
    def __init__(self, nodeinfo, alias, parentId, pageinfo, parenttitle):
        self.alias = alias
        self.structure = []
        self.parentId = parentId
        self.nodetitle = HTMLParser().unescape(nodeinfo['nodetitle'])
        self.parentnodetitle = parenttitle
        for key, value in nodeinfo.items():
            if (key == 'page'):
                if type(value) == list:
                    for item in value:
                        subitem = Page(item, alias, parentId, self.nodetitle, pageinfo)
                        self.structure.append(subitem)
                else:
                    subitem = Page(value, alias, parentId, self.nodetitle, pageinfo)
                    self.structure.append(subitem)
            elif (key == 'node'):
                if type(value) == list:
                    for item in value:
                        subitem = Node(item, alias, parentId, pageinfo, self.nodetitle)
                        self.structure.append(subitem)
                else:
                    subitem = Node(value, alias, parentId, pageinfo, self.nodetitle)
                    self.structure.append(subitem)
        self.pages = self.getPages()

    def getPages(self):
        """Returns a list of Page objects composing the Node."""
        pages = []
        for s in self.structure:
            if isinstance(s, Page):
                pages.append(s)
            elif isinstance(s, Node):
                nodepages = s.getPages()
                pages.extend(nodepages)
        return pages


class Page(Subitem, Singlepage):
    """Subitem, Singlepage subclass for consitutent Pages of compound objects.

    Attributes:
        alias       The collection alias
        id          The CDM generated identifer of the item
        info        Dict of descriptive metadata for the item, where key=field nickname (turned off by 
                    default. Retrive by calling pageinfo() or by setting pageinfo='on' when instantiating
                    the item)
        dcinfo      Dict of descriptive metadata for the item, where key=DC field name (turned off by 
                    default. Retrive by calling pageinfo() or by setting pageinfo='on' when instantiating
                    the item)
        label       The label for the page
        file        The filename of the page file
        parentnodetitle     The title of the parent node
        parentId    The CDM generated identifier of the parent item
        refurl      The CDM reference URL for the page
        fileurl     URL for the stored file for the page
        imageurl    URL for the default scaled/cropped JPEG image of a page image. Use GetImage() to 
                    set URL with different parameters 
        thumburl    URL for the page thumbnail
    """
    def __init__(self, objinfo, alias, parentId, parentnodetitle, pageinfo='off'):
        self.alias = alias
        self.id = objinfo['pageptr']
        self.label = HTMLParser().unescape(objinfo['pagetitle'])
        self.file = objinfo['pagefile']
        self.fileurl = self.getfileurl(alias, objinfo['pagefile'])
        self.parentnodetitle = parentnodetitle
        self.parentId = parentId
        refurlparts = [base, 'cdm', 'ref', 'collection', alias, 'id', self.id]
        self.refurl = '/'.join(refurlparts)
        call = Api()
        self.imageurl = call.GetImage(self.alias, self.id)
        thumburlparts = [base, 'utils/getthumbnail/collection', self.alias, 'id', self.id]
        self.thumburl = '/'.join(thumburlparts)
        if (pageinfo == 'on'):
            self.pageinfo()

    def pageinfo(self):
        """Calls dmGetItemInfo on pages to retrive page-level metadata."""
        call = Api()
        self.info = htmlunescape(call.dmGetItemInfo(self.alias, self.id))
        self.dcinfo = dcinfo(self.alias, self.info)

def dcinfo(alias, info):
    """Function for generating Dublin Core metadata."""
    dc = {}
    for key, value in info.items():
        if key in collections[alias].dcmap.keys():
            dcfield = collections[alias].dcmap[key]
            if dcfield not in dc.keys():
                dc[dcfield] = []
            for v in value.split(';'):
                if (v != '') and (v != ';'):
                    dc[dcfield].append(v.strip(';'))
    for key, value in dc.items():
        if len(value) > 1:
            dc[key] = ';'.join(value)
        elif len(value) == 1:
            dc[key] = value[0]
        else:
            dc[key] = ''
    return dc

def htmlunescape(obj):
    """Unescapes html entities in lists and dict values."""
    if isinstance(obj, dict):
        for key, value in obj.iteritems():
            obj[key] = HTMLParser().unescape(value)
        return obj
    if isinstance(obj, list):
        newlist = []
        for o in obj:
            newlist.append(HTMLParser().unescape(o))
        return newlist

class Api:
    """Class for interacting with the CDM Api.

    See: http://www.contentdm.org/help6/custom/customize2a.asp for full
    documentation on API calls.

    Attributes:
        base    The base url plus port for making calls to the CDM API
    """
    def __init__(self, base=base, port=port):
        self.base = base + port

    def dmGetDublinCoreFieldInfo(self, format='json'):
        """Calls dmGetDublinCoreFieldInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2e.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetDublinCoreFieldInfo', format]
        url = '/'.join(urlparts)
        dcinfo = urllib2.urlopen(url).read()
        return json.loads(dcinfo)

    def dmGetCollectionParameters(self, alias, format='json'):
        """Calls dmGetCollectionParameters and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2c.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionParameters', alias, format]
        url = '/'.join(urlparts)
        collparaminfo = urllib2.urlopen(url).read()
        return json.loads(collparaminfo)

    def dmGetCollectionFields(self, alias, format='json'):
        """Calls dmGetCollectionFields and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2d.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionFieldInfo', alias, format]
        url = '/'.join(urlparts)
        fieldinfo = urllib2.urlopen(url).read()
        return json.loads(fieldinfo)

    def dmGetCollectionFieldVocabulary(self, alias, field, format='json'):
        """Calls dmGetCollectionFieldVocabulary and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2q.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionFieldVocabulary', alias, field, format]
        url = '/'.join(urlparts)
        try:
            fieldvocab = urllib2.urlopen(url).read()
            return json.loads(fieldvocab)
        except ValueError:
            return []

    def dmGetItemInfo(self, alias, id, format='json'):
        """Calls dmGetItemInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2f.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetItemInfo', alias, id, format]
        url = '/'.join(urlparts)
        iteminfo = urllib2.urlopen(url).read()
        return json.loads(iteminfo, object_hook=empty_to_str)

    def dmGetCompoundObjectInfo(self, alias, id, format='json'):
        """Calls dmGetCompoundObjectInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2g.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCompoundObjectInfo', alias, id, format]
        url = '/'.join(urlparts)
        compoundinfo = urllib2.urlopen(url).read()
        return json.loads(compoundinfo, object_pairs_hook=colls.OrderedDict)

    def dmGetParent(self, alias, id, format='json'):
        """Calls GetParent and returns CDM item id of parent or '-1' if no parent.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2i.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=GetParent', alias, id, format]
        url = '/'.join(urlparts)
        parent = urllib2.urlopen(url).read()
        return json.loads(parent)['parent']
    
    def dmQuery(self, string, alias='all', field='CISOSEARCHALL', mode='exact', operator='and', maxrecs='10000',
        fields='title', sortby='nosort', start='1', suppress='1', docptr='0', suggest='0', facets='0',
        format='json', ret='items', sep="^"):
        """Calls dmQuery and returns a list of CDM item ids returned by the query.

        Set ret to 'response' to return json reponse instead.
        Full documentation at: http://www.contentdm.org/help6/custom/customize2h.asp"""
        string = string.replace(' ', '+')
        searchstrings = field + sep + string + sep + mode + sep + operator
        urlparts = [self.base, 'dmwebservices/index.php?q=dmQuery', alias, searchstrings, fields, sortby, maxrecs,
        start, suppress, docptr, suggest, facets, format]
        url = '/'.join(urlparts)
        query = urllib2.urlopen(url).read()
        response = json.loads(query, object_hook=empty_to_str)
        if ret == 'response':
            return response
        else:
            items = []
            for r in response['records']:
                alias = r['collection'].replace('/', '')
                id = str(r['pointer'])
                items.append((alias, id))
            return items

    def dmGetItemUrl(self, alias, find, format='json'):
        """Calls dmGetItemURL for a .url item and returns a URL for retrieving the resource.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2ae.asp"""
        if (find[-3:] == 'url'):
            urlparts = [self.base, 'dmwebservices', 'index.php?q=dmGetItemUrl', alias, find, format]
            url = '/'.join(urlparts)
            query = urllib2.urlopen(url).read()
            response = json.loads(query)
            return response['URL']

    
    def GetFile(self, alias, id, filename):
        """Calls GetFile and returns a URL for retrieving the file.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2ai.asp"""
        self.base = base
        urlparts = [self.base, 'utils/getfile/collection', alias, 'id', id, 'filename', filename]
        url = '/'.join(urlparts)
        return url
    
    def GetImage(self, alias, id, action='2', scale='scale', width='width', height='height', x='x', y='y', text='text',
     degrees='degrees'):
        """Calls GetImage and returns a URL for downloading a JPEG of the file.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2aj.asp"""
        url = (base + '/utils/ajaxhelper/?CISOROOT=' + alias + '&CISOPTR=' + id + '&action=' + action + '&DMSCALE=' + scale + '&DMWIDTH=' +
            width + '&DMHEIGHT=' + height + '&DMX=' + x + '&DMY=' + y + '&DMTEXT=' + text + '&DMROTATE=' + degrees)
        return url

    def GetThumbnail(self, alias, id):
        """Calls GetThunbnail and returns a URL for retrieving the thumbnail.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2ak.asp"""
        thumburlparts = [base, 'utils/getthumbnail/collection', alias, 'id', id]
        url = '/'.join(thumburlparts)
        return url

    def dmGetCollectionList(self, format='json'):
        """
         Calls dmGetCollectionList and returns a list of all visible collections.
         i
         Full documenation at http://www.contentdm.org/help6/custom/customize2b.asp
        """
        urlparts = [self.base , 'dmwebservices', 'index.php?q=dmGetCollectionList',format]
        url = '/'.join(urlparts)
        query = urllib2.urlopen(url).read()
        response = json.loads(query)
        return response

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding. Supports CSV()
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

class CSV:
    """A CSV object to make writing unicode data to CSV easier.

    Attributes:
    filename    The filename of the CSV file
    f           The CSV file
    wtr         A UnicodeWriter for the CSV file
    header      The header row of the CSV file (optional)
    """
    def __init__(self, filename, header=None):
        self.filename = filename
        self.f = open(self.filename, 'wb')
        self.wtr = UnicodeWriter(self.f)
        if header is not None:
            self.wtr.writerow(header)
        self.header = header

    def writerow(self, row):
        """Writes a row to the CSV file."""
        self.wtr.writerow(row)

    def close(self):
        """Closes the CSV file."""
        self.f.close()

def empty_to_str(obj):
    """Converts empty dicts to empty strings."""
    if len(obj) < 1:
        return ''
    else:
        return obj

if __name__ == "__main__":
    # a single page item
    single = item('calvin', '67')
    # a document
    document = item('leighhunt', '1566')
    # a monograph
    monograph = item('cwd', '20001')
