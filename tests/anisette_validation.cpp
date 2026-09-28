#include "AnisetteValidation.h"
#include <cassert>
#include <cstdlib>
#include <iostream>

template<class F> void rejects(F fn) {
    bool failed = false;
    try { fn(); } catch (const std::exception&) { failed = true; }
    assert(failed);
}

int main() {
    for (const char* zone : {"UTC", "Asia/Tokyo", "America/New_York"}) {
        setenv("TZ", zone, 1);
        tzset();
        assert(anisette::utcTimestamp("2026-09-15T15:00:00Z") == 1789484400);
        assert(anisette::utcTimestamp("1970-01-01T00:00:00Z") == 0);
    }
    for (const std::string value : {"", "garbage", "2026-02-30T12:00:00Z",
          "2026-09-15T15:00:00+09:00", "2026-09-15T15:00:00Zextra"})
        rejects([&] { anisette::utcTimestamp(value); });
    assert(anisette::routingInfo("18446744073709551615") == UINT64_MAX);
    assert(anisette::routingInfo("17106176") == 17106176);
    for (const std::string value : {"", "-1", "12x", " 12", "18446744073709551616"})
        rejects([&] { anisette::routingInfo(value); });
    std::cout << "UTC/timezone and routing-info regression tests passed\n";
}
