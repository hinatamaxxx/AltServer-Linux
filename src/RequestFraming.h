#pragma once
#include <cstdint>
#include <vector>

namespace altserver {
// AltKeeper uses the same 4 MiB JSON frame limit. IPA payloads are separate.
inline int requestSize(const std::vector<unsigned char>& bytes)
{
    if (bytes.size() != 4) return 0;
    const uint32_t size = uint32_t(bytes[0]) | (uint32_t(bytes[1]) << 8) |
                          (uint32_t(bytes[2]) << 16) | (uint32_t(bytes[3]) << 24);
    return size > 0 && size <= 4 * 1024 * 1024 ? static_cast<int>(size) : 0;
}
}
