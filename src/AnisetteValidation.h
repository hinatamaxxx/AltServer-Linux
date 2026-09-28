#pragma once
#include <cerrno>
#include <cstdint>
#include <ctime>
#include <stdexcept>
#include <string>

namespace anisette {
inline time_t utcTimestamp(const std::string& value)
{
    // The service sends UTC (Z), independent of the host's timezone/DST.
    if (value.size() != 20) throw std::invalid_argument("Invalid anisette timestamp");
    std::tm parsed = {};
    char* end = strptime(value.c_str(), "%Y-%m-%dT%H:%M:%SZ", &parsed);
    if (!end || *end) throw std::invalid_argument("Invalid anisette timestamp");
    errno = 0;
    time_t result = timegm(&parsed);
    if (errno == EOVERFLOW) throw std::invalid_argument("Anisette timestamp overflow");
    char normalized[21] = {};
    strftime(normalized, sizeof(normalized), "%Y-%m-%dT%H:%M:%SZ", &parsed);
    if (value != normalized) throw std::invalid_argument("Invalid anisette date");
    return result;
}

inline uint64_t routingInfo(const std::string& value)
{
    if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
        throw std::invalid_argument("Invalid anisette routing info");
    return std::stoull(value);
}
}
