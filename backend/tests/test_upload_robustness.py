import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import datastore, workspace, storage
from app.main import app, upload_dataset


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(datastore, "DATA_DIR", tmp_path)
    monkeypatch.setattr(datastore, "MANIFEST_PATH", tmp_path / "manifest.json")
    monkeypatch.setattr(workspace, "STORE_PATH", tmp_path / "workspace.json")
    return TestClient(app)


def test_truncation_and_unique_columns(isolated, monkeypatch):
    monkeypatch.setattr(datastore, "MAX_ROWS", 2)
    response = isolated.post('/api/datasets/upload', files={'file': ('test.csv', b'x, x,x_2\n1,2,3\n4,5,6\n7,8,9\n')})
    assert response.status_code == 200
    meta = response.json()
    assert meta['truncated'] is True
    assert meta['original_rows'] == 3
    assert meta['rows'] == 2
    assert len(set(meta['columns'])) == 3
    assert isolated.get('/api/datasets').json()[0]['truncated'] is True


def test_stream_limit_stops_reading(monkeypatch):
    monkeypatch.setattr(datastore, 'MAX_FILE_SIZE', 8)

    class Upload:
        filename = 'test.csv'
        reads = 0
        closed = False

        async def read(self, size):
            self.reads += 1
            return b'12345'

        async def close(self):
            self.closed = True

    upload = Upload()
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload_dataset(upload))
    assert error.value.status_code == 413
    assert upload.reads == 2
    assert upload.closed


def test_cascade_delete(isolated):
    dataset = datastore.save_upload('test.csv', b'x,y\n1,2\n')
    for kind in workspace.KINDS:
        workspace.add_record(kind, {'dataset_id': dataset['id']})
    response = isolated.delete('/api/datasets/' + dataset['id'])
    assert response.status_code == 200
    assert response.json()['removed'] == dict.fromkeys(workspace.KINDS, 1)
    assert all(not workspace.list_records(kind) for kind in workspace.KINDS)


def test_atomic_failure_preserves_original(tmp_path, monkeypatch):
    path = tmp_path / 'data.json'
    storage.atomic_json(path, {'old': True})

    def fail(*args):
        raise OSError('simulated replacement failure')

    monkeypatch.setattr(storage.os, 'replace', fail)
    with pytest.raises(OSError):
        storage.atomic_json(path, {'new': True})
    assert json.loads(path.read_text()) == {'old': True}
    assert list(tmp_path.iterdir()) == [path]


def test_concurrent_records_are_not_lost(isolated):
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda index: workspace.add_record('comments', {'dataset_id': 'test', 'body': str(index)}), range(24)))
    assert len(workspace.list_records('comments')) == 24


def test_file_source_does_not_claim_sync(isolated):
    dataset = datastore.save_upload('test.csv', b'x,y\n1,2\n')
    connection = workspace.add_record('connections', {'dataset_id': dataset['id']})
    response = isolated.get('/api/connections/' + connection['id'] + '/source')
    assert response.status_code == 200
    assert response.json()['live_sync'] is False
    assert 'synced_at' not in response.json()
    assert isolated.get('/api/connections/missing/source').status_code == 404


def test_excel_errors_are_generic(isolated):
    response = isolated.post('/api/datasets/upload', files={'file': ('broken.xlsx', b'not an excel file')})
    assert response.status_code == 400
    assert response.json()['detail'] == 'خواندن فایل اکسل ممکن نشد؛ قالب و سلامت فایل را بررسی کنید.'
