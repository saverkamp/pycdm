# Pycdm

Pycdm is a simple library for working with your CONTENTdm item and collection metadata as Python objects. Retrieve all metadata for an item and its pages with just a collection alias and item ID. 

    cookbook = pycdm.item('cookbooks', '2775')

Pycdm interfaces with the CONTENTdm 6 dmwebservices API to fetch metadata. You can also make direct calls to the API through the Api class:

    #returns a decoded json response for a dmGetItemInfo call
    call = Api()
    iteminfo = call.dmGetItemInfo('cookbooks', '2775')

# Installation

Pycdm works with Python 2.7x only (solely to make use of the collections.OrderedDict subclass, which preserves Node and Page object sequence within dictionaries).

Install with pip: 

    $ pip install pycdm

(or easy_install):

    $ easy_install pycdm

Open the pycdm.py file and replace the base and port variables with the base url and port of your CONTENTdm respository.

    base = 'http://yourbaseurl.edu'
    port = ':81'

# Examples

### Working with items and pages
#### Items
CONTENTdm items are one of three types: single page, compound object--document (a series of pages), or compound object--monograph (a series of pages organized into nodes, like a book divided into chapters). Calling the item() function creates an item object with attributes related to its descriptive and structural metadata. This includes:  

* descriptive metadata record (item.info, Python dict where key=field nickname)
* the Dublin Core metadata record (item.dcinfo, Python dict where key= DC field nickname)
* CONTENTdm identifier (item.id)
* the Collection object the item is part of (item.collection)
* the reference URL for the item (item.refurl)
* the page structure of theitem object (item.structure) 
* list of the item's constituent page objects (item.pages)

For single page items, you'll also get:  

* URL for the stored file for the page (item.fileurl)
* URL for the default scaled/cropped JPEG image of a page image. Use the GetImage() method to set the URL with different parameters (item.imageurl) 
* URL for the page thumbnail (item.thumburl)

To create an item object, use the item() call with collection alias and CONTENTdm item number:

    >>>letter = pycdm.item('leighhunt', '1566')

This is a document type compound object:

    >>>letter
    <pycdm.Document instance at 0x01972710>

Show the title of the item:

    >>>letter.info['title']
    u'Colburn Mayne letter to Leigh Hunt, September 30, 1850s'

Show the reference URL for the item:  

    >>> letter.refurl
    'http://digital.lib.uiowa.edu/cdm/ref/collection/leighhunt/id/1566'

####Pages
Creating an item object in pycdm also creates page objects for each page of the item. This includes some basic metadata for each page:  

* CONTENTdm identifier (.id)
* the page label (.label)
* the page's parent (item) identifier (.parentId)
* the pages parent node title (.parentnodetitle, defaults to parent item title if no parent node)
* the reference URL for the item (item.refurl)
* URL for the stored file for the page (item.fileurl)
* URL for the default scaled/cropped JPEG image of a page image. Use the GetImage() method to set the URL with different parameters (item.imageurl) 
* URL for the page thumbnail (item.thumburl)

Including the "pageinfo='on'" attribute in the item() call will retrieve all of its pages' record and Dublin Core metadata as well. (The default is "pageinfo='off'" to reduce unneccessary calls to the API):  

    >>>letter = pycdm.item('leighhunt', '1566', pageinfo='on')

Show the page labels for each page of the letter:

    >>> for p in letter.pages:
            p.label
    u'Page1'
    u'Page2'
    u'Page3'
    u'Page4'

Print the page transcriptions for each page of the letter:

    >>> for p in letter.pages:
        print p.label + ': ' + p.info['transc']
    
    Page1: September 30th  

    Dear Sir  

    Your kind letter followed me to the Co Wicklow, & reached, this morning, the Vicarage, where I am passing Michaelmas with my Brother in law a Church of England clergyman, attending church & was regularly as though I held all the Church of England doctrines; it was therefore the more refreshing to receive your few lines & learn from them that you were not displeased with my letter; In
          
    Page2: the strangers land the language we are familiar with sounds the sweetest, & I own that orthodoxy, however moderate, (as it is here) seems to cramp & restrain my feelings; I long to breathe a freer air, or to get into a Corner with a "Book for a Corner" that may send my thoughts abroad in sympathy with human nature in all its varying phases. I grieve to learn that you have been unwell, yet, as long as the mind preserves its [ ? ], & the spirits their freshness, bodily weakness may be borne cheerfully, as it is, I am certain by you. I am glad you will read my novel; you will see how carelessly it has been
          
    Page3: sent through the press, the truth is the publisher had no one to correct the proofs, & the thing was so new to me that my corrections but little improved them. this & other faults of the letter I trust you will not condemn, rather not condemn the books on their account, but look only to the Spirit in which there is I think something to please you. You will notice too that the feelings which prompted me to seek an interview with you at Hammersmith are of no recent date or hasty growth, & I trust the last chapter will not Cause you to dislike my hero & heroine for their taste in literature.
          
    Page4: I must not trespass longer on
    Your time and remain  
    Dear Sir 
    Yours very faithfully 
    Colburne Mayne  

