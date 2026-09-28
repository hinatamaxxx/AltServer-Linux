#pragma once
#include <stdexcept>
enum class ServerErrorCode { LostConnection };
struct ServerError : std::runtime_error {
    explicit ServerError(ServerErrorCode) : std::runtime_error("LostConnection") {}
};
