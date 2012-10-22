#File pycdm.py

import urllib2
import json
import time
import collections

base = 'http://digital.lib.uiowa.edu'
port = ':81'


def item(alias, id, pageinfo='off'):
    """Factory for creating Item subclass instances."""
    call = Api()
    info = call.iteminfo(alias, id)
    objinfo = call.objectinfo(alias, id)
    parent = call.parent(alias, id)
    if ('code' in objinfo):
        if (str(parent) != '-1'):
            raise RuntimeError('ID entered is not an item')
        else:
            return SinglePageItem(alias, id, info, pageinfo)
    elif ('type' in objinfo):
        if (objinfo['type'] == 'Document'):
            return Document(alias, id, info, objinfo, pageinfo)
        elif (objinfo['type'] == 'Monograph'):
            return Monograph(alias, id, info, objinfo, pageinfo)
        else:
            raise RuntimeError('error')


class Collection:
    """A CONTENTdm collection"""
    def __init__(self, alias):
        call = Api()
        params = call.collectionparameters(alias)
        fields = call.collectionfieldinfo(alias)
        self.name = params['name']
        self.alias = alias
        # fields are structured as a dictionary of objects with nickname as key (nick:Field)
        self.fields = {}
        for f in fields:
            field = Field(alias, f)
            self.fields[field.nick] = field
        self.dcmap = {}
        # map field nicknames to dc nicknames, None if no map
        for key, value in self.fields.items():
            if value.dc == 'BLANK':
                self.dcmap[key] = None
            else:
                self.dcmap[key] = value.dc


class Field:
    """A Collection field"""
    def __init__(self, alias, fieldinfo):
        self.alias = alias
        self.name = fieldinfo['name']
        self.nick = fieldinfo['nick']
        self.dc = fieldinfo['dc']
        self.req = fieldinfo['req']
        self.vocab = fieldinfo['vocab']
        self.hide = fieldinfo['hide']
        self.search = fieldinfo['search']


class Item:
    """Abstract superclass for items"""
    def __init__(self, alias, id, info):
        pass

    def pages(self):
        pass
    def pageinfo(self):
        """Call Page.pageinfo on all pages in an Item."""
        for p in self.pages():
            p.pageinfo()


class Singlepage:
    """Abstract superclass for single page objects."""
    def __init__(self):
        pass
    
    def getimageurl(self, action='2', scale='scale', width='width', height='height', x='x', y='y', text='text', degrees='degrees'):
        url = (base + '/utils/ajaxhelper/?CISOROOT=' + self.alias + '&CISOPTR=' + self.id + '&action=' + action + '&DMSCALE=' +
        scale + '&DMWIDTH=' + width + '&DMHEIGHT=' + height + '&DMX=' + x + '&DMY=' + y + '&DMTEXT=' + text + '&DMROTATE=' + degrees)
        self.imageurl = url
        return url

    def defaultimageurl(self):
        call = Api()
        self.imageurl = call.getimageurl(self.alias, self.id)


# abstract class Subitem
class Subitem:
    """Abstract superclass for constituent parts of items."""
    def __init__(self):
        pass


class SinglePageItem(Item, Singlepage):
    """Item, Singlepage subclass for single page items."""
    def __init__(self, alias, id, info, pageinfo):
        self.alias = alias
        self.id = id
        self.info = info
        self.label = info['title']
        self.file = info['find']
        self.parentnode = None
        refurlparts = [base, alias, self.id]
        self.refurl = '/'.join(refurlparts)
        fileURLparts = [base, 'utils/getfile/collection', self.alias, 'id', self.id, 'filename', self.file]
        self.fileurl = '/'.join(fileURLparts)
        self.imageurl = self.getimageurl()
    def pages(self):
        pages = []
        pages.append(self)
        return pages


