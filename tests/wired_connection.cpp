// Compile the actual production implementation with a fake device transport.
#include "../src/WiredConnection.cpp"
#include <cassert>
#include <cstring>
#include <iostream>
int mode = 0, calls = 0;
int idevice_disconnect(idevice_connection_t) { return 0; }
int transfer(uint32_t requested, uint32_t* actual) {
    ++calls;
    assert(calls < 100);
    *actual = mode == 0 ? 0 : mode == 1 ? requested + 1 : std::min(requested, uint32_t(3));
    return mode == 3 ? -1 : 0;
}
int idevice_connection_send(idevice_connection_t, const char*, uint32_t n, uint32_t* actual) {
    return transfer(n, actual);
}
int idevice_connection_receive_timeout(idevice_connection_t, char* data, uint32_t n, uint32_t* actual, unsigned int) {
    std::memset(data, 'x', n);
    return transfer(n, actual);
}
template<typename F> void rejects(F f) {
    calls = 0;
    bool failed = false;
    try { f(); } catch (const ServerError&) { failed = true; }
    assert(failed);
}
int main() {
    WiredConnection connection(std::make_shared<Device>(), nullptr);
    std::vector<unsigned char> data(10, 'x');
    for (int invalid : {0, 1, 3}) {
        mode = invalid;
        rejects([&] { connection.SendData(data).get(); });
        rejects([&] { connection.ReceiveData(10).get(); });
    }
    rejects([&] { connection.ReceiveData(-1).get(); });
    mode = 2; calls = 0;
    connection.SendData(data).get();
    assert(calls == 4);
    calls = 0;
    assert(connection.ReceiveData(10).get() == data);
    assert(calls == 4);
    assert(connection.ReceiveData(0).get().empty());
    std::cout << "Production wired transport regression tests passed\n";
}
