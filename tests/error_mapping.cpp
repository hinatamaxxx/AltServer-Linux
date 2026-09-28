#include <filesystem>
#include "InstallError.hpp"
#include "DeveloperDiskManager.h"
#include "ConnectionError.hpp"
#include <cassert>

int main()
{
    assert(!InstallError(static_cast<InstallErrorCode>(999)).localizedFailureReason());
    assert(!DeveloperDiskError(static_cast<DeveloperDiskErrorCode>(999)).localizedFailureReason());
    assert(!ConnectionError::errorForDebugServerError(DEBUGSERVER_E_SUCCESS, nullptr));
    assert(!ConnectionError::errorForMobileImageMounterError(MOBILE_IMAGE_MOUNTER_E_SUCCESS, nullptr));
    const auto debug = ConnectionError::errorForDebugServerError(static_cast<debugserver_error_t>(-999), nullptr);
    const auto disk = ConnectionError::errorForMobileImageMounterError(static_cast<mobile_image_mounter_error_t>(-999), nullptr);
    assert(debug && debug->code() == static_cast<int>(ConnectionErrorCode::Unknown));
    assert(disk && disk->code() == static_cast<int>(ConnectionErrorCode::Unknown));
}
