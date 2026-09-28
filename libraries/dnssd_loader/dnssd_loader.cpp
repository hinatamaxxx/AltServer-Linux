#include "dns_sd.h"
#include <cerrno>
#include <chrono>
#include <cstdio>
#include <string>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <unistd.h>

// Adapted from Ben-Diehlci/altserver-linux's argv/ctypes fix (AGPL-3.0).
// The static executable delegates dynamic Bonjour loading to Python.
// Only data travels in argv; service names never become Python source.
static const char* kAdvertiseHelper = R"PY(
import os, struct, sys
from ctypes import CDLL, POINTER, byref, c_void_p, c_uint32, c_uint16, c_int32, c_char_p, create_string_buffer
from threading import Event

status_fd = int(sys.argv[1])
try:
    flags, iface, name, regtype, domain, host, port, txt_hex = sys.argv[2:]
    # A leading marker preserves the distinction between NULL and an empty string.
    def nullable(value):
        return os.fsencode(value[1:]) if value.startswith('1') else None
    txt = bytes.fromhex(txt_hex)
    dll = CDLL('libdns_sd.so')
    dll.DNSServiceRegister.restype = c_int32
    dll.DNSServiceRegister.argtypes = [POINTER(c_void_p), c_uint32, c_uint32,
        c_char_p, c_char_p, c_char_p, c_char_p, c_uint16, c_uint16,
        c_void_p, c_void_p, c_void_p]
    ref = c_void_p()
    buf = create_string_buffer(txt) if txt else None
    rc = dll.DNSServiceRegister(byref(ref), int(flags), int(iface), nullable(name),
        nullable(regtype), nullable(domain), nullable(host), int(port), len(txt), buf, None, None)
except Exception:
    # Do not print names, TXT records or the command line.
    rc = -65537  # kDNSServiceErr_Unknown
os.write(status_fd, struct.pack('=i', rc))
os.close(status_fd)
if rc:
    sys.exit(1)
Event().wait()
)PY";

DNSServiceErrorType DNSSD_API DNSServiceRegister(
    DNSServiceRef* sdRef, DNSServiceFlags flags, uint32_t interfaceIndex,
    const char* name, const char* regtype, const char* domain, const char* host,
    uint16_t port, uint16_t txtLen, const void* txtRecord,
    DNSServiceRegisterReply callBack, void* context)
{
    (void)callBack;
    (void)context;
    if (!sdRef || !regtype || (txtLen && !txtRecord)) return kDNSServiceErr_BadParam;
    *sdRef = nullptr; // This bridge does not expose the helper's process-local handle.
    auto nullable = [](const char* value) { return value ? "1" + std::string(value) : "0"; };
    const std::string nameArg = nullable(name), typeArg = nullable(regtype);
    const std::string domainArg = nullable(domain), hostArg = nullable(host);
    const std::string flagsArg = std::to_string(flags), ifaceArg = std::to_string(interfaceIndex);
    const std::string portArg = std::to_string(port);
    std::string txtHex;
    const char hex[] = "0123456789abcdef";
    for (uint16_t i = 0; i < txtLen; ++i) {
        const auto byte = static_cast<const unsigned char*>(txtRecord)[i];
        txtHex += hex[byte >> 4];
        txtHex += hex[byte & 15];
    }

    int statusPipe[2];
    if (pipe2(statusPipe, O_CLOEXEC) != 0) return kDNSServiceErr_Unknown;
    const std::string fdArg = std::to_string(statusPipe[1]);
    const pid_t parent = getpid();
    const pid_t child = fork();
    if (child < 0) {
        close(statusPipe[0]);
        close(statusPipe[1]);
        return kDNSServiceErr_Unknown;
    }
    if (child == 0) {
        close(statusPipe[0]);
        if (prctl(PR_SET_PDEATHSIG, SIGTERM) == -1 || getppid() != parent ||
            fcntl(statusPipe[1], F_SETFD, 0) == -1) _exit(1);
        execlp("python3", "python3", "-c", kAdvertiseHelper, fdArg.c_str(),
               flagsArg.c_str(), ifaceArg.c_str(), nameArg.c_str(), typeArg.c_str(),
               domainArg.c_str(), hostArg.c_str(), portArg.c_str(), txtHex.c_str(),
               static_cast<char*>(nullptr));
        _exit(1);
    }
    close(statusPipe[1]);
    // Wait for the API result, not an arbitrary 'child is still alive' delay.
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(5);
    int32_t result = kDNSServiceErr_Unknown;
    size_t received = 0;
    while (received < sizeof(result)) {
        auto remaining = std::chrono::duration_cast<std::chrono::milliseconds>(
            deadline - std::chrono::steady_clock::now()).count();
        if (remaining <= 0) break;
        struct pollfd ready = {statusPipe[0], POLLIN, 0};
        const int count = poll(&ready, 1, static_cast<int>(remaining));
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) break;
        const ssize_t bytes = read(statusPipe[0], reinterpret_cast<char*>(&result) + received,
                                   sizeof(result) - received);
        if (bytes < 0 && errno == EINTR) continue;
        if (bytes <= 0) break;
        received += static_cast<size_t>(bytes);
    }
    close(statusPipe[0]);
    if (received != sizeof(result)) result = kDNSServiceErr_Unknown;
    if (result != kDNSServiceErr_NoError) {
        kill(child, SIGKILL);
        while (waitpid(child, nullptr, 0) < 0 && errno == EINTR) {}
        fprintf(stderr, "Bonjour registration helper failed (error %d).\n", result);
    }
    return result;
}

int DNSSD_API DNSServiceRefSockFD(DNSServiceRef sdRef)
{
    (void)sdRef;
    // Retain the existing bridge marker; the Linux caller never polls this value.
    return 0xDEADBEEF;
}
