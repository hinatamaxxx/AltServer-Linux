#pragma once
#include <algorithm>
#include <cstdint>
#include <functional>
#include <memory>
#include <type_traits>
#include <vector>
namespace pplx {
template<typename T> class task {
    std::function<T()> fn;
public:
    explicit task(std::function<T()> f) : fn(f) {}
    T get() { return fn(); }
};
template<typename F> auto create_task(F f) { return task<std::invoke_result_t<F>>(f); }
}
struct Device {};
using idevice_connection_t = void*;
using idevice_error_t = int;
constexpr int IDEVICE_E_SUCCESS = 0;
int idevice_disconnect(idevice_connection_t);
int idevice_connection_send(idevice_connection_t, const char*, uint32_t, uint32_t*);
int idevice_connection_receive_timeout(idevice_connection_t, char*, uint32_t, uint32_t*, unsigned int);
class WiredConnection {
    std::shared_ptr<Device> _device;
    idevice_connection_t _connection;
public:
    WiredConnection(std::shared_ptr<Device>, idevice_connection_t);
    ~WiredConnection();
    void Disconnect();
    pplx::task<void> SendData(std::vector<unsigned char>&);
    pplx::task<std::vector<unsigned char>> ReceiveData(int);
    std::shared_ptr<Device> device() const;
    idevice_connection_t connection() const;
};
