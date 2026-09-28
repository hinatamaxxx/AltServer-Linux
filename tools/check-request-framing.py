#!/usr/bin/env python3
"""Compile the generated ReceiveRequest method against a fake transport."""
from pathlib import Path
import re
import subprocess
import tempfile

source = Path('build/AltServer_patched/ClientConnection.cpp').read_text()
method = re.search(r'pplx::task<web::json::value> ClientConnection::ReceiveRequest\(\)\s*\{.*?\n\}',
                   source, re.S)
assert method, 'ReceiveRequest not found in the compiled source'
harness = r'''
#include <cpprest/json.h>
#include <cassert>
#include <iostream>
#include "RequestFraming.h"
enum class ServerErrorCode { InvalidRequest };
struct ServerError : std::runtime_error {
    explicit ServerError(ServerErrorCode) : std::runtime_error("InvalidRequest") {}
};
struct ClientConnection {
    std::vector<unsigned char> prefix, body;
    std::vector<int> reads;
    pplx::task<web::json::value> ReceiveRequest();
    pplx::task<std::vector<unsigned char>> ReceiveData(int size) {
        reads.push_back(size);
        return pplx::task_from_result(reads.size() == 1 ? prefix : body);
    }
};
''' + method.group() + r'''
int main() {
    for (const auto& prefix : std::vector<std::vector<unsigned char>>{
        {}, {1}, {1, 0, 0}, {1, 0, 0, 0, 0}, {0, 0, 0, 0},
        {255, 255, 255, 255}, {0, 0, 0, 128}, {1, 0, 64, 0}}) {
        ClientConnection connection;
        connection.prefix = prefix;
        bool rejected = false;
        try { connection.ReceiveRequest().get(); }
        catch (const ServerError&) { rejected = true; }
        assert(rejected);
        assert(connection.reads == std::vector<int>{4});
    }
    for (const uint32_t length : {2u, 4u * 1024 * 1024}) {
        ClientConnection connection;
        connection.prefix = {static_cast<unsigned char>(length), static_cast<unsigned char>(length >> 8),
            static_cast<unsigned char>(length >> 16), static_cast<unsigned char>(length >> 24)};
        connection.body.assign(length, ' ');
        connection.body[0] = '{'; connection.body[1] = '}';
        assert(connection.ReceiveRequest().get().is_object());
        assert(connection.reads == (std::vector<int>{4, static_cast<int>(length)}));
    }
    std::cout << "Production request framing: bounds and pre-allocation rejection passed\n";
}
'''
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / 'test.cpp').write_text(harness)
    subprocess.run(['clang++', '-std=c++17', '-Isrc', str(root / 'test.cpp'), '-o', str(root / 'test'),
                    '-lcpprest', '-lboost_system', '-lssl', '-lcrypto', '-lz', '-lpthread'], check=True)
    subprocess.run([str(root / 'test')], check=True, timeout=20)
