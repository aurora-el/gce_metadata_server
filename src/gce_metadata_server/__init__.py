import os
from flask import Flask, request, jsonify, make_response, redirect
from config import Config
from directory import Directory, CustomEncoder, NotDir, TrailingSlash, MissingSlash

app = Flask('gce_metadata_server')
app.config.from_object(Config())


@app.get('/<path:path>')
def get_metadata(path):
    loc, *keys = path.split('/')
    try:
        if loc not in ['project', 'instance']:
            raise NotDir(f'{loc} is not a valid metadata path')
        data = resolve(app.config[loc.upper()], keys)
        val, mime_type = display(data,
                                 recursive=bool(request.args.get('recursive')),
                                 format_=request.args.get('format'))
        res = make_response(val)
        res.mimetype = mime_type
        return res
    except NotDir as e:
        return make_response(e, 404)
    except TrailingSlash:
        return redirect(request.base_url.removesuffix('/') + request.query_string.decode())
    except MissingSlash:
        return redirect(request.base_url + '/' + request.query_string.decode())


def resolve(data, keys):
    for key in keys:
        if key == '':
            if isinstance(data, Directory):
                return data
            else:
                raise TrailingSlash(f'{data} is not a directory')
        elif isinstance(data, Directory):
            data = data.get(key)
        else:
            raise NotDir(f'{data} is not a directory')
    if isinstance(data, Directory):
        raise MissingSlash(f'{data} is a directory, to access its contents append a "/"')
    return data


def display(data, format_=None, recursive=False):
    if recursive and isinstance(data, Directory):
        if format_ == 'text':
            return '\n'.join(data.recurse()), 'text/plain'
        else:
            return CustomEncoder().encode(data), 'application/json'
    elif type(data) in [list, dict]:
        if format_ == 'text':
            return '\n'.join(data), 'text/plain'
        else:
            return CustomEncoder().encode(data), 'application/json'
    else:
        return str(data), 'text/plain'


def text_format(data):
    if isinstance(data, Directory):
        pass
    elif isinstance(data, list):
        pass
    elif isinstance(data, dict):
        pass
    else:
        str(data)


if __name__ == '__main__':
    debug = os.environ.get('DEBUG')
    port = os.environ.get('PORT', '8080')
    if debug:
        app.run(host='localhost', port=port, debug=True)
    else:
        app.run(host='metadata.google.internal', port=port)
