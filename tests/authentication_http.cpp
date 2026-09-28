// Production 2FA methods are appended by check-authentication-http.py.
#include "exposed_AppleAPI.hpp"
#include "AnisetteData.h"
#include "AuthenticationPolicy.h"
#include <cpprest/http_compression.h>
#include <cassert>
#include <cstdlib>

using namespace std;
using namespace utility;
using namespace web;
using namespace web::http;
using namespace web::http::client;
using namespace concurrency::streams;

string endpoint;
string StringFromWideString(string value) { return value; }
string WideStringFromString(string value) { return value; }
#define odslog(msg) do {} while (0)

// Only the network destination and unused API clients are substituted. The
// request builders, asynchronous 2FA methods and error parser are production code.
AppleAPI::AppleAPI() : _servicesClient(endpoint), _client(endpoint) {}
AppleAPI::~AppleAPI() = default;
http_client AppleAPI::gsaClient() { return http_client(endpoint); }

int main(int argc, char** argv)
{
    assert(argc == 5);
    endpoint = argv[1];
    const bool sms = string(argv[2]) == "sms";
    const int expectedCode = string(argv[3]) == "wrong-code"
        ? static_cast<int>(APIErrorCode::IncorrectVerificationCode) : atoi(argv[3]);
    const int expectedPrompts = atoi(argv[4]);
    auto data = make_shared<AnisetteData>("fixture-machine", "fixture-otp", "fixture-user",
        1, "fixture-device", "fixture-serial", "fixture-client", timeval{0, 0}, "en_US", "UTC");
    AppleAPI api;
    int prompts = 0;
    auto prompt = [&]() {
        ++prompts;
        return pplx::task_from_result(optional<string>("123456"));
    };
    int code = 0;
    try {
        const bool ok = (sms ? api.RequestSMSTwoFactorCode("fixture-id", "fixture-token", data, prompt)
                            : api.RequestTrustedDeviceTwoFactorCode("fixture-id", "fixture-token", data, prompt)).get();
        assert(ok);
    } catch (const Error& error) {
        code = error.code();
        assert(error.localizedDescription().find("fixture-token") == string::npos);
    }
    assert(code == expectedCode);
    assert(prompts == expectedPrompts);
}
