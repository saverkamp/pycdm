# Pycdm

Pycdm is a simple library for working with your CONTENTdm item and collection metadata as Python objects. Retrieve all metadata for an item and its pages with just a collection alias and item ID. 

    cookbook = pycdm.item('cookbooks', '2775')

Pycdm interfaces with the CONTENTdm 6 dmwebservices API to fetch metadata. You can also make direct calls to the API through the Api class:

    #returns a decoded json response for a dmGetItemInfo call
    call = Api()
    iteminfo = call.dmGetItemInfo('cookbooks', '2775')

# Installation

Pycdm works with Python 2.7x only (solely to make use of the collections.OrderedDict subclass, which preserves Node and Page object sequence within dictionaries).

Install with pip (or easy_install):

    $ pip pycdm

Open the pycdm.py file and replace the base variable with the base url of your CONTENTdm respository. You'll also want to swap out the arguments in the test code for items of your own.

# Examples

Retrieve metadata for an item:

    >>>letter = pycdm.item('leighhunt', '1566')

This is a document type compound object:

    >>>letter
    <pycdm.Document instance at 0x01972710>

Creating an item instance also creates a corresponding collection instance:

    >>>leighhunt = letter.collection
    >>>leighhunt.name
    u'Leigh Hunt Letters'

List all of the fields (by nickname) for a collection:

    >>>leighhunt.fields.keys()
    [u'fullrs', u'relati', u'contac', u'cited', u'number', u'dmrecord', u'transd', u'archiv', u'oclc', u'file', u'topica', u'topicb', u'transa', u'numbea', u'transc', u'creato', u'subjec', u'rights', u'dmoclcno', u'title', u'publis', u'find', u'note', u'source', u'transb', u'typa', u'contri', u'typb', u'type', u'descri', u'promo', u'object', u'locati', u'colleb', u'collea', u'date', u'data', u'dmmodified', u'dmcreated', u'catalo', u'chrono', u'corpor', u'digitx', u'upload', u'place', u'digiti', u'width']

List the full name of the date field:

    >>> leighhunt.fields['date'].name
    u'Date Original'

Get the Dublin Core mapping of the Topical Subject (LCSH) field:

    >>> leighhunt.dcmap['topica']
    u'subjec'

Back to that letter, get the page labels for each page:

    >>> for p in letter.pages:
            p.label
    u'Page1'
    u'Page2'
    u'Page3'
    u'Page4'

More documentation and examples coming soon...

# License

Copyright © 2012 Shawn Averkamp  <shawn-averkamp@uiowa.edu>

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

