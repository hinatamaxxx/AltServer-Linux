#include "NativeNetworkAddress.h"
#include <assert.h>

int main(void)
{
    unsigned char data[200] = {0};
    unsigned char output[200];
    for (int i = 0; i < 256; ++i) {
        data[0] = i;
        data[1] = 2;
        assert(altserver_decode_network_address(output, sizeof(output), (char*)data, 16));
        assert(output[0] == AF_INET && output[1] == 0);
        data[1] = 30;
        assert(altserver_decode_network_address(output, sizeof(output), (char*)data, 28));
        assert(output[0] == AF_INET6 && output[1] == 0);
    }
    for (int family = 0; family < 2; ++family) {
        data[0] = family ? AF_INET6 : AF_INET;
        data[1] = 0;
        size_t size = family ? 28 : 16;
        for (size_t n = 0; n < size; ++n)
            assert(!altserver_decode_network_address(output, sizeof(output), (char*)data, n));
        assert(!altserver_decode_network_address(output, size - 1, (char*)data, size));
        assert(!altserver_decode_network_address(output, sizeof(output), (char*)data, 201));
        assert(altserver_decode_network_address(output, sizeof(output), (char*)data, 200));
    }
    assert(!altserver_decode_network_address(output, sizeof(output), NULL, 200));
    return 0;
}