### Working with collections and metadata fields
#### Collections
Creating an item instance also creates a corresponding collection object. A collection object's attributes include:  

* the collection alias (.alias)
* the collection name (.name)
* the URL for the digital collection (.url)
* the collection's metadata fields (.fields, a Python dict of field objects, where key=field nickname)
* the collection field mappings to Dublin Core (.dcmap, a Python dict, where key=field nickname)

Show an item's full collection name:  

    >>>leighhunt = letter.collection    #first put the item's collection attribute into a variable
    >>>leighhunt.name                   #then call the name attribute on the collection object 
    u'Leigh Hunt Letters'

    >>>letter.collection.name           #this works too
    u'Leigh Hunt Letters'

You can also create a collection object directly:

    >>>leighhunt = pycdm.Collection('leighhunt')

Calling the getItems() method on the collection will retrieve a list of all items identifiers in the collection and put it in the .item attribute:

    >>>leighhunt.getItems()
    >>>leighhunt.items
    ['51', '58', '63', '71', '76', '84', '89', '94', '99', '105', '110', '115', '125 ', '128', '141', '152', '156', '161', '166', '169', '173', '177', '183', '185', '194', '196', '199', '203', '206', '211', '214', '218', '223', '228', '262', '267', '272', '274', '277', '279', '283', '288', '294', '298', '303', '308', '311', '316', '321', '325', '330', '335', '339', '340', '344', '350', '355', '359', '362', '367', '370', '374', '379', '383', '388', '394', '399', '404', '409', '413'...]

Now you can iterate through every item in your collection (beware, this is A LOT of API calls):

    >>>for i in leighhunt.items:
            item = pycdm.item('leighhunt', i)

But maybe you just wanted to generate a list of all reference urls in the collection:

    >>>for i in leighhunt.items:
            print "http://digital.lib.uiowa.edu/cdm/ref/collection/leighhunt/id/" + i


####Fields
When a collection object is created, field objects are created for each of its metadata fields. Fields have full names and nicknames. When working with the API, nicknames are required for requesting field information in calls, but these nicknames can be hard to find within the admin interface. You can list all of the nicknames of field objects in a collection with Collection.fields, but that's not very readable:

    >>> leighhunt.fields
    {u'fullrs': <pycdm.Field instance at 0x020BD3F0>, u'relati': <pycdm.Field instance at 0x020BD3C8>, u'contac': <pycdm.Field instance at 0x020C31E8>, u'cited': <pycdm.Field instance at 0x020BDA30>, u'number': <pycdm.Field instance at 0x020C33C8>, u'dmrecord': <pycdm.Field instance at 0x020B34E0>, u'transd': <pycdm.Field instance at 0x020BDB98>, u'archiv': <pycdm.Field instance at 0x020BDAF8>, u'oclc': <pycdm.Field instance at 0x020BD378>, u'file': <pycdm.Field instance at 0x020C3468>, u'topica': <pycdm.Field instance at 0x02090A30>, u'topicb': <pycdm.Field instance at 0x02090C60>, u'transa': <pycdm.Field instance at 0x020BD300>, u'numbea': <pycdm.Field instance at 0x020C33F0>, u'transc': <pycdm.Field instance at 0x020BD828>, u'creato': <pycdm.Field instance at 0x02090508>, u'subjec': <pycdm.Field instance at 0x02090E40>, u'rights': <pycdm.Field instance at 0x020BD210>, u'dmoclcno': <pycdm.Field instance at 0x020BD3A0>, u'title': <pycdm.Field instance at 0x02081AF8>, u'publis': <pycdm.Field instance at 0x02090530>, u'find': <pycdm.Field instance at 0x020B3C60>, u'note': <pycdm.Field instance at 0x02090DF0>, u'source': <pycdm.Field instance at 0x02090A80>, u'transb': <pycdm.Field instance at 0x020BDE18>, u'typa': <pycdm.Field instance at 0x020BD2B0>, u'contri': <pycdm.Field instance at 0x020BD8F0>, u'typb': <pycdm.Field instance at 0x020BD4B8>, u'type': <pycdm.Field instance at 0x020B3C10>, u'descri': <pycdm.Field instance at 0x02090AD0>, u'promo': <pycdm.Field instance at 0x020BDDF0>, u'object': <pycdm.Field instance at 0x020C3378>, u'locati': <pycdm.Field instance at 0x020BDF08>, u'colleb': <pycdm.Field instance at 0x020BDD28>, u'collea': <pycdm.Field instance at 0x020BDF80>, u'date': <pycdm.Field instance at 0x020905F8>, u'data': <pycdm.Field instance at 0x020C3440>, u'dmmodified': <pycdm.Field instance at 0x020B3CB0>, u'dmcreated': <pycdm.Field instance at 0x020B3C88>, u'catalo': <pycdm.Field instance at 0x020BDD50>, u'chrono': <pycdm.Field instance at 0x020B3530>, u'corpor': <pycdm.Field instance at 0x02090EE0>, u'digitx': <pycdm.Field instance at 0x020BD878>, u'upload': <pycdm.Field instance at 0x020C3490>, u'place': <pycdm.Field instance at 0x02090E90>, u'digiti': <pycdm.Field instance at 0x020C3418>, u'width': <pycdm.Field instance at 0x020C3148>}

