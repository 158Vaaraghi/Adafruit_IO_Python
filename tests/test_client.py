# Test REST client.
# Author: Tony DiCola (tdicola@adafruit.com)
import time
import unittest

from Adafruit_IO import Client, Data, Feed, Group, RequestError

import base


# Default config for tests to run against real Adafruit IO service with no proxy.
BASE_URL  = 'https://io.adafruit.com/'
PROXIES   = None

# Config to run tests against real Adafruit IO service over non-SSL and with a
# a proxy running on localhost 8888 (good for getting traces with fiddler).
#BASE_URL  = 'http://io.adafruit.vm/'
#PROXIES   = {'http': 'http://localhost:8888/'}


class TestClient(base.IOTestCase):

    # If your IP isn't put on the list of non-throttled IPs, uncomment the
    # function below to waste time between tests to prevent throttling.
    #def tearDown(self):
    #    time.sleep(30.0)

    def get_client(self):
        # Construct an Adafruit IO REST client and return it.
        return Client(self.get_test_username(), self.get_test_key(), proxies=PROXIES, base_url=BASE_URL)

    def ensure_feed_deleted(self, client, feed):
        # Delete the specified feed if it exists.
        try:
            client.delete_feed(feed)
        except RequestError:
            # Swallow the error if the feed doesn't exist.
            pass

    def ensure_group_deleted(self, client, group):
        # Delete the specified group if it exists.
        try:
            client.delete_group(group)
        except RequestError:
            # Swallow the error if the group doesn't exist.
            pass

    def empty_feed(self, client, feed):
        # Remove all the data from a specified feed (but don't delete the feed).
        data = client.data(feed)
        for d in data:
            client.delete(feed, d.id)

    def test_set_key_and_username(self):
        username = "unique_username"
        key = "unique_key_id"
        io = Client(username, key)
        self.assertEqual(username, io.username)
        self.assertEqual(key, io.key)

    def test_send_and_receive(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        response = io.send_data('TestFeed', 'foo')
        self.assertEqual(response.value, 'foo')
        data = io.receive('TestFeed')
        self.assertEqual(data.value, 'foo')

    def test_send_batch_data(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        feed = Feed(name="TestFeed")
        test_feed = aio.create_feed(feed)
        data_list = [Data(value='batch'), Data(value='batch')]
        io.send_batch_data(test_feed.key, 'foo')
        data = io.receive('TestFeed')
        self.assertEqual(data.value, 'batch')

    def test_receive_next(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        io.send_data('TestFeed', 1)
        data = io.receive_next('TestFeed')
        self.assertEqual(int(data.value), 1)

    # BUG: Previous jumps too far back: https://github.com/adafruit/io/issues/55
    @unittest.expectedFailure
    def test_receive_previous(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        io.send_data('TestFeed', 1)
        io.send_data('TestFeed', 2)
        io.receive_next('TestFeed')  # Receive 1
        io.receive_next('TestFeed')  # Receive 2
        data = io.receive_previous('TestFeed')
        self.assertEqual(int(data.value), 2)
        data = io.receive_previous('TestFeed')
        self.assertEqual(int(data.value), 1)

    def test_data_on_feed_returns_all_data(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        io.send_data('TestFeed', 1)
        io.send_data('TestFeed', 2)
        result = io.data('TestFeed')
        self.assertEqual(len(result), 2)
        self.assertEqual(int(result[0].value), 2)
        self.assertEqual(int(result[1].value), 1)

    def test_data_on_feed_and_data_id_returns_data(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        data = io.send_data('TestFeed', 1)
        result = io.data('TestFeed', data.id)
        self.assertEqual(data.id, result.id)
        self.assertEqual(int(data.value), int(result.value))

    def test_create_data(self):
        aio = self.get_client()
        self.ensure_feed_deleted(aio, 'TestFeed')
        feed = Feed(name="TestFeed")
        test_feed = aio.create_feed(feed)
        aio.send_data('TestFeed', 1)  # Make sure TestFeed exists.
        data = Data(value=42)
        result = aio.create_data('TestFeed', data)
        self.assertEqual(int(result.value), 42)

    def test_append_by_feed_name(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        feed = io.create_feed(Feed(name='TestFeed'))
        result = io.append('TestFeed', 42)
        self.assertEqual(int(result.value), 42)

    def test_append_by_feed_key(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'Test Feed Fancy Name')
        feed = io.create_feed(Feed(name='Test Feed Fancy Name'))
        result = io.append(feed.key, 42)
        self.assertEqual(int(result.value), 42)

    def test_append_by_feed_id(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        feed = io.create_feed(Feed(name='TestFeed'))
        result = io.append(feed.id, 42)
        self.assertEqual(int(result.value), 42)

    def test_create_feed(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        feed = Feed(name='TestFeed')
        result = io.create_feed(feed)
        self.assertEqual(result.name, 'TestFeed')

    def test_feeds_returns_all_feeds(self):
        io = self.get_client()
        io.send_data('TestFeed', 1)  # Make sure TestFeed exists.
        feeds = io.feeds()
        self.assertGreaterEqual(len(feeds), 1)
        names = set(map(lambda x: x.name, feeds))
        self.assertTrue('TestFeed' in names)

    def test_feeds_returns_requested_feed(self):
        io = self.get_client()
        io.send_data('TestFeed', 1)  # Make sure TestFeed exists.
        result = io.feeds('TestFeed')
        self.assertEqual(result.name, 'TestFeed')
        self.assertEqual(int(result.last_value), 1)

    def test_delete_feed(self):
        io = self.get_client()
        io.send_data('TestFeed', 'foo')  # Make sure a feed called TestFeed exists.
        io.delete_feed('TestFeed')
        self.assertRaises(RequestError, io.receive, 'TestFeed')

    def test_delete_nonexistant_feed_fails(self):
        io = self.get_client()
        self.ensure_feed_deleted(io, 'TestFeed')
        self.assertRaises(RequestError, io.delete_feed, 'TestFeed')

    def test_groups_returns_all_groups(self):
        io = self.get_client()
        groups = io.groups()
        self.assertGreaterEqual(len(groups), 1)
        names = set(map(lambda x: x.name, groups))
        self.assertTrue('GroupTest' in names)

    def test_groups_retrieves_requested_group(self):
        io = self.get_client()
        response = io.groups('GroupTest')
        self.assertEqual(response.name, 'GroupTest')
        self.assertEqual(len(response.feeds), 2)

    # BUG: Group create doesn't work: https://github.com/adafruit/io/issues/58
    @unittest.expectedFailure
    def test_create_group(self):
        io = self.get_client()
        self.ensure_group_deleted(io, 'GroupTest2')
        self.ensure_feed_deleted(io, 'GroupTest3')
        self.ensure_feed_deleted(io, 'GroupTest4')
        feed1 = io.create_feed(Feed(name='GroupTest3'))
        feed2 = io.create_feed(Feed(name='GroupTest4'))
        io.send_data('GroupTest3', 10)
        io.send_data('GroupTest4', 20)
        group = Group(name='GroupTest2', feeds=[feed1, feed2])
        response = io.create_group(group)
        self.assertEqual(response.name, 'GroupTest2')
        self.assertEqual(len(response.feeds), 2)

    # BUG: Group create doesn't work: https://github.com/adafruit/io/issues/58
    @unittest.expectedFailure
    def test_delete_group(self):
        io = self.get_client()
        self.ensure_group_deleted(io, 'GroupDeleteTest')
        group = io.create_group(Group(name='GroupDeleteTest'))
        io.delete_group('GroupDeleteTest')
        self.assertRaises(RequestError, io.groups, 'GroupDeleteTest')

    # TODO: Get by group name, key, and ID
    # TODO: Get data by name, key, ID
    # TODO: Tests around Adafruit IO keys (make multiple, test they work, etc.)
