// Linux boundary for usbmux NetworkAddress data. Native sockaddr is the
// official libimobiledevice 1.4 representation; BSD addresses are accepted
// for compatibility with macOS usbmux servers. No proxy or wire rewriting.
#pragma once
#include <netinet/in.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static int altserver_decode_network_address(void* destination, size_t capacity,
                                            const char* data, uint64_t length)
{
    if (!data || length < 2 || length > capacity) return 0;
    const unsigned char* bytes = (const unsigned char*)data;
    sa_family_t family;
    memcpy(&family, data, sizeof(family));
    if (bytes[1] == 2) family = AF_INET;       // BSD sockaddr_in
    else if (bytes[1] == 30) family = AF_INET6; // Darwin sockaddr_in6
    size_t size;
    if (family == AF_INET) size = sizeof(struct sockaddr_in);
    else if (family == AF_INET6) size = sizeof(struct sockaddr_in6);
    else return 0;
    // Never use untrusted BSD sa_len to size an allocation or copy.
    if (length < size || capacity < size) return 0;
    memset(destination, 0, capacity);
    memcpy(destination, data, size);
    memcpy(destination, &family, sizeof(family));
    return 1;
}
