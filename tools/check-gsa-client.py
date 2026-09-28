#!/usr/bin/env python3
"""Run the generated GSA factory against a local HTTP/1.1 keep-alive server."""
import http.server
from pathlib import Path
import re
import subprocess
import tempfile
import threading


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    next_id = 0

    def setup(self):
        super().setup()
        type(self).next_id += 1
        self.connection_id = type(self).next_id

    def do_GET(self):
        data = str(self.connection_id).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


source = Path('build/AltSign_patched/AppleAPI.cpp').read_text()
factory = re.search(r'web::http::client::http_client AppleAPI::gsaClient\(\)\s*\{.*?\n\}',
                    source, re.S)
assert factory, 'GSA factory not found in the compiled source'
factory = factory.group().replace('U("https://gsa.apple.com")', 'endpoint')
harness = '''
#include <cpprest/http_client.h>
#include <cassert>
using namespace web::http::client;
utility::string_t endpoint;
struct AppleAPI {
    http_client _gsaClient{endpoint};
    http_client gsaClient();
};
''' + factory + '''
int main(int argc, char** argv) {
    assert(argc == 2);
    endpoint = argv[1];
    AppleAPI api;
    auto first = api.gsaClient();
    auto second = api.gsaClient();
    assert(first.client_config().validate_certificates());
    assert(second.client_config().validate_certificates());
    auto a = first.request(web::http::methods::GET).get().extract_string().get();
    auto b = second.request(web::http::methods::GET).get().extract_string().get();
    assert(a != b); // different accepted TCP sockets, even with keep-alive enabled
}
'''
with tempfile.TemporaryDirectory() as directory, Server(('127.0.0.1', 0), Handler) as server:
    root = Path(directory)
    (root / 'test.cpp').write_text(harness)
    subprocess.run(['clang++', '-std=c++17', str(root / 'test.cpp'), '-o', str(root / 'test'),
                    '-lcpprest', '-lboost_system', '-lssl', '-lcrypto', '-lz', '-lpthread'], check=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        subprocess.run([str(root / 'test'), f'http://127.0.0.1:{server.server_port}'],
                       check=True, timeout=20)
    finally:
        server.shutdown()
        worker.join()
print('Generated GSA factory: separate TCP connections and enabled TLS validation passed')
