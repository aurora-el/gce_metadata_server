import os
from flask import Flask, request, jsonify, make_response, redirect
from config import Config
from directory import Directory, CustomEncoder, NotDir, TrailingSlash

app = Flask('gce_metadata_server')
app.config.from_object(Config())


@app.get('/project/<path:keys>')
def project(keys):
    return resolve(app.config['PROJECT'], iter(keys.split('/')))


@app.get('/instance/<path:keys>')
def instance(keys):
    data = resolve(app.config['INSTANCE'], iter(keys.split('/')))
    val, mime_type = display(data)
    res = make_response(val)
    res.mimetype = mime_type
    return res


def resolve(data, keys):
    try:
        for key in keys:
            if key == '':
                break
            if isinstance(data, Directory):
                data = data.get(key)
            else:
                raise KeyError(f'{data} is not a directory')
        else:
            if not isinstance(data, Directory):
                raise TypeError(f'{data} is not a directory')
        return data
    except NotDir as e:
        return make_response(e, 404)
    except TrailingSlash:
        return redirect(request.base_url.removesuffix('/') + request.query_string.decode())


def display(data, format_=None, recursive=False):
    if recursive:
        pass
    else:
        if type(data) in [list, dict]:
            if format_ == 'text':
                pass
            else:
                return CustomEncoder().encode(data), 'application/json'
        else:
            return str(data), 'text/plain'


if __name__ == '__main__':
    debug = os.environ.get('DEBUG')
    port = os.environ.get('PORT', '8080')
    if debug:
        app.run(host='localhost', port=port, debug=True)
    else:
        app.run(host='metadata.google.internal', port=port)