class Document(Item):
    """Item subclass for CDM document compound objects.

    A Document is composed of a series of Pages."""
    def __init__(self, alias, id, info, objinfo, pageinfo):
        self.alias = alias
        self.id = id
        self.info = info
        refurlparts = [base, alias, self.id]
        self.refurl = '/'.join(refurlparts)
        self.structure = []
        for o in objinfo['page']:
            page = Page(o, alias, self.id, self.info['title'], pageinfo)
            self.structure.append(page)
    def pages(self):
        return self.structure


class Monograph(Item):
    """Item subclass for CDM Monograph compound objects.

    A Monograph is composed of any combination of Nodes and Pages"""
    def __init__(self, alias, id, info, objinfo, pageinfo):
        self.alias = alias
        self.id = id
        self.info = info
        self.structure = []
        refurlparts = [base, alias, self.id]
        self.refurl = '/'.join(refurlparts)
        for key, value in objinfo.items():
            if key == 'node':
                subitem = Node(collections.OrderedDict(value), alias, self.id, pageinfo)
                self.structure.append(subitem)
            elif key == 'page':
                subitem = Page(value, alias, self.id, pageinfo)
                self.structure.append(subitem)
    def pages(self):
        pages = []
        for s in self.structure:
            if isinstance(s, Page):
                pages.append(s)
            elif isinstance(s, Node):
                nodepages = s.pages()
                pages.extend(nodepages)
            else:
                print 'none'
        return pages


class Node(Subitem):
    """Subitem subclass for aggregations of other Nodes and/or Pages."""
    def __init__(self, nodeinfo, alias, parent, pageinfo):
        self.alias = alias
        self.structure = []
        self.nodetitle = nodeinfo['nodetitle']
        for key, value in nodeinfo.items():
            if (key == 'page'):
                if type(value) == list:
                    for item in value:
                        subitem = Page(item, alias, parent, self.nodetitle, pageinfo)
                        self.structure.append(subitem)
                else:
                    subitem = Page(value, alias, parent, self.nodetitle, pageinfo)
                    self.structure.append(subitem)
            elif (key == 'node'):
                if type(value) == list:
                    for item in value:
                        subitem = Node(item, alias, parent, pageinfo)
                        self.structure.append(subitem)
                else:
                    subitem = Node(value, alias, parent, pageinfo)
                    self.structure.append(subitem)

    def pages(self):
        """Returns a list of Page objects composing the Node."""
        pages = []
        for s in self.structure:
            if isinstance(s, Page):
                pages.append(s)
            elif isinstance(s, Node):
                nodepages = s.pages()
                pages.extend(nodepages)
        return pages


class Page(Subitem, Singlepage):
    """Subitem, Singlepage subclass for consitutent Pages of compound objects."""
    def __init__(self, objinfo, alias, parent, parentnode, base=base, pageinfo='off'):
        self.alias = alias
        self.id = objinfo['pageptr']
        self.label = objinfo['pagetitle']
        self.file = objinfo['pagefile']
        self.parentnode = parentnode
        self.parent = parent
        refurlparts = [base, alias, self.id]
        self.refurl = '/'.join(refurlparts)
        call = Api()
        self.fileurl = call.getfileurl(self.alias, self.id, self.file)
        self.imageurl = call.getimageurl(self.alias, self.id)
        if (pageinfo == 'on'):
            self.pageinfo()
    def pageinfo(self):
        call = Api()
        self.info = call.iteminfo(self.alias, self.id)