Listing just the nicknames by using .keys() makes this a little more readable:

    >>>leighhunt.fields.keys()
    [u'fullrs', u'relati', u'contac', u'cited', u'number', u'dmrecord', u'transd', u'archiv', u'oclc', u'file', u'topica', u'topicb', u'transa', u'numbea', u'transc', u'creato', u'subjec', u'rights', u'dmoclcno', u'title', u'publis', u'find', u'note', u'source', u'transb', u'typa', u'contri', u'typb', u'type', u'descri', u'promo', u'object', u'locati', u'colleb', u'collea', u'date', u'data', u'dmmodified', u'dmcreated', u'catalo', u'chrono', u'corpor', u'digitx', u'upload', u'place', u'digiti', u'width']

But this still doesn't show us the corresponding full names of each field.  

By looking into the field objects, we can learn more about a collection's fields. Attributes of fields include:  

* the alias of the collection (.alias)
* the CDM nickname of the field (.nick)
* the Dublin Core mapping of the field (.dc)
* obligation of the field, where required=1 (.req)
* if the field is hidden, hidden=1 (.hide)
* if the field is indexed, search=1 (.search)
* if the field has controlled vocabulary, vocab=1 (.vocab)
* a list of the field's controlled vocabulary terms (.vocabterms)

Show the nickname and full name of each field (we'll sort them, too) for :

    >>> for k, v in sorted(leighhunt.fields.items()):
        print k + ": " + v.name
        
    archiv: Archival Collection
    catalo: Cataloged by
    chrono: Chronological Subject
    cited: Letter Published In
    collea: Collection Guide
    colleb: Collection Identifier
    contac: Contact Information
    contri: Contributing Institution
    corpor: Corporate Name Subject
    creato: Creator
    data: Date Digital
    date: Date Original
    descri: Description
    digiti: Digitization Specifications
    digitx: Digital Collection
    dmcreated: Date created
    dmmodified: Date modified
    dmoclcno: OCLC number
    dmrecord: CONTENTdm number
    ...

We can also find the full name of a field from the collection object. List the full name of the 'date' field:

    >>> leighhunt.fields['date'].name
    u'Date Original'

Or the DC mapping. Get the Dublin Core mapping of the 'Topical Subject (LCSH)' ('topica') field:

    >>> leighhunt.dcmap['topica']
    u'subjec'

###CSV
Working with Unicode in Python is such a pain, isn't it? And much of the work you'll do with this library might involve dumping metadata into a CSV file in perfect UTF-8. The CSV object makes this a little easier by putting the work of creating a Unicode CSV writer in the library, so you dont have to.

Create a new CSV file to write to. Include a name for your file and a header row (optional):

    >>>f = pycdm.CSV('myfile.csv', header=['foo', 'bar', 'one', 'two'])

Then do your stuff. To write a row of data to the csv file (where row = [your, list, of, values]:

    >>>f.writerow(row)

Don't forget to close your file when you're finished:

    >>>f.close()

###A word of caution!
If you haven't ever worked with the API or you don't manage your CONTENTdm server, please have a heart-to-heart with your sysadmin before you begin. Once you start working with many items or collections at once, it's very easy to generate many API calls, possibly enough to help crash your server. Your sysadmin can help you hack responsibly or give you the keys to a test instance.   

# License

Copyright © 2012 Shawn Averkamp  <shawnaverkamp@gmail.com>

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

# Contributors

Thanks to Chad Nelson (bibliotechy) for help with dmGetCollections() and dmQuery().  
