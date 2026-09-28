#pragma once

#include "Error.hpp"
#include <string>

// Matches official AltSign/notarized 468313b (2026-09-17). Share the identity
// between GSA and both trusted-device/SMS 2FA requests.
namespace altserver::auth {
inline constexpr char userAgent[] =
    "AuthKit/1 (Macintosh; OS X 26.5.2) (com.apple.dt.Xcode/26.0)";

inline void requireSuccess(int status)
{
    if (status < 200 || status >= 300) {
        // Report only status, never a response body containing account data.
        throw LocalizedAPIError(status,
            "Apple's authentication service returned HTTP " + std::to_string(status) +
            " while requesting or verifying a code.");
    }
}

inline void requireServerAvailable(int status)
{
    if (status >= 500) requireSuccess(status);
}
}
