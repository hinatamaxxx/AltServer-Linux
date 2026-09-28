#include <pplx/pplxtasks.h>
#include <cassert>
#include <cstring>
#include <iostream>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <string>
#include <vector>

using idevice_t = void*;
using lockdownd_client_t = void*;
using afc_client_t = void*;
using misagent_client_t = void*;
using lockdownd_service_descriptor_t = void*;
using plist_t = void*;
enum idevice_options { IDEVICE_LOOKUP_NETWORK = 1, IDEVICE_LOOKUP_USBMUX = 2 };
constexpr int IDEVICE_E_SUCCESS = 0, LOCKDOWN_E_SUCCESS = 0, MISAGENT_E_SUCCESS = 0;
int liveHandles = 0;
int versionMode = 0;
std::string osVersion;
void allocate(void** p) { *p = new int(1); ++liveHandles; }
void release(void* p) { if (p) { delete static_cast<int*>(p); --liveHandles; } }
void idevice_free(void* p) { release(p); }
void lockdownd_client_free(void* p) { release(p); }
void afc_client_free(void* p) { release(p); }
void misagent_client_free(void* p) { release(p); }
void lockdownd_service_descriptor_free(void* p) { release(p); }
void plist_free(void* p) { release(p); }
int idevice_new_with_options(void** p, const char*, idevice_options) { allocate(p); return 0; }
int lockdownd_client_new_with_handshake(void*, void** p, const char*) { allocate(p); return 0; }
int lockdownd_start_service(void*, const char*, void** p) { allocate(p); return 0; }
int misagent_client_new(void*, void*, void** p) { allocate(p); return 0; }
int lockdownd_get_value(void*, const char*, const char* key, void** p) {
    assert(std::string(key) == "ProductVersion");
    if (versionMode == 1) return -1;
    allocate(p); return 0;
}
void plist_get_string_val(void*, char** p) { if (versionMode != 2) *p = strdup(osVersion.c_str()); }
struct OperatingSystemVersion {
    int majorVersion;
    OperatingSystemVersion(int major, int, int) : majorVersion(major) {}
    explicit OperatingSystemVersion(const char* v) : majorVersion(std::stoi(v)) {}
};
enum class ServerErrorCode { DeviceNotFound, ConnectionFailed };
struct ServerError : std::runtime_error {
    explicit ServerError(ServerErrorCode) : std::runtime_error("connection") {}
};
struct ProvisioningProfile {
    std::string bundle;
    explicit ProvisioningProfile(std::string value) : bundle(std::move(value)) {}
    std::string bundleIdentifier() const { return bundle; }
};
using Profile = std::shared_ptr<ProvisioningProfile>;
struct DeviceManager {
    std::mutex _mutex;
    std::set<std::string> installed{"app", "extension"};
    std::vector<std::string> operations;
    bool trusted = true;
    int failInstallAt = 0, installCount = 0;
    pplx::task<void> InstallProvisioningProfiles(std::vector<Profile>, std::string,
                                                std::optional<std::set<std::string>>);
    void InstallProvisioningProfile(Profile p, misagent_client_t) {
        operations.push_back("install:" + p->bundle);
        if (++installCount == failInstallAt) throw std::runtime_error("installation failure");
        installed.insert(p->bundle);
    }
    void remove(const std::string& id) {
        operations.push_back("remove:" + id);
        installed.erase(id);
        if (installed.empty()) trusted = false;
    }
    void RemoveAllFreeProvisioningProfilesExcludingBundleIdentifiers(std::set<std::string> keep, misagent_client_t) {
        auto snapshot = installed;
        for (const auto& id : snapshot) if (!keep.count(id)) remove(id);
    }
    void RemoveProvisioningProfiles(std::set<std::string> ids, misagent_client_t) {
        for (const auto& id : ids) if (installed.count(id)) remove(id);
    }
};
// PRODUCTION_REFRESH_METHOD

int main() {
    const std::vector<Profile> replacements{std::make_shared<ProvisioningProfile>("app"),
                                           std::make_shared<ProvisioningProfile>("extension")};
    for (const std::string version : {"17.7", "18.0", "27.0"}) {
        osVersion = version;
        for (bool hasActive : {false, true}) {
            DeviceManager manager;
            std::optional<std::set<std::string>> active;
            if (hasActive) active = std::set<std::string>{"app", "extension"};
            manager.InstallProvisioningProfiles(replacements, "fixture", active).get();
            assert(manager.installed == (std::set<std::string>{"app", "extension"}));
            assert(manager.trusted == (version != "17.7"));
            assert(liveHandles == 0);
        }
    }
    osVersion = "27.0";
    for (int mode : {0, 1, 2}) {
        versionMode = mode;
        DeviceManager manager;
        manager.installed.insert("inactive");
        // Even an empty active set must retain incoming replacements.
        manager.InstallProvisioningProfiles(replacements, "fixture", std::set<std::string>{}).get();
        assert(manager.trusted);
        assert(!manager.installed.count("inactive"));
        assert(manager.operations.front() == "install:app");
        assert(manager.operations.back() == "remove:inactive");
        assert(liveHandles == 0);
    }
    versionMode = 0;
    for (const std::string invalid : {"", "unknown"}) {
        osVersion = invalid;
        DeviceManager manager;
        manager.InstallProvisioningProfiles(replacements, "fixture", std::set<std::string>{}).get();
        assert(manager.trusted && liveHandles == 0);
    }
    osVersion = "27.0";
    for (int failure : {1, 2}) {
        DeviceManager manager;
        manager.failInstallAt = failure;
        bool caught = false;
        try { manager.InstallProvisioningProfiles(replacements, "fixture", std::set<std::string>{}).get(); }
        catch (const std::runtime_error&) { caught = true; }
        assert(caught && manager.trusted);
        assert(manager.installed == (std::set<std::string>{"app", "extension"}));
        assert(liveHandles == 0);
        assert(manager._mutex.try_lock()); manager._mutex.unlock();
    }
    DeviceManager manager;
    manager.InstallProvisioningProfiles({}, "fixture", std::set<std::string>{}).get();
    assert(manager.trusted && manager.operations.empty() && liveHandles == 0);
    std::cout << "14 production profile refresh cases passed: trust continuity, legacy order, inactive cleanup, unknown OS version, failures and empty request\n";
}
