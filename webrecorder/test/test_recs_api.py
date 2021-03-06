import time
import os

from .testutils import BaseWRTests


# ============================================================================
class TestWebRecRecAPI(BaseWRTests):
    def test_home_page(self):
        res = self.testapp.get('/')
        assert 'Webrecorder' in res
        assert self.testapp.cookies == {}

    def test_create_anon_rec(self):
        res = self.testapp.post('/api/v1/recordings?user=@anon&coll=anonymous', params={'title': 'My Rec'})

        assert self.testapp.cookies['__test_sesh'] != ''

        assert res.json['recording']['id'] == 'my-rec'

        anon_user = self.get_anon_user()

        assert self.redis.exists('r:' + anon_user + ':anonymous:my-rec:info')

    def test_get_anon_rec(self):
        res = self.testapp.get('/api/v1/recordings/my-rec?user=@anon&coll=anonymous')

        assert res.json['recording']
        rec = res.json['recording']

        assert rec['size'] == 0
        assert rec['id'] == 'my-rec'
        assert rec['title'] == 'My Rec'
        assert rec['download_url'] == 'http://localhost:80/anonymous/my-rec/$download'
        assert rec['created_at'] == rec['updated_at']
        assert rec['created_at'] <= int(time.time())

    def test_create_another_anon_rec(self):
        res = self.testapp.post('/api/v1/recordings?user=@anon&coll=anonymous', params={'title': '2 Another! Recording!'})

        assert self.testapp.cookies['__test_sesh'] != ''

        assert res.json['recording']['id'] == '2-another-recording'

        anon_user = self.get_anon_user()

        assert self.redis.exists('r:' + anon_user + ':anonymous:2-another-recording:info')

    def test_list_all_recordings(self):
        res = self.testapp.get('/api/v1/recordings?user=@anon&coll=anonymous')

        recs = res.json['recordings']
        assert len(recs) == 2

        assert recs[0]['id'] == '2-another-recording'
        assert recs[0]['title'] == '2 Another! Recording!'
        assert recs[0]['download_url'] == 'http://localhost:80/anonymous/2-another-recording/$download'

        assert recs[1]['id'] == 'my-rec'
        assert recs[1]['title'] == 'My Rec'
        assert recs[1]['download_url'] == 'http://localhost:80/anonymous/my-rec/$download'

    def test_page_list_0(self):
        res = self.testapp.get('/api/v1/recordings/my-rec/pages?user=@anon&coll=anonymous')

        assert res.json == {'pages': []}

    def test_page_add_1(self):
        page = {'title': 'Example', 'url': 'http://example.com/', 'ts': '2016010203000000'}
        res = self.testapp.post('/api/v1/recordings/my-rec/pages?user=@anon&coll=anonymous', params=page)

        assert res.json == {}

    def test_page_list_1(self):
        res = self.testapp.get('/api/v1/recordings/my-rec/pages?user=@anon&coll=anonymous')

        assert res.json == {'pages': [{'title': 'Example', 'url': 'http://example.com/', 'ts': '2016010203000000'}]}

    def test_page_add_2(self):
        page = {'title': 'Example', 'url': 'http://example.com/foo/bar', 'ts': '2015010203000000'}
        res = self.testapp.post('/api/v1/recordings/my-rec/pages?user=@anon&coll=anonymous', params=page)

        assert res.json == {}

    def test_page_list_2(self):
        res = self.testapp.get('/api/v1/recordings/my-rec/pages?user=@anon&coll=anonymous')
        assert len(res.json['pages']) == 2
        assert {'title': 'Example', 'url': 'http://example.com/', 'ts': '2016010203000000'} in res.json['pages']
        assert {'title': 'Example', 'url': 'http://example.com/foo/bar', 'ts': '2015010203000000'} in res.json['pages']

    def test_collide_wb_url_format(self):
        res = self.testapp.post('/api/v1/recordings?user=@anon&coll=anonymous', params={'title': '2016'})
        assert res.json['recording']['id'] == '2016_'

    def test_collide_wb_url_format_2(self):
        res = self.testapp.post('/api/v1/recordings?user=@anon&coll=anonymous', params={'title': '2ab_'})
        assert res.json['recording']['id'] == '2ab__'

    def test_error_already_exists(self):
        res = self.testapp.post('/api/v1/recordings?user=@anon&coll=anonymous', params={'title': '2 Another Recording'}, status=400)
        assert res.json == {'error_message': 'Recording Already Exists', 'id': '2-another-recording', 'title': '2 Another! Recording!'}

    def test_error_no_such_rec(self):
        res = self.testapp.get('/api/v1/recordings/blah@$?user=@anon&coll=anonymous', status=404)
        assert res.json == {'error_message': 'Recording not found', 'id': 'blah@$'}

    def test_error_no_such_rec_pages(self):
        res = self.testapp.get('/api/v1/recordings/my-rec3/pages?user=@anon&coll=anonymous', status=404)
        assert res.json == {'error_message': 'Recording not found', 'id': 'my-rec3'}

        page = {'title': 'Example', 'url': 'http://example.com/foo/bar', 'ts': '2015010203000000'}
        res = self.testapp.post('/api/v1/recordings/my-rec3/pages?user=@anon&coll=anonymous', params=page, status=404)
        assert res.json == {'error_message': 'Recording not found', 'id': 'my-rec3'}

    def test_error_missing_user_coll(self):
        res = self.testapp.post('/api/v1/recordings', params={'title': 'Recording'}, status=400)
        assert res.json == {'error_message': "User must be specified"}

    def test_error_invalid_user_coll(self):
        res = self.testapp.post('/api/v1/recordings?user=user&coll=coll', params={'title': 'Recording'}, status=404)
        assert res.json == {"error_message": "No such user"}