class Api:
    """Class for interacting with the CDM Api.

    See: http://www.contentdm.org/help6/custom/customize2a.asp for full
    documentation on API calls."""
    def __init__(self, base=base, port=port):
        self.base = base + port

    def dublincorefieldinfo(self, format='json'):
        """Calls dmGetDublinCoreFieldInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2e.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetDublinCoreFieldInfo', format]
        url = '/'.join(urlparts)
        dcinfo = urllib2.urlopen(url).read()
        return json.loads(dcinfo)

    def collectionparameters(self, alias, format='json'):
        """Calls dmGetCollectionParameters and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2c.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionParameters', alias, format]
        url = '/'.join(urlparts)
        collparaminfo = urllib2.urlopen(url).read()
        return json.loads(collparaminfo)

    def collectionfieldinfo(self, alias, format='json'):
        """Calls dmGetCollectionFields and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2d.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionFieldInfo', alias, format]
        url = '/'.join(urlparts)
        fieldinfo = urllib2.urlopen(url).read()
        return json.loads(fieldinfo)

    def fieldvocab(self, alias, field, format='json'):
        """Calls dmGetCollectionFieldVocabulary and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2q.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCollectionFieldVocabulary', alias, field, format]
        url = '/'.join(urlparts)
        fieldvocab = urllib2.urlopen(url).read()
        return json.loads(fieldvocab)

    def iteminfo(self, alias, id, format='json'):
        """Calls dmGetItemInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2f.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetItemInfo', alias, id, format]
        url = '/'.join(urlparts)
        iteminfo = urllib2.urlopen(url).read()
        return json.loads(iteminfo)

    def objectinfo(self, alias, id, format='json'):
        """Calls dmGetCompoundObjectInfo and returns json response.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2g.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=dmGetCompoundObjectInfo', alias, id, format]
        url = '/'.join(urlparts)
        compoundinfo = urllib2.urlopen(url).read()
        return json.loads(compoundinfo, object_pairs_hook=collections.OrderedDict)

    def parent(self, alias, id, format='json'):
        """Calls GetParent and returns CDM item id of parent or '-1' if no parent.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2i.asp"""
        urlparts = [self.base, 'dmwebservices/index.php?q=GetParent', alias, id, format]
        url = '/'.join(urlparts)
        parent = urllib2.urlopen(url).read()
        return json.loads(parent)['parent']
    
    def query(self, string, alias='all', field='CISOSEARCHALL', mode='exact', operator='and', maxrecs='1024',
        fields='title', sortby='nosort', start='1', suppress='1', docptr='0', suggest='0', facets='0',
        format='json', ret='items'):
        """Calls dmQuery and returns a list of CDM item ids returned by the query.

        Set ret to 'response' to return json reponse instead.
        Full documentation at: http://www.contentdm.org/help6/custom/customize2h.asp"""
        string = string.replace(' ', '+')
        searchstrings = field + '^' + string + '^' + mode + '^' + operator
        urlparts = [self.base, 'dmwebservices/index.php?q=dmQuery', alias, searchstrings, fields, sortby, maxrecs,
        start, suppress, docptr, suggest, facets, format]
        url = '/'.join(urlparts)
        query = urllib2.urlopen(url).read()
        response = json.loads(query)
        if ret == 'response':
            return response
        else:
            items = []
            for r in response['records']:
                items.append(r['pointer'])
            return items
    
    def getfileurl(self, alias, id, filename):
        """Calls GetFile and returns a URL for retrieving the file.""

        Full documentation at: http://www.contentdm.org/help6/custom/customize2ai.asp"""
        self.base = base
        urlparts = [self.base, 'utils/getfile/collection', alias, 'id', id, 'filename', filename]
        url = '/'.join(urlparts)
        return url
    
    def getimageurl(self, alias, id, action='2', scale='scale', width='width', height='height', x='x', y='y', text='text',
     degrees='degrees'):
        """Calls GetImage and returns a URL for downloading a JPEG of the file.

        Full documentation at: http://www.contentdm.org/help6/custom/customize2aj.asp"""
        url = (base + '/utils/ajaxhelper/?CISOROOT=' + alias + '&CISOPTR=' + id + '&action=' + action + '&DMSCALE=' + scale + '&DMWIDTH=' +
            width + '&DMHEIGHT=' + height + '&DMX=' + x + '&DMY=' + y + '&DMTEXT=' + text + '&DMROTATE=' + degrees)
        return url


if __name__ == "__main__":
    # a single page item
    single = item('calvin', '67')
    # a document
    document = item('leighhunt', '1566')
    # a monograph
    monograph = item('kinnick', '3077')
