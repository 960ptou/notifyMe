from pymongo import MongoClient
from datetime import datetime

class NotifyDB:
    def __init__(self, client : MongoClient, dbname):
        self.db = client[dbname]
        self.collection = self.db['sites']  # The collection to store site data
        self.collection.create_index('url', unique=True)

    def get_all_links(self):
        """Return all existing site links."""
        return [doc['url'] for doc in self.collection.find({}, {'_id': 0, 'url': 1})]
    
    def get_all(self):
        return list(self.collection.find({}, {'_id': 0}))

    def post(self, site, title, content):
        """Add a new site."""
        if self.collection.find_one({'url': site}):
            raise ValueError(f"Site '{site}' already exists.")
        self.collection.insert_one({
            'url': site,
            'title': title,
            'last-search': datetime.now(),
            'latest-search-content': content,
            'latest-updated-date' : None
        })

    def delete(self, site):
        """Remove a site."""
        result = self.collection.delete_one({'url': site})
        if result.deleted_count == 0:
            raise ValueError(f"Site '{site}' not found.")

    def put(self, site, title=None, content=None):
        """Update site details."""
        # Build the update structure dynamically

        update_fields = {'last-search': datetime.now()}  # Always update last-search
        if title is not None:
            update_fields['title'] = title
        if content is not None:
            update_fields['latest-search-content'] = content

        if (title is not None) and (content is not None):
            update_fields['latest-updated-date'] = update_fields['last-search']

        # Perform the update
        result = self.collection.update_one(
            {'url': site},
            {'$set': update_fields}
        )
        if result.matched_count == 0:
            raise ValueError(f"Site '{site}' not found.")

    def get(self, site):
        """Get a single site's information."""
        doc = self.collection.find_one({'url': site}, {'_id': 0})
        if not doc:
            raise ValueError(f"Site '{site}' not found.")
        return doc



class PoppingDB:
    # this is to be used with Notify DB
    def __init__(self, client : MongoClient, dbname, notifiyDB : NotifyDB):
        self.db = client[dbname]
        self.collection = self.db['pending']
        self.collection.create_index('url', unique=True)
        self.ndb = notifiyDB

    def post(self, url):
        result = None
        try:
            result = self.ndb.get(url)
        except ValueError:
            # if not in ndb
            result = None

        if (result is not None) or (self.collection.find_one({'url': url}, {'_id': 0}) is not None):
            raise ValueError(f"Site {url} already exist in DB")

        self.collection.insert_one({
            'url' : url
        })

    def delete(self, url):
        """Remove a site."""
        result = self.collection.delete_one({'url': url})
        if result.deleted_count == 0:
            raise ValueError(f"Site '{url}' not found.")
        
    def get_all_url(self):
        return [doc['url'] for doc in self.collection.find({}, {'_id': 0, 'url': 1})]

    def __iter__(self):
        all_current_url = self.get_all_url()

        for url in all_current_url:
            yield url
            self.delete(url)